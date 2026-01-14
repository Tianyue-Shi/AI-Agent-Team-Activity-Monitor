from datetime import datetime
from typing import Literal, Optional
from pydantic import BaseModel, Field
from sqlalchemy import Boolean, DateTime, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

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
    mode: Literal["procedural", "agent"] = Field(
        default="procedural",
        description="procedural=always fetch, agent=AI decides"
    )
    ai_provider: Literal["openai", "claude"] = Field(
        default="openai",
        description="Which AI provider to use"
    )
    selected_user: Optional[SelectedUser] = Field(
        None,
        description="User selected from dropdown - overrides name extraction from query"
    )


class ChatResponse(BaseModel):
    """Response from /chat endpoint."""
    response: str = Field(..., description="AI-generated answer")
    mode: str = Field(..., description="Mode that was used")
    ai_provider: str = Field(..., description="AI provider that was used")
    sources_consulted: list[str] = Field(
        default_factory=list,
        description="Which data sources were queried (jira, github)"
    )


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
