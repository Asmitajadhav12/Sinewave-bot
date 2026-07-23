import os
from app.services.supabase.embedding_operations import generate_error_desc_embeddings, generate_screenshot_embedding
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import List, Optional
import logging

from app.services.supabase import get_error_by_id

router = APIRouter()
logger = logging.getLogger(__name__)

class GenerateEmbeddingsRequest(BaseModel):
    screenshot_ids: List[int] = []

@router.post("/error/{error_id}/embeddings")
async def generate_embeddings_endpoint(error_id: int, request: GenerateEmbeddingsRequest, background_tasks: BackgroundTasks):
    """
    Generates embeddings for a specific errodr description and its associated screenshots.
    This is triggered manually from the UI after creating/updating an error.
    """
    
    # Validation: Check if error exists
    error = get_error_by_id(error_id)
    if not error:
        raise HTTPException(status_code=404, detail=f"Error ID {error_id} not found.")

    # Process in background to avoid timeout
    background_tasks.add_task(process_embeddings_generation, error_id, error, request.screenshot_ids)

    return {"status": "processing", "message": f"Embedding generation started for Error {error_id}"}

async def process_embeddings_generation(error_id: int, error_data: dict, screenshot_ids: List[int]):
    """
    Background task to generate embeddings.
    """
    logger.info(f"Starting embedding generation for Error {error_id}...")
    
    try:
        # 1. Generate Embedding for Error Description (Manual Source)
        generate_error_desc_embeddings(error_id, error_data.get("errorDescription"), error_data.get("functionArea", "Unknown"))
        
        # 2. Generate Embeddings for Screenshots
        for screenshot_id in screenshot_ids:
            generate_screenshot_embedding(error_id, screenshot_id)

        logger.info(f"Embedding generation completed for Error {error_id}.")

    except Exception as e:
        logger.error(f"Critical error in embedding generation task for Error {error_id}: {e}")
