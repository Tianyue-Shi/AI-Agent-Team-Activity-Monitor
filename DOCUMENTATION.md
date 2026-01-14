# Team Activity Monitor - Technical Documentation

## Table of Contents
1. [Project Overview](#project-overview)
2. [Architecture](#architecture)
3. [Tech Stack](#tech-stack)
4. [Project Setup](#project-setup)
5. [Backend Deep Dive](#backend-deep-dive)
6. [Frontend Deep Dive](#frontend-deep-dive)
7. [API Reference](#api-reference)
8. [Data Flow](#data-flow)
9. [Design Patterns & Tradeoffs](#design-patterns--tradeoffs)
10. [Performance Optimizations](#performance-optimizations)
11. [Security Considerations](#security-considerations)

---

## Project Overview

**Team Activity Monitor** is an AI-powered chatbot that integrates with JIRA and GitHub APIs to answer questions about team member activities. The core question it answers is: *"What is [member] working on these days?"*

### Key Features
- **Dual-Mode Architecture**: Procedural (deterministic) vs Agentic (AI-decides) modes
- **Multi-Provider AI Support**: OpenAI GPT and Anthropic Claude
- **Real API Integration**: JIRA Cloud and GitHub REST APIs
- **Prompt Version Control**: Append-only system prompts with rollback capability
- **Mock Data Fallback**: Demo users for testing without real API keys
- **User Selection Dropdown**: Unified list of real and mock team members

---

## Architecture

![Team Activity Monitor Architecture](./Team%20Activity%20Monitor%20Architecture.drawio.png)

---

## Tech Stack

### Backend
| Technology | Version | Purpose |
|------------|---------|---------|
| **Python** | 3.13+ | Core language |
| **FastAPI** | 0.109+ | Web framework (async, type hints, auto-docs) |
| **Uvicorn** | 0.27+ | ASGI server |
| **SQLAlchemy** | 2.0+ | ORM with async support |
| **aiosqlite** | 0.22+ | Async SQLite driver |
| **Pydantic** | 2.5+ | Data validation & settings |
| **httpx** | 0.26+ | Async HTTP client for external APIs |
| **openai** | 1.12+ | OpenAI SDK |
| **anthropic** | 0.18+ | Anthropic Claude SDK |

### Frontend
| Technology | Version | Purpose |
|------------|---------|---------|
| **React** | 19.2+ | UI library |
| **Vite** | 7.2+ | Build tool & dev server |
| **Tailwind CSS** | 4.1+ | Utility-first CSS |
| **Lucide React** | 0.562+ | Icon library |
| **React Router** | 7.12+ | Client-side routing |

### External APIs
| Service | API Version | Authentication |
|---------|-------------|----------------|
| **JIRA Cloud** | REST API v3 | Basic Auth (email:token) |
| **GitHub** | REST API v3 | Bearer token |
| **OpenAI** | Chat Completions | API key |
| **Anthropic** | Messages API | API key |

---

## Project Setup

### Prerequisites
- Python 3.13+
- Node.js 18+
- JIRA Cloud account (optional)
- GitHub account (optional)
- OpenAI API key
- Anthropic API key (optional)

### Backend Setup

```bash
# 1. Navigate to backend
cd backend

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Create .env file
cat > .env << EOF
# AI Providers
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...

# JIRA Configuration (optional)
JIRA_BASE_URL=https://your-domain.atlassian.net
JIRA_EMAIL=your-email@example.com
JIRA_API_TOKEN=your-api-token

# GitHub Configuration (optional)
GITHUB_TOKEN=ghp_...

# Debug mode
DEBUG=false
EOF

# 5. Run server
uvicorn app.main:app --reload --port 8000
```

### Frontend Setup

```bash
# 1. Navigate to frontend
cd frontend

# 2. Install dependencies
npm install

# 3. Run dev server
npm run dev
```

### Access Points
- **Frontend**: http://localhost:5173
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

---

## Backend Deep Dive

### Directory Structure

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py           # FastAPI app, lifespan, CORS, debug endpoints
│   ├── config.py         # Pydantic Settings (env vars)
│   ├── database.py       # SQLAlchemy async engine, session factory
│   ├── models.py         # ORM models + Pydantic schemas
│   ├── seed.py           # Default prompt seeding
│   ├── routers/
│   │   ├── __init__.py
│   │   ├── chat.py       # /chat endpoints
│   │   └── prompts.py    # /prompts endpoints
│   └── services/
│       ├── __init__.py
│       ├── ai_providers.py   # OpenAI/Claude abstraction
│       ├── chat_engine.py    # Dual-mode logic
│       ├── github_client.py  # GitHub API client
│       └── jira_client.py    # JIRA API client
├── requirements.txt
├── team_monitor.db       # SQLite database (auto-created)
└── .env                  # Environment variables
```

### Key Components

#### 1. Configuration (`config.py`)
```python
class Settings(BaseSettings):
    openai_api_key: str = ""
    anthropic_api_key: str = ""
    jira_base_url: str = ""
    jira_email: str = ""
    jira_api_token: str = ""
    github_token: str = ""
    debug: bool = False
    database_url: str = "sqlite+aiosqlite:///./team_monitor.db"
    
    model_config = SettingsConfigDict(env_file=".env")

@lru_cache()  # Singleton pattern
def get_settings() -> Settings:
    return Settings()
```

#### 2. Database (`database.py`)
- **Async SQLAlchemy 2.0** with `aiosqlite` driver
- **Session management** via FastAPI `Depends(get_db)`
- **Auto-commit/rollback** in context manager

#### 3. Models (`models.py`)
- **SQLAlchemy ORM**: `SystemPrompt` table
- **Pydantic Schemas**: Request/Response validation
  - `ChatRequest`, `ChatResponse`
  - `PromptCreate`, `PromptResponse`, `PromptHistoryResponse`
  - `SelectedUser` (for dropdown selection)

#### 4. Chat Engine (`chat_engine.py`)
The **core business logic** implementing dual-mode architecture:

**Procedural Mode:**
```
User Query → Extract Username → Fetch JIRA → Fetch GitHub → AI Summary
```
- Always fetches both data sources
- Deterministic, reliable
- Higher latency and API costs

**Agentic Mode:**
```
User Query → AI (with tools) → [Tool Calls?] → Execute Tools → AI Response
```
- AI decides whether to fetch data
- Uses OpenAI/Claude function calling
- Lower cost for simple queries
- Non-deterministic

#### 5. AI Providers (`ai_providers.py`)
**Strategy Pattern** implementation:

```python
class AIProvider(ABC):
    @abstractmethod
    async def generate(messages, system_prompt) -> AIResponse
    
    @abstractmethod
    async def generate_with_tools(messages, tools, system_prompt) -> AIResponse

class OpenAIProvider(AIProvider): ...
class ClaudeProvider(AIProvider): ...

def get_ai_provider(name: str) -> AIProvider:  # Factory
```

#### 6. API Clients (`jira_client.py`, `github_client.py`)
**Repository Pattern** with fallback:

```python
class JiraClient:
    _use_mock: bool  # True if no credentials
    
    async def get_user_issues(username) -> JiraUserActivity:
        if self._use_mock:
            return await self._get_mock_issues(username)
        else:
            return await self._get_real_issues(username)
```

---

## Frontend Deep Dive

### Directory Structure

```
frontend/
├── src/
│   ├── main.jsx          # React entry point
│   ├── App.jsx           # Root component
│   ├── index.css         # Tailwind imports
│   ├── api/
│   │   └── client.js     # API client (fetch wrapper)
│   └── components/
│       ├── ChatInterface.jsx   # Main chat UI
│       ├── MessageBubble.jsx   # Message display
│       └── AdminPanel.jsx      # Prompt management
├── index.html
├── package.json
├── vite.config.js
├── tailwind.config.js
└── postcss.config.js
```

### Key Components

#### ChatInterface.jsx
- **State Management**: `useState` for messages, mode, provider, team members
- **User Selection**: Dropdown with real JIRA/GitHub users + mock users
- **Mode Toggle**: Procedural vs Agent
- **Provider Toggle**: OpenAI vs Claude
- **Auto-scroll**: `useRef` + `scrollIntoView`

#### API Client (`client.js`)
```javascript
async function fetchAPI(endpoint, options = {}) {
  const response = await fetch(`http://localhost:8000${endpoint}`, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  });
  if (!response.ok) throw new Error(error.detail);
  return response.json();
}

export async function sendChatMessage(query, mode, aiProvider, selectedUser) {
  return fetchAPI('/chat', {
    method: 'POST',
    body: JSON.stringify({ query, mode, ai_provider: aiProvider, selected_user: selectedUser }),
  });
}
```

---

## API Reference

### Chat Endpoints

#### `POST /chat`
Main chat endpoint - answers team activity questions.

**Request:**
```json
{
  "query": "What is John working on?",
  "mode": "procedural",        // or "agent"
  "ai_provider": "openai",     // or "claude"
  "selected_user": {           // optional
    "id": "mock_john",
    "display_name": "John",
    "source": "mock",
    "jira_display_name": "John",
    "github_username": "john"
  }
}
```

**Response:**
```json
{
  "response": "John is working on...",
  "mode": "procedural",
  "ai_provider": "openai",
  "sources_consulted": ["jira", "github"]
}
```

#### `GET /chat/modes`
Returns available chat modes.

#### `GET /chat/providers`
Returns available AI providers with configuration status.

#### `GET /chat/team`
Returns unified list of real + mock team members.

### Prompt Endpoints

#### `GET /prompts/current`
Get the active system prompt.

#### `POST /prompts/update`
Create a new prompt version (append-only).

#### `GET /prompts/history`
Get all prompt versions for audit trail.

#### `POST /prompts/rollback/{version}`
Create new version with old prompt text.

#### `GET /prompts/{version}`
Get a specific prompt version.

### Debug Endpoints

| Endpoint | Purpose |
|----------|---------|
| `GET /debug/activity/{username}` | Test JIRA + GitHub fetch |
| `GET /debug/jira/status` | JIRA connection status |
| `GET /debug/github/status` | GitHub connection status |
| `GET /debug/ai-status` | AI provider configuration |

---

## Data Flow

### Chat Request Flow (Procedural Mode)

```
1. Frontend sends POST /chat
   │
2. FastAPI validates request (Pydantic)
   │
3. Chat Router fetches active SystemPrompt from DB
   │
4. Chat Engine determines user:
   │  └─ selected_user from dropdown? → Use platform-specific identifiers
   │  └─ No selection? → Extract username from query (regex)
   │
5. Determine data source:
   │  └─ Mock user? → Force _use_mock = True
   │  └─ Real user? → Use real APIs
   │
6. Fetch data (parallel):
   │  ├─ JIRA Client → get_user_issues(username)
   │  └─ GitHub Client → get_user_activity(username)
   │
7. Format data into context string
   │
8. AI Provider generates summary:
   │  └─ System prompt + Context + Query → AI → Response
   │
9. Return ChatResponse to frontend
```

### Prompt Update Flow

```
1. Admin submits new prompt text
   │
2. POST /prompts/update
   │
3. Get max version number
   │
4. Deactivate all existing prompts (is_active = False)
   │
5. Create new row: version = max + 1, is_active = True
   │
6. Never delete or modify old rows (audit trail)
```

---

## Design Patterns & Tradeoffs

### 1. Dual-Mode Architecture

| Aspect | Procedural | Agentic |
|--------|------------|---------|
| **Data Fetching** | Always fetch both | AI decides |
| **Reliability** | High (deterministic) | Medium (AI-dependent) |
| **Latency** | Higher (always 2 API calls) | Lower (may skip) |
| **Cost** | Higher (always uses tokens) | Lower (smarter) |
| **Use Case** | Critical dashboards | Casual chat |

**Tradeoff**: Reliability vs Efficiency

### 2. Strategy Pattern (AI Providers)

```python
class AIProvider(ABC):
    @abstractmethod
    async def generate(...) -> AIResponse
    @abstractmethod
    async def generate_with_tools(...) -> AIResponse
```

**Benefit**: Easy to add new providers (Gemini, Llama, etc.)
**Tradeoff**: Slight abstraction overhead

### 3. Repository Pattern (API Clients)

```python
class JiraClient:
    async def get_user_issues(username) -> JiraUserActivity
    # Implementation hidden (mock vs real)
```

**Benefit**: Swap between mock/real without changing business logic
**Tradeoff**: Additional layer of indirection

### 4. Append-Only Pattern (Prompts)

**Why not UPDATE?**
- Full audit trail
- Easy rollback
- No data loss
- "Blame" capability

**Tradeoff**: Database grows over time (mitigated by small text data)

### 5. Singleton Pattern (Settings)

```python
@lru_cache()
def get_settings() -> Settings:
    return Settings()
```

**Benefit**: Single configuration instance, env vars loaded once
**Tradeoff**: Settings are immutable during runtime (restart required)

### 6. Factory Pattern (AI Provider Creation)

```python
def get_ai_provider(name: str) -> AIProvider:
    if name == "openai": return OpenAIProvider(...)
    if name == "claude": return ClaudeProvider(...)
```

**Benefit**: Decoupled creation, easy to extend
**Tradeoff**: Extra function call

---

## Performance Optimizations

### 1. Async Everything
- **FastAPI** async endpoints
- **aiosqlite** async database
- **httpx** async HTTP client
- **openai/anthropic** async SDK

**Impact**: Non-blocking I/O, better concurrency

### 2. Lazy Client Initialization

```python
def _get_client(self):
    if self._client is None:
        self._client = httpx.AsyncClient(...)
    return self._client
```

**Impact**: Resources created only when needed

### 3. Cached Settings

```python
@lru_cache()
def get_settings() -> Settings:
```

**Impact**: Environment variables parsed once

### 4. Database Session Pooling

```python
AsyncSessionLocal = async_sessionmaker(
    engine,
    expire_on_commit=False,  # Keep objects usable
)
```

**Impact**: Efficient connection reuse

### 5. Parallel Data Fetching (Potential)

Currently sequential, but easily parallelizable:
```python
jira_data, github_data = await asyncio.gather(
    jira_client.get_user_issues(username),
    github_client.get_user_activity(username),
)
```

### 6. Frontend Optimizations
- **Vite** hot module replacement
- **React 19** concurrent features
- **Tailwind CSS** purging (smaller bundle)

---

## Security Considerations

### 1. Environment Variables
- Sensitive keys in `.env` (gitignored)
- Never commit credentials

### 2. CORS Configuration
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Specific origins
    allow_credentials=True,
)
```

### 3. Input Validation
- **Pydantic** models validate all requests
- `Field(min_length=1)` prevents empty queries
- `Literal["procedural", "agent"]` restricts mode values

### 4. API Token Security
- JIRA: Basic Auth (email:token base64)
- GitHub: Bearer token
- AI: API keys in headers

### 5. SQL Injection Prevention
- **SQLAlchemy ORM** parameterized queries
- No raw SQL strings

### 6. Rate Limiting (Not Implemented)
- Potential improvement: Add rate limiting middleware
- Consider: `slowapi` or custom solution

---

## Good to Know

### Mock vs Real User Detection

```python
MOCK_USERS = {"john", "sarah", "mike", "lisa"}
REAL_USER_ALIASES = {"justin", "justin shi", "shi", "tianyue-shi"}

# Mock users → Force mock data
# Real users → Use real APIs
```

### Username Resolution

```python
USERNAME_ALIASES = {
    "justin": {
        "jira": "Justin Shi",      # JIRA display name
        "github": "Tianyue-Shi",   # GitHub username
    }
}
```

Different platforms use different identifiers!

### GitHub Events API Limitation

The GitHub Events API doesn't always include commit details in `PushEvent` payloads. Solution: Fetch commits directly from `/repos/{owner}/{repo}/commits?author={username}`.

### Database Location

SQLite database: `backend/team_monitor.db`
- Auto-created on first run
- Contains `system_prompts` table

### Hot Reload

- **Backend**: `uvicorn --reload` watches for file changes
- **Frontend**: Vite HMR for instant updates
- **Note**: `.env` changes require server restart (cached settings)
