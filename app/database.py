import os
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base

# Загрузка переменных окружения из .env
load_dotenv()

# Получение URL для подключения к базе данных
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise ValueError("❌ DATABASE_URL is not set in .env")

# Преобразуем URL для использования с asyncpg драйвером
DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://")

# Создание асинхронного движка SQLAlchemy
engine = create_async_engine(
    DATABASE_URL,
    echo=False,
    future=True
)

# Фабрика для создания асинхронных сессий
async_session = async_sessionmaker(engine, expire_on_commit=False)

# Базовый класс для ORM-моделей
Base = declarative_base()

# Генератор сессии для зависимости FastAPI
async def get_db():
    async with async_session() as session:
        yield session
