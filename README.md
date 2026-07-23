# 🤖 Sinewave Bot

An AI-powered knowledge management and error resolution platform developed during my Full Stack Development Internship at **Appwizer Solutions (OPC) Private Limited**.

The application enables users to manage product-specific errors, store troubleshooting knowledge, generate embeddings, retrieve relevant solutions using semantic search, and interact through an intelligent chatbot powered by OpenAI.

---

## 🚀 Features

- 📋 Error Knowledge Base Management
- 🔍 Semantic Search using OpenAI Embeddings
- 🤖 AI-powered Chatbot for Error Resolution
- 🖼️ Screenshot Upload & Management
- 📊 Dashboard with Error Statistics
- 📈 Product-wise Error Tracking
- 🔐 Authentication & Authorization
- 📌 Trello Integration for Issue Tracking
- ☁️ Supabase Database Integration
- 📱 Responsive Modern UI

---

## 🛠️ Tech Stack

### Frontend
- Next.js (App Router)
- React.js
- TypeScript
- Tailwind CSS
- ShadCN UI
- Sonner
- Recharts

### Backend
- FastAPI
- Python
- REST APIs
- OpenAI API
- Supabase
- Trello API

### Database
- Supabase PostgreSQL

### AI
- OpenAI GPT-4o Mini
- text-embedding-3-small

### Tools
- Git
- GitHub
- VS Code
- Postman

---

# 📂 Project Structure

```
Sinewave-bot/
│
├── Frontend/
│   ├── app/
│   ├── components/
│   ├── public/
│   ├── lib/
│   └── package.json
│
├── Backend/
│   ├── app/
│   ├── services/
│   ├── routers/
│   ├── deploy/
│   ├── requirements.txt
│   └── ingest.py
│
└── README.md
```

---

# ⚙️ Installation

## Clone Repository

```bash
git clone https://github.com/Asmitajadhav12/Sinewave-bot.git
```

```bash
cd Sinewave-bot
```

---

## Frontend Setup

```bash
cd Frontend
```

Install dependencies

```bash
npm install
```

Run

```bash
npm run dev
```

---

## Backend Setup

```bash
cd Backend
```

Create Virtual Environment

```bash
python -m venv venv
```

Activate

Windows

```bash
venv\Scripts\activate
```

Linux/Mac

```bash
source venv/bin/activate
```

Install Dependencies

```bash
pip install -r requirements.txt
```

Create a `.env` file using `.env.example`.

Run Backend

```bash
uvicorn app.main:app --reload
```

---

# 📊 Workflow

```
User
      │
      ▼
Frontend (Next.js)
      │
      ▼
FastAPI Backend
      │
      ├────────► OpenAI API
      │
      ├────────► Supabase Database
      │
      └────────► Trello API
```

---

# ✨ Key Functionalities

- Product Management
- Function Area Management
- Error Logging
- AI-powered Error Resolution
- Screenshot Storage
- Dashboard Analytics
- Embedding Generation
- Semantic Search
- Trello Ticket Creation

---

# 🔮 Future Enhancements

- Role-based Access Control
- Multi-language Support
- Email Notifications
- Advanced Analytics Dashboard
- Conversation History
- Docker Deployment
- CI/CD Pipeline

---

# 👩‍💻 Author

**Asmita Kiran Jadhav**

📧 Email: jadhavasmita.1272004@gmail.com

🔗 LinkedIn: https://www.linkedin.com/in/asmita-jadhav-17724b259/

💻 GitHub: https://github.com/Asmitajadhav12

---

## ⭐ If you found this project useful, consider giving it a star!
