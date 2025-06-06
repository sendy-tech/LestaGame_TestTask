from pydantic import BaseModel, ConfigDict
from sqlalchemy import Column, Integer, String, ForeignKey, Float, DateTime, func
from sqlalchemy.orm import relationship
from app.database import Base

class FileUpload(Base):
    """
    Представляет загруженный файл с метаданными:
    - user_id: пользователь-владелец
    - created_at: дата и время загрузки
    - unique_words: количество уникальных слов
    """
    __tablename__ = "fileuploads"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, nullable=False)
    content = Column(String, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    unique_words = Column(Integer, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="files")
    collections = relationship(
        "Collection",
        secondary="collection_documents",
        back_populates="files",
        lazy="selectin"
    )
    word_stat = relationship("WordStat", back_populates="file", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<FileUpload(id={self.id}, filename={self.filename})>"


class WordStat(Base):
    """
    Представляет статистику слова в загруженном документе:
    - file_id: внешний ключ к файлу
    - user_id: пользователь, загрузивший файл
    - word: слово
    - tf: term frequency
    - idf: inverse document frequency
    """
    __tablename__ = "word_stat"

    id = Column(Integer, primary_key=True)
    file_id = Column(Integer, ForeignKey("fileuploads.id", ondelete="CASCADE"))
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    word = Column(String, nullable=False)
    tf = Column(Float)
    idf = Column(Float)

    file = relationship("FileUpload", back_populates="word_stat")
    user = relationship("User", back_populates="word_stat")

class FileUploadShort(BaseModel):
    id: int
    filename: str

    model_config = ConfigDict(from_attributes=True)
