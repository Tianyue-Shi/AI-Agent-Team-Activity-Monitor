# AI Agent Team Activity Monitor

An AI-powered chatbot that integrates with JIRA and GitHub APIs to answer questions about team member activities. Ask questions like *"What is John working on?"* and get AI-generated summaries of their work.

## Features

- **2-AI-Call Pipeline**: Efficient architecture with Router Agent (tool calling) + Response Agent (formatting)
- **Multi-Provider AI**: Supports OpenAI GPT and Anthropic Claude
- **Smart Routing**: AI decides which data sources to query (JIRA, GitHub, both, or none)
- **Real API Integration**: Connects to JIRA Cloud and GitHub
- **Conversation History**: SQLite-backed chat history with follow-up support
- **Mock Data Fallback**: Demo users available for testing without API keys
- **Markdown Responses**: Rich formatting with tables, bullet points, and structured analysis

## Architecture

![Team Activity Monitor Architecture](./Team%20Activity%20Monitor%20Architecture-Page-2.jpg)

## Tech Stack

| Layer | Technologies |
|-------|-------------|
| **Frontend** | React 19, Vite, Tailwind CSS, React Markdown |
| **Backend** | Python 3.13+, FastAPI, SQLAlchemy, SQLite |
| **AI Providers** | OpenAI GPT, Anthropic Claude |
| **External APIs** | JIRA Cloud, GitHub |

## Quick Start

### Prerequisites
- Python 3.13+
- Node.js 18+
- OpenAI API key (required)
- JIRA/GitHub credentials (optional - mock data available)

### Backend
```bash
cd backend
python3 -m venv venv && source venv/bin/activate  # Windows: venv\Scripts\activate
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

## Example Queries

| Query | Route | Description |
|-------|-------|-------------|
| "Hello" | None | Greeting - no data fetched |
| "What is John working on?" | Both | Fetches JIRA + GitHub |
| "Show me Sarah's JIRA tickets" | JIRA only | Fetches JIRA data |
| "What has Mike committed recently?" | GitHub only | Fetches GitHub data |

## Project Structure

```
backend/
├── app/
│   ├── main.py              # FastAPI application
│   ├── routers/
│   │   └── chat.py          # Chat endpoint (2-AI-call pipeline)
│   ├── services/
│   │   ├── micro_agents.py  # Router + Response agents
│   │   ├── intent_classifier.py  # Username extraction (regex)
│   │   ├── jira_client.py   # JIRA API client
│   │   ├── github_client.py # GitHub API client
│   │   └── ai_providers.py  # OpenAI/Claude wrappers
│   └── prompts.yaml         # System prompts for agents
└── requirements.txt

frontend/
├── src/
│   ├── App.jsx
│   ├── components/
│   │   ├── ChatInterface.jsx  # Main chat UI with history
│   │   └── MessageBubble.jsx  # Message rendering with markdown
│   └── api/
│       └── client.js          # API client
└── package.json
```

## Documentation

| Document | Description |
|----------|-------------|
| [ARCHITECTURE.md](./ARCHITECTURE.md) | Architecture decisions, trade-offs, micro-agent pattern |
| [DOCUMENTATION.md](./DOCUMENTATION.md) | Full technical docs, API reference, design patterns |
