# AI-Agent-Team-Activity-Monitor

An AI-powered chatbot that integrates with JIRA and GitHub APIs to answer questions about team member activities. Ask questions like *"What is John working on these days?"* and get AI-generated summaries of their work.

## Features

- **Dual-Mode Chat**: Procedural (deterministic) vs Agentic (AI-decides) modes
- **Multi-Provider AI**: Supports OpenAI GPT and Anthropic Claude
- **Real API Integration**: Connects to JIRA Cloud and GitHub
- **Prompt Management**: Version-controlled system prompts with rollback capability
- **Mock Data Fallback**: Demo users available for testing without API keys

## Architecture

![Team Activity Monitor Architecture](./Team%20Activity%20Monitor%20Architecture.drawio.png)

## Tech Stack

| Layer | Technologies |
|-------|-------------|
| **Frontend** | React 19, Vite, Tailwind CSS |
| **Backend** | Python 3.13+, FastAPI, SQLAlchemy, SQLite |
| **External APIs** | JIRA Cloud, GitHub, OpenAI, Anthropic |

## Quick Start

### Prerequisites
- Python 3.13+
- Node.js 18+
- OpenAI API key (required)
- JIRA/GitHub credentials (optional - mock data available)

### Backend
```bash
cd backend
python -m venv venv && source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env  # Then edit .env with your API keys
uvicorn app.main:app --reload --port 8000
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

## Access Points

| Service | URL |
|---------|-----|
| Frontend | http://localhost:5173 |
| Backend API | http://localhost:8000 |
| API Documentation | http://localhost:8000/docs |

## Documentation

For detailed technical documentation including API reference, design patterns, and implementation details, see [DOCUMENTATION.md](./DOCUMENTATION.md).

