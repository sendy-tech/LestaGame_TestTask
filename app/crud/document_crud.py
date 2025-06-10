from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, func

from app.models.document import FileUpload, WordStat
from app.schemas import FileUploadCreate, WordStatCreate
import logging

logger = logging.getLogger(__name__)

# === ДОКУМЕНТЫ ===

# Создание нового файла
async def create_file_upload(db: AsyncSession, user_id: int, file_data: FileUploadCreate) -> FileUpload:
    new_file = FileUpload(user_id=user_id, **file_data.dict())
    db.add(new_file)
    await db.commit()
    await db.refresh(new_file)
    return new_file

# Получение всех файлов пользователя
async def get_user_files(db: AsyncSession, user_id: int) -> List[FileUpload]:
    result = await db.execute(select(FileUpload).where(FileUpload.user_id == user_id))
    return result.scalars().all()

# Удаление файла пользователя
async def delete_file_upload(db: AsyncSession, file_id: int, user_id: int) -> Optional[FileUpload]:
    result = await db.execute(
        select(FileUpload).where(FileUpload.id == file_id, FileUpload.user_id == user_id)
    )
    file = result.scalar_one_or_none()
    if file:
        await db.delete(file)
        await db.commit()
        logger.info(f"Удалён файл ID={file_id} пользователем ID={user_id}")
    return file

# Подсчёт всех документов
async def count_documents(db: AsyncSession) -> int:
    result = await db.execute(select(func.count()).select_from(FileUpload))
    return result.scalar_one()

# === СТАТИСТИКА ===

# Добавление записи WordStat
async def create_word_stat(db: AsyncSession, stat_data: WordStatCreate) -> WordStat:
    word_stat = WordStat(**stat_data.dict())
    db.add(word_stat)
    await db.commit()
    await db.refresh(word_stat)
    return word_stat

# Получение статистики по файлу
async def get_word_stat_for_file(db: AsyncSession, file_id: int) -> List[WordStat]:
    result = await db.execute(select(WordStat).where(WordStat.file_id == file_id))
    return result.scalars().all()

# Удаление статистики по файлу
async def delete_word_stat_for_file(db: AsyncSession, file_id: int) -> None:
    await db.execute(delete(WordStat).where(WordStat.file_id == file_id))
    await db.commit()
