import os
from pathlib import Path
from typing import Optional, List
import logging
from .supabase_client import supabase

logger = logging.getLogger(__name__)

ASSETS_DIR = os.getenv("ASSETS_DIR")

def create_error_screenshot(error_id: int, screenshot_url: str, extracted_text: str, created_by: Optional[int] = None) -> Optional[int]:
    """
    Inserts a record into the error_screenshots table.
    """
    try:
        logger.info(f"Saving error screenshot for error_id: {error_id}. Text length: {len(extracted_text)}")
        data = {
            "error_id": error_id,
            "screenshot_url": screenshot_url,
            "extracted_text": extracted_text,
            "created_by": created_by
        }

        # Using standard REST API insert
        response = supabase.table("error_screenshots").insert({
            "error_id": error_id,
            "screenshot_url": screenshot_url,
            "extracted_text": extracted_text,
            "created_by": created_by
        }).execute()
        
        if response.data:
            logger.info(f"Screenshot saved successfully. ID: {response.data}")
            return response.data
    except Exception as e:
        import traceback
        logger.error(f"Error creating error screenshot data={data}: {e}")
        traceback.print_exc()
        return None

def get_screenshot_by_id(screenshot_id: int) -> Optional[dict]:
    """
    Fetches screenshot details by ID.
    """
    try:
        response = supabase.table("error_screenshots").select("*").eq("id", screenshot_id).execute()
        if response.data:
            return response.data[0]
        return None
    except Exception as e:
        logger.error(f"Error fetching screenshot {screenshot_id}: {e}")
        return None

def get_screenshots_by_error_id(error_id: int) -> List[dict]:
    """
    Fetches all screenshots associated with an error ID.
    """
    try:
        response = supabase.table("error_screenshots").select("*").eq("error_id", error_id).execute()
        return response.data if response.data else []
    except Exception as e:
        logger.error(f"Error fetching screenshots for error {error_id}: {e}")
        return []

def delete_screenshot(screenshot_ids: int) -> bool:
    """
    Deletes a screenshot record and its associated embedding.
    Does NOT delete the actual file from disk (as we might want to keep it or it's complex to map URL to path reliably here without more context).
    """
    try:
        logger.info(f"Deleting screenshot {screenshot_ids}...")
        
        # 1. Delete associated embedding first (if any)
        # We need to find the embedding that links to this screenshot.
        # Options:
        # A. Query error_embeddings where metadata contains screenshot URL or ID?
        #    ingest.py uses metadata: "Source: screenshot | Image: {url}"
        #    But we have `screenshot_id` in `error_embeddings` if we added that column? 
        #    In `generate_screenshot_embedding` we didn't pass screenshot_id to `insert_error_embedding` because `supabase_service.py` (now `embedding_operations.py`) didn't support it in python function signature yet, 
        #    BUT `ingest.py` RPC call `ingest_create_embedding` DID support p_screenshot_id.
        #    Let's fetch the screenshot first to get the URL.
        
        # Delete embedding by metadata match (safer for now until we are sure about screenshot_id column usage in embeddings)
        supabase.table("error_embeddings").delete().in_("screenshot_id", screenshot_ids).execute()
        logger.info(f"Deleted embedding for screenshot {screenshot_ids}")

        # 2. Delete screenshot record
        res_screenshot = supabase.table("error_screenshots").delete().in_("id", screenshot_ids).select().execute()
        logger.info(f"Deleted screenshot record {screenshot_ids}")

        for screenshot in res_screenshot.data:
            asset_path = screenshot["screenshot_url"]
            file_path = Path(f"{ASSETS_DIR}/{asset_path}")
            if file_path.exists():
                file_path.unlink()
                logger.info(f"File deleted: {file_path}")
            else:
                logger.warning(f"File {file_path} does not exist") 
        
        return True
    except Exception as e:
        logger.error(f"Error deleting screenshot {screenshot_ids}: {e}")
        return False
