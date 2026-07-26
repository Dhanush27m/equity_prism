import pdfplumber
from langchain_text_splitters import RecursiveCharacterTextSplitter

CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200

_splitter = RecursiveCharacterTextSplitter(
    chunk_size=CHUNK_SIZE,
    chunk_overlap=CHUNK_OVERLAP,
    separators=["\n\n", "\n", ". ", " ", ""],
)


def extract_pages(path: str) -> list[tuple[int, str]]:
    pages: list[tuple[int, str]] = []
    with pdfplumber.open(path) as pdf:
        for i, page in enumerate(pdf.pages, start=1):
            text = page.extract_text() or ""
            text = text.strip()
            if text:
                pages.append((i, text))
    return pages


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


def extract_and_chunk(path: str) -> tuple[int, list[dict]]:
    pages = extract_pages(path)
    return len(pages), chunk_pages(pages)
