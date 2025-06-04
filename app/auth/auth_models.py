from sqlalchemy import Column, Integer, String, DateTime, func
from app.database import Base
from pydantic import BaseModel

# SQLAlchemy модель пользователя
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    created_at = Column(DateTime, server_default=func.now())

# Pydantic-схема для создания пользователя (регистрация)
class UserCreate(BaseModel):
    username: str
    password: str