from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from database.models import *


async def get_users(session: AsyncSession) -> list[User]:
    result = await session.execute(select(User))
    return result.scalars().all()


async def create_user(session: AsyncSession, telegram_id: int):
    new_user = User(telegram_id=telegram_id)
    session.add(new_user)
    await session.commit()
    return new_user

