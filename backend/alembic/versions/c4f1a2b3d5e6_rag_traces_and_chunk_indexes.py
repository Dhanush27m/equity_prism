"""rag traces and document_chunk retrieval indexes

Revision ID: c4f1a2b3d5e6
Revises: 002e0f3c7c67
Create Date: 2026-07-26 09:00:00.000000

Component: Backend -> Data Layer -> Alembic migration (third/current in the chain)
Purpose: adds rag_traces (the RAG question/answer audit table written by
document_research.py and rag_eval.py) and the two indexes hybrid retrieval depends on —
an HNSW cosine index for pgvector's vector_search and a GIN full-text index for
fulltext_search (see app/rag/retrieval.py).
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = 'c4f1a2b3d5e6'
down_revision: Union[str, None] = '002e0f3c7c67'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'rag_traces',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('question', sa.Text(), nullable=False),
        sa.Column('answer', sa.Text(), nullable=False),
        sa.Column('chunk_ids', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('citations', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('model', sa.String(length=64), nullable=True),
        sa.Column('source', sa.String(length=16), nullable=True),
        sa.Column('trace_id', sa.String(length=64), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.execute(
        "CREATE INDEX ix_document_chunks_embedding_hnsw "
        "ON document_chunks USING hnsw (embedding vector_cosine_ops)"
    )
    op.execute(
        "CREATE INDEX ix_document_chunks_content_fts "
        "ON document_chunks USING gin (to_tsvector('english', content))"
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_document_chunks_content_fts")
    op.execute("DROP INDEX IF EXISTS ix_document_chunks_embedding_hnsw")
    op.drop_table('rag_traces')
