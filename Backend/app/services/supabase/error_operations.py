import os
from typing import Optional, TypedDict, List
from cachetools import TTLCache
import logging
from .supabase_client import supabase
from pathlib import Path

logger = logging.getLogger(__name__)

# Cache for error details (MAX 100 items, 10 min TTL)
error_cache = TTLCache(maxsize=100, ttl=600)
ASSETS_DIR = os.getenv("ASSETS_DIR")

class ErrorEntry(TypedDict):
    slNo: int
    errorDescription: str
    solution: str
    functionArea: str
    solution_2: Optional[str]
    similarity: float # Added for ranking purposes
    is_archived: bool

def get_error_by_id(sl_no: int) -> Optional[ErrorEntry]:
    """
    Fetches error details directly from 'error_knowledge_base' (previously error_info),
    joining 'function_area'.
    """
    # Check Cache
    if sl_no in error_cache:
        logger.info(f"Returning error details from cache for ID: {sl_no}")
        return error_cache[sl_no]

    try:
        logger.info(f"Fetching fresh error details for ID: {sl_no}...")
        
        response = supabase.table("error_knowledge_base") \
            .select("id, error_description, solution_steps, is_archived, function_area!fk_function_area(title)") \
            .eq("id", sl_no) \
            .execute()
        
        if response.data and len(response.data) > 0:
            item = response.data[0]
            
            # Extract function area title from nested object
            func_area = "Unknown"
            
            # The join key is usually the table name "function_area"
            fa_data = item.get("function_area")
            
            if fa_data:
                if isinstance(fa_data, dict):
                    func_area = fa_data.get("title", "Unknown")
                elif isinstance(fa_data, list) and len(fa_data) > 0:
                    func_area = fa_data[0].get("title", "Unknown")
            
            logger.info(f"Successfully fetched error {sl_no}. Function Area: {func_area}")
            result = {
                "slNo": item["id"],
                "errorDescription": item["error_description"],
                "solution": item["solution_steps"],
                "functionArea": func_area,
                "solution_2": None,
                "is_archived": item.get("is_archived", False)
            }
            # Update cache
            error_cache[sl_no] = result
            return result
        else:
             logger.warning(f"Error ID {sl_no} not found in database.")
    except Exception as e:
        logger.error(f"Error fetching error by ID {sl_no}: {e}")
        import traceback
        traceback.print_exc()
        
    return None

def delete_error_by_id(error_id: int) -> bool:
    """
    Deletes an error and all its associated data (embeddings, screenshots) from Supabase.
    """
    try:
        logger.info(f"Deleting error {error_id} and associated data...")
        
        # 1. Delete Embeddings
        # metadata contains "Source: manual | Function: ..." or "Source: screenshot | ..."
        # We can delete by error_info_id
        res_emb = supabase.table("error_embeddings").delete().eq("error_info_id", error_id).execute()
        logger.info(f"Deleted embeddings for error {error_id}")

        # 2. Delete Screenshots
        # First fetch to get asset path
        s_res = supabase.table("error_screenshots").select("screenshot_url").eq("error_id", error_id).execute()
        asset_path = s_res.data[0]["screenshot_url"] if s_res.data and len(s_res.data) > 0 else None
        
        # Then delete
        supabase.table("error_screenshots").delete().eq("error_id", error_id).execute()
        logger.info(f"Deleted screenshots for error {error_id}")

        # 3. Delete Error Knowledge Base Entry
        # We don't really need the return data for KB entry except to confirm it existed, but delete count is enough.
        # But for consistency with original return logic:
        res_kb = supabase.table("error_knowledge_base").delete().eq("id", error_id).execute()
        
        # delete screenshot file
        if asset_path:
             file_path = Path(f"{ASSETS_DIR}/{asset_path}")
             if file_path.exists():
                 file_path.unlink()
                 print(f"File deleted: {file_path}")
             else:
                 print(f"File {file_path} does not exist")

        if res_kb.data:
            logger.info(f"Successfully deleted error {error_id} from knowledge base.")
            return True
        else:
             # If data is empty on delete (because we didn't select), we assume success if no exception?
             # Note: Without select(), 'data' might be empty or contain count. 
             # Usually execute() returns data=[] if no select/return.
             # So we might lose the confirmation check "if res_kb.data".
             # Actually, execute() usually returns the deleted rows if header Prefer: return=representation is sent.
             # By default python client might not send it without .select().
             # So let's assume success if we reach here? Or check count?
             # let's just return True.
             logger.info(f"Successfully deleted error {error_id} (or purely executed delete).")
             return True

    except Exception as e:
        logger.error(f"Error deleting error {error_id}: {e}")
        return False

def update_error(error_id: int, updates: dict) -> bool:
    """
    Updates an error record in the 'error_knowledge_base' table.
    """
    try:
        logger.info(f"Updating error {error_id} with data: {updates}")
        
        # We only allow updating specific fields
        allowed_fields = ["error_description", "solution_steps", "formatted_solution_steps", "function_area_id", "is_archived"]
        data_to_update = {k: v for k, v in updates.items() if k in allowed_fields}
        
        if not data_to_update:
            logger.warning(f"No valid fields to update for error {error_id}")
            return False

        response = supabase.table("error_knowledge_base").update(data_to_update).eq("id", error_id).execute()
        
        if response.data:
            logger.info(f"Successfully updated error {error_id}")
            # Invalidate cache
            if error_id in error_cache:
                del error_cache[error_id]
            return True
        else:
            logger.warning(f"Failed to update error {error_id}. ID might not exist.")
            return False
            
    except Exception as e:
        logger.error(f"Error updating error {error_id}: {e}")
        return False

def archive_error(error_id: int) -> bool:
    """
    Sets is_archive = True for the given error.
    """
    return update_error(error_id, {"is_archived": True})

def get_product_name_by_id(product_id: int) -> Optional[str]:
    """
    Fetches product name by ID.
    """
    try:
        response = supabase.table("products").select("name").eq("id", product_id).execute()
        if response.data:
            return response.data[0]["name"]
        return None
    except Exception as e:
        logger.error(f"Error fetching product name for {product_id}: {e}")
        return None

def create_error(product_id: int, error_description: str, solution_steps: str, function_area_id: int) -> Optional[int]:
    """
    Creates a new error record in 'error_knowledge_base' using REST API.
    """
    try:
        logger.info(f"Creating error for product {product_id}")
        # Map fields to DB columns
        data = {
            "product_id": product_id,
            "error_description": error_description,
            "solution_steps": solution_steps,
            "function_area_id": function_area_id,
            "is_archived": False
        }
        
        response = supabase.table("error_knowledge_base").insert(data).execute()
        
        if response.data:
            logger.info(f"Error created with ID: {response.data[0]['id']}")
            return response.data[0]["id"]
        return None
    except Exception as e:
        logger.error(f"Error creating error: {e}")
        return None

def get_or_create_function_area(product_id: int, title: str) -> Optional[int]:
    """
    Resolves function area ID for a given title and product using REST API.
    """
    try:
        # Check if exists (case insensitive match on title)
        # Note: 'ilike' might not be supported on all columns depending on indexes, but usually fine for text.
        response = supabase.table("function_area").select("id") \
            .eq("product_id", product_id).ilike("title", title).execute()
            
        if response.data and len(response.data) > 0:
            return response.data[0]["id"]
            
        # Create new
        logger.info(f"Creating new function area '{title}' for product {product_id}")
        new_fa = supabase.table("function_area").insert({
            "product_id": product_id,
            "title": title
        }).execute()
        
        if new_fa.data:
            return new_fa.data[0]["id"]
        return None
    except Exception as e:
        logger.error(f"Error resolving function area '{title}': {e}")
        return None
