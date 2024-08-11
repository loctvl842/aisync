import asyncio
import contextlib
import enum
from typing import Any, AsyncGenerator, Generator, List, Optional, Sequence, Tuple, Union
from typing import (
    cast as typing_cast,
)
from uuid import uuid4

import sqlalchemy
from sqlalchemy import ForeignKey, Index, SQLColumnExpression, String, cast, create_engine, func, select, text
from sqlalchemy.dialects.postgresql import JSONB, JSONPATH, UUID, insert
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.future import Engine
from sqlalchemy.orm import DeclarativeBase, Session, mapped_column, relationship, scoped_session, sessionmaker


class Base(DeclarativeBase): ...


_classes: Any = None

COMPARISONS_TO_NATIVE = {
    "$eq": "==",
    "$ne": "!=",
    "$lt": "<",
    "$lte": "<=",
    "$gt": ">",
    "$gte": ">=",
}

SPECIAL_CASED_OPERATORS = {
    "$in",
    "$nin",
    "$between",
    "$exists",
}

TEXT_OPERATORS = {
    "$like",
    "$ilike",
}

LOGICAL_OPERATORS = {"$and", "$or", "$not"}

SUPPORTED_OPERATORS = set(COMPARISONS_TO_NATIVE).union(TEXT_OPERATORS).union(LOGICAL_OPERATORS).union(SPECIAL_CASED_OPERATORS)


class DistanceStrategy(str, enum.Enum):
    """Enumerator of the Distance strategies."""

    EUCLIDEAN = "l2"
    COSINE = "cosine"
    MAX_INNER_PRODUCT = "inner"


DEFAULT_DISTANCE_STRATEGY = DistanceStrategy.COSINE


def _get_embedding_collection_store(schema: Optional[str] = None, vector_dimension: Optional[int] = None):
    global _classes
    if _classes is not None:
        return _classes

    from pgvector.sqlalchemy import Vector  # type: ignore

    class Collection(Base):
        __tablename__ = "collections"
        __allow_unmapped__ = True

        id = mapped_column(UUID, primary_key=True, default=uuid4)
        name = mapped_column(String, nullable=False, unique=True)
        cmetadata = mapped_column(JSONB)

        embeddings = relationship(
            "Embedding",
            back_populates="collection",
            passive_deletes=True,
        )

        __table_args__ = ({"schema": schema},)

        @classmethod
        def get_by_name(cls, session: Session, name: str) -> Optional["Collection"]:
            return session.query(cls).filter(typing_cast(mapped_column, cls.name) == name).first()

        @classmethod
        async def aget_by_name(cls, session: AsyncSession, name: str) -> Optional["Collection"]:
            return (await session.execute(select(Collection).where(typing_cast(mapped_column, cls.name) == name))).scalars().first()

        @classmethod
        def get_or_create(
            cls,
            session: Session,
            name: str,
            cmetadata: Optional[dict] = None,
        ) -> Tuple["Collection", bool]:
            """Get or create a collection.
            Returns:
                 Where the bool is True if the collection was created.
            """  # noqa: E501
            created = False
            collection = cls.get_by_name(session, name)
            if collection:
                return collection, created

            collection = cls(name=name, cmetadata=cmetadata)
            session.add(collection)
            session.commit()
            created = True
            return collection, created

        @classmethod
        async def aget_or_create(
            cls,
            session: AsyncSession,
            name: str,
            cmetadata: Optional[dict] = None,
        ) -> Tuple["Collection", bool]:
            """
            Get or create a collection.
            Returns [Collection, bool] where the bool is True if the collection was created.
            """  # noqa: E501
            created = False
            collection = await cls.aget_by_name(session, name)
            if collection:
                return collection, created

            collection = cls(name=name, cmetadata=cmetadata)
            session.add(collection)
            await session.commit()
            created = True
            return collection, created

    class Embedding(Base):
        __tablename__ = "embeddings"
        __allow_unmapped__ = True

        id = mapped_column(String, nullable=True, primary_key=True, index=True, unique=True)

        collection_id = mapped_column(
            UUID(as_uuid=True),
            ForeignKey(f"{schema}.{Collection.__tablename__}.id" if schema else f"{Collection.__tablename__}.id"),
        )
        collection = relationship("Collection", back_populates="embeddings")

        embedding: Vector = mapped_column(Vector(vector_dimension))
        document = mapped_column(String, nullable=True)
        cmetadata = mapped_column(JSONB, nullable=True)

        __table_args__ = (
            Index(
                "ix_cmetadata_gin",
                "cmetadata",
                postgresql_using="gin",
                postgresql_ops={"cmetadata": "jsonb_path_ops"},
            ),
            {"schema": schema},
        )

    _classes = (Collection, Embedding)

    return _classes


class PGVector:
    def __init__(
        self,
        schema: str,
        embedder,
        *,
        connection: Union[None, Engine, AsyncEngine, str] = None,
        embedding_length: Optional[int] = None,
        distance_strategy: DistanceStrategy = DEFAULT_DISTANCE_STRATEGY,
        engine_args: Optional[dict[str, Any]] = None,
        async_mode: bool = False,
    ):
        self.async_mode = async_mode
        self.embedder = embedder
        self._embedding_length = embedding_length
        self._distance_strategy = distance_strategy
        self._schema = schema
        self._async_engine: Optional[AsyncEngine] = None
        self._async_init = False

        if isinstance(connection, str):
            if async_mode:
                self._async_engine = create_async_engine(connection, **(engine_args or {}))
            else:
                self._engine = create_engine(url=connection, **(engine_args or {}))
        elif isinstance(connection, Engine):
            self.async_mode = False
            self._engine = connection
        elif isinstance(connection, AsyncEngine):
            self.async_mode = True
            self._async_engine = connection
        else:
            raise ValueError(
                "connection should be a connection string or an instance of " "sqlalchemy.engine.Engine or sqlalchemy.ext.asyncio.engine.AsyncEngine"
            )

        self.session_maker: Union[scoped_session, async_sessionmaker]
        if self.async_mode:
            self.session_maker = async_sessionmaker(bind=self._async_engine)
        else:
            self.session_maker = scoped_session(sessionmaker(bind=self._engine))

        if not self.async_mode:
            self.__post_init__()

    def __post_init__(self):
        self.Collection, self.Embedding = _get_embedding_collection_store(self._schema, self._embedding_length)

        self._create_vector_extension()
        self._create_schema_if_not_exists()
        self._create_tables_if_not_exists()

    async def __apost_init__(self):
        async with asyncio.Lock():
            if self._async_init:
                return
            self._async_init = True

            self.Collection, self.Embedding = _get_embedding_collection_store(self._schema, self._embedding_length)

            await self._acreate_vector_extension()
            await self._acreate_schema_if_not_exists()
            await self._acreate_tables_if_not_exists()

    def _create_vector_extension(self):
        """Synchronously create the pgvector extension in the database if it does not already exist."""
        with self._engine.connect() as connection:
            connection.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
            connection.commit()

    async def _acreate_vector_extension(self):
        """Asynchronously create the pgvector extension in the database if it does not already exist."""
        async with self._async_engine.connect() as connection:
            await connection.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
            await connection.commit()

    def _create_schema_if_not_exists(self):
        """Synchronously create the schema in the database if it does not already exist."""
        with self._engine.connect() as connection:
            connection.execute(text(f"CREATE SCHEMA IF NOT EXISTS {self._schema}"))
            connection.commit()

    async def _acreate_schema_if_not_exists(self):
        """Asynchronously create the schema in the database if it does not already exist."""
        async with self._async_engine.connect() as connection:
            await connection.execute(text(f"CREATE SCHEMA IF NOT EXISTS {self._schema}"))
            await connection.commit()

    def _create_tables_if_not_exists(self):
        """Synchronously create the tables in the schema if they do not already exist."""
        self._create_schema_if_not_exists()
        with self._engine.begin() as connection:
            Base.metadata.create_all(bind=connection)

    async def _acreate_tables_if_not_exists(self):
        """Asynchronously create the tables in the schema if they do not already exist."""
        await self._acreate_schema_if_not_exists()
        async with self._async_engine.begin() as connection:
            await connection.run_sync(lambda conn: Base.metadata.create_all(bind=conn))

    def create_collection(self, name: str, cmetadata: Optional[dict] = None):
        """Synchronously create a new collection in the database."""
        with self._make_sync_session() as session:
            try:
                self.Collection.get_or_create(session, name, cmetadata)
                session.commit()
            except IntegrityError:
                session.rollback()
                raise ValueError(f"Collection with name {name} already exists.")

    async def acreate_collection(self, name: str, cmetadata: Optional[dict] = None):
        """Asynchronously create a new collection in the database."""
        await self.__apost_init__()  # Lazy async init
        async with self._make_async_session() as session:
            try:
                await self.Collection.aget_or_create(session, name, cmetadata)
                await session.commit()
            except IntegrityError:
                await session.rollback()
                raise ValueError(f"Collection with name {name} already exists.")

    def get_collection(self, collection_name: str, session: Session) -> Any:
        assert not self._async_engine, "This method must be called without async_mode"
        return self.Collection.get_by_name(session, collection_name)

    async def aget_collection(self, collection_name: str, session: AsyncSession) -> Any:
        assert self._async_engine, "This method must be called with async_mode"
        await self.__apost_init__()  # Lazy async init
        return await self.Collection.aget_by_name(session, collection_name)

    def delete_collection(self, collection_id: str):
        """Synchronously delete a collection from the database."""
        with self._make_sync_session() as session:
            try:
                collection = session.query(self.Collection).filter_by(id=collection_id).first()
                if collection:
                    session.delete(collection)
                    session.commit()
                else:
                    raise ValueError(f"Collection with id {collection_id} does not exist.")
            except Exception as e:
                session.rollback()
                raise e

    async def adelete_collection(self, collection_id: str):
        """Asynchronously delete a collection from the database."""
        await self.__apost_init__()  # Lazy async init
        async with self._make_async_session() as session:
            try:
                collection = await session.get(self.Collection, collection_id)
                if collection:
                    await session.delete(collection)
                    await session.commit()
                else:
                    raise ValueError(f"Collection with id {collection_id} does not exist.")
            except Exception as e:
                await session.rollback()
                raise e

    @contextlib.contextmanager
    def _make_sync_session(self) -> Generator[Session, None, None]:
        """Make an async session."""
        if self.async_mode:
            raise ValueError("Attempting to use a sync method in when async mode is turned on. " "Please use the corresponding async method instead.")
        with self.session_maker() as session:
            yield typing_cast(Session, session)

    @contextlib.asynccontextmanager
    async def _make_async_session(self) -> AsyncGenerator[AsyncSession, None]:
        """Make an async session."""
        if not self.async_mode:
            raise ValueError(
                "Attempting to use an async method in when sync mode is turned on. " "Please use the corresponding async method instead."
            )
        async with self.session_maker() as session:
            yield typing_cast(AsyncSession, session)

    def add_documents(
        self,
        collection_name: str,
        documents: Sequence[str],
        metadatas: Optional[List[dict]] = None,
        *,
        ids: Optional[List[str]] = None,
    ):
        assert not self._async_engine, "This method must be called with sync_mode"
        if ids is None:
            ids = [str(uuid4()) for _ in documents]

        if not metadatas:
            metadatas = [{}] * len(documents)

        embeddings = self.embedder.embed_documents(list(documents))

        with self._make_sync_session() as session:  # type: ignore[arg-type]
            collection = self.get_collection(collection_name, session)
            if not collection:
                raise ValueError("Collection not found")
            data = [
                {
                    "id": id,
                    "collection_id": collection.id,
                    "embedding": embedding,
                    "document": document,
                    "cmetadata": metadata or {},
                }
                for id, embedding, document, metadata in zip(ids, embeddings, documents, metadatas)
            ]
            stmt = insert(self.Embedding).values(data)
            on_conflict_stmt = stmt.on_conflict_do_update(
                index_elements=["id"],
                set_={
                    "embedding": stmt.excluded.embedding,
                    "document": stmt.excluded.document,
                    "cmetadata": stmt.excluded.cmetadata,
                },
            )
            session.execute(on_conflict_stmt)
            session.commit()
        return ids

    async def aadd_documents(
        self,
        collection_name: str,
        documents: Sequence[str],
        metadatas: Optional[List[dict]] = None,
        *,
        ids: Optional[List[str]] = None,
    ):
        await self.__apost_init__()  # Lazy async init
        if ids is None:
            ids = [str(uuid4()) for _ in documents]

        if not metadatas:
            metadatas = [{}] * len(documents)

        embeddings = self.embedder.embed_documents(list(documents), self._embedding_length)

        async with self._make_async_session() as session:  # type: ignore[arg-type]
            collection = await self.aget_collection(collection_name, session)
            if not collection:
                raise ValueError("Collection not found")
            data = [
                {
                    "id": id,
                    "collection_id": collection.id,
                    "embedding": embedding,
                    "document": document,
                    "cmetadata": metadata or {},
                }
                for id, embedding, document, metadata in zip(ids, embeddings, documents, metadatas)
            ]
            stmt = insert(self.Embedding).values(data)
            on_conflict_stmt = stmt.on_conflict_do_update(
                index_elements=["id"],
                set_={
                    "embedding": stmt.excluded.embedding,
                    "document": stmt.excluded.document,
                    "cmetadata": stmt.excluded.cmetadata,
                },
            )
            await session.execute(on_conflict_stmt)
            await session.commit()
        return ids

    def similarity_search(
        self,
        collection_name: str,
        query: str,
        k: int = 4,
        filter: Optional[dict] = None,
        **kwargs: Any,
    ):
        assert not self._async_engine, "This method must be called without async_mode"
        embedding = self.embedder.embed_query(text=query)
        results = self.__query_collection(collection_name=collection_name, embedding=embedding, k=k, filter=filter)
        return results

    async def asimilarity_search(
        self,
        collection_name: str,
        query: str,
        k: int = 4,
        filter: Optional[dict] = None,
        **kwargs: Any,
    ):
        await self.__apost_init__()  # Lazy async init
        embedding = self.embedder.embed_query(text=query)
        results = await self.__aquery_collection(collection_name=collection_name, embedding=embedding, k=k, filter=filter)
        return results

    @property
    def distance_strategy(self) -> Any:
        if self._distance_strategy == DistanceStrategy.EUCLIDEAN:
            return self.Embedding.embedding.l2_distance
        elif self._distance_strategy == DistanceStrategy.COSINE:
            return self.Embedding.embedding.cosine_distance
        elif self._distance_strategy == DistanceStrategy.MAX_INNER_PRODUCT:
            return self.Embedding.embedding.max_inner_product
        else:
            raise ValueError(
                f"Got unexpected value for distance: {self._distance_strategy}. "
                f"Should be one of {', '.join([ds.value for ds in DistanceStrategy])}."
            )

    def __query_collection(
        self,
        collection_name: str,
        embedding: List[float],
        k: int = 4,
        filter: Optional[dict] = None,
    ):
        """Query the collection."""
        with self._make_sync_session() as session:  # type: ignore[arg-type]
            collection = self.get_collection(collection_name, session)
            if not collection:
                raise ValueError("Collection not found")

            filter_by = [self.Embedding.collection_id == collection.id]
            if filter:
                filter_clauses = self._create_filter_clause(filter)
                if filter_clauses is not None:
                    filter_by.append(filter_clauses)

            results: Sequence[Any] = (
                session.query(self.Embedding, self.distance_strategy(embedding).label("distance"))
                .filter(*filter_by)
                .order_by(sqlalchemy.asc("distance"))
                .join(self.Collection, self.Embedding.collection_id == self.Collection.id)
                .limit(k)
                .all()
            )

            return results

    async def __aquery_collection(
        self,
        collection_name: str,
        embedding: List[float],
        k: int = 4,
        filter: Optional[dict] = None,
    ):
        """Query the collection."""
        async with self._make_async_session() as session:
            collection = await self.aget_collection(collection_name, session)
            if not collection:
                raise ValueError("Collection not found")

            filter_by = [self.Embedding.collection_id == collection.id]
            if filter:
                filter_clauses = self._create_filter_clause(filter)
                if filter_clauses is not None:
                    filter_by.append(filter_clauses)

            stmt = (
                select(self.Embedding, self.distance_strategy(embedding).label("distance"))
                .filter(*filter_by)
                .order_by(sqlalchemy.asc("distance"))
                .join(self.Collection, self.Embedding.collection_id == self.Collection.id)
                .limit(k)
            )
            results: Sequence[Any] = (await session.execute(stmt)).all()

            return results

    def _create_filter_clause(self, filters: Any) -> Any:
        """Convert LangChain IR filter representation to matching SQLAlchemy clauses.

        At the top level, we still don't know if we're working with a field
        or an operator for the keys. After we've determined that we can
        call the appropriate logic to handle filter creation.

        Args:
            filters: Dictionary of filters to apply to the query.

        Returns:
            SQLAlchemy clause to apply to the query.
        """
        if not isinstance(filters, dict):
            raise ValueError(f"Invalid type: Expected a dictionary but got type: {type(filters)}")

        if len(filters) == 1:
            key, value = list(filters.items())[0]
            if key.startswith("$"):
                # Then it's an operator
                if key.lower() not in ["$and", "$or", "$not"]:
                    raise ValueError(f"Invalid filter condition. Expected $and, $or or $not " f"but got: {key}")
            else:
                # Then it's a field
                return self._handle_field_filter(key, filters[key])

            if key.lower() == "$and":
                if not isinstance(value, list):
                    raise ValueError(f"Expected a list, but got {type(value)} for value: {value}")
                and_ = [self._create_filter_clause(el) for el in value]
                if len(and_) > 1:
                    return sqlalchemy.and_(*and_)
                elif len(and_) == 1:
                    return and_[0]
                else:
                    raise ValueError("Invalid filter condition. Expected a dictionary " "but got an empty dictionary")
            elif key.lower() == "$or":
                if not isinstance(value, list):
                    raise ValueError(f"Expected a list, but got {type(value)} for value: {value}")
                or_ = [self._create_filter_clause(el) for el in value]
                if len(or_) > 1:
                    return sqlalchemy.or_(*or_)
                elif len(or_) == 1:
                    return or_[0]
                else:
                    raise ValueError("Invalid filter condition. Expected a dictionary " "but got an empty dictionary")
            elif key.lower() == "$not":
                if isinstance(value, list):
                    not_conditions = [self._create_filter_clause(item) for item in value]
                    not_ = sqlalchemy.and_(*[sqlalchemy.not_(condition) for condition in not_conditions])
                    return not_
                elif isinstance(value, dict):
                    not_ = self._create_filter_clause(value)
                    return sqlalchemy.not_(not_)
                else:
                    raise ValueError(f"Invalid filter condition. Expected a dictionary " f"or a list but got: {type(value)}")
            else:
                raise ValueError(f"Invalid filter condition. Expected $and, $or or $not " f"but got: {key}")
        elif len(filters) > 1:
            # Then all keys have to be fields (they cannot be operators)
            for key in filters.keys():
                if key.startswith("$"):
                    raise ValueError(f"Invalid filter condition. Expected a field but got: {key}")
            # These should all be fields and combined using an $and operator
            and_ = [self._handle_field_filter(k, v) for k, v in filters.items()]
            if len(and_) > 1:
                return sqlalchemy.and_(*and_)
            elif len(and_) == 1:
                return and_[0]
            else:
                raise ValueError("Invalid filter condition. Expected a dictionary " "but got an empty dictionary")
        else:
            raise ValueError("Got an empty dictionary for filters.")

    def _handle_field_filter(
        self,
        field: str,
        value: Any,
    ) -> SQLColumnExpression:
        """Create a filter for a specific field.

        Args:
            field: name of field
            value: value to filter
                If provided as is then this will be an equality filter
                If provided as a dictionary then this will be a filter, the key
                will be the operator and the value will be the value to filter by

        Returns:
            sqlalchemy expression
        """
        if field.startswith("$"):
            raise ValueError(f"Invalid filter condition. Expected a field but got an operator: " f"{field}")

        # Allow [a-zA-Z0-9_], disallow $ for now until we support escape characters
        if not field.isidentifier():
            raise ValueError(f"Invalid field name: {field}. Expected a valid identifier.")

        if isinstance(value, dict):
            # This is a filter specification
            if len(value) != 1:
                raise ValueError(
                    "Invalid filter condition. Expected a value which "
                    "is a dictionary with a single key that corresponds to an operator "
                    f"but got a dictionary with {len(value)} keys. The first few "
                    f"keys are: {list(value.keys())[:3]}"
                )
            operator, filter_value = list(value.items())[0]
            # Verify that that operator is an operator
            if operator not in SUPPORTED_OPERATORS:
                raise ValueError(f"Invalid operator: {operator}. " f"Expected one of {SUPPORTED_OPERATORS}")
        else:  # Then we assume an equality operator
            operator = "$eq"
            filter_value = value

        if operator in COMPARISONS_TO_NATIVE:
            # Then we implement an equality filter
            # native is trusted input
            native = COMPARISONS_TO_NATIVE[operator]
            return func.jsonb_path_match(
                self.Embedding.cmetadata,
                cast(f"$.{field} {native} $value", JSONPATH),
                cast({"value": filter_value}, JSONB),
            )
        elif operator == "$between":
            # Use AND with two comparisons
            low, high = filter_value

            lower_bound = func.jsonb_path_match(
                self.Embedding.cmetadata,
                cast(f"$.{field} >= $value", JSONPATH),
                cast({"value": low}, JSONB),
            )
            upper_bound = func.jsonb_path_match(
                self.Embedding.cmetadata,
                cast(f"$.{field} <= $value", JSONPATH),
                cast({"value": high}, JSONB),
            )
            return sqlalchemy.and_(lower_bound, upper_bound)
        elif operator in {"$in", "$nin", "$like", "$ilike"}:
            # We'll do force coercion to text
            if operator in {"$in", "$nin"}:
                for val in filter_value:
                    if not isinstance(val, (str, int, float)):
                        raise NotImplementedError(f"Unsupported type: {type(val)} for value: {val}")

                    if isinstance(val, bool):  # b/c bool is an instance of int
                        raise NotImplementedError(f"Unsupported type: {type(val)} for value: {val}")

            queried_field = self.Embedding.cmetadata[field].astext

            if operator in {"$in"}:
                return queried_field.in_([str(val) for val in filter_value])
            elif operator in {"$nin"}:
                return ~queried_field.in_([str(val) for val in filter_value])
            elif operator in {"$like"}:
                return queried_field.like(filter_value)
            elif operator in {"$ilike"}:
                return queried_field.ilike(filter_value)
            else:
                raise NotImplementedError()
        elif operator == "$exists":
            if not isinstance(filter_value, bool):
                raise ValueError("Expected a boolean value for $exists " f"operator, but got: {filter_value}")
            condition = func.jsonb_exists(
                self.Embedding.cmetadata,
                field,
            )
            return condition if filter_value else ~condition
        else:
            raise NotImplementedError()
