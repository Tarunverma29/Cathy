# 🧠 Cathy

## AI Companion & Mental Well-Being Monitoring Platform

Cathy is a locally hosted AI companion that combines conversational AI, long-term memory, emotion detection, psychological analysis, risk assessment, multi-user support, Telegram integration, and a web platform.

---

# ✨ Features

- 🤖 Local LLM conversations via Ollama
- 🧠 Persona-driven responses
- 💾 Persistent conversation memory
- 😊 Emotion classification
- 📊 Mental health trend tracking
- ⚠️ Risk score detection
- 👥 Multi-user support
- 💬 Multi-chat management
- 📱 Telegram bot integration
- 🖥 Local CLI interface
- 📈 Streamlit admin dashboard
- 🌐 FastAPI backend
- ⚛️ React frontend foundation

---

# 🏗 Architecture

```text
User
 │
 ├── Local CLI
 ├── Telegram Bot
 └── Web Frontend (React)
          │
          ▼
      FastAPI Backend
          │
 ┌────────┼────────┐
 ▼        ▼        ▼
LLM    Memory   Mental Health
          │
          ▼
      PostgreSQL
          │
 ┌────────┼────────┐
 ▼        ▼        ▼
Users   Chats   Emotional Logs
          │
          ▼
    Admin Dashboard
```

---

# 📂 Project Structure

```text
app/
├── local_cli.py
└── telegram_bot.py

core/
├── llm.py
├── memory.py
├── embeddings.py
├── prompt.py
└── chat_service.py

mental/
├── classifier.py
├── reasoning.py
├── patterns.py
├── risk_engine.py
├── responder.py
└── logger.py

database/
├── db.py
├── chats.py
├── messages.py
├── telegram_users.py
└── engine.py

dashboard/
└── live_dashboard.py

personas/
├── cathy.txt
├── christina.txt
└── cathyESFJ-updated.txt

web/
├── backend/
└── frontend/
```

---

# 🧠 How Cathy Works

```text
User Message
      │
      ▼
Conversation Retrieval
      │
      ▼
Emotion Classification
      │
      ▼
Psychological Analysis
      │
      ▼
Pattern Detection
      │
      ▼
Risk Score Generation
      │
      ▼
Memory Retrieval
      │
      ▼
Prompt Construction
      │
      ▼
LLM Response
      │
      ▼
Database Storage
      │
      ▼
Dashboard Update
```

---

# ❤️ Mental Health Pipeline

### Emotion Classification

Model:
- j-hartmann/emotion-english-distilroberta-base

Detects:
- Joy
- Sadness
- Anger
- Fear
- Surprise
- Disgust
- Neutral

### Psychological Reasoning

Analyzes:
- Emotional state
- Mental well-being indicators
- Psychological concerns

### Pattern Detection

Tracks:
- Depression streaks
- Emotional trends
- Behaviour changes

### Risk Engine

Combines:
- Emotion score
- Psychological analysis
- Historical patterns

Risk Levels:

| Score | Level |
|---------|---------|
| 0-5 | Low |
| 6-9 | Moderate |
| 10-14 | High |
| 15+ | Critical |

---

# 💾 Memory System

Uses:

- Sentence Transformers
- all-MiniLM-L6-v2
- pgvector

Workflow:

```text
Message
   │
   ▼
Embedding Generation
   │
   ▼
Vector Storage
   │
   ▼
Similarity Search
   │
   ▼
Relevant Memory Retrieval
```

---

# 🗄 Database

PostgreSQL + pgvector

Core Tables:

### users
Stores user identities

### chats
Stores chat sessions

### messages
Stores conversation history and embeddings

### emotional_logs
Stores emotion analysis and risk scores

---

# 🤖 Telegram Bot

Features:

- Multi-user conversations
- Persistent memory
- Emotion monitoring
- Risk detection
- Chat switching
- New chat creation
- Chat deletion

Run:

```bash
python run.py
```

---

# 💻 Local CLI

Terminal-based interface with:

- Create chat
- Switch chat
- Delete chat
- Continue chat

Run:

```bash
python app/local_cli.py
```

---

# 📊 Dashboard

Built with:

- Streamlit
- Plotly
- Pandas

Shows:

- Registered users
- Emotional trends
- Risk scores
- User activity
- Mental health indicators

Run:

```bash
streamlit run dashboard/live_dashboard.py
```

---

# 🌐 Web Platform

## Backend

Technology:
- FastAPI

Location:

```text
web/backend
```

## Frontend

Technology:
- React
- Vite
- Tailwind CSS

Location:

```text
web/frontend
```

---

# ⚙ Installation

## 1. Clone Repository

```bash
git clone https://github.com/Tarunverma29/Cathy.git
cd Cathy
```

## 2. Create Virtual Environment

```bash
python -m venv venv
source venv/bin/activate
```

## 3. Install Dependencies

```bash
pip install -r requirements_local.txt
```

## 4. Install Ollama

Download and install Ollama, then pull a model:

```bash
ollama pull qwen3:8b
```

## 5. Setup PostgreSQL

Create database and required tables using the files inside:

```text
Cathy_database setup/
```

Files:
- database_setup_commands.txt
- pg_vector_setup.txt

---

# 🛠 Tech Stack

### AI
- Ollama
- Qwen
- Gemma
- Transformers
- Sentence Transformers
- PyTorch

### Backend
- Python
- FastAPI

### Database
- PostgreSQL
- SQLAlchemy
- pgvector
- psycopg2

### Frontend
- React
- Vite
- Tailwind CSS

### Dashboard
- Streamlit
- Plotly
- Pandas

### Messaging
- python-telegram-bot

---

# 🚀 Future Roadmap

- WebSocket streaming
- Voice interaction
- Mobile application
- Therapist dashboard
- Advanced psychological profiling
- Real-time analytics
- Enhanced memory retrieval
- RAG integration

---

# 📜 License

This project is intended for educational and research purposes.

Mental health insights generated by Cathy should not be considered medical diagnosis or professional clinical advice.
