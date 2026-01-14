"""
Chat Router - Main chat endpoint for the Team Activity Monitor.
"""

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import SystemPrompt, ChatRequest, ChatResponse
from app.services import generate_response

router = APIRouter()


# =============================================================================
# POST /chat - Main chat endpoint
# =============================================================================

@router.post("", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Main chat endpoint - answers questions about team activity.
    
    Request body:
    {
        "query": "What is John working on?",
        "mode": "procedural" | "agent",
        "ai_provider": "openai" | "claude"
    }
    
    Mode differences:
    - procedural: ALWAYS fetches from JIRA and GitHub, then summarizes
    - agent: AI DECIDES whether to fetch using function calling
    
    The active system prompt is fetched from the database, allowing
    runtime configuration without code changes.
    """
    # Get the active system prompt from database
    result = await db.execute(
        select(SystemPrompt).where(SystemPrompt.is_active == True)
    )
    active_prompt = result.scalar_one_or_none()
    
    system_prompt = ""
    if active_prompt:
        system_prompt = active_prompt.prompt_text
    
    # Generate response using the chat engine
    # If a user is selected from dropdown, pass their platform-specific identifiers
    engine_response = await generate_response(
        query=request.query,
        mode=request.mode,
        ai_provider=request.ai_provider,
        system_prompt=system_prompt,
        selected_user=request.selected_user,
    )
    
    return ChatResponse(
        response=engine_response.response,
        mode=engine_response.mode,
        ai_provider=engine_response.ai_provider,
        sources_consulted=engine_response.sources_consulted,
    )


# =============================================================================
# GET /chat/modes - List available modes (for frontend)
# =============================================================================

@router.get("/modes")
async def get_available_modes():
    """
    Get list of available chat modes.
    
    Useful for frontend to dynamically show mode options.
    """
    return {
        "modes": [
            {
                "id": "procedural",
                "name": "Standard",
                "description": "Always fetches data from JIRA and GitHub. Reliable but slower.",
            },
            {
                "id": "agent",
                "name": "Smart Agent",
                "description": "AI decides when to fetch data. Efficient but less predictable.",
            },
        ],
        "default": "procedural",
    }


# =============================================================================
# GET /chat/providers - List available AI providers
# =============================================================================

@router.get("/providers")
async def get_available_providers():
    """
    Get list of available AI providers.
    
    Also indicates which providers are configured (have API keys).
    """
    from app.config import get_settings
    settings = get_settings()
    
    return {
        "providers": [
            {
                "id": "openai",
                "name": "OpenAI GPT",
                "configured": bool(settings.openai_api_key),
                "models": ["gpt-5-nano"],
            },
            {
                "id": "claude",
                "name": "Claude",
                "configured": bool(settings.anthropic_api_key),
                "models": ["claude-haiku-4-5"],
            },
        ],
        "default": "openai",
    }


# =============================================================================
# GET /chat/team - List available team members (real + mock)
# =============================================================================

@router.get("/team")
async def get_team_members():
    """
    Get list of team members from JIRA, GitHub, and mock data.
    
    Returns a unified list of users that can be selected in the frontend dropdown.
    Each user has platform-specific identifiers for accurate API queries.
    """
    from app.services import get_jira_client, get_github_client
    
    members = []
    seen_ids = set()  # Avoid duplicates
    
    # ==========================================================================
    # Fetch real users from JIRA
    # ==========================================================================
    jira_client = get_jira_client()
    if not jira_client._use_mock:
        try:
            jira_users = await jira_client.get_all_users()
            for user in jira_users:
                # Only include active human users (skip bots/apps)
                if user.get("active") and user.get("email"):
                    user_id = f"jira_{user.get('account_id', '')}"
                    if user_id not in seen_ids:
                        seen_ids.add(user_id)
                        members.append({
                            "id": user_id,
                            "display_name": user.get("display_name", "Unknown"),
                            "email": user.get("email"),
                            "source": "jira",
                            "is_real": True,
                            # Platform-specific identifiers for API queries
                            "jira_account_id": user.get("account_id"),
                            "jira_display_name": user.get("display_name"),
                            "github_username": None,  # Will be filled if matched
                        })
        except Exception as e:
            print(f"Error fetching JIRA users: {e}")
    
    # ==========================================================================
    # Fetch real users from GitHub (authenticated user's info)
    # ==========================================================================
    github_client = get_github_client()
    if not github_client._use_mock:
        try:
            github_status = await github_client.test_connection()
            github_user = github_status.get("user")
            github_name = github_status.get("name")
            
            if github_status.get("authenticated") and github_user:
                user_id = f"github_{github_user}"
                # Try to match with existing JIRA user by name
                matched = False
                for member in members:
                    # Check if JIRA display name is contained in GitHub name or vice versa
                    jira_name = member["display_name"].lower()
                    gh_name = (github_name or "").lower()
                    if gh_name and (jira_name in gh_name or gh_name in jira_name or any(
                        word in gh_name for word in jira_name.split()
                    )):
                        member["github_username"] = github_user
                        matched = True
                        break
                
                if not matched and user_id not in seen_ids:
                    seen_ids.add(user_id)
                    members.append({
                        "id": user_id,
                        "display_name": github_name or github_user,
                        "email": None,
                        "source": "github",
                        "is_real": True,
                        "jira_account_id": None,
                        "jira_display_name": github_name or github_user,
                        "github_username": github_user,
                    })
        except Exception as e:
            print(f"Error fetching GitHub user: {e}")
    
    # ==========================================================================
    # Add mock users for demonstration
    # ==========================================================================
    mock_users = [
        {"username": "john", "display_name": "John", "role": "Backend Developer"},
        {"username": "sarah", "display_name": "Sarah", "role": "Frontend Developer"},
        {"username": "mike", "display_name": "Mike", "role": "DevOps Engineer"},
        {"username": "lisa", "display_name": "Lisa", "role": "Full Stack Developer"},
    ]
    
    for mock in mock_users:
        user_id = f"mock_{mock['username']}"
        if user_id not in seen_ids:
            seen_ids.add(user_id)
            members.append({
                "id": user_id,
                "display_name": mock["display_name"],
                "email": None,
                "source": "mock",
                "is_real": False,
                "role": mock.get("role"),
                "jira_account_id": None,
                "jira_display_name": mock["display_name"],  # Mock data uses display name
                "github_username": mock["username"],  # Mock data uses username
            })
    
    return {
        "members": members,
        "total_real": len([m for m in members if m.get("is_real")]),
        "total_mock": len([m for m in members if not m.get("is_real")]),
    }
