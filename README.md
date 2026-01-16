# AI Agent Team Activity Monitor

An AI-powered chatbot that integrates with JIRA and GitHub APIs to answer questions about team member activities. Ask questions like *"What is John working on?"* and get AI-generated summaries of their work.

## Features

- **2-AI-Call Pipeline**: Efficient architecture with Router Agent (tool calling) + Response Agent (formatting)
- **Multi-Provider AI**: Supports OpenAI GPT and Anthropic Claude
- **Real API Integration**: Connects to JIRA Cloud and GitHub
- **Conversation History**: SQLite-backed chat history with follow-up support
- **Mock Data Fallback**: Demo users available for testing without API keys

## Architecture: Simplified Micro-Agent Pattern

This project implements a **2-agent pipeline** as a practical demonstration of the micro-agent pattern.

### Current Implementation (2 Agents)

```
┌─────────────┐    ┌─────────────────┐    ┌─────────────────┐
│ User Query  │───▶│  Router Agent   │───▶│ Response Agent  │
└─────────────┘    │ (with tools)    │    │ (formatting)    │
                   └─────────────────┘    └─────────────────┘
                          │
                   ┌──────┴──────┐
                   ▼             ▼
              jira_agent    github_agent
              (tool)        (tool)
```

**Flow:**
1. **Username Extraction** (regex, instant): Extract team member name from query
2. **AI Call 1 - Router Agent**: Decides which tools to call (JIRA, GitHub, both, or none)
3. **AI Call 2 - Response Agent**: Formats the fetched data into clean markdown

### Ideal Micro-Agent Architecture (4+ Agents)

```
┌─────────┐   ┌──────────────┐   ┌──────────────┐   ┌──────────┐
│ Intent  │──▶│ Orchestrator │──▶│ JIRA Agent   │──▶│ Response │
│ Agent   │   │    Agent     │   │ GitHub Agent │   │  Agent   │
└─────────┘   └──────────────┘   └──────────────┘   └──────────┘
```

In a full micro-agent architecture, each agent has a single responsibility:
- **Intent Agent**: Parse user intent and extract entities
- **Orchestrator Agent**: Decide which data sources to query
- **JIRA Agent**: Specialized for JIRA API interactions
- **GitHub Agent**: Specialized for GitHub API interactions
- **Response Agent**: Format and present the final response

### Trade-offs

| Approach | Pros | Cons |
|----------|------|------|
| **Full micro-agents** | Better separation of concerns, lower cost per call, highly specialized | More development time, complex orchestration |
| **Simplified (current)** | Faster to build, easier to debug, demonstrates core concepts | Larger prompts, less specialized |

### Why This Approach?

1. **Demonstrates core concepts**: Tool calling, agent orchestration, data aggregation
2. **Practical for scope**: Balances sophistication with implementation time
3. **Extensible**: Can be expanded to full micro-agent pattern by splitting Router Agent into Intent + Orchestrator

## Tech Stack

| Layer | Technologies |
|-------|-------------|
| **Frontend** | React 19, Vite, Tailwind CSS |
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
│   │   ├── ChatInterface.jsx  # Main chat UI
│   │   └── MessageBubble.jsx  # Message rendering with markdown
│   └── api/
│       └── client.js          # API client
└── package.json
```

## Documentation

For detailed technical documentation including API reference, design patterns, and implementation details, see [DOCUMENTATION.md](./DOCUMENTATION.md).
