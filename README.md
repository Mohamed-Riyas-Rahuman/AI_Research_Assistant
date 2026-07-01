# AI Research Assistant (RAG + LLM)

Upload research papers, ask questions in plain English, and get answers
generated **only** from your documents — with page-level citations.

Built to showcase RAG, vector search, prompt engineering, and a full
FastAPI + JS stack for AI Engineer / Data Scientist / ML Engineer interviews.

---

## How it works

```
Upload PDF → Extract text per page → Split into overlapping chunks
   → Embed chunks (sentence-transformers) → Store in FAISS
   → User asks a question → Embed question → Similarity search top-k chunks
   → Build prompt (context + question) → Gemini LLM → Answer + citations
```

## Tech stack

| Layer        | Choice                                   |
|--------------|-------------------------------------------|
| Backend      | Python, FastAPI                          |
| LLM          | Gemini (`gemini-1.5-flash`)              |
| Vector DB    | FAISS (cosine similarity via inner product) |
| Embeddings   | `sentence-transformers/all-MiniLM-L6-v2` |
| PDF parsing  | `pypdf`                                  |
| Frontend     | HTML / CSS / vanilla JS (dark + light theme) |
| PDF export   | `reportlab`                              |

## Features implemented

- Multi-PDF upload, chunked with 500-word windows and 100-word overlap
- Persistent FAISS index (survives server restarts) under `vector_store/`
- Conversation memory per browser session (last 5 turns sent back to the LLM)
- Page-level citations shown as pills under each answer
- Keyword search across all stored chunks
- Voice input via the Web Speech API
- Dark / light theme toggle
- "Download answer as PDF" button on every response
- "I don't know" fallback when the answer isn't in the uploaded documents

## Setup

```bash
cd AI_Research_Assistant
python -m venv venv
source venv/bin/activate        # venv\Scripts\activate on Windows

pip install -r requirements.txt
```

Create a `.env` file in the project root with your Gemini API key:

```
GOOGLE_API_KEY=your_key_here
```

Get a free key at https://aistudio.google.com/app/apikey

## Run

```bash
uvicorn app:app --reload
```

Open http://127.0.0.1:8000

## Project structure

```
AI_Research_Assistant/
├── app.py                 # FastAPI entrypoint
├── backend/
│   ├── api.py              # routes: upload, ask, search, download, clear
│   ├── rag.py               # retrieval + prompt assembly
│   ├── llm.py                # Gemini wrapper + prompt template
│   ├── vector_db.py           # FAISS wrapper + embeddings
│   └── pdf_loader.py           # PDF text extraction + chunking
├── data/papers/             # uploaded PDFs are stored here
├── vector_store/             # persisted FAISS index + metadata
├── templates/index.html       # frontend markup
├── static/css/style.css        # dark/light theme styling
├── static/js/script.js          # chat, upload, voice, theme logic
└── requirements.txt
```

## Interview talking points

- **Chunking strategy**: word-based chunks with overlap to avoid splitting
  a sentence (and its meaning) across two chunks.
- **Why cosine similarity**: embeddings are L2-normalized before being added
  to FAISS, so a plain inner-product index (`IndexFlatIP`) behaves like
  cosine similarity, which is the standard metric for semantic search.
- **Grounding / hallucination control**: the system prompt forces the model
  to answer only from retrieved context and explicitly say "I don't know"
  otherwise — this is the core idea behind RAG reducing hallucination
  versus a vanilla LLM call.
- **Citations**: every chunk carries its source filename and page number
  through retrieval into the final response, so answers are auditable.
- **Swappable LLM**: `backend/llm.py` isolates the model call — swapping
  Gemini for OpenAI only touches one file.

## Notes

- The embedding model downloads (~80MB) the first time you run the app.
- This sandbox environment used to author these files has no internet
  access, so dependencies haven't been pip-installed or executed here —
  run the setup steps above in your own environment.
