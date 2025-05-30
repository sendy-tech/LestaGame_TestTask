from sqlalchemy import Column, Integer, String, Float, DateTime, func
from database import Base

class FileUpload(Base):
    __tablename__ = "file_uploads"

    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, server_default=func.now())
    unique_words = Column(Integer)

class WordStat(Base):
    __tablename__ = "word_stats"

    id = Column(Integer, primary_key=True)
    file_id = Column(Integer)
    word = Column(String)
    tf = Column(Float)
    idf = Column(Float)