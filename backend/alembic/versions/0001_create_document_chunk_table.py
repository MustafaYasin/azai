"""
create document chunk table

Revision ID: 0001
Revises:
Create Date: 2025-01-13 17:06:11.657065

"""

from collections.abc import Sequence

import pgvector.sqlalchemy
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Create pgvector extension first
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    # Changed table name from 'document_chunk' to 'chunk'
    op.create_table(
        "chunk",
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("chunk_content", sa.Text(), nullable=False),
        sa.Column("embedding", pgvector.sqlalchemy.Vector(1536), nullable=True),
        sa.Column("is_embedded", sa.Boolean(), nullable=False),
        sa.Column("page_number", sa.Integer(), nullable=False),
        sa.Column("chunk_title", sa.String(), nullable=False),
        sa.Column("meta", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_chunk")),
    )
    op.create_index(op.f("ix_chunk_chunk_title"), "chunk", ["chunk_title"], unique=False)
    op.create_index(op.f("ix_chunk_is_embedded"), "chunk", ["is_embedded"], unique=False)
    op.create_index(op.f("ix_chunk_page_number"), "chunk", ["page_number"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_document_chunk_page_number"), table_name="document_chunk")
    op.drop_index(op.f("ix_document_chunk_is_embedded"), table_name="document_chunk")
    op.drop_index(op.f("ix_document_chunk_chunk_title"), table_name="document_chunk")
    op.drop_table("document_chunk")
    # Don't drop the vector extension as other tables might use it
