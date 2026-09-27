import os
from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

BASE_DIR = Path(__file__).resolve().parent.parent
SQLITE_DB_PATH = BASE_DIR / "news_app.db"

ASYNC_DATABASE_URL = os.getenv(
    "DATABASE_URL",
    f"sqlite+aiosqlite:///{SQLITE_DB_PATH.as_posix()}",
)

engine_kwargs = {"echo": False}
if ASYNC_DATABASE_URL.startswith("sqlite+aiosqlite"):
    from sqlalchemy.pool import NullPool

    # SQLite 本地文件连接开销很小，用 NullPool 避免连接跨事件循环复用的问题
    # （脚本里多次 asyncio.run、测试框架每个用例新循环时尤其重要）
    engine_kwargs["poolclass"] = NullPool
else:
    engine_kwargs.update(
        {
            "pool_size": 10,
            "max_overflow": 20,
        }
    )

async_engine = create_async_engine(ASYNC_DATABASE_URL, **engine_kwargs)

if ASYNC_DATABASE_URL.startswith("sqlite+aiosqlite"):
    from sqlalchemy import event

    @event.listens_for(async_engine.sync_engine, "connect")
    def _set_sqlite_pragma(dbapi_connection, _record):
        # 写操作遇锁时等待而非立刻报 database is locked；外键约束默认开启
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA busy_timeout=5000")
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

AsyncSessionLocal = async_sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
