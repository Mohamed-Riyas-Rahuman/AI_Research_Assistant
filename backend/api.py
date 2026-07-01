"""
api.py
------
All FastAPI routes for the AI Research Assistant.

Endpoints
---------
POST /api/upload          upload one or more PDFs, chunk + embed + store them
GET  /api/sources          list of uploaded PDF filenames
POST /api/ask              ask a question, get an answer + citations
GET  /api/history/{sid}    fetch chat history for a session
POST /api/search           keyword search across stored chunks (Feature 8)
POST /api/download-answer  generate a downloadable PDF of a Q&A pair
POST /api/clear            wipe the vector store
"""

import io
import shutil
import uuid
from pathlib import Path
from typing import List, Dict

from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import StreamingResponse, JSONResponse

from backend.pdf_loader import load_and_chunk_pdf
from backend.vector_db import VectorStore
from backend.rag import answer_question, keyword_search

router = APIRouter()

DATA_DIR = Path("data/papers")
DATA_DIR.mkdir(parents=True, exist_ok=True)

store = VectorStore(store_dir="vector_store")

# In-memory chat history per session (Feature 2 / Feature 7).
# session_id -> list of {"question": ..., "answer": ...}
CHAT_HISTORY: Dict[str, List[Dict]] = {}


def _history_as_text(session_id: str, max_turns: int = 5) -> str:
    turns = CHAT_HISTORY.get(session_id, [])[-max_turns:]
    lines = []
    for t in turns:
        lines.append(f"User: {t['question']}\nAssistant: {t['answer']}")
    return "\n\n".join(lines)


# --------------------------------------------------------------------- #
# Upload
# --------------------------------------------------------------------- #
@router.post("/upload")
async def upload_pdfs(files: List[UploadFile] = File(...)):
    if not files:
        raise HTTPException(status_code=400, detail="No files received.")

    uploaded = []
    for f in files:
        if not f.filename.lower().endswith(".pdf"):
            continue

        dest_path = DATA_DIR / f.filename
        with open(dest_path, "wb") as out:
            shutil.copyfileobj(f.file, out)

        records = load_and_chunk_pdf(str(dest_path), f.filename)
        store.add_records(records)

        uploaded.append({"filename": f.filename, "chunks": len(records)})

    if not uploaded:
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")

    return {"uploaded": uploaded, "stats": store.stats()}


# --------------------------------------------------------------------- #
# Sources / stats
# --------------------------------------------------------------------- #
@router.get("/sources")
async def get_sources():
    return store.stats()


# --------------------------------------------------------------------- #
# Ask a question
# --------------------------------------------------------------------- #
@router.post("/ask")
async def ask(
    question: str = Form(...),
    session_id: str = Form(default=""),
    top_k: int = Form(default=3),
):
    if not session_id:
        session_id = str(uuid.uuid4())

    history_text = _history_as_text(session_id)
    answer, citations = answer_question(store, question, top_k=top_k, chat_history=history_text)

    CHAT_HISTORY.setdefault(session_id, []).append({
        "question": question,
        "answer": answer,
    })

    return {
        "session_id": session_id,
        "answer": answer,
        "citations": citations,
    }


# --------------------------------------------------------------------- #
# Chat history
# --------------------------------------------------------------------- #
@router.get("/history/{session_id}")
async def get_history(session_id: str):
    return {"session_id": session_id, "history": CHAT_HISTORY.get(session_id, [])}


# --------------------------------------------------------------------- #
# Keyword search (Feature 8)
# --------------------------------------------------------------------- #
@router.post("/search")
async def search_keyword(keyword: str = Form(...)):
    results = keyword_search(store, keyword)
    return {"keyword": keyword, "results": results}


# --------------------------------------------------------------------- #
# Download answer as PDF (Feature 5)
# --------------------------------------------------------------------- #
@router.post("/download-answer")
async def download_answer(question: str = Form(...), answer: str = Form(...)):
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.lib.pagesizes import A4

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    styles = getSampleStyleSheet()
    story = [
        Paragraph("AI Research Assistant - Answer", styles["Title"]),
        Spacer(1, 16),
        Paragraph(f"<b>Question:</b> {question}", styles["Normal"]),
        Spacer(1, 12),
        Paragraph(f"<b>Answer:</b> {answer}", styles["Normal"]),
    ]
    doc.build(story)
    buffer.seek(0)

    return StreamingResponse(
        buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": "attachment; filename=answer.pdf"},
    )


# --------------------------------------------------------------------- #
# Clear store
# --------------------------------------------------------------------- #
@router.post("/clear")
async def clear_store():
    store.clear()
    CHAT_HISTORY.clear()
    for f in DATA_DIR.glob("*.pdf"):
        f.unlink()
    return {"status": "cleared"}
