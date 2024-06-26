from langchain.text_splitter import CharacterTextSplitter
from .universal_loader import UniversalLoader

from machine.models import DocCollection

from core.logger import syslog
from core.settings import settings

from typing import Dict
from core.db.session import Dialect, sessions
from sqlalchemy import select
from uuid import uuid4


    
class DocumentMemory:
    def __init__(self, config=None, embedder=None):
        self.document_loader = UniversalLoader()
        self.vectorstore = None
        self.config = config or {}
        self.splitted_documents = []
        # self.connection_string = settings.LANGCHAIN_PGVECTOR_URI
        self.embedder = embedder

    def read(self, file_path,chunk_size=800,chunk_overlap=0):
        """Loads and processes the document specified by file_path."""
        syslog.info("Loading documents - 1")
        loader = self.document_loader.choose_loader()
        documents = loader(file_path).load()
        syslog.info("Loading documents - 2")
        # Split the document into smaller chunks
        text_splitter = CharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
        docs = text_splitter.split_documents(documents)
        all_content = [doc.page_content for doc in docs]
        syslog.info(len(all_content))
        syslog.info("Loading documents - 3")
        syslog.info(f'{type(all_content)}')
        
        all_embeddings = self.embedder.embed_documents(texts=list(all_content))
        syslog.info("Loading documents - 4")

        index = 0
        for doc in docs:
            self.splitted_documents.append({
                "doc_metadata": doc.metadata,
                "page_content": doc.page_content,
                "embedding": all_embeddings[index]
            })
            index += 1

    async def add_docs(self) -> None:
        if len(self.splitted_documents) == 0:
            return
        sessions[Dialect.PGVECTOR].set_session_context(str(uuid4()))
        async with sessions[Dialect.PGVECTOR].session() as session:
            for doc in self.splitted_documents:
                # syslog.info(f'{doc}')
                session.add(DocCollection(doc_metadata=doc["doc_metadata"], page_content=doc["page_content"], embedding=doc["embedding"], id=uuid4()))
            await session.commit()
        self.splitted_documents = []

    async def similarity_search(self, vectorized_input, k = 4) -> str:
        await self.add_docs()
        res = "## Relevant knowledge:\n\n"
        # DB Session for similarity search
        # syslog.info(f'{vectorized_input}')
        sessions[Dialect.PGVECTOR].set_session_context(str(uuid4()))
        async with sessions[Dialect.PGVECTOR].session() as session:
            # Top self._top_matches similarity search neighbors from input and output tables
            doc_match = await session.scalars(
                select(DocCollection).order_by(DocCollection.embedding.l2_distance(vectorized_input)).limit(k)
            )
            counter = 1
            for doc in doc_match:
                res += f"- Document {counter}: {doc.page_content}\n\n"
                counter += 1
            await session.commit()
        return res