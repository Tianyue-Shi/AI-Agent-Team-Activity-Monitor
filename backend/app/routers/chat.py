import json
import uuid
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models import (
    Conversation,
    ConversationMessage,
    ChatRequest,
    ChatResponse,
    ConversationResponse,
    ConversationWithMessagesResponse,
    ConversationListResponse,
    MessageResponse,
)
from app.services.ai_providers import Message
from app.services.intent_classifier import extract_username
from app.services.micro_agents import router_agent, response_agent

router = APIRouter()


# =============================================================================
# Helper Functions
# =============================================================================

async def get_or_create_conversation(
    db: AsyncSession,
    conversation_id: Optional[str] = None,
) -> Conversation:
    """Get existing conversation or create a new one."""
    if conversation_id:
        result = await db.execute(
            select(Conversation).where(Conversation.id == conversation_id)
        )
        conversation = result.scalar_one_or_none()
        if conversation:
            return conversation
    
    # Create new conversation
    new_conversation = Conversation(
        id=str(uuid.uuid4()),
    )
    db.add(new_conversation)
    await db.flush()
    return new_conversation


async def save_message(
    db: AsyncSession,
    conversation_id: str,
    role: str,
    content: str,
    metadata: Optional[dict] = None,
) -> ConversationMessage:
    """Save a message to the conversation."""
    message = ConversationMessage(
        conversation_id=conversation_id,
        role=role,
        content=content,
        metadata_json=json.dumps(metadata) if metadata else None,
    )
    db.add(message)
    await db.flush()
    return message


def generate_conversation_title(query: str) -> str:
    """Generate a title from the first message."""
    title = query[:50].strip()
    if len(query) > 50:
        title += "..."
    return title


# =============================================================================
# POST /chat - Main chat endpoint (2-AI-call pipeline)
# =============================================================================

@router.post("", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Main chat endpoint - answers questions about team activity.
    
    Uses a streamlined 2-AI-call pipeline:
    1. Extract username via regex (instant, no LLM)
    2. Router Agent (AI Call 1): Decides which tools to call, fetches data
    3. Response Agent (AI Call 2): Formats the final response
    
    Request body:
    {
        "query": "What is John working on?",
        "ai_provider": "openai" | "claude",
        "selected_user": {...} (optional),
        "conversation_id": "uuid" (optional, for follow-ups)
    }
    """
    # Step 1: Get or create conversation
    conversation = await get_or_create_conversation(db, request.conversation_id)
    
    if not conversation.title:
        conversation.title = generate_conversation_title(request.query)
    
    # Step 2: Save user message
    await save_message(
        db=db,
        conversation_id=conversation.id,
        role="user",
        content=request.query,
    )
    
    # Step 3: Extract username via regex (instant, no LLM)
    username = extract_username(request.query)
    
    # If a user was selected from dropdown, use that instead
    if request.selected_user:
        username = (
            request.selected_user.jira_display_name or
            request.selected_user.github_username or
            request.selected_user.display_name
        )
    
    # Step 4: AI Call 1 - Router decides and fetches data via tools
    router_result = await router_agent(
        query=request.query,
        username=username,
        ai_provider=request.ai_provider,
    )
    
    # Step 5: AI Call 2 - Response agent formats the output
    response_text = await response_agent(
        query=request.query,
        data=router_result,
        ai_provider=request.ai_provider,
    )
    
    # Step 6: Save assistant response
    response_metadata = {
        "route": router_result.route,
        "username": username,
        "sources": [],
    }
    if router_result.jira_data:
        response_metadata["sources"].append("jira")
    if router_result.github_data:
        response_metadata["sources"].append("github")
    
    await save_message(
        db=db,
        conversation_id=conversation.id,
        role="assistant",
        content=response_text,
        metadata=response_metadata,
    )
    
    # Step 7: Return response
    return ChatResponse(
        response=response_text,
        conversation_id=conversation.id,
        ai_provider=request.ai_provider,
        intent=router_result.route,
        entities={"username": username},
        sources_consulted=response_metadata["sources"],
    )


# =============================================================================
# GET /chat/providers - List available AI providers
# =============================================================================

@router.get("/providers")
async def get_available_providers():
    """Get list of available AI providers."""
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
# GET /chat/team - List available team members
# =============================================================================

@router.get("/team")
async def get_team_members():
    """
    Get list of team members from JIRA, GitHub, and mock data.
    """
    from app.services import get_jira_client, get_github_client
    
    members = []
    seen_ids = set()
    
    # Fetch real users from JIRA
    jira_client = get_jira_client()
    if not jira_client._use_mock:
        try:
            jira_users = await jira_client.get_all_users()
            for user in jira_users:
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
                            "jira_account_id": user.get("account_id"),
                            "jira_display_name": user.get("display_name"),
                            "github_username": None,
                        })
        except Exception as e:
            print(f"Error fetching JIRA users: {e}")
    
    # Fetch real users from GitHub
    github_client = get_github_client()
    if not github_client._use_mock:
        try:
            github_status = await github_client.test_connection()
            github_user = github_status.get("user")
            github_name = github_status.get("name")
            
            if github_status.get("authenticated") and github_user:
                user_id = f"github_{github_user}"
                matched = False
                for member in members:
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
    
    # Add mock users for demonstration
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
                "jira_display_name": mock["display_name"],
                "github_username": mock["username"],
            })
    
    return {
        "members": members,
        "total_real": len([m for m in members if m.get("is_real")]),
        "total_mock": len([m for m in members if not m.get("is_real")]),
    }


# =============================================================================
# Conversation Management Endpoints
# =============================================================================

@router.get("/conversations", response_model=ConversationListResponse)
async def list_conversations(
    limit: int = 20,
    db: AsyncSession = Depends(get_db),
):
    """List all conversations, ordered by most recent."""
    message_count_subquery = (
        select(
            ConversationMessage.conversation_id,
            func.count(ConversationMessage.id).label("message_count")
        )
        .group_by(ConversationMessage.conversation_id)
        .subquery()
    )
    
    result = await db.execute(
        select(
            Conversation,
            func.coalesce(message_count_subquery.c.message_count, 0).label("message_count")
        )
        .outerjoin(message_count_subquery, Conversation.id == message_count_subquery.c.conversation_id)
        .order_by(Conversation.updated_at.desc())
        .limit(limit)
    )
    rows = result.all()
    
    return ConversationListResponse(
        conversations=[
            ConversationResponse(
                id=conv.id,
                title=conv.title,
                created_at=conv.created_at,
                updated_at=conv.updated_at,
                message_count=msg_count,
            )
            for conv, msg_count in rows
        ],
        total=len(rows),
    )


@router.get("/conversations/{conversation_id}", response_model=ConversationWithMessagesResponse)
async def get_conversation(
    conversation_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Get a specific conversation with all its messages."""
    result = await db.execute(
        select(Conversation)
        .where(Conversation.id == conversation_id)
        .options(selectinload(Conversation.messages))
    )
    conversation = result.scalar_one_or_none()
    
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    return ConversationWithMessagesResponse(
        id=conversation.id,
        title=conversation.title,
        created_at=conversation.created_at,
        updated_at=conversation.updated_at,
        messages=[
            MessageResponse(
                id=msg.id,
                role=msg.role,
                content=msg.content,
                created_at=msg.created_at,
                metadata=json.loads(msg.metadata_json) if msg.metadata_json else None,
            )
            for msg in conversation.messages
        ],
    )


@router.delete("/conversations/{conversation_id}")
async def delete_conversation(
    conversation_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Delete a conversation and all its messages."""
    result = await db.execute(
        select(Conversation)
        .where(Conversation.id == conversation_id)
        .options(selectinload(Conversation.messages))
    )
    conversation = result.scalar_one_or_none()
    
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    await db.delete(conversation)
    
    return {"status": "deleted", "conversation_id": conversation_id}


@router.post("/conversations/new")
async def create_new_conversation(
    db: AsyncSession = Depends(get_db),
):
    """Create a new empty conversation."""
    conversation = Conversation(
        id=str(uuid.uuid4()),
    )
    db.add(conversation)
    await db.flush()
    
    return {
        "conversation_id": conversation.id,
        "status": "created",
    }
