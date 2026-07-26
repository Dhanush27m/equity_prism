from app.core.config import get_settings

settings = get_settings()

_model = None


def _get_model():
    global _model
    if _model is None:
        from sentence_transformers import CrossEncoder

        _model = CrossEncoder(settings.rerank_model)
    return _model


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
