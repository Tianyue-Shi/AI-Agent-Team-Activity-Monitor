from datetime import datetime
from typing import Literal, Optional, Dict, Any
from pydantic import BaseModel, Field
from sqlalchemy import Boolean, DateTime, Integer, String, Text, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


# =============================================================================
# SQLAlchemy ORM Models (Database Tables)
# =============================================================================

class SystemPrompt(Base):
    """
    Stores system prompts with version history.
    
    Key design: We never delete or update prompts.
    Each change creates a new row with incremented version.
    Only one prompt has is_active=True at a time.
    
    NOTE: This table is kept for backwards compatibility.
    New system uses YAML-based prompts loaded at startup.
    """
    __tablename__ = "system_prompts"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    prompt_text: Mapped[str] = mapped_column(Text, nullable=False)
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    is_active: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, 
        server_default=func.now(),  # Database sets this automatically
        nullable=False
    )
    
    def __repr__(self):
        return f"<SystemPrompt v{self.version} active={self.is_active}>"


class Conversation(Base):
    """
    Stores conversation sessions.
    
    Each conversation has a unique ID and contains multiple messages.
    This enables conversation history and follow-up questions.
    """
    __tablename__ = "conversations"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True)  # UUID
    title: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)  # Auto-generated from first message
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )
    
    # Relationship to messages
    messages: Mapped[list["ConversationMessage"]] = relationship(
        "ConversationMessage",
        back_populates="conversation",
        order_by="ConversationMessage.created_at",
        cascade="all, delete-orphan",
    )
    
    def __repr__(self):
        return f"<Conversation {self.id[:8]}... messages={len(self.messages) if self.messages else 0}>"


class ConversationMessage(Base):
    """
    Stores individual messages within a conversation.
    
    Each message has a role (user or assistant) and content.
    Metadata stores additional info like intent, sources, etc.
    """
    __tablename__ = "conversation_messages"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    conversation_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("conversations.id", ondelete="CASCADE"),
        nullable=False
    )
    role: Mapped[str] = mapped_column(String(20), nullable=False)  # "user" or "assistant"
    content: Mapped[str] = mapped_column(Text, nullable=False)
    
    # Store metadata as JSON string (intent, sources, entities, etc.)
    metadata_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        nullable=False
    )
    
    # Relationship back to conversation
    conversation: Mapped["Conversation"] = relationship(
        "Conversation",
        back_populates="messages"
    )
    
    def __repr__(self):
        return f"<Message {self.role}: {self.content[:30]}...>"


# =============================================================================
# Pydantic Schemas (API Request/Response Validation)
# =============================================================================

# --- Chat Schemas ---

class SelectedUser(BaseModel):
    """User selected from the dropdown - provides platform-specific identifiers."""
    id: str = Field(..., description="Unique user ID (e.g., 'jira_123', 'github_user', 'mock_john')")
    display_name: str = Field(..., description="User's display name")
    source: Literal["jira", "github", "mock"] = Field(..., description="Where this user came from")
    jira_display_name: Optional[str] = Field(None, description="Name to use for JIRA queries")
    github_username: Optional[str] = Field(None, description="GitHub username for API queries")


class ChatRequest(BaseModel):
    """Request body for /chat endpoint."""
    query: str = Field(..., min_length=1, description="User's question")
    ai_provider: Literal["openai", "claude"] = Field(
        default="openai",
        description="Which AI provider to use"
    )
    selected_user: Optional[SelectedUser] = Field(
        None,
        description="User selected from dropdown - overrides name extraction from query"
    )
    conversation_id: Optional[str] = Field(
        None,
        description="Conversation ID for continuing a conversation. If not provided, starts new conversation."
    )


class ChatResponse(BaseModel):
    """Response from /chat endpoint."""
    response: str = Field(..., description="AI-generated answer (markdown formatted)")
    conversation_id: str = Field(..., description="Conversation ID for follow-up messages")
    ai_provider: str = Field(..., description="AI provider that was used")
    intent: str = Field(..., description="Classified intent of the query")
    entities: Dict[str, Any] = Field(
        default_factory=dict,
        description="Extracted entities from the query"
    )
    sources_consulted: list[str] = Field(
        default_factory=list,
        description="Which data sources were queried (jira, github)"
    )


# --- Conversation Schemas ---

class MessageResponse(BaseModel):
    """A single message in a conversation."""
    id: int
    role: str
    content: str
    created_at: datetime
    metadata: Optional[Dict[str, Any]] = None
    
    model_config = {"from_attributes": True}


class ConversationResponse(BaseModel):
    """Response containing conversation details."""
    id: str
    title: Optional[str]
    created_at: datetime
    updated_at: datetime
    message_count: int = 0
    
    model_config = {"from_attributes": True}


class ConversationWithMessagesResponse(BaseModel):
    """Full conversation with all messages."""
    id: str
    title: Optional[str]
    created_at: datetime
    updated_at: datetime
    messages: list[MessageResponse] = []
    
    model_config = {"from_attributes": True}


class ConversationListResponse(BaseModel):
    """List of conversations."""
    conversations: list[ConversationResponse]
    total: int


# --- Prompt Schemas ---

class PromptCreate(BaseModel):
    """Request to create a new prompt version."""
    prompt_text: str = Field(..., min_length=10, description="The new prompt text")


class PromptResponse(BaseModel):
    """Response containing prompt details."""
    id: int
    prompt_text: str
    version: int
    is_active: bool
    created_at: datetime
    
    model_config = {"from_attributes": True}  # Enable ORM mode


class PromptHistoryResponse(BaseModel):
    """List of all prompt versions."""
    prompts: list[PromptResponse]
    total_versions: int


# --- Health Check ---

class HealthResponse(BaseModel):
    """Health check response."""
    status: str = "healthy"
    timestamp: datetime = Field(default_factory=datetime.now)
