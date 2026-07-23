import os
import urllib.parse
import urllib.request
import urllib.error
import datetime
import json
import base64
import sys

# Ensure this path is importable for error_handlers
# sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.trello_service import add_comment_to_card
from app.utils.error_handlers import handle_error

WHATSAPP_TOKEN = os.environ.get("WHATSAPP_ACCESS_TOKEN") or os.environ.get("WHATSAPP_TOKEN")
PHONE_NUMBER_ID = os.environ.get("WHATSAPP_PHONE_NUMBER_ID") or os.environ.get("PHONE_NUMBER_ID")

def get_ist_timestamp():
    # UTC + 5:30
    ist_time = datetime.datetime.utcnow() + datetime.timedelta(hours=5, minutes=30)
    timestamp = ist_time.strftime("%Y-%m-%d %H:%M:%S IST")
    return timestamp

def format_buttons_for_comment(buttons):
    if not buttons:
        return "No buttons"

    lines = []
    for btn in buttons:
        reply = btn.get("reply", {})
        title = reply.get("title", "Unknown")
        # btn_id = reply.get("id", "unknown_id")
        lines.append(f"• {title}")

    return "\n".join(lines)

def format_list_sections_for_comment(sections):
    if not sections:
        return "No list items"

    lines = []
    for section in sections:
        section_title = section.get("title", "Options")
        lines.append(f"📂 {section_title}")

        rows = section.get("rows", [])
        for row in rows:
            title = row.get("title", "Unknown")
            # row_id = row.get("id", "unknown_id")
            lines.append(f"  • {title}")

    return "\n".join(lines)

def get_media_url(media_id):
    """Fetch the actual CDN download URL from WhatsApp Graph API."""
    try:
        url = f"https://graph.facebook.com/v21.0/{media_id}"
        headers = {"Authorization": f"Bearer {WHATSAPP_TOKEN}"}
        req = urllib.request.Request(url, headers=headers, method="GET")
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode())
            return data.get("url")
    except Exception as e:
        print("[WHATSAPP] ❌ Error fetching media URL:", str(e))
        return None
    
def send_whatsapp_message(to, message):
    if not WHATSAPP_TOKEN or not PHONE_NUMBER_ID:
        print("[WHATSAPP] ❌ Missing Token or Phone ID")
        return

    url = f"https://graph.facebook.com/v21.0/{PHONE_NUMBER_ID}/messages"
    headers = {"Authorization": f"Bearer {WHATSAPP_TOKEN}", "Content-Type": "application/json"}
    data = {"messaging_product": "whatsapp","to": to,"text": {"body": message}}
    # print("Message sent :" +   message) 
    _post(url, headers, data)

def send_interactive_buttons(to, body_text, buttons):
    if not WHATSAPP_TOKEN or not PHONE_NUMBER_ID:
        return

    url = f"https://graph.facebook.com/v21.0/{PHONE_NUMBER_ID}/messages"
    headers = {"Authorization": f"Bearer {WHATSAPP_TOKEN}", "Content-Type": "application/json"}
    data = {"messaging_product": "whatsapp","to": to,"type": "interactive",
        "interactive": {"type": "button","body": {"text": body_text},"action": {"buttons": buttons}}}
    # print("Message sent :" +   body_text) 
    _post(url, headers, data)

def send_image(to, image_url, caption):
    if not WHATSAPP_TOKEN or not PHONE_NUMBER_ID:
        return

    url = f"https://graph.facebook.com/v21.0/{PHONE_NUMBER_ID}/messages"
    headers = {"Authorization": f"Bearer {WHATSAPP_TOKEN}", "Content-Type": "application/json"}
    data = {"messaging_product": "whatsapp","to": to,"type": "image",
        "image": {"link": image_url, "caption": caption}}
    _post(url, headers, data)

def _post(url, headers, data):
    req = urllib.request.Request(
        url,
        data=json.dumps(data).encode("utf-8"),
        headers=headers,
        method="POST"
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            pass # print("WhatsApp API Response:", resp.status, resp.read().decode())

    except urllib.error.HTTPError as e:
        error_body = e.read().decode()
        print("WhatsApp API Error:", error_body)
        raise Exception(f"WhatsApp API HTTPError: {error_body}")

    except Exception as e:
        print("WhatsApp Request Error:", str(e))
        raise


def send_interactive_list(to, body_text, sections, button_text="Select"):
    if not WHATSAPP_TOKEN or not PHONE_NUMBER_ID:
        return

    url = f"https://graph.facebook.com/v21.0/{PHONE_NUMBER_ID}/messages"
    headers = {
        "Authorization": f"Bearer {WHATSAPP_TOKEN}",
        "Content-Type": "application/json"
    }
    
    data = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "interactive",
        "interactive": {
            "type": "list",
            "body": {"text": body_text},
            "action": {
                "button": button_text,
                "sections": sections
            }
        }
    }
    
    # print("Interactive list sent:", body_text)
    _post(url, headers, data)

def send_fallback_message(to, card_id, lang="en"):
    msg = (
        "Looks like something went wrong on our side.\n"
        "Please try again later 🙏"
        if lang == "en"
        else
        "आमच्या सर्व्हरकडून काहीतरी अडचण आली आहे.\n"
        "कृपया थोड्या वेळाने पुन्हा प्रयत्न करा 🙏"
    )

    timestamp = get_ist_timestamp()
    try:
        send_whatsapp_message(to, msg)
        if card_id:
            comment = (
                "🤖 BOT Message\n"
                f"🕒 {timestamp}\n\n"
                f"{msg}"
            )
            add_comment_to_card(card_id, comment)
    except Exception as e:
        print("[WHATSAPP] ❌ Failed to send fallback message:", str(e))

def safe_send_message(to, message, card_id, lang="en"):
    timestamp = get_ist_timestamp()
    try:
        send_whatsapp_message(to, message)    
        if card_id:
            comment = (
                "🤖 BOT Message\n"
                f"🕒 {timestamp}\n\n"
                f"{message}"
            )

            add_comment_to_card(card_id, comment)
    except Exception as e:
        print("[SAFE_SEND] ❌ Message send failed:", str(e))
        handle_error(
            error=e,
            user_id=to,
            flow="send_whatsapp_message",
            payload={"message": message}
        )
        send_fallback_message(to, card_id, lang)
        # raise # Don't raise in production bot loop, just log
        
def safe_send_buttons(to, body_text, buttons, card_id=None, lang="en"):    
    timestamp = get_ist_timestamp()
    try:
        send_interactive_buttons(to, body_text, buttons)  
        if card_id:
            buttons_text = format_buttons_for_comment(buttons)
            comment = (
                "🤖 BOT Message\n"
                f"🕒 {timestamp}\n\n"
                f"{body_text}\n\n"
                "📌 Buttons:\n"
                f"{buttons_text}"
            )
            add_comment_to_card(card_id, comment)
    except Exception as e:
        print("[SAFE_SEND] ❌ Button send failed:", str(e))
        handle_error(
            error=e,
            user_id=to,
            flow="send_interactive_buttons",
            payload={
                "body_text": body_text,
                "buttons": buttons
            }
        )
        send_fallback_message(to, card_id, lang)
        
def safe_send_list(to, body_text, sections, card_id=None, button_text="Select", lang="en"):
    timestamp = get_ist_timestamp()
    try:
        send_interactive_list(to, body_text, sections, button_text)  
        if card_id:
            list_text = format_list_sections_for_comment(sections)
            comment = (
                "🤖 BOT Message\n"
                f"🕒 {timestamp}\n\n"
                f"{body_text}\n\n"
                "📋 List Options:\n"
                f"{list_text}"
            )
            add_comment_to_card(card_id, comment)
    except Exception as e:
        print("[SAFE_SEND] ❌ List send failed:", str(e))
        handle_error(
            error=e,
            user_id=to,
            flow="send_interactive_list",
            payload={"sections": sections}
        )
        send_fallback_message(to, card_id, lang)

def safe_send_image(to, image_url, caption, card_id, lang="en"):
    timestamp = get_ist_timestamp()
    try:
        send_image(to, image_url, caption)  
        if card_id:
            comment = (
                "🤖 BOT Message\n"
                f"🕒 {timestamp}\n\n"
                f"{image_url}\n{caption}"
            )
            add_comment_to_card(card_id, comment)
    except Exception as e:
        print("[SAFE_SEND] ❌ Image send failed:", str(e))
        handle_error(
            error=e,
            user_id=to,
            flow="send_image",
            payload={"image_url": image_url}
        )
        send_fallback_message(to, card_id, lang)

def download_image_as_base64(media_url):
    """Downloads media from URL and converts to Base64 string."""
    try:
        headers = {"Authorization": f"Bearer {WHATSAPP_TOKEN}"}
        req = urllib.request.Request(media_url, headers=headers, method="GET")
        with urllib.request.urlopen(req, timeout=10) as resp:
            return base64.b64encode(resp.read()).decode('utf-8')
    except Exception as e:
        print(f"[WHATSAPP] ❌ Error downloading media: {str(e)}")
        return None
