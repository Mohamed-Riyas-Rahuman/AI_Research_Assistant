"""
app.py
------
Entry point. Run with:

    uvicorn app:app --reload

Serves the frontend (templates/index.html + static/) and mounts the
/api/* routes defined in backend/api.py.
"""

from dotenv import load_dotenv
load_dotenv()  # reads GOOGLE_API_KEY from a local .env file if present
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from backend.api import router as api_router

load_dotenv()  # reads GOOGLE_API_KEY from a local .env file if present

BASE_DIR = Path(__file__).resolve().parent

app = FastAPI(title="AI Research Assistant")

app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

app.include_router(api_router, prefix="/api")


@app.get("/")
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})
