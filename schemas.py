from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any
import os
from dotenv import load_dotenv

load_dotenv()

# Configuration
MAX_TEXT_LENGTH = int(os.getenv("MAX_TEXT_LENGTH", 1000))
MAX_BATCH_SIZE = int(os.getenv("MAX_BATCH_SIZE", 100))

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
        
        # Accept all ISO 639-1 (2-letter) and ISO 639-2/639-3 (3-letter) codes
        # Plus region variants like en-US, zh-CN, etc.
        v_clean = v.lower().strip()
        
        # Basic format validation for ISO codes
        if len(v_clean) < 2 or len(v_clean) > 10:
            raise ValueError('Language code must be between 2-10 characters (ISO 639 format)')
        
        # Allow alphanumeric and hyphens for region codes (e.g., en-US, zh-CN)
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
        
        # Validate each text in the list
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
        
        # Accept all ISO 639-1 (2-letter) and ISO 639-2/639-3 (3-letter) codes
        # Plus region variants like en-US, zh-CN, etc.
        v_clean = v.lower().strip()
        
        # Basic format validation for ISO codes
        if len(v_clean) < 2 or len(v_clean) > 10:
            raise ValueError('Language code must be between 2-10 characters (ISO 639 format)')
        
        # Allow alphanumeric and hyphens for region codes (e.g., en-US, zh-CN)
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

class HealthCheckResponse(BaseModel):
    status: str
    version: str
    services: Dict[str, Any]
    cache_stats: Dict[str, Any]
    database_connected: bool
    uptime_seconds: float

class CacheStatsResponse(BaseModel):
    l1_cache: Dict[str, Any]
    l2_cache: Dict[str, Any]
    total_translations: int
    cache_hit_rate: float

class SupportedLanguagesResponse(BaseModel):
    supported_languages: Dict[str, str]
    indian_languages: Dict[str, str]
    total_count: int

class MinimalTranslationResponse(BaseModel):
    translated_text: str
    source_language: str
    target_language: str

class MinimalBatchTranslationResponse(BaseModel):
    results: List[MinimalTranslationResponse]
    total_count: int
    successful_count: int
    failed_count: int
