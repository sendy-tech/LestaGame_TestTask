from sqlalchemy import Column, Integer, String, Float, DateTime, func, ForeignKey
from database import Base

# Модель загрузки файла
class FileUpload(Base):
    """
    Представляет загруженный файл.

    Хранит:
    - дату/время загрузки
    - количество уникальных слов
    """
    __tablename__ = "file_uploads"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, server_default=func.now(), nullable=False)
    unique_words = Column(Integer, nullable=False)


# Модель статистики слов
class WordStat(Base):
    """
    Представляет статистику одного слова из загруженного файла.

    Хранит:
    - идентификатор файла
    - само слово
    - TF
    - IDF
    """
    __tablename__ = "word_stats"

    id = Column(Integer, primary_key=True, index=True)
    file_id = Column(Integer, ForeignKey("file_uploads.id"), nullable=False)
    word = Column(String, nullable=False)
    tf = Column(Float, nullable=False)
    idf = Column(Float, nullable=False)
