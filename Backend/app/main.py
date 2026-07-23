import os
import logging
from typing import Dict, Any, List, Optional
from fastapi import FastAPI, Request, BackgroundTasks, HTTPException, Query, UploadFile, File, Form, Response
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import shutil
import uuid
import base64
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from app.utils import safe_send_message, safe_send_buttons, safe_send_list, get_media_url, download_image_as_base64
from app.utils.error_handlers import handle_error
from app.state_manager import state_manager, BotState, update_state
from datetime import datetime, timezone
from app.services.supabase import get_error_by_id, create_error_screenshot, create_error_stat, update_error_stat_resolution, record_error_stat_and_update_state
from app.services.openai_service import extract_text_from_image
from app.services.query_service import find_error_match
from app.services.trello_service import create_messages_card, create_card, add_comment_to_card, move_card_to_list

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# Mount the assets directory to serve static files
ASSETS_DIR = Path(os.getenv("ASSETS_DIR"))
ASSETS_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/assets", StaticFiles(directory=ASSETS_DIR), name="assets")

@app.get("/")
async def root():
    return {"status": "OK"}

@app.get("/webhook")  
async def verify_webhook(
    mode: str = Query(None, alias="hub.mode"),
    token: str = Query(None, alias="hub.verify_token"),
    challenge: str = Query(None, alias="hub.challenge")
):
    """
    Verifies the webhook with WhatsApp.
    """
    if not mode:
        return Response("OK", media_type="text/plain")

    if mode == "subscribe" and token == os.getenv("VERIFY_TOKEN"):
        return Response(challenge, media_type="text/plain")

    raise HTTPException(status_code=403, detail="Invalid verify token")

@app.post("/upload-screenshot")
async def upload_screenshot(
    request: Request,
    file: UploadFile = File(...),
    error_id: int = Form(...),
    extracted_text: str = Form(None),
    created_by: int = Form(None)
):
    """
    Uploads a screenshot, saves it locally, and records metadata in the database.
    """
    try:
        # Generate unique filename
        file_extension = file.filename.split(".")[-1] if "." in file.filename else "jpg"
        filename = f"{uuid.uuid4()}.{file_extension}"
        file_path = f"{ASSETS_DIR}/{filename}"
        
        # Save file locally
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        # Construct public URL
        # Assumption: The server is accessible via the base URL of the request
        base_url = str(request.base_url)
        # Remove trailing slash from base_url if present and add to path
        if base_url.endswith("/"):
             base_url = base_url[:-1]
        
        screenshot_url = f"{base_url}/assets/{filename}"
        
        # Auto-OCR if extracted_text is not provided or empty
        final_extracted_text = extracted_text
        if not final_extracted_text or final_extracted_text.strip() == "":
             try:
                 # Read file again for OCR (file pointer is at end after copy)
                 with open(file_path, "rb") as image_file:
                     encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
                     logger.info("Performing auto-OCR on uploaded image...")
                     final_extracted_text = extract_text_from_image(encoded_string)
                     logger.info(f"Auto-OCR result: {final_extracted_text[:50]}...")
             except Exception as ocr_error:
                 logger.error(f"Auto-OCR failed: {ocr_error}")
                 final_extracted_text = "OCR Failed"
        
        # Save to Database
        record_id = create_error_screenshot(error_id, screenshot_url, final_extracted_text, created_by)
        
        if record_id:
            return {
                "status": "success",
                "message": "Screenshot uploaded and verified.",
                "data": {
                    "id": record_id,
                    "screenshot_url": screenshot_url,
                    "extracted_text": final_extracted_text
                }
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to save record to database")

    except Exception as e:
        logger.error(f"Error uploading screenshot: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/webhook")
async def receive_message(request: Request, background_tasks: BackgroundTasks):
    """
    Receives messages from WhatsApp and processes them in the background.
    """
    body = await request.json()
    
    # Check if it's a valid WhatsApp message event
    try:
        if body.get("object") == "whatsapp_business_account":
            for entry in body.get("entry", []):
                for change in entry.get("changes", []):
                    value = change.get("value", {})
                    if "messages" in value:
                        # Process message in background to return 200 OK immediately
                        background_tasks.add_task(process_message, value)
            return {"status": "received"}
    except Exception as e:
        logger.error(f"Error parsing webhook body: {e}")
        return {"status": "error", "message": str(e)}


    return {"status": "ignored"}

from app.routers import embedding_generation_router, error_management_router
app.include_router(embedding_generation_router.router, prefix="/api")
app.include_router(error_management_router.router, prefix="/api")

async def process_message(value: Dict[str, Any]):
    """
    Core logic for handling the message (Ported from Lambda).
    """
    try:
        messages = value.get("messages", [])
        if not messages:
            return

        message = messages[0]
        from_number = message.get("from")
        msg_type = message.get("type")
        contacts = value.get("contacts", [])
        user_name = contacts[0].get("profile", {}).get("name") if contacts else None

        logger.info(f"Processing message from {from_number} type {msg_type}")

        # State Management
        state = state_manager.get_data(from_number)
        card_id = state.get("trello_card_id")
        
        # 1. Message Card Creation (Start of Conversation / Session)
        # If no card exists or state is empty, create a new "Message Card"
        if not card_id or state_manager.get_state(from_number) == BotState.START:
            card_id = create_messages_card(from_number, user_name)
            # Update state with new card_id (careful not to overwrite other state data if preserving)
            state_manager.update_data(from_number, {"trello_card_id": card_id})

        # Append incoming user message to the card as a comment
        # Extract text/response
        text_body = ""
        media_url = None
        base64_img = None
        extracted_text = None
        
        if msg_type == "text":
            text_body = message["text"]["body"].strip()
            add_comment_to_card(card_id, f"👤 User: {text_body}")
        elif msg_type == "interactive":
            int_type = message["interactive"]["type"]
            if int_type == "button_reply":
                text_body = message["interactive"]["button_reply"]["id"]
                title = message["interactive"]["button_reply"]["title"]
                add_comment_to_card(card_id, f"👤 User clicked button: {title} ({text_body})")
            elif int_type == "list_reply":
                text_body = message["interactive"]["list_reply"]["id"]
                title = message["interactive"]["list_reply"]["title"]
                add_comment_to_card(card_id, f"👤 User selected list option: {title} ({text_body})")
        elif msg_type == "image":
            text_body = message["image"].get("caption", "").strip()
            media_id = message["image"]["id"]
            media_url = get_media_url(media_id)
            
            # Extract Text from Image immediately for Trello & Search
            try:
                base64_img = download_image_as_base64(media_url)
                if base64_img:
                    extracted_text = extract_text_from_image(base64_img)
                    if extracted_text:
                        add_comment_to_card(card_id, f"👤 User sent image: {media_url}\n\n📝 Extracted Text:\n{extracted_text}\n\nCaption: {text_body}")
                        # Prepend extracted text to text_body for search context if caption is empty
                        if not text_body:
                            text_body = extracted_text
                    else:
                         add_comment_to_card(card_id, f"👤 User sent image: {media_url}\n(No text extracted)\nCaption: {text_body}")
                else:
                    add_comment_to_card(card_id, f"👤 User sent image: {media_url}\n(Failed to download)\nCaption: {text_body}")
            except Exception as e:
                logger.error(f"Failed to extract text from image: {e}")
                add_comment_to_card(card_id, f"👤 User sent image: {media_url}\n(OCR Failed)\nCaption: {text_body}")


        # Global Commands
        if text_body.lower() in ["hi", "hello", "hey", "start"]:
            state_manager.set_state(from_number, BotState.PROVIDE_ERROR)
            # Persist card_id across state reset/set
            state_manager.update_data(from_number, {"trello_card_id": card_id})
            
            safe_send_message(
                from_number,
                "*Hi* there 👋\nWelcome to SineWave Support.\nI’m here to help you with any issue you’re facing. Please share a few details about the problem, or upload a screenshot if you have one—I’ll take a look and guide you from there.\nIf you’re done, you can simply type *bye* to *exit* the chat.",
                card_id
            )
            return

        if text_body.lower() in ["bye", "exit"]:
            safe_send_message(from_number, "Thank you for using SineWave Support \nWishing you a smooth and stress-free filing experience. 👋", card_id)
            state_manager.reset_state(from_number)
            return

        # State Machine Logic
        current_state = state_manager.get_state(from_number)
        
        # Auto-transition from START to PROVIDE_ERROR if user sends something else
        if current_state == BotState.START:
            current_state = BotState.PROVIDE_ERROR
            state_manager.set_state(from_number, BotState.PROVIDE_ERROR)
            state_manager.update_data(from_number, {"trello_card_id": card_id})

        if current_state == BotState.WELCOME:
            # Note: This state might be unreachable if we default to PROVIDE_ERROR on Start, 
            # but implemented for consistency with legacy logic.
            if text_body == "btn_report" or "report" in text_body.lower():
                state_manager.set_state(from_number, BotState.PROVIDE_ERROR)
                state_manager.update_data(from_number, {"trello_card_id": card_id})
                safe_send_message(from_number, "Please share details about the problem.", card_id)
            elif text_body == "btn_exit" or "exit" in text_body.lower():
                safe_send_message(from_number, "Thank you for using SineWave Support. 👋", card_id)
                state_manager.reset_state(from_number)
            else:
                safe_send_buttons(from_number, "Please select a valid option:", [
                    {"type": "reply", "reply": {"id": "btn_report", "title": "Report Error"}},
                    {"type": "reply", "reply": {"id": "btn_exit", "title": "Exit"}}
                ], card_id)

        elif current_state == BotState.PROVIDE_ERROR:
            if text_body.lower() in ["yes", "btn_yes"]:
                 safe_send_message(from_number, "✅ Excellent! Glad I could help.", card_id)
                 state_manager.reset_state(from_number)
                 return
            
            # Create dedicated "Issue Card" with extracted text if available
            issue_desc = text_body
            if extracted_text and extracted_text != text_body:
                issue_desc += f"\n\n📝 Extracted Image Text:\n{extracted_text}"

            # Capture timestamp when user sends query
            query_received_at = datetime.now(timezone.utc).isoformat()
            
            issue_context = {
                "text": issue_desc,
                "images": [media_url] if media_url else [],
                "query_received_at": query_received_at
            }
            issue_card_id, issue_card_url = create_card(from_number, issue_context)
            if issue_card_url:
                add_comment_to_card(card_id, f"📝 Issue captured in card: {issue_card_url}")
                # Save issue_card_id and timestamp to state for later resolution
                state_manager.update_data(from_number, {
                    "issue_card_id": issue_card_id, 
                    "query_received_at": query_received_at
                })

            safe_send_message(from_number, "Thanks for sharing that 😊\nI’m checking the details for you now. Please give me a moment…", card_id)
            
            # Use pre-extracted text for search
            matches = find_error_match(text_body, base64_img, extracted_text=extracted_text)
            logger.info(f"Main Process: Found {len(matches)} matches from query engine.")
            
            # Log matches to Trello
            if matches:
                 match_summaries = "\n".join([f"- {m['slNo']}: {m['errorDescription']}" for m in matches[:3]])
                 add_comment_to_card(card_id, f"🔍 Found matches:\n{match_summaries}")
            else:
                 add_comment_to_card(card_id, "🔍 No matches found.")

            if matches:
                # Check for Function Area Disambiguation
                distinct_functions = list(set(m['functionArea'] for m in matches))
                
                if len(distinct_functions) > 1:
                    # Case: Multiple Function Areas -> Ask User
                    buttons = []
                    for func in distinct_functions[:3]: # WhatsApp limits to 3 buttons
                        # Create a safe ID (sluggify)
                        safe_id = f"fn_{func.replace(' ', '_')[:20]}"
                        buttons.append({"type": "reply", "reply": {"id": safe_id, "title": func[:20]}})
                    
                    safe_send_buttons(from_number, "I found multiple possibilities. Which area does this relate to?", buttons, card_id)
                    # Store the matches temporarily in state to filter later
                    state_manager.update_data(from_number, {"matches": matches, "card_id": card_id, "trello_card_id": card_id})
                    state_manager.set_state(from_number, "SELECT_FUNCTION_AREA")
                    return

                # Case: Single Match or Single Function Area (already filtered by query_service)
                if len(matches) == 1:
                    match = matches[0]
                    sol_steps = match.get("formatted_solution_steps") or "No formatted solution available."
                    response_text = (
                        "Alright, I’ve reviewed the information carefully 🔍\n"
                        "Here’s what seems to be causing the issue:\n"
                        "*What’s happening:*\n"
                        f"{match['errorDescription']} (ID: {match['slNo']})\n\n"
                        "*Let’s fix this step by step:*\n"
                        f"{sol_steps}\n\n"
                        "Once the details are updated, the error should be resolved."
                    )
                    
                    # Create stats entry and update state
                    record_error_stat_and_update_state(from_number, match, card_id)
                    
                    state_manager.set_state(from_number, BotState.SOLUTION_PROVIDED)
                    safe_send_message(from_number, response_text, card_id)
                    safe_send_buttons(from_number, "Did this fix the problem for you?", [
                        {"type": "reply", "reply": {"id": "btn_yes", "title": "Yes"}},
                        {"type": "reply", "reply": {"id": "btn_no", "title": "No"}}
                    ], card_id)
                else:
                     # Fallback: Multiple matches in SAME function area (should be rare due to query_service logic)
                     # For now, just pick the first one as "Best Guess"
                     match = matches[0]
                     sol_steps = match.get("formatted_solution_steps") or "No formatted solution available."
                     response_text = (
                        "I found a few similar issues in that area. Here is the most likely solution:\n\n"
                        f"*Error:* {match['errorDescription']}\n"
                        f"*Solution:*\n{sol_steps}"
                     )
                     
                     # Create stats entry and update state
                     record_error_stat_and_update_state(from_number, match, card_id)

                     state_manager.set_state(from_number, BotState.SOLUTION_PROVIDED)
                     safe_send_message(from_number, response_text, card_id)
                     safe_send_buttons(from_number, "Did this fix the problem?", [
                        {"type": "reply", "reply": {"id": "btn_yes", "title": "Yes"}},
                        {"type": "reply", "reply": {"id": "btn_no", "title": "No"}}
                     ], card_id)

            else:
                # No matches found -> fallback to OpenAI (as per new requirements)
                # TODO: Implement OpenAI Chat Completion fallback here if desired
                safe_send_message(from_number, "I couldn't find a specific solution. Please contact support at 0806 548 5434.", card_id)

        elif current_state == "SELECT_FUNCTION_AREA":
            # Handle user selection of function area
            selected_func_slug = text_body.replace("fn_", "") # simplistic
            
            # Retrieve stored matches
            state_data = state_manager.get_data(from_number)
            matches = state_data.get("matches", [])
            
            # Filter matches by selected function (fuzzy check)
            filtered_matches = [m for m in matches if m['functionArea'].replace(' ', '_')[:20] in text_body or text_body in m['functionArea']]
            
            if not filtered_matches:
                 # Fallback if slug matching fails, try exact title from button title
                 filtered_matches = [m for m in matches if m['functionArea'] == text_body]

            if len(filtered_matches) == 1:
                match = filtered_matches[0]
                sol_steps = match.get("formatted_solution_steps") or "No formatted solution available."
                response_text = (
                    "Alright, I’ve reviewed the information carefully 🔍\n"
                    "Here’s what seems to be causing the issue:\n"
                    "*What’s happening:*\n"
                    f"{match['errorDescription']} (ID: {match['slNo']})\n\n"
                    "*Let’s fix this step by step:*\n"
                    f"{sol_steps}\n\n"
                    "Once the details are updated, the error should be resolved."
                )
                
                # Create stats entry and update state
                record_error_stat_and_update_state(from_number, match, card_id)
                
                state_manager.set_state(from_number, BotState.SOLUTION_PROVIDED)
                safe_send_message(from_number, response_text, card_id)
                safe_send_buttons(from_number, "Did this fix the problem?", [
                    {"type": "reply", "reply": {"id": "btn_yes", "title": "Yes"}},
                    {"type": "reply", "reply": {"id": "btn_no", "title": "No"}}
                ], card_id)
            elif len(filtered_matches) > 1:
                 # Still multiple matches in this area? Go to OpenAI
                 # For now, just show the first one
                 match = filtered_matches[0]
                 sol_steps = match.get("formatted_solution_steps") or "No formatted solution available."
                 response_text = (
                    f"*Error:* {match['errorDescription']}\n\n"
                    f"*Solution:*\n{sol_steps}"
                )
                 
                 # Create stats entry and update state
                 record_error_stat_and_update_state(from_number, match, card_id)

                 state_manager.set_state(from_number, BotState.SOLUTION_PROVIDED)
                 safe_send_message(from_number, response_text, card_id)
                 safe_send_buttons(from_number, "Did this fix the problem?", [
                    {"type": "reply", "reply": {"id": "btn_yes", "title": "Yes"}},
                    {"type": "reply", "reply": {"id": "btn_no", "title": "No"}}
                 ], card_id)
            else:
                safe_send_message(from_number, "Selection not recognized. Please start over.", card_id)
                state_manager.set_state(from_number, BotState.PROVIDE_ERROR)

        elif current_state == BotState.SELECT_ERROR:
             # Legacy state (kept for safety or removed if fully replaced)
             pass

        elif current_state == BotState.SOLUTION_PROVIDED:
            # Retrieve stat_id
            state_data = state_manager.get_data(from_number)
            stat_id = state_data.get("stat_id")

            if text_body == "btn_yes" or "yes" in text_body.lower():
                safe_send_message(from_number, "✅ Excellent! Glad I could help.", card_id)
                
                # Update stats
                if stat_id:
                    update_error_stat_resolution(stat_id, True)
                
                # Move issue card to Resolved list if exists
                state_data = state_manager.get_data(from_number)
                issue_card_id = state_data.get("issue_card_id")
                if issue_card_id:
                    move_card_to_list(issue_card_id)
                    add_comment_to_card(card_id, f"✅ Issue {issue_card_id} marked as Resolved.")
                
                state_manager.reset_state(from_number)
            elif text_body == "btn_no" or "no" in text_body.lower():
                safe_send_message(from_number, "Dear Sir,\n\nWith reference to your query, a solution is currently not available.\n\nWe request you to please raise a callback request or contact us directly at 0806 548 5434 for further assistance.\n\nThank you for your understanding.\n\nBest regards,\nSinewave Team", card_id)
                
                # Update stats
                if stat_id:
                    update_error_stat_resolution(stat_id, False)

                state_manager.reset_state(from_number)

            else:
                safe_send_message(from_number, "Please reply with Yes or No.", card_id)

    except Exception as e:
        logger.error(f"Error processing message: {e}")
        # Log to Trello Tech Issues
        handle_error(e, user_id=value.get("messages", [{}])[0].get("from"), flow="process_message", payload=value)

# ---------------------------------------------------------
# Batch Ingestion API
# ---------------------------------------------------------
from pydantic import BaseModel


class ScreenshotItem(BaseModel):
    error_id: int
    screenshot_path: str

@app.post("/errors/screenshots")
async def ingest_screenshots(items: List[ScreenshotItem], background_tasks: BackgroundTasks):
    """
    Batch ingests screenshots using OpenAI GPT-4o-mini:
    1. Extract Text (OpenAI Vision)
    2. Insert into error_screenshots
    3. Generate Embedding
    4. Insert into error_embeddings
    """
    # Import locally to avoid circular deps if any, though openai_service is safe
    from app.services.openai_service import extract_text_from_image_path, get_embedding
    from app.services.supabase_service import insert_error_embedding, create_error_screenshot
    
    results = []
    
    for item in items:
        try:
            # 1. Construct absolute path
            full_path = os.path.abspath(f"{ASSETS_DIR}/{item.screenshot_path}")
            
            if not os.path.exists(full_path):
                results.append({"error_id": item.error_id, "status": "failed", "reason": f"File not found: {full_path}"})
                continue
            
            # 2. Extract Text (OpenAI GPT-4o-mini)
            extracted_text = extract_text_from_image_path(full_path)
            if not extracted_text:
                extracted_text = "No text extracted"
            
            # 3. Insert into error_screenshots
            screenshot_url = f"/assets/{item.screenshot_path}"
            create_error_screenshot(item.error_id, screenshot_url, extracted_text, created_by=None)
            
            # 4. Generate Embedding
            embedding = get_embedding(extracted_text)
            
            # 5. Insert into error_embeddings
            insert_error_embedding(item.error_id, embedding, extracted_text)
            
            results.append({
                "error_id": item.error_id, 
                "status": "success", 
                "extracted_text_preview": extracted_text
            })
            
        except Exception as e:
            logger.error(f"Error capturing screenshot for error {item.error_id}: {e}")
            results.append({"error_id": item.error_id, "status": "failed", "reason": str(e)})

    return {"results": results}
