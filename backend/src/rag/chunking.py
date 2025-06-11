import uuid
from typing import Any

from database import open_session
from database.models import Chunk
from docling.chunking import HybridChunker

from rag.tokenizer import OpenAITokenizerWrapper


class DocumentChunker:
    def __init__(self, max_tokens: int = 8191, merge_peers: bool = True):
        self.tokenizer = OpenAITokenizerWrapper()
        self.max_tokens = max_tokens
        self.merge_peers = merge_peers
        self.chunker = HybridChunker(
            tokenizer=self.tokenizer,
            max_tokens=self.max_tokens,
            merge_peers=self.merge_peers,
        )

    def chunk_docling_document(self, document: Any) -> list[Any]:
        chunk_iter = self.chunker.chunk(dl_doc=document)
        return list(chunk_iter)

    def chunk_text(self, text: str, max_tokens: int | None = None) -> list[dict[str, Any]]:
        max_tokens = max_tokens or self.max_tokens
        paragraphs = [p for p in text.split('\n\n') if p.strip()]

        chunks = []
        for i, para in enumerate(paragraphs):
            tokens = self.tokenizer.tokenize(para)

            if len(tokens) <= max_tokens:
                chunks.append({
                    "text": para,
                    "meta": {
                        "page_no": 1,
                        "index": i
                    }
                })
            else:
                words = para.split()
                current_chunk = []
                current_length = 0

                for word in words:
                    word_tokens = self.tokenizer.tokenize(word)
                    if current_length + len(word_tokens) <= max_tokens:
                        current_chunk.append(word)
                        current_length += len(word_tokens)
                    else:
                        chunks.append({
                            "text": " ".join(current_chunk),
                            "meta": {
                                "page_no": 1,
                                "index": i
                            }
                        })
                        current_chunk = [word]
                        current_length = len(word_tokens)

                if current_chunk:
                    chunks.append({
                        "text": " ".join(current_chunk),
                        "meta": {
                            "page_no": 1,
                            "index": i
                        }
                    })

        return chunks

    def store_chunks(self, chunks: list[Any], source: str, is_docling: bool = True) -> int:
        with open_session() as session:
            for i, chunk in enumerate(chunks):
                if is_docling:
                    page_numbers = sorted(set(
                        prov.page_no
                        for item in chunk.meta.doc_items
                        for prov in item.prov
                    )) if hasattr(chunk.meta, "doc_items") else []

                    heading = chunk.meta.headings[0] if (hasattr(chunk.meta, "headings") and chunk.meta.headings) else None

                    text = chunk.text

                    page_number = page_numbers[0] if page_numbers else i

                    meta = {
                        "page_numbers": page_numbers,
                        "title": heading,
                        "chunk_size": self.max_tokens,
                        "source": source
                    }
                else:
                    text = chunk["text"]
                    page_number = chunk["meta"].get("page_no", 1)
                    meta = {
                        "page_numbers": [page_number],
                        "source": source,
                        "chunk_size": self.max_tokens
                    }

                db_chunk = Chunk(
                    id=uuid.uuid4(),
                    chunk_content=text,
                    chunk_title=source,
                    page_number=page_number,
                    is_embedded=False,
                    meta=meta
                )
                session.add(db_chunk)
            session.commit()

            return len(chunks)
