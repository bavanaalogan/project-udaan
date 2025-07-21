from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any
from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
import hashlib
import os
from dotenv import load_dotenv

load_dotenv()

# Configuration
MAX_TEXT_LENGTH = int(os.getenv("MAX_TEXT_LENGTH", 1000))
MAX_BATCH_SIZE = int(os.getenv("MAX_BATCH_SIZE", 100))

# SQLAlchemy Models
Base = declarative_base()

class Translation(Base):
    __tablename__ = "translations"
    
    id = Column(Integer, primary_key=True, index=True)
    text_hash = Column(String(64), index=True)
    source_text = Column(Text, nullable=False)
    target_language = Column(String(10), nullable=False, index=True)
    source_language = Column(String(10), default="auto")
    translated_text = Column(Text, nullable=False)
    translation_service = Column(String(50))
    confidence = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    is_cached = Column(Boolean, default=True)
    
    @staticmethod
    def generate_hash(text: str, target_language: str) -> str:
        """Generate a unique hash for text + target language combination"""
        combined = f"{text.lower().strip()}:{target_language.lower()}"
        return hashlib.sha256(combined.encode()).hexdigest()

# Pydantic Models
class TranslationRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=MAX_TEXT_LENGTH, description="Text to translate")
    target_language: str = Field(..., min_length=2, max_length=10, description="Target language code (e.g., 'ta', 'hi', 'en')")
    source_language: str = Field(default="auto", min_length=2, max_length=10, description="Source language code or 'auto' for detection")
    
    @validator('text')
    def validate_text(cls, v):
        if not v or v.isspace():
            raise ValueError('Text cannot be empty or only whitespace')
        return v.strip()
    
    @validator('target_language', 'source_language')
    def validate_language_codes(cls, v):
        if v == "auto":
            return v
        
        v_clean = v.lower().strip()
        
        if len(v_clean) < 2 or len(v_clean) > 10:
            raise ValueError('Language code must be between 2-10 characters (ISO 639 format)')
        
        if not all(c.isalnum() or c == '-' for c in v_clean):
            raise ValueError('Language code must contain only letters, numbers, and hyphens')
        
        return v_clean

class BatchTranslationRequest(BaseModel):
    texts: List[str] = Field(..., min_items=1, max_items=MAX_BATCH_SIZE, description="List of texts to translate")
    target_language: str = Field(..., min_length=2, max_length=10, description="Target language code")
    source_language: str = Field(default="auto", min_length=2, max_length=10, description="Source language code or 'auto'")
    
    @validator('texts')
    def validate_texts(cls, v):
        if not v:
            raise ValueError('Texts list cannot be empty')
        
        validated_texts = []
        for i, text in enumerate(v):
            if not text or text.isspace():
                raise ValueError(f'Text at index {i} cannot be empty or only whitespace')
            if len(text) > MAX_TEXT_LENGTH:
                raise ValueError(f'Text at index {i} exceeds maximum length of {MAX_TEXT_LENGTH} characters')
            validated_texts.append(text.strip())
        
        return validated_texts
    
    @validator('target_language', 'source_language')
    def validate_language_codes(cls, v):
        if v == "auto":
            return v
        
        v_clean = v.lower().strip()
        
        if len(v_clean) < 2 or len(v_clean) > 10:
            raise ValueError('Language code must be between 2-10 characters (ISO 639 format)')
        
        if not all(c.isalnum() or c == '-' for c in v_clean):
            raise ValueError('Language code must contain only letters, numbers, and hyphens')
        
        return v_clean

class TranslationResponse(BaseModel):
    translated_text: str
    source_language: str
    target_language: str
    service: str
    confidence: int = Field(ge=0, le=100, description="Confidence score (0-100)")
    original_text: str
    cache_level: Optional[str] = None
    processing_time_ms: Optional[float] = None
    error: Optional[str] = None

class BatchTranslationResponse(BaseModel):
    results: List[TranslationResponse]
    total_count: int
    successful_count: int
    failed_count: int
    total_processing_time_ms: float
    cache_hits: int
    api_calls: int

class MinimalTranslationResponse(BaseModel):
    translated_text: str
    source_language: str
    target_language: str

class MinimalBatchTranslationResponse(BaseModel):
    results: List[MinimalTranslationResponse]
    total_count: int
    successful_count: int
    failed_count: int
