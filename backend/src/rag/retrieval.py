from collections.abc import Sequence

from openai import OpenAI
from sqlmodel import select

from database import open_session
from database.models import Chunk


class Retriever:
    def __init__(self, api_key: str, model: str = "text-embedding-3-small"):
        self.client = OpenAI(api_key=api_key)
        self.model = model

    def create_query_embedding(self, query: str) -> list[float]:
        response = self.client.embeddings.create(
            model=self.model,
            input=query,
            encoding_format="float"
        )
        return response.data[0].embedding

    def find_relevant_chunks(self, query: str, k: int = 3) -> Sequence[Chunk]:
        query_embedding = self.create_query_embedding(query)

        with open_session() as session:
            chunks = session.exec(
                select(Chunk)
                .where(Chunk.is_embedded == True)
                .order_by(Chunk.embedding.l2_distance(query_embedding))
                .limit(k)
            ).all()

            return chunks

    def format_context(self, chunks: Sequence[Chunk]) -> str:
        context = "\n\n".join(
            f"""=== Dokumentenauszug ===
Quelle: {chunk.chunk_title}
Seite: {chunk.page_number + 1}

{chunk.chunk_content}

=================="""
            for chunk in chunks
        )
        return context
