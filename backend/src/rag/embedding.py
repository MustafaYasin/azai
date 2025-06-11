
from openai import OpenAI
from sqlmodel import select

from database import open_session
from database.models import Chunk


class Embedder:
    def __init__(self, api_key: str, model: str = "text-embedding-3-small"):
        self.client = OpenAI(api_key=api_key)
        self.model = model

    def create_embedding(self, text: str) -> list[float]:
        response = self.client.embeddings.create(
            model=self.model,
            input=text,
            encoding_format="float"
        )
        return response.data[0].embedding

    def process_pending_embeddings(self, batch_size: int = 100) -> int:
        total_processed = 0

        with open_session() as session:
            chunks = session.exec(
                select(Chunk).where(Chunk.is_embedded == False)
            ).all()

            if not chunks:
                return 0

            total_chunks = len(chunks)

            for i in range(0, total_chunks, batch_size):
                batch = chunks[i:i + batch_size]
                try:
                    texts = [chunk.chunk_content for chunk in batch]

                    response = self.client.embeddings.create(
                        model=self.model,
                        input=texts,
                        encoding_format="float"
                    )

                    for chunk, embedding_data in zip(batch, response.data, strict=False):
                        chunk.embedding = embedding_data.embedding
                        chunk.is_embedded = True

                    session.commit()
                    total_processed += len(batch)

                except Exception as e:
                    session.rollback()
                    raise Exception(f"Error processing batch: {e!s}")

        return total_processed

    def calculate_embedding_cost(self, text_list: list[str]) -> tuple[int, float]:
        import tiktoken
        enc = tiktoken.encoding_for_model(self.model)
        total_tokens = sum(len(enc.encode(text)) for text in text_list)
        cost = (total_tokens / 1000) * 0.0004
        return total_tokens, cost
