import logging
import os
from datetime import datetime, timezone
from typing import Optional, Dict, Any
from app.services.supabase.supabase_client import supabase
from app.state_manager import state_manager

logger = logging.getLogger(__name__)

def create_error_stat(
    error_id: int, 
    product_id: int, 
    user_phone_number: str, 
    reported_at: Optional[datetime] = None
) -> Optional[int]:
    """
    Creates a new entry in the error_stats table.
    
    Args:
        error_id: The ID of the error from error_knowledge_base.
        product_id: The ID of the product.
        user_phone_number: The user's phone number.
        reported_at: (Optional) The timestamp when the error was reported. Defaults to now if not provided.
    
    Returns:
        The ID of the created stats record, or None if failed.
    """
    try:
        data = {
            "error_id": error_id,
            "product_id": product_id,
            "user_phone_number": user_phone_number,
            "is_resolved": False  # Initial state
        }
        
        if reported_at:
            data["reported_at"] = reported_at.isoformat()
            
        logger.info(f"Creating error_stats entry: {data}")
        
        response = supabase.table("error_stats").insert(data).execute()
        
        if response.data:
            stat_id = response.data[0]['id']
            logger.info(f"Created error_stats record with ID: {stat_id}")
            return stat_id
        else:
            logger.error("Failed to create error_stats record: No data returned.")
            return None

    except Exception as e:
        logger.error(f"Error creating error_stats record: {e}")
        return None

def update_error_stat_resolution(stat_id: int, is_resolved: bool) -> bool:
    """
    Updates the is_resolved status of an error_stats record.
    
    Args:
        stat_id: The ID of the stats record.
        is_resolved: True if the error was resolved, False otherwise.
        
    Returns:
        True if successful, False otherwise.
    """
    try:
        data = {
            "is_resolved": is_resolved
        }
        
        if is_resolved:
            data["resolved_at"] = datetime.now(timezone.utc).isoformat()
        
        logger.info(f"Updating error_stats {stat_id}: {data}")
        
        response = supabase.table("error_stats").update(data).eq("id", stat_id).execute()
        
        if response.data:
            logger.info(f"Updated error_stats {stat_id} successfully.")
            return True
        else:
            logger.error(f"Failed to update error_stats {stat_id}: No data returned (record might not exist).")
            return False

    except Exception as e:
        logger.error(f"Error updating error_stats {stat_id}: {e}")
        return False

def record_error_stat_and_update_state(from_number: str, match: Dict[str, Any], card_id: str) -> Optional[int]:
    """
    Helper function to create an error stat entry and update the state manager.
    """
    try:
        # Avoid circular import by importing here if strictly necessary, but we already imported state_manager at top
        state_data = state_manager.get_data(from_number)
        query_received_at_str = state_data.get("query_received_at")
        query_received_at = datetime.fromisoformat(query_received_at_str) if query_received_at_str else None
        
        stat_id = create_error_stat(
            error_id=match["slNo"],
            product_id=match["productId"],
            user_phone_number=from_number,
            reported_at=query_received_at
        )
        
        state_manager.update_data(from_number, {
            "match_id": match["slNo"], 
            "card_id": card_id, 
            "trello_card_id": card_id, 
            "stat_id": stat_id
        })
        return stat_id
    except Exception as e:
        logger.error(f"Error in record_error_stat_and_update_state: {e}")
        return None
