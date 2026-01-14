from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.database import init_db
from app.models import HealthResponse

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for startup and shutdown events.
    """
    # === STARTUP ===
    print("🚀 Starting Team Activity Monitor...")
    
    # Initialize database tables
    await init_db()
    print("✅ Database initialized")
    
    # Seed default prompt if needed (we'll add this later)
    from app.seed import seed_default_prompt
    await seed_default_prompt()
    print("✅ Default prompt seeded")
    
    yield  # Application runs here
    
    # === SHUTDOWN ===
    print("👋 Shutting down...")


# Create FastAPI application
app = FastAPI(
    title="Team Activity Monitor",
    description="AI chatbot that integrates with JIRA and GitHub to answer team activity questions",
    version="1.0.0",
    lifespan=lifespan,
)


# Configure CORS
# Origins are loaded from CORS_ORIGINS environment variable (comma-separated)
# Default includes local development servers
cors_origins = [origin.strip() for origin in settings.cors_origins.split(",")]
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =============================================================================
# Health Check Endpoint
# =============================================================================

@app.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check():
    """
    Health check endpoint.
    
    Used by load balancers and monitoring tools to verify the service is running.
    """
    return HealthResponse()


# =============================================================================
# Include Routers
# =============================================================================

from app.routers import chat_router, prompts_router

app.include_router(chat_router, prefix="/chat", tags=["Chat"])
app.include_router(prompts_router, prefix="/prompts", tags=["Prompts"])


# =============================================================================
# Root Endpoint
# =============================================================================

@app.get("/", tags=["Root"])
async def root():
    """Root endpoint with API information."""
    return {
        "name": "Team Activity Monitor API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health"
    }


# =============================================================================
# Debug Endpoints (for testing mock clients)
# =============================================================================

@app.get("/debug/activity/{username}", tags=["Debug"])
async def debug_get_activity(username: str):
    """
    Debug endpoint to test JIRA and GitHub clients.
    
    Try: /debug/activity/john, /debug/activity/sarah, /debug/activity/unknown
    """
    from app.services import get_jira_client, get_github_client
    
    jira = get_jira_client()
    github = get_github_client()
    
    jira_data = await jira.get_user_issues(username)
    github_data = await github.get_user_activity(username)
    
    return {
        "username": username,
        "jira": {
            "issues": [
                {
                    "key": issue.key,
                    "summary": issue.summary,
                    "status": issue.status,
                    "priority": issue.priority,
                }
                for issue in jira_data.issues
            ],
            "total": jira_data.total_count,
            "error": jira_data.error,
        },
        "github": {
            "recent_commits": [
                {
                    "sha": commit.sha,
                    "message": commit.message,
                    "repo": commit.repo,
                }
                for commit in github_data.commits[:3]  # Last 3 commits
            ],
            "open_prs": [
                {
                    "number": pr.number,
                    "title": pr.title,
                    "repo": pr.repo,
                }
                for pr in github_data.pull_requests
                if pr.state == "open"
            ],
            "active_repos": github_data.active_repos,
            "error": github_data.error,
        },
    }


@app.get("/debug/ai/{provider}", tags=["Debug"])
async def debug_test_ai(provider: str, message: str = "Say hello in one sentence"):
    """
    Debug endpoint to test AI providers.
    
    Try: /debug/ai/openai?message=Hello or /debug/ai/claude?message=Hello
    """
    from app.services import get_ai_provider, Message
    
    try:
        ai = get_ai_provider(provider)
        response = await ai.generate(
            messages=[Message(role="user", content=message)],
            system_prompt="You are a helpful assistant. Be concise.",
        )
        return {
            "provider": provider,
            "model": response.model,
            "response": response.content,
            "error": response.error,
        }
    except ValueError as e:
        return {"error": str(e)}


@app.get("/debug/ai-status", tags=["Debug"])
async def debug_ai_status():
    """
    Check which AI providers are configured.
    
    Returns which providers have API keys set.
    """
    from app.config import get_settings
    settings = get_settings()
    
    return {
        "openai": {
            "configured": bool(settings.openai_api_key),
            "key_preview": settings.openai_api_key[:10] + "..." if settings.openai_api_key else None,
        },
        "claude": {
            "configured": bool(settings.anthropic_api_key),
            "key_preview": settings.anthropic_api_key[:10] + "..." if settings.anthropic_api_key else None,
        },
    }


@app.get("/debug/chat", tags=["Debug"])
async def debug_chat(
    query: str = "What is John working on?",
    mode: str = "procedural",
    ai_provider: str = "openai",
):
    """
    Debug endpoint to test the full chat engine.
    
    Examples:
    - /debug/chat?query=What is John working on?&mode=procedural
    - /debug/chat?query=Hello&mode=agent
    - /debug/chat?query=Show me Sarah's activity&mode=agent&ai_provider=claude
    
    Key difference:
    - Procedural: ALWAYS fetches from JIRA and GitHub
    - Agent: AI DECIDES whether to fetch (smarter, more efficient)
    """
    from app.services import generate_response
    
    result = await generate_response(
        query=query,
        mode=mode,
        ai_provider=ai_provider,
    )
    
    return {
        "query": query,
        "mode": result.mode,
        "ai_provider": result.ai_provider,
        "response": result.response,
        "sources_consulted": result.sources_consulted,
        "extracted_username": result.extracted_username,
        "debug_info": result.debug_info,
    }


@app.get("/debug/extract-username", tags=["Debug"])
async def debug_extract_username(query: str):
    """
    Debug the username extraction from queries.
    
    Examples:
    - /debug/extract-username?query=What is John working on?
    - /debug/extract-username?query=Show me Sarah's recent activity
    """
    from app.services import extract_username
    
    return {
        "query": query,
        "extracted_username": extract_username(query),
    }


# =============================================================================
# GitHub API Debug Endpoints
# =============================================================================

@app.get("/debug/github/test-connection", tags=["Debug", "GitHub"])
async def debug_github_test_connection():
    """
    Test GitHub API connection and authentication.
    
    Returns connection status, authenticated user, and rate limit info.
    """
    from app.services import get_github_client
    
    client = get_github_client()
    return await client.test_connection()


@app.get("/debug/github/activity/{username}", tags=["Debug", "GitHub"])
async def debug_github_activity(username: str):
    """
    Fetch real GitHub activity for a user.
    
    Examples:
    - /debug/github/activity/octocat (GitHub's mascot)
    - /debug/github/activity/torvalds (Linus Torvalds)
    - /debug/github/activity/YOUR_USERNAME
    
    Returns:
    - Recent commits from push events
    - Pull requests (open, closed, merged)
    - Active repositories
    """
    from app.services import get_github_client
    
    client = get_github_client()
    activity = await client.get_user_activity(username)
    
    return {
        "username": activity.username,
        "is_real_data": activity.is_real_data,
        "error": activity.error,
        "total_commits": activity.total_commits,
        "total_prs": activity.total_prs,
        "commits": [
            {
                "sha": c.sha,
                "message": c.message,
                "repo": c.repo,
                "date": c.date.isoformat(),
            }
            for c in activity.commits
        ],
        "pull_requests": [
            {
                "number": pr.number,
                "title": pr.title,
                "repo": pr.repo,
                "state": pr.state,
                "url": pr.url,
                "created_at": pr.created_at.isoformat(),
                "updated_at": pr.updated_at.isoformat(),
            }
            for pr in activity.pull_requests
        ],
        "active_repos": activity.active_repos,
    }


@app.get("/debug/github/status", tags=["Debug", "GitHub"])
async def debug_github_status():
    """
    Check GitHub API configuration status.
    
    Returns whether token is configured and connection test result.
    """
    from app.config import get_settings
    from app.services import get_github_client
    
    settings = get_settings()
    client = get_github_client()
    connection_test = await client.test_connection()
    
    return {
        "token_configured": bool(settings.github_token),
        "token_preview": settings.github_token[:10] + "..." if settings.github_token else None,
        "connection": connection_test,
    }


# =============================================================================
# JIRA API Debug Endpoints
# =============================================================================

@app.get("/debug/jira/test-connection", tags=["Debug", "JIRA"])
async def debug_jira_test_connection():
    """
    Test JIRA API connection and authentication.
    
    Returns connection status, authenticated user info.
    """
    from app.services import get_jira_client
    
    client = get_jira_client()
    return await client.test_connection()


@app.get("/debug/jira/issues/{username}", tags=["Debug", "JIRA"])
async def debug_jira_issues(username: str):
    """
    Fetch JIRA issues assigned to a user.
    
    Examples:
    - /debug/jira/issues/john (mock user)
    - /debug/jira/issues/YOUR_DISPLAY_NAME (real user)
    
    Note: JIRA Cloud uses display names, not usernames.
    Try your full name as it appears in JIRA.
    """
    from app.services import get_jira_client
    
    client = get_jira_client()
    activity = await client.get_user_issues(username)
    
    return {
        "username": activity.username,
        "is_real_data": activity.is_real_data,
        "error": activity.error,
        "total_count": activity.total_count,
        "issues": [
            {
                "key": issue.key,
                "summary": issue.summary,
                "status": issue.status,
                "priority": issue.priority,
                "type": issue.issue_type,
                "url": issue.url,
                "updated": issue.updated.isoformat(),
            }
            for issue in activity.issues
        ],
    }


@app.get("/debug/jira/users", tags=["Debug", "JIRA"])
async def debug_jira_users():
    """
    List all JIRA users (for finding valid usernames).
    
    Useful for discovering what names to use in queries.
    """
    from app.services import get_jira_client
    
    client = get_jira_client()
    users = await client.get_all_users()
    
    return {
        "total": len(users),
        "users": users,
    }


@app.get("/debug/jira/status", tags=["Debug", "JIRA"])
async def debug_jira_status():
    """
    Check JIRA API configuration status.
    
    Returns whether credentials are configured and connection test result.
    """
    from app.config import get_settings
    from app.services import get_jira_client
    
    settings = get_settings()
    client = get_jira_client()
    connection_test = await client.test_connection()
    
    return {
        "base_url_configured": bool(settings.jira_base_url),
        "base_url": settings.jira_base_url if settings.jira_base_url else None,
        "email_configured": bool(settings.jira_email),
        "email": settings.jira_email if settings.jira_email else None,
        "token_configured": bool(settings.jira_api_token),
        "token_preview": settings.jira_api_token[:10] + "..." if settings.jira_api_token else None,
        "connection": connection_test,
    }
