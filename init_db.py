import asyncio
from app.database import engine, Base

async def init():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        print("✅ Таблицы успешно созданы")

if __name__ == "__main__":
    asyncio.run(init())
