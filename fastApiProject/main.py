import asyncio
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

load_dotenv()

from routers import favorite, history, news, users
from services.news_sync import ensure_sync_schema, sync_loop
from utils.db_init import init_database
from utils.exception_handlers import register_exception_handlers

BASE_DIR = Path(__file__).resolve().parent
UPLOAD_DIR = BASE_DIR / "uploads"
AVATAR_DIR = UPLOAD_DIR / "avatars"
AVATAR_DIR.mkdir(parents=True, exist_ok=True)

app = FastAPI()
register_exception_handlers(app)
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup_news_sync():
    await init_database()
    await ensure_sync_schema()
    app.state.news_sync_stop_event = asyncio.Event()
    app.state.news_sync_task = asyncio.create_task(sync_loop(app.state.news_sync_stop_event))


@app.on_event("shutdown")
async def shutdown_news_sync():
    stop_event = getattr(app.state, "news_sync_stop_event", None)
    task = getattr(app.state, "news_sync_task", None)
    if stop_event is not None:
        stop_event.set()
    if task is not None:
        await task


@app.get("/")
async def root():
    return {"message": "Hello World"}


app.include_router(news.router)
app.include_router(users.router)
app.include_router(favorite.router)
app.include_router(history.router)
