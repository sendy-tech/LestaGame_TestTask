from pydantic import BaseModel, constr
from typing import List, Optional
from datetime import datetime

# === FILE UPLOAD ===

class FileUploadBase(BaseModel):
    unique_words: int

class FileUploadCreate(FileUploadBase):
    """Схема создания записи о файле (ввод)"""
    pass

class FileUploadRead(FileUploadBase):
    """Схема вывода данных о файле (вывод)"""
    id: int
    user_id: int
    created_at: datetime
    filename: str
    content: str

    model_config = {
        "from_attributes": True
    }

# === WORD STAT ===

class WordStatBase(BaseModel):
    word: str
    tf: float
    idf: float

class WordStatCreate(WordStatBase):
    file_id: int

class WordStatRead(WordStatBase):
    id: int
    file_id: int

    model_config = {
        "from_attributes": True
    }

# === COLLECTION ===

class CollectionCreate(BaseModel):
    name: str
    description: Optional[str] = None

class CollectionRead(BaseModel):
    id: int
    name: str
    description: Optional[str]
    user_id: int

    model_config = {
        "from_attributes": True
    }

class CollectionWithFilesRead(CollectionRead):
    """Список файлов в коллекции"""
    files: List[FileUploadRead]

class CollectionWithDocumentIDs(BaseModel):
    """Список имён документов в коллекции"""
    collection_id: int
    collection_name: str
    documents_name: List[str]

    model_config = {
        "from_attributes": True
    }

class CollectionDocumentIDsRead(BaseModel):
    document_ids: List[int]

# === MERGED STATS FOR COLLECTION ===

class MergedStatRead(BaseModel):
    word: str
    tf: float
    idf: float

# === USER ===

class UserRead(BaseModel):
    id: int
    username: str
    created_at: datetime

    model_config = {
        "from_attributes": True
    }

class UserCreate(BaseModel):
    username: str
    password: constr(min_length=8)

# === STATUS&VERSION ===
class StatusResponse(BaseModel):
    status: str

class VersionResponse(BaseModel):
    version: str
