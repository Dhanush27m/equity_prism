"""
Component: Backend -> RAG Pipeline -> Embeddings
Belongs to: called from both ingestion (embedding document chunks) and query time
(embedding the user's question) — app/rag/ingestion.py and app/rag/pipeline.py.
Purpose: a single embed_texts()/embed_query() interface backed by two interchangeable
implementations of the same all-MiniLM-L6-v2 model (384-dim): sentence-transformers
(PyTorch, local default) or fastembed (ONNX, no torch — used in the hosted profile to
keep the Docker image small enough for Render's free tier).
"""

from app.core.config import get_settings

settings = get_settings()

EMBEDDING_DIM = 384

_model = None
_fastembed = None


# Lazily loads (once) the PyTorch sentence-transformers model — the local/self-hosted default.
def _get_model():
    global _model
    if _model is None:
        from sentence_transformers import SentenceTransformer

        _model = SentenceTransformer(settings.embedding_model)
    return _model


# Lazily loads (once) the ONNX fastembed model — used when EMBEDDING_BACKEND=fastembed
# (the hosted profile). Same weights as above, re-exported to ONNX, no torch dependency.
def _get_fastembed():
    global _fastembed
    if _fastembed is None:
        from fastembed import TextEmbedding

        _fastembed = TextEmbedding(model_name=f"sentence-transformers/{settings.embedding_model}")
    return _fastembed


# Embeds a batch of texts (document chunks) using whichever backend is configured.
# Both paths return the same 384-dim vector space, so the choice is purely operational
# (image size / no-torch), not a retrieval-quality trade-off.
def embed_texts(texts: list[str]) -> list[list[float]]:
    if not texts:
        return []
    if settings.embedding_backend == "fastembed":
        model = _get_fastembed()
        return [vec.tolist() for vec in model.embed(texts)]
    model = _get_model()
    vectors = model.encode(texts, batch_size=32, normalize_embeddings=True, show_progress_bar=False)
    return [v.tolist() for v in vectors]


# Convenience for embedding a single query string (used at retrieval time).
def embed_query(text: str) -> list[float]:
    return embed_texts([text])[0]
