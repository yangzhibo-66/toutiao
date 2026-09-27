from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from models.ai_chat import AiChat


async def save_chat(db: AsyncSession, user_id: int, message: str, response: str):
    record = AiChat(user_id=user_id, message=message, response=response)
    db.add(record)
    await db.flush()
    await db.refresh(record)
    return record


async def get_user_history(db: AsyncSession, user_id: int, skip: int = 0, limit: int = 20):
    stmt = (
        select(AiChat)
        .where(AiChat.user_id == user_id)
        .order_by(AiChat.created_at.desc(), AiChat.id.desc())
        .offset(skip)
        .limit(limit)
    )
    result = await db.execute(stmt)
    items = result.scalars().all()

    count_stmt = select(func.count()).select_from(AiChat).where(AiChat.user_id == user_id)
    total = (await db.execute(count_stmt)).scalar_one()
    return items, total


async def delete_user_chat(db: AsyncSession, user_id: int, chat_id: int):
    result = await db.execute(delete(AiChat).where(AiChat.id == chat_id, AiChat.user_id == user_id))
    return result.rowcount > 0
