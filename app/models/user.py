from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from app.database import Base
from pydantic import BaseModel

class User(Base):
    """
    Модель пользователя:
    - username: уникальное имя пользователя
    - hashed_password: пароль в зашифрованном виде
    """
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)

    collections = relationship("Collection", back_populates="user", cascade="all, delete-orphan")
    files = relationship("FileUpload", back_populates="user", cascade="all, delete-orphan")
    word_stat = relationship("WordStat", back_populates="user", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<User(id={self.id}, username={self.username})>"


class UserCreate(BaseModel):
    """
    Pydantic-схема для регистрации нового пользователя.
    """
    username: str
    password: str
