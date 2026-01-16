"""
Services package - External API clients and AI agents.

This package implements a 2-AI-call architecture:
- Router Agent (AI Call 1): Decides and fetches data via tool calling
- Response Agent (AI Call 2): Formats the final response

Modules:
- jira_client: JIRA API integration
- github_client: GitHub API integration
- ai_providers: OpenAI and Claude wrappers
- intent_classifier: Username extraction (regex-based)
- micro_agents: Router and Response agents
- prompt_loader: YAML prompt management
"""

# API Clients
from app.services.jira_client import JiraClient, get_jira_client, JiraUserActivity
from app.services.github_client import GitHubClient, get_github_client, GitHubUserActivity

# AI Providers
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
)

# Username Extraction (regex-based, no LLM)
from app.services.intent_classifier import (
    extract_username,
    is_known_user,
    get_platform_username,
    USERNAME_ALIASES,
    KNOWN_USERNAMES,
)

# Micro Agents (2-AI-call architecture)
from app.services.micro_agents import (
    router_agent,
    response_agent,
    jira_agent,
    github_agent,
    RouterResult,
    ROUTER_TOOLS,
)

# Prompt Loader
from app.services.prompt_loader import (
    load_prompts,
    get_prompt,
    get_router_agent_prompt,
    get_response_agent_prompt,
    reload_prompts,
)

__all__ = [
    # JIRA Client
    "JiraClient",
    "get_jira_client",
    "JiraUserActivity",
    # GitHub Client
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
    # Username Extraction
    "extract_username",
    "is_known_user",
    "get_platform_username",
    "USERNAME_ALIASES",
    "KNOWN_USERNAMES",
    # Micro Agents
    "router_agent",
    "response_agent",
    "jira_agent",
    "github_agent",
    "RouterResult",
    "ROUTER_TOOLS",
    # Prompt Loader
    "load_prompts",
    "get_prompt",
    "get_router_agent_prompt",
    "get_response_agent_prompt",
    "reload_prompts",
]
