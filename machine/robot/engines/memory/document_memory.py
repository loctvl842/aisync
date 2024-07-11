from uuid import uuid4

from langchain.text_splitter import CharacterTextSplitter
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert

from core.db.session import Dialect, sessions
from core.db.transactional import Transactional
from core.db.utils import SessionContext
from core.logger import syslog
from machine.robot.models import DocCollection

from .universal_loader import UniversalLoader


class DocumentMemory:
    def __init__(self, config=None, embedder=None):
        self.document_loader = UniversalLoader()
        self.vectorstore = None
        self.config = config or {}
        self.splitted_documents = []
        self.embedder = embedder

    def read(self, suit: str, file_path: str, chunk_size=800, chunk_overlap=0):
        """Loads and processes the document specified by file_path."""

        loader = self.document_loader.choose_loader()
        if loader is None:
            syslog.error(f"Unsupported file type: {self.document_loader.file_type}")
            raise ValueError(f"Unsupported file type: {self.document_loader.file_type}")

        documents = loader(file_path).load()

        # get the file name from file path
        file_name = file_path.split("/")[-1]

        syslog.info(f"Processing document: {file_name}")
        # Split the document into smaller chunks
        text_splitter = CharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
        docs = text_splitter.split_documents(documents)
        all_content = [doc.page_content for doc in docs]

        all_embeddings = self.embedder.embed_documents(texts=list(all_content))

        for index, doc in enumerate(docs):
            key = f"{suit}_{file_name}_chunk{index}"

            self.splitted_documents.append(
                {
                    "key": key,
                    "doc_metadata": doc.metadata,
                    "page_content": doc.page_content,
                    "embedding": all_embeddings[index],
                    "document_name": file_name,
                }
            )

    @SessionContext(dialect=Dialect.PGVECTOR)
    @Transactional(dialect=Dialect.PGVECTOR)
    async def add_docs(self) -> None:
        if len(self.splitted_documents) == 0:
            return
        sessions[Dialect.PGVECTOR].set_session_context(str(uuid4()))
        session = sessions[Dialect.PGVECTOR].session

        stmt = (
            insert(DocCollection)
            .values(self.splitted_documents)
            .on_conflict_do_update(
                index_elements=["key"],
                set_={col: getattr(insert(DocCollection).excluded, col) for col in self.splitted_documents[0]},
            )
            .returning(DocCollection)
        )
        await session.execute(stmt)
        self.splitted_documents = []

    async def similarity_search(self, vectorized_input, document_name, k=4) -> str:
        await self.add_docs()
        res = "## Relevant knowledge:\n\n"
        # DB Session for similarity search
        sessions[Dialect.PGVECTOR].set_session_context(str(uuid4()))
        async with sessions[Dialect.PGVECTOR].session() as session:
            # Top self._top_matches similarity search neighbors from input and output tables
            doc_match = await session.scalars(
                select(DocCollection)
                .where(DocCollection.document_name.in_(document_name))
                .order_by(DocCollection.embedding.l2_distance(vectorized_input))
                .limit(k)
            )
            counter = 1
            for doc in doc_match:
                res += f"- Document {counter}: {doc.page_content}\n\n"
                counter += 1
            await session.commit()
        return res
