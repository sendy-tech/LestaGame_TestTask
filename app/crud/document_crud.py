from typing import List, Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, func

from app.models.document import FileUpload, WordStat
from app.schemas import FileUploadCreate, WordStatCreate
import logging

logger = logging.getLogger(__name__)


# === FILE UPLOAD ===

async def create_file_upload(
    db: AsyncSession,
    user_id: int,
    file_data: FileUploadCreate
) -> FileUpload:
    new_file = FileUpload(user_id=user_id, **file_data.dict())
    db.add(new_file)
    await db.commit()
    await db.refresh(new_file)
    return new_file


async def get_user_files(db: AsyncSession, user_id: int) -> List[FileUpload]:
    result = await db.execute(
        select(FileUpload).where(FileUpload.user_id == user_id)
    )
    return result.scalars().all()


async def delete_file_upload(
    db: AsyncSession,
    file_id: int,
    user_id: int
) -> Optional[FileUpload]:
    result = await db.execute(
        select(FileUpload).where(
            FileUpload.id == file_id,
            FileUpload.user_id == user_id
        )
    )
    file = result.scalar_one_or_none()
    if file:
        await db.delete(file)
        await db.commit()
    logger.info(f"Удалён файл ID={file_id} пользователем ID={user_id}")
    return file


async def count_documents(db: AsyncSession) -> int:
    result = await db.execute(select(func.count()).select_from(FileUpload))
    return result.scalar_one()


# === WORD STAT ===

async def create_word_stat(
    db: AsyncSession,
    stat_data: WordStatCreate
) -> WordStat:
    word_stat = WordStat(**stat_data.dict())
    db.add(word_stat)
    await db.commit()
    await db.refresh(word_stat)
    return word_stat


async def get_word_stat_for_file(db: AsyncSession, file_id: int) -> List[WordStat]:
    result = await db.execute(
        select(WordStat).where(WordStat.file_id == file_id)
    )
    return result.scalars().all()


async def delete_word_stat_for_file(db: AsyncSession, file_id: int) -> None:
    await db.execute(
        delete(WordStat).where(WordStat.file_id == file_id)
    )
    await db.commit()
