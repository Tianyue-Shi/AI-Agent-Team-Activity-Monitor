"""
Services package - External API clients and business logic.

This package contains:
- jira_client: JIRA API integration
- github_client: GitHub API integration
- ai_providers: OpenAI and Claude wrappers
- chat_engine: Procedural and Agentic chat logic
"""

from app.services.jira_client import JiraClient, get_jira_client, JiraUserActivity
from app.services.github_client import GitHubClient, get_github_client, GitHubUserActivity
from app.services.ai_providers import (
    AIProvider,
    OpenAIProvider,
    ClaudeProvider,
    get_ai_provider,
    AIResponse,
    Message,
    ToolCall,
    ToolDefinition,
    ToolParameter,
    AVAILABLE_TOOLS,
)
from app.services.chat_engine import (
    generate_response,
    generate_procedural_response,
    generate_agent_response,
    ChatEngineResponse,
    extract_username,
)

__all__ = [
    # JIRA
    "JiraClient",
    "get_jira_client", 
    "JiraUserActivity",
    # GitHub
    "GitHubClient",
    "get_github_client",
    "GitHubUserActivity",
    # AI Providers
    "AIProvider",
    "OpenAIProvider",
    "ClaudeProvider",
    "get_ai_provider",
    "AIResponse",
    "Message",
    "ToolCall",
    "ToolDefinition",
    "ToolParameter",
    "AVAILABLE_TOOLS",
    # Chat Engine
    "generate_response",
    "generate_procedural_response",
    "generate_agent_response",
    "ChatEngineResponse",
    "extract_username",
]
