
from enum import unique
from typing import List, Optional
from app.services.supabase.supabase_client import supabase
from app.services.supabase.error_operations import ErrorEntry, get_error_by_id
from app.services.openai_service import get_embedding, extract_text_from_image
from cachetools import TTLCache
from app.utils.error_handlers import handle_error
import logging

logger = logging.getLogger(__name__)

# Cache for search results (MAX 100 queries, 10 min TTL)
search_cache = TTLCache(maxsize=100, ttl=600)

def find_error_match(query_text: str, base64_image: Optional[str] = None, extracted_text: Optional[str] = None) -> List[ErrorEntry]:
    """
    Finds matching errors using a multi-stage approach:
    1. OCR Extraction (if image provided).
    2. Exact/Key Phrase Match on `error_screenshots` table.
    3. Semantic Search (Embedding match) via RPC.
    4. Disambiguation (Filtering duplicates).
    """
    try:
        # 1. Image Processing
        logger.info(f"Starting Error Match. Has Image: {bool(base64_image)}, Input Text Length: {len(query_text) if query_text else 0}")
        matched_records = []
        # Check Cache for text-only queries (caching images is tricky, skipping for now)
        if not base64_image and not extracted_text and query_text in search_cache:
            logger.info(f"Returning search results from cache for query: '{query_text[:50]}'")
            return search_cache[query_text]
        
        if base64_image or extracted_text:
            image_text = extracted_text
            if not image_text and base64_image:
                image_text = extract_text_from_image(base64_image)
                
            if image_text:
                logger.info(f"OCR Extracted Text: {image_text}...")
                # If we have an image, the query IS the image text primarily, or a mix.
                # Strategy: Use image text for Exact Match first.
                query_text = f"{image_text}".strip()

                if not query_text:
                    return []
                
        try:
            logger.info(f"Tier 1 Searching for exact match in error_embeddings for query: '{query_text[:50]}...'")
            # Increased limit to 5 to allow for filtering of archived errors
            response = supabase.table("error_embeddings") \
                .select("error_info_id") \
                .filter("content", "wfts", query_text) \
                .limit(1) \
                .execute()
            
            if response.data and len(response.data) > 0:
                logger.info(f"Tier 1 Found {len(response.data)} potential matches. Filtering archived...")
                
                valid_matches = []
                for record in response.data:
                    eid = record['error_info_id']
                    # Fetch details to check archive status
                    # optimization: could fetch all IDs in one query if we had a bulk fetch function
                    # but for 5 items, individual fetching is acceptable for now.
                    err_detail = get_error_by_id(eid)
                    if err_detail and not err_detail.get('is_archive', False):
                        valid_matches.append(record)
                        # We only need one good match for Tier 1
                        break
                    elif err_detail and err_detail.get('is_archive', False):
                        logger.info(f"Skipping archived error {eid} in Tier 1.")

                if valid_matches:
                    logger.info(f"Tier 1 Success: Found valid non-archived match.")
                    matched_records = valid_matches
                else:
                    logger.info("Tier 1: All found matches were archived or invalid.")
            else:
                logger.info(f"Tier 1: No matches found.")
        except Exception as e:
            logger.error(f"Tier 1 (Exact Match on Knowledge Base) failed: {e}")
            handle_error(e, flow="query_service.error_embeddings", payload={"query": query_text})
            
        # --- TIER 2: SEMANTIC SEARCH ---
        # Used if Tier 1 failed or no image provided
        if matched_records is None or len(matched_records) == 0:
            try:
                logger.info(f"Initiating Tier 2: Semantic Search for query: '{query_text[:50]}...'")
                query_emb = get_embedding(query_text)
                
                if not query_emb:
                    logger.error("Error: Embedding generation returned None or empty list.")
                    return []
                    
                logger.info(f"Calling match_errors_sinewave RPC with embedding length: {len(query_emb)}")
                response = supabase.postgrest.rpc(
                    "match_errors_sinewave", 
                    {
                        "query_embedding": query_emb,
                        "match_threshold": 0.8, 
                        "match_count": 10 # Increased count to allow for filtering
                    }
                ).execute()
                
                if response.data and len(response.data) > 0:
                    logger.info(f"Semantic Search found {len(response.data)} matches. Filtering archived...")
                    
                    # RPC return structure depends on the function definition. 
                    # Usually returns list of dicts with error_id or id.
                    # Assuming it returns similar to what we need or we fetch details.
                    # The current code below expects matched_records to have 'error_info_id' or similar if it reuses Tier 1 logic?
                    # Wait, lines 98-102 assume matched_records[0]['error_info_id']. 
                    # RPC `match_errors_sinewave` likely returns `id` (error_id), `similarity`, etc.
                    # Let's check how it was used:
                    # Line 100: error_detail = get_error_by_id_internal(matched_records[0]['error_info_id'])
                    # If RPC returns `id`, we need to map it.
                    # Standard Supabase vector match returns `id`, `content`, `similarity`.
                    
                    # Let's be robust.
                    rpc_matches = response.data
                    valid_matches = []
                    
                    for match in rpc_matches:
                        # Handle varied return keys
                        eid = match.get('id') or match.get('error_info_id')
                        if not eid: continue
                        
                        err_detail = get_error_by_id(eid)
                        if err_detail and not err_detail.get('is_archive', False):
                             # Normalize to structure expected by downstream
                             match['error_info_id'] = eid 
                             valid_matches.append(match)
                        elif err_detail and err_detail.get('is_archive', False):
                            logger.info(f"Skipping archived error {eid} in Tier 2.")
                            
                    if valid_matches:
                        matched_records = valid_matches
                        logger.info(f"Tier 2: Found {len(valid_matches)} valid non-archived matches.")
                    else:
                        logger.info("Tier 2: All matches were archived.")
                        return []
                else:
                    logger.error("RPC call returned no data.")
                    return []
            except Exception as e:
                logger.error(f"Semantic search failed: {e}")
                handle_error(e, flow="query_service.find_error_match.semantic", payload={"query": query_text})
                return []

        if matched_records is not None and len(matched_records) > 0:
            # Perfect match from either Tier 1 or Tier 2
            # We already fetched details during filtering, could optimize to return them directly 
            # but to keep structure simple, we fetch again or use the cache (which acts as the optimization).
            
            # If multiple, do we return list? 
            # The interface returns List[ErrorEntry].
            # Logic at line 100 returns only [0].
            # For disambiguation (Tier 3? not visible here but implied by return type list), 
            # we might want to return all candidates.
            # But the detailed "disambiguation" usually happens if we return multiple.
            # The original code returned [error_detail] (list of 1) for Tier 1 
            # or used `matched_records` for Tier 2 but loop at 100 uses [0].
            # Actually line 100 only processes [0].
            # "error_detail = get_error_by_id_internal(matched_records[0]['error_info_id'])"
            # This implies strictly 1 result is returned?
            # But the signature says List[ErrorEntry].
            
            # Let's try to return all valid matches if Tier 2, or just top 1 if Tier 1?
            # Original code: "return [error_detail]" (line 102).
            # This suggests it only ever returned the top match found.
            
            final_results = []
            for rec in matched_records:
                eid = rec.get('error_info_id') or rec.get('id')
                det = get_error_by_id(eid)
                if det and not det.get('is_archive', False):
                    final_results.append(det)
            
            # Deduplicate by ID
            unique_results = deduplicate_errors(final_results)
            return unique_results
            
        return []
    except Exception as e:
        logger.error(f"Unexpected error in find_error_match: {e}")
        handle_error(e, flow="query_service.find_error_match", payload={"query": query_text})
        return []

def get_error_by_id_internal(error_id: int) -> Optional[ErrorEntry]:
    # Reuse existing logic but might need adapting if IDs differ
    # The existing get_error_by_id searches 'vectors' table metadata.
    # Ideally should search the main 'error_info' table if it exists.
    return get_error_by_id(error_id)

def deduplicate_errors(errors: List[ErrorEntry]) -> List[ErrorEntry]:
    seen = set()
    unique = []
    for err in errors:
        if err['slNo'] not in seen:
            seen.add(err['slNo'])
            unique.append(err)
    if len(errors) != len(unique):
        logger.info(f"Deduplicated matches from {len(errors)} to {len(unique)}")
    return unique
