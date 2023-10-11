from sqlalchemy import Column
from sqlalchemy import String
from sqlalchemy import Integer
from database.db import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, autoincrement=True, primary_key=True, index=True)
    telegram_id = Column(Integer, unique=True)
    level = Column(String, default="A1")