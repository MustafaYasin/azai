import uuid
from typing import Any

from pgvector.sqlalchemy import Vector
from sqlalchemy import Column, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlmodel import Field

from database.mixins import TimestampMixin


class Chunk(TimestampMixin, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    chunk_content: str = Field(sa_type=Text)
    embedding: list[float] | None = Field(default=None, sa_column=Column(Vector(1536)))
    is_embedded: bool = Field(default=False, index=True)

    page_number: int = Field(index=True)
    chunk_title: str = Field(index=True)

    meta: dict[str, Any] = Field(default={}, sa_type=JSONB)
