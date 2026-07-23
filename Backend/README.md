# Sinewave WhatsApp Bot (EC2 Version)

This project has been migrated from AWS Lambda to a FastAPI application suitable for deployment on an EC2 instance.

## 📂 Project Structure

- `app/`: Main application code.
  - `main.py`: FastAPI server logic.
  - `utils.py`: WhatsApp API utilities.
  - `services/`: Business logic (OpenAI, Supabase).
- `ingest.py`: Script to ingest Excel data into Supabase Vector Store.
- `legacy/`: Archived Lambda code (for reference).
- `setup_ec2.sh`: One-click setup script for EC2 (Ubuntu).
- `start_bot.sh`: Script to start the bot in a `tmux` session.

## 🧪 Local Testing

You can test the bot locally without exposing it to the internet.

1.  **Setup Environment**:
    ```bash
    cp .env.example .env
    # Edit .env with your actual keys
    pip install -r requirements.txt
    ```

2.  **Run Server**:
    ```bash
    uvicorn app.main:app --reload
    ```

3.  **Simulate WhatsApp**:
    In a separate terminal, run:
    ```bash
    python test_local.py
    ```
    This script will:
    - Verify the webhook connection.
    - Send a "Hi" message.
    - Send a sample error message ("Schedule UD").

    Check the `uvicorn` terminal to see the bot's logs and responses.

## 🚀 Deployment on EC2

1.  **Launch Instance**: Use `t3.medium` with Ubuntu.
2.  **Clone Repo**:
    ```bash
    git clone <YOUR_REPO_URL>
    cd <REPO_NAME>
    ```
3.  **Setup Environment**:
    ```bash
    chmod +x setup_ec2.sh
    ./setup_ec2.sh
    ```
4.  **Configure Secrets**:
    Create a `.env` file with your keys:
    ```ini
    OPENAI_API_KEY=sk-...
    SUPABASE_URL=...
    SUPABASE_SERVICE_ROLE_KEY=...
    WHATSAPP_PHONE_NUMBER_ID=...
    WHATSAPP_ACCESS_TOKEN=...
    VERIFY_TOKEN=...
    EMBEDDING_MODEL=text-embedding-3-small
    LLM_MODEL=gpt-4o-mini
    ```
5.  **Run Ingestion** (One-time):
    Upload your Excel file and run:
    ```bash
    source venv/bin/activate
    python ingest.py --file errors.xlsx
    ```
6.  **Start Bot**:
    ```bash
    chmod +x start_bot.sh
    ./start_bot.sh
    ```
7.  **Verify**:
    Check logs: `tmux attach -t bot`

## ⚠️ Notes

- **Missing Utilities**: The original `whatsapp_utils.py` and `trello_utils.py` were missing.
  - `app/utils.py` implements standard WhatsApp sending logic.
  - Trello integration is currently **stubbed** in `app/main.py`. You will need to re-implement it if needed.
- **Port**: The bot runs on port 8000. Ensure your EC2 Security Group allows traffic on port 8000 (or configure Nginx as a reverse proxy).
