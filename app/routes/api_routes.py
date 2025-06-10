from http import HTTPStatus

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.responses import JSONResponse

from app.auth.auth_services import authenticate_user, create_access_token
from app.auth.dependencies import get_current_user
from app.crud import document_crud, collection_crud, user_crud
from app.database import get_db, async_session
from app.models.collection import CollectionsAddRequest
from app.models.user import User, UserCreate
from app.models.document import FileUpload, FileUploadShort
from app.schemas import (WordStatRead, CollectionWithDocumentIDs)
from app.services import inverse_document_frequency
from app.services import huffman_encode

router = APIRouter()


# === DOCUMENTS ===

@router.get(
    "/documents",
    response_model=list[FileUploadShort],
    summary="Получить список загруженных документов",
    tags=["Документ"],
    description="Возвращает список документов ('id', название), загруженных текущим пользователем."
)
async def list_documents(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user)
):
    if user is None:
        raise HTTPException(status_code=401, detail="Пользователь не авторизован")

    try:
        return await document_crud.get_user_files(db, user.id)
    except Exception as e:
        import logging
        logging.exception("Ошибка при получении документов")
        raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера")



@router.get(
    "/documents/{document_id}",
    summary="Получить документ",
    description="Возвращает содержимое документа",
    tags=["Документ"]
)
async def get_document(document_id: int, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    file = await db.get(FileUpload, document_id)
    if not file or file.user_id != user.id:
        raise HTTPException(status_code=404, detail="Документ не найден")
    return {
        "content": file.content
    }


@router.get(
    "/documents/{document_id}/statistics",
    response_model=list[WordStatRead],
    summary="Статистика по документу",
    description="Получает TF/IDF статистику по конкретному документу",
    tags=["Документ"]
)
async def get_document_stat(document_id: int, db: AsyncSession = Depends(get_db),
                             user: User = Depends(get_current_user)):
    file = await db.get(FileUpload, document_id)
    if not file or file.user_id != user.id:
        raise HTTPException(status_code=404, detail="Документ не найден")
    return await document_crud.get_word_stat_for_file(db, document_id)

@router.get(
    "/documents/{document_id}/huffman",
    summary="Код Хаффмана по документу",
    description="Возвращает содержимое документа, закодированное с помощью алгоритма Хаффмана",
    tags=["Документ"]
)
async def get_document_huffman(
    document_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user)
):
    file = await db.get(FileUpload, document_id)
    if not file or file.user_id != user.id:
        raise HTTPException(status_code=404, detail="Документ не найден")

    content = file.content
    if not content:
        raise HTTPException(status_code=400, detail="Документ пустой")

    encoded_text, huffman_tree = huffman_encode(content)

    return {
        "encoded": encoded_text,
        "tree": huffman_tree  # для справки/отладки
    }



@router.delete(
    "/documents/{document_id}",
    summary="Удалить документ",
    description="Удаляет документ",
    tags=["Документ"]
)
async def delete_document(document_id: int, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    file = await document_crud.delete_file_upload(db, document_id, user.id)
    if not file:
        raise HTTPException(status_code=404, detail="Документ не найден")
    await document_crud.delete_word_stat_for_file(db, document_id)
    return {"detail": "Документ и статистика удалены"}


# === COLLECTIONS ===

@router.get(
    "/collections",
    response_model=list[CollectionWithDocumentIDs],
    summary="Список коллекций",
    description="Получить список коллекций с id и списком входящих в них документов",
    tags=["Коллекция"]
)
async def list_collections(db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    if user is None:
        raise HTTPException(status_code=401, detail="Пользователь не авторизован")
    return await collection_crud.get_user_collections_with_ids(db, user)



@router.get(
    "/collections/{collection_id}",
    summary="Содержимое коллекции",
    description="Получить список ID документов, входящих в конкретную коллекцию",
    tags=["Коллекция"]
)
async def get_collection_documents(collection_id: int, db: AsyncSession = Depends(get_db),
                                   user: User = Depends(get_current_user)):
    collection = await collection_crud.get_collection_by_id(db, collection_id, user)
    if not collection:
        raise HTTPException(status_code=404, detail="Коллекция не найдена")
    return [file.id for file in collection.files]


@router.get(
    "/collections/{collection_id}/statistics",
    summary="TF/IDF по коллекции",
    description="Считает объединённый TF для всех документов коллекции и возвращает IDF",
    tags=["Коллекция"]
)
async def get_collection_statistics(collection_id: int, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    stats = await collection_crud.get_collection_word_stat(db, collection_id, user)
    words = [s["word"] for s in stats]

    idf_map = await inverse_document_frequency(db, user, words)

    print(f"IDF Map: {idf_map}")###############

    merged_stat = []
    for s in stats:
        idf = idf_map.get(s["word"], 0.0)
        merged_stat.append({
            "word": s["word"],
            "tf": round(s["tf"], 6),
            "idf": round(idf, 6)
        })

    return sorted(merged_stat, key=lambda x: x["idf"], reverse=True)


@router.post(
    "/collection/add_document_to_collections/{document_id}",
    summary="Добавить документ в несколько коллекций",
    description="Добавляет указанный документ во все указанные коллекции пользователя",
    tags=["Коллекция"]
)
async def add_document_to_collections(
    document_id: int,
    request: CollectionsAddRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user)
):
    added_collections = []
    for collection_id in request.collection_ids:
        result = await collection_crud.add_file_to_collection(db, collection_id, document_id, user)
        if result:
            added_collections.append(collection_id)
    if not added_collections:
        raise HTTPException(status_code=404, detail="Коллекции или документ не найдены или нет доступа")
    return {
        "detail": f"Документ добавлен в {len(added_collections)} коллекций",
        "collections_added": added_collections
    }


@router.delete(
    "/collection/{collection_id}/{document_id}",
    summary="Удалить документ из коллекции",
    description="Удаляет документ из указанной коллекции",
    tags=["Коллекция"]
)
async def remove_document_from_collection(collection_id: int, document_id: int, db: AsyncSession = Depends(get_db),
                                          user: User = Depends(get_current_user)):
    result = await collection_crud.remove_file_from_collection(db, collection_id, document_id, user)
    if not result:
        raise HTTPException(status_code=404, detail="Коллекция или документ не найдены")
    return {"detail": "Документ удалён из коллекции"}


# === USERS ===

@router.post(
    "/login",
    summary="Залогиниться",
    description="Получить токен авторизации и установить его в cookie",
    tags=["Пользователь"]
)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db)
):
    user = await authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=400, detail="Неверное имя пользователя или пароль")

    access_token = create_access_token(data={"sub": str(user.id)})

    # Создаём ответ
    response = JSONResponse(content={"access_token": access_token, "token_type": "bearer"})

    # Устанавливаем токен в cookie
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,       # Защита от доступа через JS
        secure=False,        # True в проде с HTTPS
        samesite="lax",      # Или "strict", если нужно
        max_age=60 * 60 * 24 # 24 часа
    )

    return response


@router.post(
    "/register",
    summary="Зарегистрироваться",
    description="Создать личную учётную запись, чтобы получить доступ к полному функционалу",
    tags=["Пользователь"]
)
async def register(data: UserCreate, db: AsyncSession = Depends(get_db)):
    existing_user = await user_crud.get_user_by_username(db, data.username)
    if existing_user:
        raise HTTPException(status_code=400, detail="Пользователь с таким именем уже существует")
    await user_crud.create_user(db, username=data.username, password=data.password)
    return {"detail": "Пользователь зарегистрирован"}


@router.get(
    "/logout",
    summary="Выход пользователя",
    description="Удаляет токен авторизации и завершает сессию",
    tags=["Пользователь"]
)
async def logout_user(request: Request):
    response = RedirectResponse("/", status_code=302)
    response.delete_cookie("access_token", path="/")
    return response


@router.patch(
    "/user/{user_id}",
    summary="Изменить пароль",
    description="Позволяет пользователю изменить свой пароль",
    tags=["Пользователь"]
)
async def change_password(user_id: int, new_password: str, db: AsyncSession = Depends(get_db),
                          current_user: User = Depends(get_current_user)):
    if user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Недостаточно прав")
    await user_crud.update_password(db, user_id, new_password)
    return {"detail": "Пароль обновлён"}


@router.delete(
    "/user/{user_id}",
    summary="Удалить пользователя",
    description="Удаляет аккаунт пользователя и все связанные с ним данные",
    tags=["Пользователь"]
)
async def delete_user(user_id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    if user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Недостаточно прав")
    await user_crud.delete_user(db, user_id)
    response = RedirectResponse("/", status_code=302)
    response.delete_cookie("Authorization")
    return response


# === METRICS ===

@router.get(
    "/metrics",
    summary="Метрики API",
    description="Простейшие диагностические метрики: количество пользователей, документов и коллекций в JSON формате",
    tags=["Сервис"]
)
async def get_metrics(current_user: User = Depends(get_current_user)
                      ,db: AsyncSession = Depends(get_db)):
    if not current_user:
        return RedirectResponse("/auth/login", status_code=HTTPStatus.SEE_OTHER)
    document_count = await document_crud.count_documents(db)
    collection_count = await collection_crud.count_collections(db)
    async with async_session() as session:
        total_uploads = await session.scalar(
            select(func.count()).select_from(FileUpload).where(FileUpload.user_id == current_user.id)
        )
        result = await session.execute(
            select(FileUpload)
            .where(FileUpload.user_id == current_user.id)
            .order_by(FileUpload.id.desc())
            .limit(1)
        )
        last_upload = result.scalars().first()

        unique_words = last_upload.unique_words if last_upload else 0

    return JSONResponse(content={
        "total_uploads": total_uploads,
        "unique_words": unique_words,
        "documents": document_count,
        "collections": collection_count
    })
