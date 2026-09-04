"""
Component: Backend -> RAG Pipeline -> Query-time reranking (optional)
Belongs to: called from app/rag/pipeline.py's research(), only when RERANK_ENABLED=true.
Purpose: re-scores the RRF-merged candidate chunks with a cross-encoder that jointly
scores (query, passage) pairs — more accurate than independent embedding similarity, but
a second torch-based model to load, which is why it's disabled in the hosted/free-tier
profile and only on by default locally.
"""

from app.core.config import get_settings

settings = get_settings()

_model = None


# Lazily loads (once) the cross-encoder model.
def _get_model():
    global _model
    if _model is None:
        from sentence_transformers import CrossEncoder

        _model = CrossEncoder(settings.rerank_model)
    return _model


# Scores every (query, chunk) pair with the cross-encoder and returns the top_n
# highest-scoring chunks, re-sorted by that score.
def rerank(query: str, candidates: list[dict], top_n: int) -> list[dict]:
    if not candidates:
        return []
    model = _get_model()
    pairs = [(query, c["content"]) for c in candidates]
    scores = model.predict(pairs, show_progress_bar=False)
    for c, s in zip(candidates, scores):
        c["rerank_score"] = float(s)
    ranked = sorted(candidates, key=lambda c: c["rerank_score"], reverse=True)
    return ranked[:top_n]
