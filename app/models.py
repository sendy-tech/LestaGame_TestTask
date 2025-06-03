from sqlalchemy import Column, Integer, String, Float, DateTime, func, ForeignKey
from app.database import Base

# Модель загрузки файла
class FileUpload(Base):
    __tablename__ = "file_uploads"
    """
    Представляет загруженный файл.

    Хранит:
    - дату/время загрузки
    - количество уникальных слов
    """
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    timestamp = Column(DateTime, server_default=func.now())
    unique_words = Column(Integer)

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

    id = Column(Integer, primary_key=True)
    file_id = Column(Integer, ForeignKey("file_uploads.id", ondelete="CASCADE"))
    word = Column(String)
    tf = Column(Float)
    idf = Column(Float)
