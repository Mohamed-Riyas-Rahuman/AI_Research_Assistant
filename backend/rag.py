"""
rag.py
------
Glues retrieval (vector_db) and generation (llm) together, and formats
citations for the frontend.
"""

from typing import List, Dict, Tuple
from backend.vector_db import VectorStore
from backend.llm import generate_answer

TOP_K = 3


def build_context(chunks: List[Dict]) -> str:
    """Joins retrieved chunks into a single context block, tagging each
    with its source/page so the LLM (and the citation list) can point
    back to the right document."""
    parts = []
    for c in chunks:
        parts.append(f"[Source: {c['source']} | Page {c['page']}]\n{c['text']}")
    return "\n\n---\n\n".join(parts)


def format_citations(chunks: List[Dict]) -> List[Dict]:
    seen = set()
    citations = []
    for c in chunks:
        key = (c["source"], c["page"])
        if key in seen:
            continue
        seen.add(key)
        citations.append({
            "source": c["source"],
            "page": c["page"],
            "score": round(c.get("score", 0.0), 3),
        })
    return citations


def answer_question(
    store: VectorStore,
    question: str,
    top_k: int = TOP_K,
    chat_history: str = "",
) -> Tuple[str, List[Dict]]:
    chunks = store.search(question, top_k=top_k)

    if not chunks:
        return (
            "No documents have been uploaded yet, so I have nothing to search. "
            "Upload a PDF first.",
            [],
        )

    context = build_context(chunks)
    answer = generate_answer(context, question, chat_history)
    citations = format_citations(chunks)

    return answer, citations


def keyword_search(store: VectorStore, keyword: str, top_k: int = 10) -> List[Dict]:
    """Simple substring search across stored chunks (Feature 8)."""
    keyword_lower = keyword.lower()
    matches = [
        r for r in store.metadata if keyword_lower in r["text"].lower()
    ]
    return matches[:top_k]
