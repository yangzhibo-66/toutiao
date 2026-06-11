from sqlalchemy import select

from config.db_conf import AsyncSessionLocal, async_engine
from models.favorite import Favorite
from models.history import History
from models.news import Category, News
from models.users import User, UserToken

ALL_MODELS = [
    Category,
    News,
    User,
    UserToken,
    Favorite,
    History,
]

DEFAULT_CATEGORIES = [
    {"name": "头条", "sort_order": 1},
    {"name": "社会", "sort_order": 2},
    {"name": "国内", "sort_order": 3},
    {"name": "国际", "sort_order": 4},
    {"name": "娱乐", "sort_order": 5},
    {"name": "体育", "sort_order": 6},
    {"name": "军事", "sort_order": 7},
    {"name": "科技", "sort_order": 8},
    {"name": "财经", "sort_order": 9},
]


async def seed_default_categories() -> None:
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(Category))
        existing_categories = {item.name: item for item in result.scalars().all()}

        for category in DEFAULT_CATEGORIES:
            existing = existing_categories.get(category["name"])
            if existing:
                if existing.sort_order != category["sort_order"]:
                    existing.sort_order = category["sort_order"]
                    session.add(existing)
                continue

            session.add(Category(**category))

        await session.commit()


async def init_database() -> None:
    async with async_engine.begin() as conn:
        for model in ALL_MODELS:
            await conn.run_sync(model.metadata.create_all)

    await seed_default_categories()
