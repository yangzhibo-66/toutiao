import asyncio
import os
from contextlib import asynccontextmanager
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.staticfiles import StaticFiles

load_dotenv()

from routers import ai, favorite, history, news, users
from services.news_sync import ensure_sync_schema, sync_loop
from utils.db_init import init_database
from utils.exception_handlers import register_exception_handlers

BASE_DIR = Path(__file__).resolve().parent
UPLOAD_DIR = BASE_DIR / "uploads"
AVATAR_DIR = UPLOAD_DIR / "avatars"
AVATAR_DIR.mkdir(parents=True, exist_ok=True)

@asynccontextmanager
async def lifespan(target_app: FastAPI):
    await init_database()
    await ensure_sync_schema()
    stop_event = asyncio.Event()
    sync_task = asyncio.create_task(sync_loop(stop_event))
    target_app.state.news_sync_stop_event = stop_event
    target_app.state.news_sync_task = sync_task
    yield
    stop_event.set()
    await sync_task


app = FastAPI(lifespan=lifespan)
register_exception_handlers(app)
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")
# 新闻列表/详情响应体较大，GZip 可显著节省移动端流量
app.add_middleware(GZipMiddleware, minimum_size=1024)

# 允许的前端来源，多个用逗号分隔，如 CORS_ORIGINS=http://localhost:5173,http://192.168.1.10:5173
# 未配置时保持通配（便于本地/局域网调试），生产环境建议显式配置
_CORS_ORIGINS = [origin.strip() for origin in os.getenv("CORS_ORIGINS", "").split(",") if origin.strip()] or ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_CORS_ORIGINS,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@asynccontextmanager
async def lifespan(target_app: FastAPI):
    await init_database()
    await ensure_sync_schema()
    stop_event = asyncio.Event()
    sync_task = asyncio.create_task(sync_loop(stop_event))
    target_app.state.news_sync_stop_event = stop_event
    target_app.state.news_sync_task = sync_task
    yield
    stop_event.set()
    await sync_task


@app.get("/")
async def root():
    return {"message": "Hello World"}


app.include_router(news.router)
app.include_router(users.router)
app.include_router(favorite.router)
app.include_router(history.router)
app.include_router(ai.router)
