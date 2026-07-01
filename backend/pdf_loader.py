"""
pdf_loader.py
--------------
Handles reading PDF files and splitting their text into overlapping chunks
suitable for embedding + retrieval.
"""

from pathlib import Path
from typing import List, Dict
from pypdf import PdfReader


def extract_pages(pdf_path: str) -> List[Dict]:
    """
    Reads a PDF and returns a list of {"page": int, "text": str} dicts,
    one per page. Empty pages are skipped.
    """
    reader = PdfReader(pdf_path)
    pages = []
    for i, page in enumerate(reader.pages, start=1):
        text = page.extract_text() or ""
        text = text.strip()
        if text:
            pages.append({"page": i, "text": text})
    return pages


def chunk_text(text: str, chunk_size: int = 500, overlap: int = 100) -> List[str]:
    """
    Splits text into overlapping word-based chunks.

    chunk_size : number of words per chunk
    overlap    : number of words repeated between consecutive chunks,
                 so that sentences spanning a chunk boundary keep their
                 meaning intact.
    """
    words = text.split()
    if not words:
        return []

    chunks = []
    start = 0
    step = max(chunk_size - overlap, 1)

    while start < len(words):
        end = start + chunk_size
        chunk = " ".join(words[start:end])
        chunks.append(chunk)
        if end >= len(words):
            break
        start += step

    return chunks


def load_and_chunk_pdf(
    pdf_path: str,
    source_name: str,
    chunk_size: int = 500,
    overlap: int = 100,
) -> List[Dict]:
    """
    Full pipeline for one PDF: extract pages -> chunk each page's text.

    Returns a list of dicts:
        {
            "text": "...",
            "source": "Research_Paper.pdf",
            "page": 8
        }
    These dicts are what gets embedded and stored in the vector DB,
    and "source"/"page" are what let us show citations later.
    """
    pages = extract_pages(pdf_path)
    records = []

    for page_data in pages:
        page_num = page_data["page"]
        for chunk in chunk_text(page_data["text"], chunk_size, overlap):
            records.append({
                "text": chunk,
                "source": source_name,
                "page": page_num,
            })

    return records


def load_and_chunk_directory(
    directory: str,
    chunk_size: int = 500,
    overlap: int = 100,
) -> List[Dict]:
    """Convenience helper: chunk every PDF found in a directory."""
    all_records = []
    for pdf_file in sorted(Path(directory).glob("*.pdf")):
        all_records.extend(
            load_and_chunk_pdf(str(pdf_file), pdf_file.name, chunk_size, overlap)
        )
    return all_records
