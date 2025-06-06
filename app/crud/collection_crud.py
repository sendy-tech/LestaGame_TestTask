from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload

from app.models.user import User
from app.models.collection import Collection
from app.models.document import FileUpload, WordStat
from app.schemas import CollectionCreate


async def create_collection(
    db: AsyncSession,
    user: User,
    collection_data: CollectionCreate
) -> Collection:
    new_collection = Collection(
        name=collection_data.name,
        description=collection_data.description,
        user_id=user.id
    )
    db.add(new_collection)
    await db.commit()
    await db.refresh(new_collection)
    return new_collection


async def get_user_collections(db: AsyncSession, user: User):
    result = await db.execute(
        select(Collection)
        .options(selectinload(Collection.files))
        .where(Collection.user_id == user.id)
    )
    return result.scalars().all()

async def get_user_collections_with_ids(db: AsyncSession, user: User):
    result = await db.execute(
        select(Collection)
        .where(Collection.user_id == user.id)
        .options(selectinload(Collection.files))
    )
    collections = result.scalars().all()

    return [
        {
            "collection_id": collection.id,
            "collection_name": collection.name,
            "documents_name": [file.filename for file in collection.files]
        }
        for collection in collections
    ]


async def get_collection_by_id(
    db: AsyncSession,
    collection_id: int,
    user: User
) -> Collection | None:
    result = await db.execute(
        select(Collection)
        .options(selectinload(Collection.files))
        .where(
            Collection.id == collection_id,
            Collection.user_id == user.id
        )
    )
    return result.scalar_one_or_none()


async def add_file_to_collection(
    db: AsyncSession,
    collection_id: int,
    file_id: int,
    user: User
):
    collection = await get_collection_by_id(db, collection_id, user)

    if not collection:
        # Создаём новую коллекцию без id
        collection = Collection(name=f"Коллекция {collection_id}", user_id=user.id)
        db.add(collection)
        await db.commit()  # Коммит, чтобы получить id и привязать объект
        await db.refresh(collection)

    file = await db.get(FileUpload, file_id)
    if not file or file.user_id != user.id:
        return None

    if file not in collection.files:
        collection.files.append(file)
        await db.commit()
        await db.refresh(collection)

    return collection


async def remove_file_from_collection(
    db: AsyncSession,
    collection_id: int,
    file_id: int,
    user: User
):
    collection = await get_collection_by_id(db, collection_id, user)
    if not collection:
        return None
    file = await db.get(FileUpload, file_id)
    if file and file in collection.files:
        collection.files.remove(file)
        await db.commit()
    return collection


async def get_collection_word_stat(
    db: AsyncSession,
    collection_id: int,
    user: User
) -> list[dict]:
    collection = await get_collection_by_id(db, collection_id, user)
    if not collection:
        return []

    file_ids = [file.id for file in collection.files]
    if not file_ids:
        return []

    result = await db.execute(
        select(
            WordStat.word,
            func.sum(WordStat.tf).label("sum_tf"),
        )
        .where(WordStat.file_id.in_(file_ids))
        .group_by(WordStat.word)
    )
    rows = result.all()
    return [{"word": row.word, "tf": row.sum_tf} for row in rows]


async def get_or_create_default_collection(db: AsyncSession, user: User) -> Collection:
    result = await db.execute(
        select(Collection).where(Collection.name == "default", Collection.user_id == user.id)
    )
    collection = result.scalar_one_or_none()
    if not collection:
        collection = Collection(name="default", user_id=user.id)
        db.add(collection)
    return collection


async def add_file_to_default_collection(db: AsyncSession, file: FileUpload, user: User) -> None:
    from app.crud.collection_crud import get_or_create_default_collection

    result = await db.execute(
        select(Collection)
        .options(selectinload(Collection.files))
        .where(Collection.name == "default", Collection.user_id == user.id)
    )
    collection = result.scalar_one_or_none()

    if not collection:
        collection = await get_or_create_default_collection(db, user)

    if all(f.id != file.id for f in collection.files):
        collection.files.append(file)

async def count_collections(db: AsyncSession) -> int:
    result = await db.execute(select(func.count()).select_from(Collection))
    return result.scalar_one()
