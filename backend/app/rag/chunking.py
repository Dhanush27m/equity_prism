"""
Component: Backend -> RAG Pipeline -> Ingestion (text extraction + chunking)
Belongs to: called from app/rag/ingestion.py (and app/eval/rag_eval.py for the eval
corpus) when a PDF is uploaded.
Purpose: extracts page-tagged text from a PDF and splits it into overlapping,
paragraph-aware chunks — the unit that gets embedded and stored for later retrieval.
"""

import pdfplumber
from langchain_text_splitters import RecursiveCharacterTextSplitter

CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200

# Prefers paragraph breaks, then sentence, then word, then raw character splits — only
# falls back to a mid-sentence cut when a paragraph itself exceeds CHUNK_SIZE. This is
# the only use of LangChain in the whole project (a plain utility, no chains/agents).
_splitter = RecursiveCharacterTextSplitter(
    chunk_size=CHUNK_SIZE,
    chunk_overlap=CHUNK_OVERLAP,
    separators=["\n\n", "\n", ". ", " ", ""],
)


# Extracts text per page from a PDF on disk, dropping blank pages. Returns
# (page_number, text) tuples so page numbers survive into citations later.
def extract_pages(path: str) -> list[tuple[int, str]]:
    pages: list[tuple[int, str]] = []
    with pdfplumber.open(path) as pdf:
        for i, page in enumerate(pdf.pages, start=1):
            text = page.extract_text() or ""
            text = text.strip()
            if text:
                pages.append((i, text))
    return pages


# Splits each page's text into chunks, tagging every chunk with its source page number
# and a running chunk_index (used as DocumentChunk.chunk_index).
def chunk_pages(pages: list[tuple[int, str]]) -> list[dict]:
    chunks: list[dict] = []
    index = 0
    for page_number, text in pages:
        for piece in _splitter.split_text(text):
            piece = piece.strip()
            if not piece:
                continue
            chunks.append({"chunk_index": index, "content": piece, "page_number": page_number})
            index += 1
    return chunks


# Convenience wrapper combining both steps — used by the document ingestion task.
def extract_and_chunk(path: str) -> tuple[int, list[dict]]:
    pages = extract_pages(path)
    return len(pages), chunk_pages(pages)
