from .supabase_client import supabase
from .error_operations import get_error_by_id, delete_error_by_id, update_error, archive_error
from .screenshot_operations import create_error_screenshot, get_screenshot_by_id, get_screenshots_by_error_id
from .embedding_operations import insert_error_embedding, delete_manual_embedding, check_embedding_exists
from .stats_operations import create_error_stat, update_error_stat_resolution, record_error_stat_and_update_state

__all__ = [
    "supabase",
    "get_error_by_id",
    "delete_error_by_id",
    "update_error",
    "archive_error",
    "create_error_screenshot",
    "get_screenshot_by_id",
    "get_screenshots_by_error_id",
    "insert_error_embedding",
    "delete_manual_embedding",
    "check_embedding_exists",
    "create_error_stat",
    "update_error_stat_resolution",
    "record_error_stat_and_update_state"
]
