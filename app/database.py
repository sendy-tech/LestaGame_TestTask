import os
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base

# Загрузка переменных окружения из .env
load_dotenv()

# Получение URL для подключения к базе данных
DB_USER = os.getenv("POSTGRES_USER")
DB_PASSWORD = os.getenv("POSTGRES_PASSWORD")
DB_HOST = os.getenv("POSTGRES_HOST", "postgres")
DB_NAME = os.getenv("POSTGRES_DB")

if not all([DB_USER, DB_PASSWORD, DB_HOST, DB_NAME]):
    raise ValueError("❌ Missing DB config variables")

DATABASE_URL = f"postgresql+asyncpg://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}"

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
