from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import text
import time
from typing import Dict, Any, Optional

# Local imports
from schemas import (TranslationRequest, TranslationResponse, BatchTranslationRequest, BatchTranslationResponse,
                    MinimalTranslationResponse, MinimalBatchTranslationResponse)
from models import Translation
from database import get_db, init_database, get_db_session
from cache_manager import cache_manager
from translation_services import translation_service

# Initialize FastAPI microservice
app = FastAPI(
    title="Translation Microservice",
    description="High-performance translation microservice with multi-level caching, ISO language support, and 1000 character limit",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware for microservice
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["POST", "GET"],
    allow_headers=["content-type", "authorization"],
)

# Global variables for tracking
start_time = time.time()
total_translations = 0

@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    init_database()
    print("🚀 Translation Microservice Started!")
    print("📝 POST /translate - Single translation (max 1000 chars)")
    print("📝 POST /translate/batch - Batch translations")
    print("🌍 Supports all ISO 639 language codes")
    print("🔄 Multi-level caching enabled")
    print("⚡ Parallel processing ready")

@app.post("/translate", response_model=TranslationResponse)
async def translate_text(
    request: TranslationRequest, 
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    POST /translate - Single text translation
    
    Request Body (JSON):
    {
        "text": "Hello world",
        "target_language": "ta", 
        "source_language": "auto"
    }
    
    Response (JSON):
    {
        "translated_text": "வணக்கம் உலகம்",
        "source_language": "en",
        "target_language": "ta",
        "service": "mymemory",
        "confidence": 85,
        "original_text": "Hello world",
        "cache_level": "L1",
        "processing_time_ms": 45.2
    }
    """
    start_time_ms = time.time() * 1000
    global total_translations
    
    try:
        # Check multi-level cache first (L1 → L2)
        cached_result = await cache_manager.get(request.text, request.target_language)
        if cached_result:
            processing_time = (time.time() * 1000) - start_time_ms
            cached_result["processing_time_ms"] = round(processing_time, 2)
            return TranslationResponse(**cached_result)
        
        # Not in cache, translate using cascading services
        translation_result = await translation_service.translate(
            request.text, 
            request.target_language, 
            request.source_language
        )
        
        # Store in multi-level cache for future requests
        await cache_manager.set(request.text, request.target_language, translation_result)
        
        # Store in database (background task)
        background_tasks.add_task(
            store_translation_in_db,
            request.text, translation_result
        )
        
        # Calculate processing time and format response
        processing_time = (time.time() * 1000) - start_time_ms
        translation_result["processing_time_ms"] = round(processing_time, 2)
        translation_result["cache_level"] = None  # Fresh translation
        
        total_translations += 1
        
        return TranslationResponse(**translation_result)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Translation failed: {str(e)}")

@app.post("/translate/batch")
async def translate_batch(
    request: BatchTranslationRequest,
    background_tasks: BackgroundTasks,
    minimal: bool = Query(False, description="Return minimal response without metadata"),
    db: Session = Depends(get_db)
):
    """
    POST /translate/batch - Batch text translation with parallel processing
    
    Request Body (JSON):
    {
        "texts": ["Hello", "Good morning", "Thank you"],
        "target_language": "ta",
        "source_language": "auto"
    }
    
    Response (JSON):
    {
        "results": [
            {
                "translated_text": "வணக்கம்",
                "source_language": "en",
                "target_language": "ta",
                "service": "mymemory",
                "confidence": 85,
                "original_text": "Hello",
                "cache_level": "L2"
            },
            ...
        ],
        "total_count": 3,
        "successful_count": 3,
        "failed_count": 0,
        "total_processing_time_ms": 125.7,
        "cache_hits": 1,
        "api_calls": 2
    }
    """
    start_time_ms = time.time() * 1000
    global total_translations
    
    try:
        results = []
        cache_hits = 0
        api_calls = 0
        
        # Process all translations with individual timing
        for text in request.texts:
            individual_start = time.time() * 1000
            
            # Check multi-level cache first
            cached_result = await cache_manager.get(text, request.target_language)
            if cached_result:
                # Add individual processing time for cache hit
                cached_result["processing_time_ms"] = round((time.time() * 1000) - individual_start, 2)
                results.append(cached_result)
                cache_hits += 1
            else:
                # Translate using cascading services
                translation_result = await translation_service.translate(
                    text, 
                    request.target_language, 
                    request.source_language
                )
                
                # Add individual processing time and cache level
                translation_result["processing_time_ms"] = round((time.time() * 1000) - individual_start, 2)
                translation_result["cache_level"] = "fresh"  # Fresh translation, not cached
                
                # Store in multi-level cache
                await cache_manager.set(text, request.target_language, translation_result)
                
                # Store in database (background)
                background_tasks.add_task(
                    store_translation_in_db,
                    text, translation_result
                )
                
                results.append(translation_result)
                api_calls += 1
        
        # Calculate statistics
        total_processing_time = (time.time() * 1000) - start_time_ms
        successful_count = len([r for r in results if not r.get("error")])
        failed_count = len(results) - successful_count
        
        total_translations += len(results)
        
        # Return minimal or full response based on query parameter
        if minimal:
            # Clean minimal response
            minimal_results = [
                MinimalTranslationResponse(
                    translated_text=result["translated_text"],
                    source_language=result["source_language"],
                    target_language=result["target_language"]
                ) for result in results if not result.get("error")
            ]
            
            return MinimalBatchTranslationResponse(
                results=minimal_results,
                total_count=len(results),
                successful_count=successful_count,
                failed_count=failed_count
            )
        else:
            # Full response with metadata
            response_results = [TranslationResponse(**result) for result in results]
            
            return BatchTranslationResponse(
                results=response_results,
                total_count=len(results),
                successful_count=successful_count,
                failed_count=failed_count,
                total_processing_time_ms=round(total_processing_time, 2),
                cache_hits=cache_hits,
                api_calls=api_calls
            )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Batch translation failed: {str(e)}")

@app.get("/health")
async def health_check():
    """Comprehensive health check with actual service testing"""
    import httpx
    
    health_results = {
        "status": "unknown",
        "version": "1.0.0",
        "timestamp": time.time(),
        "services": {},
        "cache_stats": {},
        "database_connected": False,
        "uptime_seconds": round(time.time() - start_time, 2),
        "total_translations": total_translations,
        "max_text_length": 1000,
        "supported_methods": ["POST"]
    }
    
    service_checks = []
    
    try:
        # 1. Test Database Connection
        try:
            with get_db_session() as db:
                result = db.execute(text("SELECT 1")).fetchone()
                if result and result[0] == 1:
                    health_results["database_connected"] = True
                    service_checks.append(True)
                else:
                    service_checks.append(False)
        except Exception as e:
            print(f"⚠️ Database health check failed: {e}")
            service_checks.append(False)
        
        # 2. Test MyMemory API
        mymemory_status = {
            "configured": bool(translation_service.mymemory_api_key),
            "reachable": False,
            "response_time_ms": None,
            "error": None
        }
        
        if translation_service.mymemory_api_key:
            try:
                start_test = time.time() * 1000
                async with httpx.AsyncClient(timeout=5) as client:
                    test_response = await client.get(
                        f"{translation_service.mymemory_base_url}/get",
                        params={"q": "test", "langpair": "en|es", "key": translation_service.mymemory_api_key}
                    )
                    if test_response.status_code == 200:
                        mymemory_status["reachable"] = True
                        mymemory_status["response_time_ms"] = round((time.time() * 1000) - start_test, 2)
                        service_checks.append(True)
                    else:
                        mymemory_status["error"] = f"HTTP {test_response.status_code}"
                        service_checks.append(False)
            except Exception as e:
                mymemory_status["error"] = str(e)[:100]
                service_checks.append(False)
        else:
            service_checks.append(False)
        
        health_results["services"]["mymemory"] = mymemory_status
        
        # 3. Test LibreTranslate API
        libretranslate_status = {
            "reachable": False,
            "response_time_ms": None,
            "error": None
        }
        
        try:
            start_test = time.time() * 1000
            async with httpx.AsyncClient(timeout=10) as client:
                test_response = await client.get(f"{translation_service.libretranslate_base_url}/languages")
                if test_response.status_code == 200:
                    libretranslate_status["reachable"] = True
                    libretranslate_status["response_time_ms"] = round((time.time() * 1000) - start_test, 2)
                    service_checks.append(True)
                else:
                    libretranslate_status["error"] = f"HTTP {test_response.status_code}"
                    service_checks.append(False)
        except Exception as e:
            libretranslate_status["error"] = str(e)[:100]
            service_checks.append(False)
        
        health_results["services"]["libretranslate"] = libretranslate_status
        
        # 4. Test Redis Connection
        redis_status = {
            "connected": False,
            "response_time_ms": None,
            "error": None
        }
        
        if cache_manager.redis_client:
            try:
                start_test = time.time() * 1000
                ping_result = cache_manager.redis_client.ping()
                if ping_result:
                    redis_status["connected"] = True
                    redis_status["response_time_ms"] = round((time.time() * 1000) - start_test, 2)
                    service_checks.append(True)
                else:
                    redis_status["error"] = "Ping failed"
                    service_checks.append(False)
            except Exception as e:
                redis_status["error"] = str(e)[:100]
                service_checks.append(False)
        else:
            redis_status["error"] = "Redis client not initialized"
            service_checks.append(False)
        
        health_results["services"]["redis"] = redis_status
        
        # 5. Mock Fallback Status
        mock_status = {
            "enabled": translation_service.enable_mock_fallback,
            "dictionary_size": len(translation_service.mock_translations) if translation_service.enable_mock_fallback else 0
        }
        health_results["services"]["mock_fallback"] = mock_status
        if translation_service.enable_mock_fallback:
            service_checks.append(True)
        
        # 6. Get detailed cache statistics
        cache_stats = cache_manager.get_cache_stats()
        health_results["cache_stats"] = cache_stats
        
        # 7. Determine overall health status
        critical_services = service_checks[:2]  # Database and MyMemory are critical
        total_services = len(service_checks)
        healthy_services = sum(service_checks)
        
        if all(critical_services) and healthy_services >= total_services * 0.8:  # 80% services healthy
            health_results["status"] = "healthy"
        elif any(critical_services):  # At least one critical service working
            health_results["status"] = "degraded"
        else:
            health_results["status"] = "unhealthy"
        
        # Add service summary
        health_results["service_summary"] = {
            "total_services": total_services,
            "healthy_services": healthy_services,
            "health_percentage": round((healthy_services / total_services) * 100, 1) if total_services > 0 else 0
        }
        
        return health_results
        
    except Exception as e:
        health_results["status"] = "error"
        health_results["error"] = str(e)
        return health_results

def store_translation_in_db(text: str, translation_result: Dict[str, Any]):
    """Background task to store translation in database"""
    try:
        with get_db_session() as db:
            text_hash = Translation.generate_hash(text, translation_result["target_language"])
            
            # Check if translation already exists
            existing = db.query(Translation).filter(Translation.text_hash == text_hash).first()
            
            if not existing:
                # Store new translation
                db_translation = Translation(
                    text_hash=text_hash,
                    source_text=text,
                    target_language=translation_result["target_language"],
                    source_language=translation_result["source_language"],
                    translated_text=translation_result["translated_text"],
                    translation_service=translation_result["service"],
                    confidence=translation_result["confidence"],
                    is_cached=True
                )
                db.add(db_translation)
                db.commit()
                
    except Exception as e:
        print(f"⚠️ Database storage failed: {e}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app", 
        host="0.0.0.0", 
        port=8000, 
        reload=True,
        log_level="info"
    )
