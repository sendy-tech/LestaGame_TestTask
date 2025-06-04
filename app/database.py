import os
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base

# Загрузка переменных окружения
load_dotenv()

# Получение и проверка DATABASE_URL
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise ValueError("❌ DATABASE_URL is not set in .env")

# Преобразуем для использования с asyncpg
DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://")

# Создание асинхронного движка и сессии
engine = create_async_engine(DATABASE_URL, echo=True)
async_session = async_sessionmaker(engine, expire_on_commit=False)

# Базовый класс моделей
Base = declarative_base()

async def get_db():
    async with async_session() as session:
        yield session