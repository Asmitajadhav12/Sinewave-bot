import datetime
import traceback
from app.services.trello_service import create_tech_issue_card

def handle_error(error, user_id=None, flow=None, payload=None):
    """
    Logs an error to Trello as a Tech Issue card.
    """
     # UTC → IST (UTC + 5:30)
    ist_time = datetime.datetime.utcnow() + datetime.timedelta(hours=5, minutes=30)
    timestamp = ist_time.strftime("%Y-%m-%d %H:%M:%S IST")
    
    trace = traceback.format_exc()

    title = f"🚨 WhatsApp Bot Error | {timestamp}"

    description = f"""
🕒 Time:
{timestamp}

👤 User:
{user_id}

🔀 Flow:
{flow}

❌ Error:
{str(error)}

🧵 Traceback:
{trace}

📦 Payload:
{payload}
"""

    # print(description)
    create_tech_issue_card(title, description)
