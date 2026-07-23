import os
from typing import List, Optional, Any
import logging
from .supabase_client import supabase

from app.services.supabase.screenshot_operations import get_screenshot_by_id
from app.services.openai_service import extract_text_from_image_path, get_embedding


logger = logging.getLogger(__name__)

ASSETS_DIR = os.getenv("ASSETS_DIR")

def insert_error_embedding(error_id: int, embedding: List[float], content: str, metadata: str = "", screenshot_id: Optional[int] = None) -> bool:
    """
    Inserts a record into the error_embeddings table using REST API.
    """
    try:
        logger.info(f"Inserting embedding for error_id: {error_id}. Metadata: {metadata}")
        # Using standard REST API insert
        data = {
            "error_info_id": error_id,
            "content": content,
            "embedding": embedding,
            "metadata": metadata
        }
        if screenshot_id:
             data["screenshot_id"] = screenshot_id

        response = supabase.table("error_embeddings").insert(data).execute()
        
        logger.info(f"Embedding inserted successfully for error_id {error_id}.")
        return True
    except Exception as e:
        logger.error(f"Error inserting embedding for error_id {error_id}: {e}")
        return False

def delete_manual_embedding(error_id: int) -> bool:
    """
    Deletes the 'manual' source embedding for a specific error.
    Used when the error description is updated.
    """
    try:
        # Metadata pattern: "Source: manual | Function: ..."
        # We use a filter to target this.
        # Note: metadata is a JSONB or text column? In ingest.py it's treated as text in the dict, 
        # but supabase might store it as such. 
        # Based on ingest.py: p_metadata: f"Source: manual | Function: {func}"
        # It seems it's a text column in 'error_embeddings' based on usage.
        
        # We delete where error_info_id = error_id AND metadata LIKE 'Source: manual%'
        response = supabase.table("error_embeddings") \
            .delete() \
            .eq("error_info_id", error_id) \
            .like("metadata", "Source: manual%") \
            .execute()
            
        logger.info(f"Deleted manual embedding for error {error_id}")
        return True
    except Exception as e:
        logger.error(f"Error deleting manual embedding for error {error_id}: {e}")
        return False

def check_embedding_exists(error_id: int, source_type: str, screenshot_id: Optional[int] = None) -> bool:
    """
    Checks if an embedding exists for the given source.
    matched via metadata LIKE 'Source: {source_type}%'
    If screenshot_id is provided, matches 'Source: screenshot | Screenshot ID: {screenshot_id}'
    """
    try:
        query = supabase.table("error_embeddings").select("id").eq("error_info_id", error_id)
        
        if source_type == "manual":
            query = query.like("metadata", "Source: manual%")
        elif source_type == "screenshot" and screenshot_id:
             query = query.eq("screenshot_id", screenshot_id)
        else:
            return False

        response = query.execute()
        return bool(response.data and len(response.data) > 0)
    except Exception as e:
        logger.error(f"Error checking embedding existence: {e}")
        return False

def generate_error_desc_embeddings(error_id: int, description: Optional[str], func_area: Optional[str] = "N/A"):
    """
    function to generate embeddings for error description.
    """
    logger.info(f"Starting embedding generation for Error description for {error_id}...")
    
    try:
        if description:
            try:
                # Text content for embedding
                text_content = f"Error: {description}" 
                # (Matches ingest.py format: f"Error: {desc}")
                
                # Metadata
                # (Matches ingest.py format: f"Source: manual | Function: {func}")
                meta_manual = f"Source: manual | Function: {func_area}"
                
                logger.info(f"Generating manual error description embedding for Error {error_id}...")
                emb_manual = get_embedding(text_content)
                
                if emb_manual:
                    success = insert_error_embedding(error_id, emb_manual, text_content, meta_manual)
                    if success:
                        logger.info(f"Manual error description embedding saved for Error {error_id}.")
                    else:
                        logger.error(f"Failed to save manual error description embedding for Error {error_id}.")
            except Exception as e:
                logger.error(f"Error generating manual error description embedding for Error {error_id}: {e}")
    except Exception as e:
        logger.error(f"Critical error in error description embedding generation for Error {error_id}: {e}")

def generate_screenshot_embedding(error_id: int, screenshot_id: int):
    """
    function to generate embedding for a screenshot.
    """
    logger.info(f"Starting embedding generation for Screenshot {screenshot_id} of Error {error_id}...")

    try:
        screenshot = get_screenshot_by_id(screenshot_id)
        if not screenshot:
            logger.warning(f"Screenshot ID {screenshot_id} not found for Error {error_id}, skipping.")
            return
        
        extracted_text = screenshot.get("extracted_text")
        screenshot_url = screenshot.get("screenshot_url") # relative or full url? 
        # ingest.py uses: f"Source: screenshot | Image: {db_image_url}"
        # db_image_url in ingest.py is passed as p_screenshot_url to create_error_screenshot.
        # So screenshot['screenshot_url'] should be what we want.
        
        if not extracted_text or extracted_text == "No text extracted":
            logger.info(f"Screenshot {screenshot_id} has no extracted text, so extracting text")
            base_assets_path = os.path.abspath(ASSETS_DIR)
            image_path = os.path.join(base_assets_path, screenshot_url)
            extracted_text = extract_text_from_image_path(image_path) or "No text extracted"
            # TODO: update extracted text in screenshots table

        logger.info(f"Generating embedding for Screenshot {screenshot_id}...")
        
        # Metadata
        meta_screen = f"Source: screenshot | Image: {screenshot_url}"
        
        emb_screen = get_embedding(extracted_text)
        
        if emb_screen:
            # Note: insert_error_embedding currently doesn't support passing screenshot_id directly 
            # based on the signature I saw in previous turn (it calls ingest_create_embedding RPC).
            # Wait, let me check supabase_service.py again.
            # insert_error_embedding takes (error_id, embedding, content, metadata). 
            # The RPC `ingest_create_embedding` accepted p_screenshot_id in ingest.py line 223!
            # I need to update insert_error_embedding in supabase_service.py to accept screenshot_id too if I want to link it properly.
            # OR I can just pass None if the RPC handles it, but ingest.py passed it.
            
            # Let's check supabase_service.py content from Step 11.
            # It calls `ingest_create_embedding` with p_error_info_id, p_content, p_embedding, p_metadata.
            # It DOES NOT pass p_screenshot_id.
            
            # I should update `insert_error_embedding` in `supabase_service.py` to support `screenshot_id`.
            
            success = insert_error_embedding(error_id, emb_screen, extracted_text, meta_screen, screenshot_id=screenshot_id)
            if success:
                logger.info(f"Screenshot embedding saved for Screenshot {screenshot_id}.")
    except Exception as e:
        logger.error(f"Error processing screenshot {screenshot_id}: {e}")
