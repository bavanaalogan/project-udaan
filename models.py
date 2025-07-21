from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
import hashlib

Base = declarative_base()

class Translation(Base):
    __tablename__ = "translations"
    
    id = Column(Integer, primary_key=True, index=True)
    text_hash = Column(String(64), index=True)  # SHA256 hash of original text
    source_text = Column(Text, nullable=False)
    target_language = Column(String(10), nullable=False, index=True)
    source_language = Column(String(10), default="auto")
    translated_text = Column(Text, nullable=False)
    translation_service = Column(String(50))  # mymemory, libretranslate, mock
    confidence = Column(Integer, default=0)  # 0-100
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    is_cached = Column(Boolean, default=True)
    
    @staticmethod
    def generate_hash(text: str, target_language: str) -> str:
        """Generate a unique hash for text + target language combination"""
        combined = f"{text.lower().strip()}:{target_language.lower()}"
        return hashlib.sha256(combined.encode()).hexdigest()
    
    def __repr__(self):
        return f"<Translation(id={self.id}, service={self.translation_service}, lang={self.target_language})>"
