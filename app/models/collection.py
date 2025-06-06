from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base
from pydantic import BaseModel
from typing import List

class CollectionDocument(Base):
    __tablename__ = "collection_documents"

    id = Column(Integer, primary_key=True)
    collection_id = Column(Integer, ForeignKey("collections.id", ondelete="CASCADE"))
    document_id = Column(Integer, ForeignKey("fileuploads.id", ondelete="CASCADE"))

    def __repr__(self):
        return f"<CollectionDocument(collection_id={self.collection_id}, document_id={self.document_id})>"


class Collection(Base):
    __tablename__ = "collections"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(String, nullable=True)

    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    user = relationship("User", back_populates="collections")

    files = relationship(
        "FileUpload",
        secondary="collection_documents",
        back_populates="collections",
        lazy="selectin"
    )

    def __repr__(self):
        return f"<Collection(id={self.id}, name={self.name})>"

class CollectionsAddRequest(BaseModel):
    collection_ids: List[int]
