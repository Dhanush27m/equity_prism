from app.core.config import get_settings

settings = get_settings()

EMBEDDING_DIM = 384

_model = None
_fastembed = None


def _get_model():
    global _model
    if _model is None:
        from sentence_transformers import SentenceTransformer

        _model = SentenceTransformer(settings.embedding_model)
    return _model


def _get_fastembed():
    global _fastembed
    if _fastembed is None:
        from fastembed import TextEmbedding

        _fastembed = TextEmbedding(model_name=f"sentence-transformers/{settings.embedding_model}")
    return _fastembed


def embed_texts(texts: list[str]) -> list[list[float]]:
    if not texts:
        return []
    if settings.embedding_backend == "fastembed":
        model = _get_fastembed()
        return [vec.tolist() for vec in model.embed(texts)]
    model = _get_model()
    vectors = model.encode(texts, batch_size=32, normalize_embeddings=True, show_progress_bar=False)
    return [v.tolist() for v in vectors]


def embed_query(text: str) -> list[float]:
    return embed_texts([text])[0]
