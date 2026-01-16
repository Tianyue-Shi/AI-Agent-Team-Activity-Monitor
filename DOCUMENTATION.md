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
- **2-AI-Call Pipeline**: Router Agent (with tool calling) + Response Agent (formatting)
- **Multi-Provider AI Support**: OpenAI GPT and Anthropic Claude
- **Real API Integration**: JIRA Cloud and GitHub REST APIs
- **Conversation History**: SQLite-backed chat sessions with follow-up support
- **Mock Data Fallback**: Demo users for testing without real API keys
- **User Selection Dropdown**: Unified list of real and mock team members

---

## Architecture

![Team Activity Monitor Architecture](./Team%20Activity%20Monitor%20Architecture-Page-2.jpg)

### Pipeline Flow

1. **Username Extraction** (regex, instant): Extract team member name from query
2. **AI Call 1 - Router Agent**: Uses function calling to decide which tools to invoke (JIRA, GitHub, both, or none for greetings)
3. **AI Call 2 - Response Agent**: Formats the fetched data into detailed, well-structured markdown

See [ARCHITECTURE.md](./ARCHITECTURE.md) for detailed trade-offs and micro-agent pattern discussion.

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
| **openai** | 1.12+ | OpenAI SDK (with function calling) |
| **anthropic** | 0.18+ | Anthropic Claude SDK (with tool use) |
| **PyYAML** | 6.0+ | YAML prompt loading |

### Frontend
| Technology | Version | Purpose |
|------------|---------|---------|
| **React** | 19.2+ | UI library |
| **Vite** | 7.2+ | Build tool & dev server |
| **Tailwind CSS** | 4.1+ | Utility-first CSS |
| **Lucide React** | 0.562+ | Icon library |
| **React Markdown** | 9.0+ | Markdown rendering |

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
- OpenAI API key (required)
- JIRA Cloud account (optional)
- GitHub account (optional)
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
# AI Providers (at least OpenAI required)
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...

# JIRA Configuration (optional - mock data available)
JIRA_BASE_URL=https://your-domain.atlassian.net
JIRA_EMAIL=your-email@example.com
JIRA_API_TOKEN=your-api-token

# GitHub Configuration (optional - mock data available)
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
│   ├── main.py              # FastAPI app, lifespan, CORS, debug endpoints
│   ├── config.py            # Pydantic Settings (env vars)
│   ├── database.py          # SQLAlchemy async engine, session factory
│   ├── models.py            # ORM models + Pydantic schemas
│   ├── prompts.yaml         # System prompts for agents (YAML)
│   ├── routers/
│   │   ├── __init__.py
│   │   ├── chat.py          # /chat endpoints (2-AI-call pipeline)
│   │   └── prompts.py       # /prompts endpoints (legacy)
│   └── services/
│       ├── __init__.py
│       ├── ai_providers.py      # OpenAI/Claude abstraction with tool support
│       ├── micro_agents.py      # Router Agent + Response Agent + tool functions
│       ├── intent_classifier.py # Username extraction (regex only)
│       ├── prompt_loader.py     # YAML prompt loading with caching
│       ├── github_client.py     # GitHub API client
│       └── jira_client.py       # JIRA API client
├── requirements.txt
├── team_monitor.db          # SQLite database (auto-created)
└── .env                     # Environment variables
```

### Key Components

#### 1. Micro Agents (`micro_agents.py`)

The core AI pipeline with two agents and tool functions:

```python
# Tool definitions for Router Agent
ROUTER_TOOLS = [
    ToolDefinition(
        name="jira_agent",
        description="Fetch JIRA tickets for a user",
        parameters={"username": "string"}
    ),
    ToolDefinition(
        name="github_agent", 
        description="Fetch GitHub activity for a user",
        parameters={"username": "string"}
    ),
]

# AI Call 1: Router Agent
async def router_agent(query, username, ai_provider) -> RouterResult:
    """Decides which tools to call based on query intent."""
    response = await ai.generate_with_tools(
        messages=[{"role": "user", "content": query}],
        tools=ROUTER_TOOLS,
        system_prompt=get_router_agent_prompt()
    )
    # Execute tool calls and return data
    return RouterResult(route=route, jira_data=..., github_data=...)

# AI Call 2: Response Agent  
async def response_agent(query, data, ai_provider) -> str:
    """Formats fetched data into detailed markdown response."""
    context = _format_jira_context(data.jira_data) + _format_github_context(data.github_data)
    return await ai.generate(
        messages=[{"role": "user", "content": f"{context}\n\nQuery: {query}"}],
        system_prompt=get_response_agent_prompt()
    )
```

#### 2. Intent Classifier (`intent_classifier.py`)

Lightweight regex-based username extraction:

```python
USERNAME_PATTERNS = [
    r"(?:what(?:'s| is| has)?|show|tell|get|find|check)\s+(\w+)(?:'s)?",
    r"(?:working on|doing|up to|status)\s+(?:for\s+)?(\w+)",
    r"(\w+)(?:'s)?\s+(?:tickets?|issues?|prs?|commits?|activity)",
]

KNOWN_USERNAMES = {"john", "sarah", "mike", "lisa", "justin"}

def extract_username(query: str) -> Optional[str]:
    """Extract username from query using regex patterns."""
    for pattern in USERNAME_PATTERNS:
        match = re.search(pattern, query, re.IGNORECASE)
        if match and match.group(1).lower() in KNOWN_USERNAMES:
            return match.group(1).lower()
    return None
```

#### 3. AI Providers (`ai_providers.py`)

**Strategy Pattern** with tool/function calling support:

```python
class AIProvider(ABC):
    @abstractmethod
    async def generate(messages, system_prompt) -> AIResponse
    
    @abstractmethod
    async def generate_with_tools(messages, tools, system_prompt) -> AIResponse

class OpenAIProvider(AIProvider):
    async def generate_with_tools(self, messages, tools, system_prompt):
        # Convert tools to OpenAI function format
        functions = [tool.to_openai_function() for tool in tools]
        response = await self.client.chat.completions.create(
            model="gpt-4o",
            messages=messages,
            functions=functions,
            function_call="auto"
        )
        return AIResponse(content=..., tool_calls=...)

class ClaudeProvider(AIProvider):
    async def generate_with_tools(self, messages, tools, system_prompt):
        # Convert tools to Claude tool format
        claude_tools = [tool.to_claude_tool() for tool in tools]
        response = await self.client.messages.create(
            model="claude-sonnet-4-20250514",
            messages=messages,
            tools=claude_tools
        )
        return AIResponse(content=..., tool_calls=...)
```

#### 4. API Clients (`jira_client.py`, `github_client.py`)

**Repository Pattern** with automatic mock fallback for known mock users:

```python
class JiraClient:
    async def get_user_issues(self, username: str) -> JiraUserActivity:
        # Force mock for known mock users
        if username.lower() in MOCK_JIRA_DATA:
            return self._get_mock_issues(username)
        
        # Use real API if configured
        if not self._use_mock:
            return await self._get_real_issues(username)
        
        return self._get_mock_issues(username)
```

#### 5. Prompt Loader (`prompt_loader.py`)

YAML-based prompts with caching:

```python
@lru_cache(maxsize=1)
def _load_prompts() -> dict:
    """Load prompts from YAML file (cached)."""
    yaml_path = Path(__file__).parent.parent / "prompts.yaml"
    with open(yaml_path) as f:
        return yaml.safe_load(f)

def get_router_agent_prompt() -> str:
    return _load_prompts()["router_agent"]

def get_response_agent_prompt() -> str:
    return _load_prompts()["response_agent"]
```

---

## Frontend Deep Dive

### Directory Structure

```
frontend/
├── src/
│   ├── main.jsx          # React entry point
│   ├── App.jsx           # Root component with routing
│   ├── index.css         # Tailwind imports
│   ├── api/
│   │   └── client.js     # API client (fetch wrapper)
│   └── components/
│       ├── ChatInterface.jsx   # Main chat UI with history
│       ├── MessageBubble.jsx   # Message display with markdown
│       └── AdminPanel.jsx      # Legacy prompt management
├── index.html
├── package.json
├── vite.config.js
├── tailwind.config.js
└── postcss.config.js
```

### Key Components

#### ChatInterface.jsx
- **State Management**: `useState` for messages, conversations, provider, team members
- **Conversation History**: Sidebar with past conversations, auto-load on selection
- **User Selection**: Dropdown with real JIRA/GitHub users + mock users
- **Provider Toggle**: OpenAI vs Claude
- **Auto-scroll**: `useRef` + `scrollIntoView`
- **Markdown Support**: Full markdown rendering via `react-markdown`

#### MessageBubble.jsx
- **Markdown Rendering**: Tables, code blocks, lists, bold/italic
- **Metadata Display**: Source badges (JIRA, GitHub), AI provider
- **Copy Button**: Copy response to clipboard

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

export async function sendChatMessage(query, aiProvider, selectedUser, conversationId) {
  return fetchAPI('/chat', {
    method: 'POST',
    body: JSON.stringify({ 
      query, 
      ai_provider: aiProvider, 
      selected_user: selectedUser,
      conversation_id: conversationId 
    }),
  });
}
```

---

## API Reference

### Chat Endpoints

#### `POST /chat`
Main chat endpoint - answers team activity questions using 2-AI-call pipeline.

**Request:**
```json
{
  "query": "What is John working on?",
  "ai_provider": "openai",
  "selected_user": {
    "id": "mock_john",
    "display_name": "John",
    "source": "mock",
    "jira_display_name": "John",
    "github_username": "john"
  },
  "conversation_id": "uuid-string"
}
```

**Response:**
```json
{
  "response": "John is working on...",
  "ai_provider": "openai",
  "sources_consulted": ["jira", "github"],
  "conversation_id": "uuid-string",
  "metadata": {
    "route": "both",
    "username": "john"
  }
}
```

#### `GET /chat/conversations`
Returns list of past conversations.

**Response:**
```json
{
  "conversations": [
    {
      "id": "uuid",
      "title": "John's activity",
      "created_at": "2025-01-15T10:00:00Z",
      "message_count": 5
    }
  ]
}
```

#### `GET /chat/conversations/{id}`
Returns a specific conversation with messages.

#### `POST /chat/conversations/new`
Creates a new conversation.

#### `DELETE /chat/conversations/{id}`
Deletes a conversation.

#### `GET /chat/providers`
Returns available AI providers with configuration status.

#### `GET /chat/team`
Returns unified list of real + mock team members.

### Debug Endpoints

| Endpoint | Purpose |
|----------|---------|
| `GET /debug/chat?query=...` | Test chat pipeline directly |
| `GET /debug/activity/{username}` | Test JIRA + GitHub fetch |
| `GET /debug/jira/status` | JIRA connection status |
| `GET /debug/github/status` | GitHub connection status |
| `GET /debug/ai-status` | AI provider configuration |

---

## Data Flow

### Chat Request Flow (2-AI-Call Pipeline)

```
1. Frontend sends POST /chat
   │
2. FastAPI validates request (Pydantic)
   │
3. Get or create conversation (SQLite)
   │
4. Save user message to database
   │
5. Extract username:
   │  ├─ selected_user provided? → Use platform-specific identifiers
   │  └─ No selection? → Extract from query via regex
   │
6. AI CALL 1 - Router Agent:
   │  ├─ Receives query + username context
   │  ├─ Decides: call jira_agent? github_agent? both? neither?
   │  ├─ Executes tool functions if needed
   │  └─ Returns: RouterResult { route, jira_data, github_data }
   │
7. AI CALL 2 - Response Agent:
   │  ├─ Receives query + fetched data context
   │  ├─ Formats data into detailed markdown
   │  └─ Returns: formatted response string
   │
8. Save assistant message to database
   │
9. Return ChatResponse to frontend
```

### Conversation History Flow

```
1. User clicks conversation in History panel
   │
2. Frontend calls GET /chat/conversations/{id}
   │
3. Backend fetches conversation + messages from SQLite
   │
4. Frontend displays last N messages in chat area
   │
5. User sends new message → attached to same conversation_id
```

---

## Design Patterns & Tradeoffs

### Architecture Trade-offs

| Approach | Pros | Cons |
|----------|------|------|
| **Full micro-agents (4+)** | Better separation of concerns, lower cost per call, highly specialized | More development time, complex orchestration |
| **2-Agent (current)** | Faster to build, easier to debug, demonstrates core concepts | Larger prompts, less specialized |

**Why 2 Agents?**
1. **Demonstrates core concepts**: Tool calling, agent orchestration, data aggregation
2. **Practical for scope**: Balances sophistication with implementation time
3. **Extensible**: Can be expanded by splitting Router Agent into Intent + Orchestrator

### 1. Tool Calling Pattern

```python
# Router Agent uses AI function calling
ROUTER_TOOLS = [
    ToolDefinition(name="jira_agent", ...),
    ToolDefinition(name="github_agent", ...),
]

# AI decides which tools to call based on query
response = await ai.generate_with_tools(messages, tools=ROUTER_TOOLS)
for tool_call in response.tool_calls:
    result = await execute_tool(tool_call)
```

**Benefit**: AI intelligently routes queries to appropriate data sources
**Tradeoff**: Requires AI provider with function calling support

### 2. Strategy Pattern (AI Providers)

```python
class AIProvider(ABC):
    @abstractmethod
    async def generate(...) -> AIResponse
    @abstractmethod
    async def generate_with_tools(...) -> AIResponse

# Factory creates appropriate provider
def get_ai_provider(name: str) -> AIProvider:
    if name == "openai": return OpenAIProvider(...)
    if name == "claude": return ClaudeProvider(...)
```

**Benefit**: Easy to add new providers (Gemini, Llama, etc.)

### 3. Repository Pattern (API Clients)

```python
class JiraClient:
    async def get_user_issues(username) -> JiraUserActivity
```

**Benefit**: Swap between mock/real without changing business logic

### 4. YAML Configuration (Prompts)

```yaml
# prompts.yaml
router_agent: |
  You are a routing agent...
  
response_agent: |
  You are a response formatting agent...
```

**Benefit**: Easy to edit prompts without code changes, loaded once at startup
**Tradeoff**: Requires server restart for prompt changes

### 5. Singleton Pattern (Settings)

```python
@lru_cache()
def get_settings() -> Settings:
    return Settings()
```

**Benefit**: Single configuration instance, env vars loaded once
**Tradeoff**: Settings are immutable during runtime

---

## Performance Optimizations

### 1. 2-Call Pipeline
- Previous approaches required 3-4 AI calls
- Current: exactly 2 AI calls for data queries, 1 for greetings
- **Impact**: ~50% reduction in response time

### 2. Regex-Based Username Extraction
- No AI call needed for username extraction
- Pattern matching is instant (<1ms)
- **Impact**: Saves one AI call latency

### 3. Async Everything
- **FastAPI** async endpoints
- **aiosqlite** async database
- **httpx** async HTTP client
- **openai/anthropic** async SDK
- **Impact**: Non-blocking I/O, better concurrency

### 4. Cached Prompt Loading

```python
@lru_cache(maxsize=1)
def _load_prompts() -> dict:
    """Load prompts once from YAML file."""
```

**Impact**: No file I/O on each request

### 5. Lazy Client Initialization

```python
def _get_client(self):
    if self._client is None:
        self._client = httpx.AsyncClient(...)
    return self._client
```

**Impact**: Resources created only when needed

### 6. Parallel Tool Execution (Potential)

When Router Agent requests both tools:
```python
jira_data, github_data = await asyncio.gather(
    jira_agent(username),
    github_agent(username),
)
```

---

## Security Considerations

### 1. Environment Variables
- Sensitive keys in `.env` (gitignored)
- Never commit credentials

### 2. CORS Configuration
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
)
```

### 3. Input Validation
- **Pydantic** models validate all requests
- `Field(min_length=1)` prevents empty queries

### 4. API Token Security
- JIRA: Basic Auth (email:token base64)
- GitHub: Bearer token
- AI: API keys in headers

### 5. SQL Injection Prevention
- **SQLAlchemy ORM** parameterized queries
- No raw SQL strings

---

## Good to Know

### Username Resolution

Different platforms use different identifiers:
```python
def get_platform_username(username: str, platform: str) -> str:
    """Resolve username for specific platform."""
    if username.lower() in USERNAME_ALIASES:
        return USERNAME_ALIASES[username.lower()].get(platform, username)
    return username
```

### Database Location

SQLite database: `backend/team_monitor.db`
- Auto-created on first run
- Contains: `conversations`, `messages` tables
