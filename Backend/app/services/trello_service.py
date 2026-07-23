import os
import urllib.parse
import urllib.request
import urllib.error
import json
from datetime import datetime

# --------------------------------------------------------------------- 
# Trello credentials (from Lambda environment variables)
# --------------------------------------------------------------------- 
TRELLO_KEY = os.environ.get("TRELLO_KEY")
TRELLO_TOKEN = os.environ.get("TRELLO_TOKEN")
TRELLO_LIST_ID = os.environ.get("TRELLO_LIST_ID")
TRELLO_TECH_ISSUE_LIST_ID = os.environ.get("TRELLO_TECH_ISSUE_LIST_ID")
TRELLO_MESSAGE_LIST_ID = os.environ.get("TRELLO_MESSAGE_LIST_ID")
TRELLO_RESOLVED_LIST_ID = os.environ.get("TRELLO_RESOLVED_LIST_ID", "6971f7c236ab190a85a71704")

# --------------------------------------------------------------------- 
# Move Trello card to List
# --------------------------------------------------------------------- 
def move_card_to_list(card_id, list_id=TRELLO_RESOLVED_LIST_ID):
    """
    Moves a card to a specific list (default: Resolved List).
    """
    if not card_id or not list_id:
        print("[TRELLO] ⚠️ Missing card_id or list_id for move.")
        return False

    url = f"https://api.trello.com/1/cards/{card_id}"
    params = urllib.parse.urlencode({
        "key": TRELLO_KEY,
        "token": TRELLO_TOKEN,
        "idList": list_id,
        "pos": "top" 
    }).encode("utf-8")

    try:
        req = urllib.request.Request(url, data=params, method="PUT")
        with urllib.request.urlopen(req, timeout=10) as resp:
            result = json.loads(resp.read().decode())
            print(f"[TRELLO] ✅ Card {card_id} moved to list {list_id}")
            return True
    except Exception as e:
        print("[TRELLO] ❌ Error moving card:", str(e))
        return False

# --------------------------------------------------------------------- 
# Create Trello card
# --------------------------------------------------------------------- 

def create_card(user_id, context):
    """
    Creates a Trello card in the configured list.
    Returns (card_id, short_url) on success, (None, None) on failure.
    """

    print("Create card called:")

    images = context.get('images', [])
    valid_images = [img for img in images if img]

    print("After images:")
    card_name = f"Issue from {user_id}"
    timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
    text = context.get('text', 'No Description Provided')
    
    desc_lines = [
        f"**Reported by:** {user_id}",
        f"**Timestamp:** {timestamp}",
        f"**Description:** {text}"
    ]
    if valid_images:
        desc_lines.append(f"**See Attached Images:** ")

    card_desc = "\n".join(desc_lines)

    params = urllib.parse.urlencode({
        "idList": TRELLO_LIST_ID,
        "key": TRELLO_KEY,
        "token": TRELLO_TOKEN,
        "name": card_name,
        "desc": card_desc,
        "pos": "top"
    }).encode("utf-8")

    try:
        req = urllib.request.Request("https://api.trello.com/1/cards", data=params, method="POST")
        with urllib.request.urlopen(req, timeout=10) as resp:
            result = json.loads(resp.read().decode())
            card_id = result.get("id")
            card_url = result.get("shortUrl")
            print(f"[TRELLO] ✅ Card created for {user_id}: {card_url}")
            # If image URL is present, attach it
            if valid_images and card_id:
                for idx, image in enumerate(valid_images, start=1):
                    print(f"Processing image {idx}: {image}")
                    attachImage(card_id,image)
            return card_id, card_url
    except Exception as e:
        print("[TRELLO] ❌ Error creating card:", str(e))
        return None, None


# --------------------------------------------------------------------- 
# Attach image to Trello card
# --------------------------------------------------------------------- 
def attachImage(card_id, image_url):
    """
    Attaches an image URL to an existing Trello card and sets it as the cover.
    """
    if not card_id or not image_url:
        print("[TRELLO] ⚠️ Missing card_id or image_url for attachment.")
        return

    api_url = f"https://api.trello.com/1/cards/{card_id}/attachments"
    params = urllib.parse.urlencode({
        "key": TRELLO_KEY,
        "token": TRELLO_TOKEN,
        "url": image_url,
        "mimeType": "image/jpeg",
        "setCover": "true"
    }).encode("utf-8")

    try:
        req = urllib.request.Request(api_url, data=params, method="POST")
        with urllib.request.urlopen(req, timeout=10) as resp:
            result = json.loads(resp.read().decode())
            print(f"[TRELLO] 📎 Image attached to card {card_id}: {result.get('url')}")
            return result.get('url')
    except urllib.error.HTTPError as e:
        err = e.read().decode()
        print("[TRELLO] ❌ HTTP error attaching image:", err)
    except Exception as e:
        print("[TRELLO] ❌ Error attaching image:", str(e))


def create_tech_issue_card(title, description):
    url = "https://api.trello.com/1/cards"

    payload = {
        "name": title,
        "desc": description,
        "idList": TRELLO_TECH_ISSUE_LIST_ID,
        "key": TRELLO_KEY,
        "token": TRELLO_TOKEN,
    }

    data = urllib.parse.urlencode(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data)

    try:
        with urllib.request.urlopen(req, timeout=10):
            pass
    except Exception as e:
        print("[TRELLO ERROR]", str(e))

def create_messages_card(phone, user_name=None):
    """
    Creates a Trello card for WhatsApp message tracking
    """
    url = "https://api.trello.com/1/cards"

    # Ensure list ID is available
    if not TRELLO_MESSAGE_LIST_ID:
        print("[TRELLO] ⚠️ Missing TRELLO_MESSAGE_LIST_ID")
        return None

    payload = urllib.parse.urlencode({
        "key": TRELLO_KEY,
        "token": TRELLO_TOKEN,
        "idList": TRELLO_MESSAGE_LIST_ID,
        "name": f"WhatsApp Interaction - {phone}",
        "desc": f"📞 Phone: {phone}\n👤 Name: {user_name or 'Unknown'}",
        "pos": "top"
    }).encode("utf-8")

    try:
        req = urllib.request.Request(url, data=payload, method="POST")
        with urllib.request.urlopen(req, timeout=10) as resp:
            result = json.loads(resp.read().decode())
            card_id = result.get("id")
            print(f"[TRELLO] ✅ Message card created: {card_id}")
            return card_id
    except Exception as e:
        print("[TRELLO] ❌ Error creating message card:", str(e))
        return None


def add_comment_to_card(card_id, message):
    """
    Adds a comment to an existing Trello card
    """
    # print("into add comment section")
    if not card_id or not message:
        print("[TRELLO] ⚠️ Missing card_id or message")
        return None

    # ✅ key & token MUST be query params
    url = (
        f"https://api.trello.com/1/cards/{card_id}/actions/comments"
        f"?key={TRELLO_KEY}&token={TRELLO_TOKEN}"
    )
    # print(f"[TRELLO] 💬 Adding comment to card url {url}")
    payload = urllib.parse.urlencode({
        "text": message
    }).encode("utf-8")

    try:
        req = urllib.request.Request(
            url,
            data=payload,
            method="POST",
            headers={
                "Content-Type": "application/x-www-form-urlencoded"
            }
        )

        with urllib.request.urlopen(req, timeout=10) as resp:
            result = json.loads(resp.read().decode())
            # print(f"[TRELLO] 💬 Comment added to card {card_id}")
            return result

    except urllib.error.HTTPError as e:
        print("[TRELLO] ❌ HTTP error adding comment:", e.code, e.read().decode())
    except Exception as e:
        print("[TRELLO] ❌ Error adding comment:", str(e))
