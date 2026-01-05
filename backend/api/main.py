"""FastAPI main application for translation service."""
import logging
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, HTTPException, UploadFile, File, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from pydantic import BaseModel, Field

from config import settings
from translator.engine import engine
from translator.cache import cache
from translator.document_processor import processor

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown events."""
    logger.info("Starting translation service...")
    yield
    logger.info("Shutting down translation service...")


app = FastAPI(
    title="LangGraph Translation Service",
    description="AI-powered English ↔ Korean translation service",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Pydantic models
class TranslateRequest(BaseModel):
    """Request model for text translation."""
    text: str = Field(..., min_length=1, description="Text to translate")


class TranslateResponse(BaseModel):
    """Response model for text translation."""
    original: str
    detected_language: str
    translation: str
    quality_score: float


class HealthResponse(BaseModel):
    """Response model for health check."""
    status: str
    version: str


class StatsResponse(BaseModel):
    """Response model for statistics."""
    cache_stats: dict
    total_translations: int


# API endpoints
@app.get("/api/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "version": "1.0.0"
    }


@app.get("/api/stats", response_model=StatsResponse)
async def get_stats():
    """Get translation statistics."""
    stats = cache.get_stats()
    return {
        "cache_stats": stats,
        "total_translations": stats["total_requests"]
    }


@app.post("/api/translate", response_model=TranslateResponse)
async def translate_text(request: TranslateRequest):
    """
    Translate text between English and Korean.
    
    Automatically detects language and translates to the other language.
    Results are cached for 24 hours.
    """
    try:
        text = request.text.strip()
        
        if not text:
            raise HTTPException(status_code=400, detail="Text cannot be empty")
        
        # Check cache first
        cached_result = cache.get(text)
        if cached_result:
            logger.info("Returning cached translation")
            return cached_result
        
        # Perform translation
        logger.info(f"Translating text: {len(text)} characters")
        result = engine.translate(text)
        
        if "error" in result:
            raise HTTPException(status_code=500, detail=result["error"])
        
        # Cache the result
        cache.set(text, result)
        
        return result
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Translation error: {e}")
        raise HTTPException(status_code=500, detail=f"Translation failed: {str(e)}")


@app.post("/api/translate/document")
async def translate_document(file: UploadFile = File(...)):
    """
    Translate uploaded document (PDF, DOCX, TXT).
    
    Returns translated document as downloadable file.
    """
    try:
        # Validate file
        if not file.filename:
            raise HTTPException(status_code=400, detail="No filename provided")
        
        if not processor.is_supported(file.filename):
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported file format. Supported: {processor.SUPPORTED_FORMATS}"
            )
        
        # Check file size (10MB limit)
        content = await file.read()
        if len(content) > 10 * 1024 * 1024:
            raise HTTPException(status_code=400, detail="File too large. Maximum size: 10MB")
        
        # Extract text
        logger.info(f"Processing document: {file.filename}")
        from io import BytesIO
        text = processor.extract_text(file.filename, BytesIO(content))
        
        if not text.strip():
            raise HTTPException(status_code=400, detail="No text extracted from document")
        
        # Chunk and translate
        chunks = processor.chunk_text(text)
        translated_chunks = []
        
        for i, chunk in enumerate(chunks):
            logger.info(f"Translating chunk {i + 1}/{len(chunks)}")
            
            # Check cache for each chunk
            cached = cache.get(chunk)
            if cached:
                translated_chunks.append(cached["translation"])
            else:
                result = engine.translate(chunk)
                if "error" not in result:
                    translated_chunks.append(result["translation"])
                    cache.set(chunk, result)
                else:
                    translated_chunks.append(f"[Translation error: {result['error']}]")
        
        # Combine translations
        full_translation = "\n\n".join(translated_chunks)
        
        # Generate output file
        output_format = "txt"  # Always return as TXT for simplicity
        output_content = processor.save_translated_document(
            file.filename,
            full_translation,
            output_format
        )
        
        # Create filename
        from pathlib import Path
        base_name = Path(file.filename).stem
        output_filename = f"{base_name}_translated.{output_format}"
        
        return Response(
            content=output_content,
            media_type="text/plain",
            headers={
                "Content-Disposition": f"attachment; filename={output_filename}"
            }
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Document translation error: {e}")
        raise HTTPException(status_code=500, detail=f"Document translation failed: {str(e)}")


@app.websocket("/ws/translate")
async def websocket_translate(websocket: WebSocket):
    """
    WebSocket endpoint for real-time translation.
    
    Client sends text, server responds with translation.
    """
    await websocket.accept()
    logger.info("WebSocket connection established")
    
    try:
        while True:
            # Receive text from client
            data = await websocket.receive_text()
            
            if not data.strip():
                await websocket.send_json({
                    "error": "Empty text received"
                })
                continue
            
            logger.info(f"WebSocket translation request: {len(data)} characters")
            
            # Check cache
            cached = cache.get(data)
            if cached:
                await websocket.send_json(cached)
                continue
            
            # Translate
            try:
                result = engine.translate(data)
                if "error" not in result:
                    cache.set(data, result)
                    await websocket.send_json(result)
                else:
                    await websocket.send_json({
                        "error": result["error"]
                    })
            except Exception as e:
                logger.error(f"WebSocket translation error: {e}")
                await websocket.send_json({
                    "error": str(e)
                })
    
    except WebSocketDisconnect:
        logger.info("WebSocket connection closed")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
