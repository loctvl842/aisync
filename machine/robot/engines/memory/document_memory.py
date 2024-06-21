from langchain.text_splitter import CharacterTextSplitter
from langchain_community.document_loaders import TextLoader
from langchain_postgres.vectorstores import PGVector


class DocumentMemory:
    def __init__(self, config=None, embedder=None):
        self.splitted_documents = []
        self.vectorstore = None
        self.config = config or {}
        self.connection_string = "postgresql+psycopg://postgres:postgres@localhost:5432/aisync"
        self.embedder = embedder

    def read(self, file_path):
        """Loads and processes the document specified by file_path."""
        documents = TextLoader(file_path).load()

        # Split the document into smaller chunks
        text_splitter = CharacterTextSplitter(chunk_size=1000, chunk_overlap=0)
        self.splitted_documents = text_splitter.split_documents(documents)

    async def similarity_search(self, query, k=4):

        if self.vectorstore is None:

            # Create the PGVector store

            self.vectorstore = await PGVector.afrom_documents(
                embedding=self.embedder,
                documents=self.splitted_documents,
                collection_name="document_collection",  # Choose a collection name
                connection=self.connection_string,
                pre_delete_collection=True,
            )
        vectorized_input = self.embedder.embed_query(text=query)

        relevant_docs = await self.vectorstore.asimilarity_search_by_vector(vectorized_input, k)
        res = "## Relevant knowledge:\n"

        counter = 1
        for doc in relevant_docs:
            res += f"- Document {counter}: {doc.page_content}\n\n"
            counter += 1

        return res
