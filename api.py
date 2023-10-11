from fastapi import FastAPI, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from database import service, db
import uvicorn

api = FastAPI()


@api.get("/get_users")
async def get_users(session: AsyncSession = Depends(db.get_session)):
    users = await service.get_users(session)
    return users


@api.post("/create_user")
async def create_user(telegram_id: int = None, session: AsyncSession = Depends(db.get_session)):
        new_user = await service.create_user(session, telegram_id)
        return new_user


if __name__ == '__main__':
    uvicorn.run(api, host="localhost", port=8000)