# Initialize PGVector
import asyncio

from machine.robot.aisync.engines.embedder import get_embedder_object
from machine.robot.aisync.store.pgvector import PGVector


def main_sync():
    embedder = get_embedder_object(("EmbedderOpenAI", {"dimensions": 768}))

    pgvector = PGVector(
        schema="my_schema_1",
        embedder=embedder,  # Replace with your actual embedder instance
        connection="postgresql+psycopg2://postgres:thangcho@localhost:5432/test",
        embedding_length=768,
    )

    # Create a new collection
    pgvector.create_collection(name="my_collection", cmetadata={"description": "My collection metadata"})
    with pgvector.session_maker() as session:
        c = pgvector.get_collection("my_collection", session)

        # pgvector.add_documents("my_collection", ["what is this", "I'm fine"], ids=["3", "4"])
        pgvector.add_documents("my_collection", ["what is this", "I'm fine"], ids=["3", "4"], metadatas=[{"id": 3}, {"id": 4}])
        results = pgvector.similarity_search("my_collection", "what?", 2)
        for e, s in results:
            print(e.document, s)


async def main_async():
    embedder = get_embedder_object(("EmbedderOpenAI", {"dimensions": 768}))

    pgvector = PGVector(
        schema="my_schema_1",
        embedder=embedder,  # Replace with your actual embedder instance
        connection="postgresql+asyncpg://postgres:thangcho@localhost:5432/test",
        embedding_length=768,
        async_mode=True,  # Enable async mode
    )

    # Create a new collection asynchronously
    await pgvector.acreate_collection(name="my_collection", cmetadata={"description": "My collection metadata"})

    # Access the collection asynchronously
    async with pgvector.session_maker() as session:
        c = await pgvector.aget_collection("my_collection", session)
        print(c.name, c.cmetadata)
    await pgvector.aadd_documents("my_collection", ["what is this", "I'm fine"], ids=["1", "2"], metadatas=[{"id": 1}, {"id": 2}])
    results = await pgvector.asimilarity_search("my_collection", "what i this", k=2, filter={"id": {"$in": ["1", "2"]}})
    for e, s in results:
        print(e.id, e.document, s)


if __name__ == "__main__":
    # main_sync()
    asyncio.run(main_async())
