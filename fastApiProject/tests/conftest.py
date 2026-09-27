"""pytest 共享夹具。

关键点：所有环境变量必须在导入任何应用模块之前设置，
因为 db_conf / ai 等模块在 import 时就读取了环境变量。
"""

import asyncio
import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# 测试专用数据库：每次会话重建
_TEST_DB_DIR = PROJECT_ROOT / ".pytest-tmp"
_TEST_DB_DIR.mkdir(exist_ok=True)
_TEST_DB = _TEST_DB_DIR / "news_app_test.db"
if _TEST_DB.exists():
    _TEST_DB.unlink()

os.environ["DATABASE_URL"] = f"sqlite+aiosqlite:///{_TEST_DB.as_posix()}"
os.environ["NEWS_SYNC_RUN_ON_STARTUP"] = "false"
os.environ["NEWS_SYNC_ADMIN_TOKEN"] = "test-sync-token"
# 置空 AI Key：AI 接口走"数据库兜底"路径，测试不依赖外部服务
os.environ["DASHSCOPE_API_KEY"] = ""

import pytest  # noqa: E402


@pytest.fixture(scope="session")
def _database():
    """在独立事件循环里初始化测试库（建表 + 播种分类）。"""
    from utils.db_init import init_database

    asyncio.run(init_database())


@pytest.fixture
async def client(_database):
    from httpx import ASGITransport, AsyncClient

    from main import app

    # 注意：httpx 的 ASGITransport 不会触发 FastAPI 的 startup 事件，
    # 所以这里不会启动后台新闻同步任务，数据库初始化由 _database 夹具完成。
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as http:
        yield http
