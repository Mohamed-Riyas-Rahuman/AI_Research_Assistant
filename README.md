# 🤖 AI Research Assistant — RAG + LLM

> Upload research papers. Ask questions in plain English. Get answers generated **only** from your documents — with page-level citations.

Built to demonstrate **RAG (Retrieval-Augmented Generation)** — a core concept in AI Engineer, Data Scientist, and ML Engineer roles.

---

## 📸 What It Does

- Upload one or multiple PDF research papers
- Ask any question about them in a chat interface
- The app finds the most relevant passages from your PDFs
- Sends those passages to an LLM (Groq + LLaMA)
- Returns a grounded answer with **source file + page number citations**
- If the answer is not in your documents → it says **"I don't know"** (no hallucination)

---

## 🧠 How RAG Works (Simple Explanation)

```
You upload a PDF
       ↓
Text is extracted page by page
       ↓
Each page is split into 500-word chunks (with 100-word overlap)
       ↓
Each chunk is converted into a vector (384 numbers) using sentence-transformers
       ↓
Vectors are stored in FAISS (a vector database)
       ↓
You ask a question
       ↓
Question is also converted into a vector
       ↓
FAISS finds the top 3 most similar chunk vectors
       ↓
Those 3 chunks become the "context"
       ↓
Context + Question are sent to Groq LLaMA model
       ↓
LLM answers using ONLY the context
       ↓
Answer + Citations shown in chat
```

This is called **RAG — Retrieval-Augmented Generation**

---

## 🗂️ Project Structure

```
AI_Research_Assistant/
│
├── app.py                      ← Entry point. Starts the server.
├── .env                        ← Your API keys (never share this)
├── requirements.txt            ← All Python libraries
│
├── backend/
│   ├── api.py                  ← All URL routes (/upload, /ask, /search)
│   ├── pdf_loader.py           ← Reads PDFs, splits into chunks
│   ├── vector_db.py            ← Embeds chunks, stores in FAISS, searches
│   ├── rag.py                  ← Retrieves chunks + calls LLM + citations
│   └── llm.py                  ← Talks to Groq AI (LLaMA model)
│
├── data/
│   └── papers/                 ← Uploaded PDFs saved here
│
├── vector_store/               ← FAISS index saved here (persists on restart)
│
├── templates/
│   └── index.html              ← The webpage (HTML structure)
│
└── static/
    ├── css/style.css           ← Dark/light theme styling
    └── js/script.js            ← Chat, upload, voice, theme logic
```

---

## ⚙️ Tech Stack

| Layer           | Technology                          |
|-----------------|--------------------------------------|
| Backend         | Python, FastAPI                     |
| Web Server      | Uvicorn                             |
| LLM             | Groq API (LLaMA 3.1 8B Instant)     |
| Vector Database | FAISS (Facebook AI Similarity Search)|
| Embeddings      | sentence-transformers (all-MiniLM-L6-v2) |
| PDF Reading     | pypdf                               |
| Frontend        | HTML, CSS, Vanilla JavaScript       |
| PDF Export      | reportlab                           |
| Config          | python-dotenv                       |

---

## 🚀 Setup & Installation

### Step 1 — Clone or download the project

```bash
cd AI_Research_Assistant
```

### Step 2 — Create a virtual environment

```bash
python -m venv venv

# Activate on Windows
venv\Scripts\activate

# Activate on Mac/Linux
source venv/bin/activate
```

### Step 3 — Install all libraries

```bash
pip install -r requirements.txt
```

> ⚠️ Note: `sentence-transformers` will download the embedding model (~80MB) the first time you run the server. This is normal.

### Step 4 — Get your Groq API Key (Free)

1. Go to **https://console.groq.com**
2. Sign up with your Google account
3. Click **API Keys** → **Create API key**
4. Copy the key (starts with `gsk_...`)

### Step 5 — Create your `.env` file

Create a file named `.env` in the root of the project (same folder as `app.py`):

```
GROQ_API_KEY=gsk_your_actual_key_here
```

Rules:
- No spaces around `=`
- No quotes needed
- Never share or upload this file

### Step 6 — Run the server

```bash
uvicorn app:app --reload
```

### Step 7 — Open in browser

```
http://127.0.0.1:8000
```

---

## 📖 How to Use

1. **Upload PDFs** — Click the upload zone on the left sidebar or drag and drop PDF files
2. **Wait for indexing** — The sidebar shows how many chunks are indexed
3. **Ask a question** — Type in the chat box and click Ask
4. **See answer + citations** — The answer appears with source file and page number pills
5. **Keyword search** — Use the sidebar search to find specific terms across all documents
6. **Voice input** — Click the 🎙 mic button to speak your question
7. **Download answer** — Click "Download PDF" under any answer to save it
8. **Toggle theme** — Click "Toggle theme" in the sidebar for light mode
9. **Clear all** — Click "Clear all data" to wipe documents and start fresh

---

## 🔗 How Files Connect to Each Other

```
app.py
  └── imports backend/api.py (all routes)
  └── serves templates/index.html (the webpage)
  └── serves static/ (CSS and JS)

backend/api.py
  └── calls pdf_loader.py → when PDF is uploaded
  └── calls vector_db.py  → to store and search chunks
  └── calls rag.py        → when question is asked

backend/rag.py
  └── calls vector_db.py  → to search similar chunks
  └── calls llm.py        → to generate the answer

backend/llm.py
  └── calls Groq API      → over the internet

static/js/script.js (browser)
  └── calls /api/upload   → to upload PDFs
  └── calls /api/ask      → to ask questions
  └── calls /api/sources  → to list uploaded PDFs
  └── calls /api/search   → for keyword search
  └── calls /api/clear    → to wipe all data
```

---

## 🌐 API Endpoints

| Method | URL                    | What it does                              |
|--------|------------------------|-------------------------------------------|
| GET    | `/`                    | Serves the web interface                  |
| POST   | `/api/upload`          | Upload one or more PDF files              |
| GET    | `/api/sources`         | Get list of uploaded PDFs + chunk count   |
| POST   | `/api/ask`             | Ask a question, returns answer + citations|
| GET    | `/api/history/{id}`    | Get chat history for a session            |
| POST   | `/api/search`          | Keyword search across all stored chunks   |
| POST   | `/api/download-answer` | Download a Q&A pair as a PDF file         |
| POST   | `/api/clear`           | Wipe all documents and vector store       |

---

## ✨ Features

- ✅ Multi-PDF upload — upload 50 papers at once
- ✅ Persistent FAISS index — survives server restarts
- ✅ Conversation memory — last 5 Q&A turns sent to LLM
- ✅ Page-level citations — every answer shows source file + page
- ✅ Keyword search — find specific terms across all documents
- ✅ Voice input — speak your question (Web Speech API)
- ✅ Dark / light theme toggle
- ✅ Download answer as PDF (reportlab)
- ✅ "I don't know" fallback — no hallucination

---

## 📦 Dependencies

```
fastapi==0.115.0
uvicorn[standard]==0.30.6
python-multipart==0.0.9
pypdf==4.3.1
sentence-transformers==3.0.1
faiss-cpu==1.8.0
groq
numpy==1.26.4
jinja2==3.1.4
python-dotenv==1.0.1
reportlab==4.2.2
```

---

## ⚠️ Common Issues & Fixes

| Error | Fix |
|-------|-----|
| `GROQ_API_KEY is not set` | Check `.env` file exists in project root with correct key |
| `ModuleNotFoundError: groq` | Run `pip install groq` |
| File upload not working | Make sure you removed the `uploadZone.addEventListener("click")` line from script.js |
| `load_dotenv` not loading key | Move `load_dotenv()` to the very first lines of `app.py` before all other imports |
| Model decommissioned error | Change model name in `llm.py` to `llama-3.1-8b-instant` |
| 429 quota exceeded | You are using wrong model or quota exhausted — switch to Groq free tier |

---

## 👤 Author

**Mohamed Riyas Rahuman M**
M.Sc. Data Science with Business Analytics
Rathinam College of Arts and Science (2024–2026)

- Skills: Python, FastAPI, SQL, PostgreSQL, Power BI, RAG, FAISS, LLMs

---

## 📄 License

MIT License — free to use, modify, and share.

