"""
Component: Backend -> Data Layer -> ORM model (RAG observability)
Belongs to: written by app/agents/document_research.py after every document-grounded
answer, and by app/eval/rag_eval.py during offline evaluation.
Purpose: an audit trail of RAG question/answer pairs — which chunks were retrieved,
what citations were produced, which model answered, and the LangFuse trace id — kept
for later inspection, not read back by any live endpoint today.
"""

from datetime import datetime

from sqlalchemy import DateTime, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class RagTrace(Base):
    __tablename__ = "rag_traces"

    id: Mapped[int] = mapped_column(primary_key=True)
    question: Mapped[str] = mapped_column(Text)
    answer: Mapped[str] = mapped_column(Text)
    chunk_ids: Mapped[list] = mapped_column(JSONB, default=list)
    citations: Mapped[list] = mapped_column(JSONB, default=list)
    model: Mapped[str | None] = mapped_column(String(64), nullable=True)
    source: Mapped[str | None] = mapped_column(String(16), nullable=True)
    trace_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
