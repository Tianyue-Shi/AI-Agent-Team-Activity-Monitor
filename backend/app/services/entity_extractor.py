"""
Entity Extractor - Extracts structured entities from user queries.

This module identifies key entities like usernames, timeframes, projects,
and query focus from natural language queries.
"""

import json
import re
from typing import Optional, Literal

from pydantic import BaseModel

from app.services.ai_providers import get_ai_provider, Message
from app.services.prompt_loader import get_entity_extractor_prompt


class ExtractedEntities(BaseModel):
    """
    Entities extracted from a user query.
    
    All fields are optional - a query might not contain all entity types.
    """
    username: Optional[str] = None
    timeframe: Optional[str] = None  # "today", "this week", "last 7 days", etc.
    project: Optional[str] = None  # Repository or project name
    query_focus: Optional[Literal["status", "count", "details", "summary", "comparison"]] = None


# =============================================================================
# Username Alias Mapping
# =============================================================================
# Maps various ways users might refer to team members
# This should be expanded based on your actual team

USERNAME_ALIASES = {
    # Real user - Justin Shi
    "justin": "justin",
    "justin shi": "justin",
    "shi": "justin",
    "tianyue-shi": "justin",
    "tianyue": "justin",
    # Mock users for demo
    "john": "john",
    "sarah": "sarah", 
    "mike": "mike",
    "lisa": "lisa",
}

# Known usernames (for validation)
KNOWN_USERNAMES = {"justin", "john", "sarah", "mike", "lisa"}


# =============================================================================
# Regex Patterns for Entity Extraction
# =============================================================================

# Patterns to extract usernames from queries
USERNAME_PATTERNS = [
    r"what (?:is|has) (\w+(?:\s+\w+)?)\s+(?:working|doing|been)",
    r"show (?:me\s+)?(\w+(?:\s+\w+)?)'?s?\s+(?:recent\s+|current\s+)?(?:activity|issues|work|tickets|commits|prs)",
    r"(?:activity|issues|work|tickets)\s+(?:for|of)\s+(\w+(?:\s+\w+)?)",
    r"(\w+(?:\s+\w+)?)'?s?\s+(?:jira|github|activity|issues|work|commits|prs)",
    r"(?:for|about|of)\s+(\w+(?:\s+\w+)?)\??$",
    r"^(\w+)\s+(?:has|is|activity|status)",
]

# Patterns to extract timeframes
TIMEFRAME_PATTERNS = [
    (r"today", "today"),
    (r"yesterday", "yesterday"),
    (r"this week", "this week"),
    (r"last week", "last week"),
    (r"this month", "this month"),
    (r"last month", "last month"),
    (r"last (\d+) days?", "last {0} days"),
    (r"past (\d+) days?", "last {0} days"),
    (r"(\d+) days? ago", "{0} days ago"),
    (r"recently", "recent"),
    (r"recent", "recent"),
]

# Query focus indicators
FOCUS_INDICATORS = {
    "count": ["how many", "count", "number of", "total"],
    "status": ["status", "state", "where is", "progress"],
    "details": ["details", "show me", "list", "what are"],
    "summary": ["summary", "overview", "summarize", "brief"],
    "comparison": ["compare", "versus", "vs", "difference", "between"],
}


def _extract_username_regex(query: str) -> Optional[str]:
    """Extract username using regex patterns."""
    query_lower = query.lower()
    
    # First check for known aliases directly in query
    for alias, canonical in USERNAME_ALIASES.items():
        if alias in query_lower:
            return canonical
    
    # Try regex patterns
    for pattern in USERNAME_PATTERNS:
        match = re.search(pattern, query_lower)
        if match:
            potential_name = match.group(1).strip()
            # Filter out common words
            if potential_name not in {"the", "a", "an", "my", "your", "their", "our", "they", "them", "this", "that"}:
                # Check if it matches a known alias
                if potential_name in USERNAME_ALIASES:
                    return USERNAME_ALIASES[potential_name]
                # Check if it's a known username
                if potential_name in KNOWN_USERNAMES:
                    return potential_name
                # Return as-is (might be a new user)
                return potential_name
    
    return None


def _extract_timeframe_regex(query: str) -> Optional[str]:
    """Extract timeframe using regex patterns."""
    query_lower = query.lower()
    
    for pattern, template in TIMEFRAME_PATTERNS:
        match = re.search(pattern, query_lower)
        if match:
            if match.groups():
                return template.format(*match.groups())
            return template
    
    return None


def _extract_query_focus(query: str) -> Optional[str]:
    """Determine what aspect of work the user is asking about."""
    query_lower = query.lower()
    
    for focus, indicators in FOCUS_INDICATORS.items():
        if any(ind in query_lower for ind in indicators):
            return focus
    
    # Default to summary for general activity questions
    if any(word in query_lower for word in ["working on", "doing", "activity", "status"]):
        return "summary"
    
    return None


def _extract_project_regex(query: str) -> Optional[str]:
    """Extract project/repository name from query."""
    query_lower = query.lower()
    
    # Patterns for project extraction
    project_patterns = [
        r"(?:in|on|for)\s+(?:the\s+)?(?:repo(?:sitory)?|project)\s+['\"]?(\w+(?:-\w+)*)['\"]?",
        r"(?:repo(?:sitory)?|project)\s+['\"]?(\w+(?:-\w+)*)['\"]?",
        r"(\w+(?:-\w+)*)\s+(?:repo(?:sitory)?|project)",
    ]
    
    for pattern in project_patterns:
        match = re.search(pattern, query_lower)
        if match:
            return match.group(1)
    
    return None


async def extract_entities(
    query: str,
    ai_provider: str = "openai",
    use_fast_path: bool = True,
) -> ExtractedEntities:
    """
    Extract entities from a user query.
    
    Args:
        query: The user's query text
        ai_provider: Which AI provider to use ("openai" or "claude")
        use_fast_path: If True, try regex extraction first
        
    Returns:
        ExtractedEntities with extracted values (None for unextracted fields)
    """
    # Try fast regex-based extraction first
    if use_fast_path:
        entities = ExtractedEntities(
            username=_extract_username_regex(query),
            timeframe=_extract_timeframe_regex(query),
            project=_extract_project_regex(query),
            query_focus=_extract_query_focus(query),
        )
        
        # If we got a username, that's usually enough
        if entities.username:
            return entities
    
    # Fall back to LLM extraction for better accuracy
    return await _llm_extract(query, ai_provider)


async def _llm_extract(query: str, ai_provider: str) -> ExtractedEntities:
    """
    Use LLM to extract entities from query.
    
    More accurate than regex but slower.
    """
    ai = get_ai_provider(ai_provider)
    system_prompt = get_entity_extractor_prompt()
    
    user_message = f"""Extract entities from this query and respond with a JSON object:

Query: "{query}"

Respond ONLY with a JSON object in this exact format:
{{
    "username": "name or null",
    "timeframe": "timeframe or null",
    "project": "project name or null",
    "query_focus": "status|count|details|summary|comparison or null"
}}

Use null (not "null" string) for any entity you cannot extract."""

    try:
        response = await ai.generate(
            messages=[Message(role="user", content=user_message)],
            system_prompt=system_prompt,
        )
        
        # Parse JSON from response
        content = response.content.strip()
        
        # Handle potential markdown code blocks
        if content.startswith("```"):
            lines = content.split("\n")
            content = "\n".join(lines[1:-1])
        
        result = json.loads(content)
        
        # Normalize username if it matches an alias
        username = result.get("username")
        if username and username.lower() in USERNAME_ALIASES:
            username = USERNAME_ALIASES[username.lower()]
        
        # Validate query_focus
        query_focus = result.get("query_focus")
        valid_focuses = {"status", "count", "details", "summary", "comparison"}
        if query_focus and query_focus not in valid_focuses:
            query_focus = None
        
        return ExtractedEntities(
            username=username,
            timeframe=result.get("timeframe"),
            project=result.get("project"),
            query_focus=query_focus,
        )
        
    except (json.JSONDecodeError, KeyError, TypeError) as e:
        # Fall back to regex extraction
        return ExtractedEntities(
            username=_extract_username_regex(query),
            timeframe=_extract_timeframe_regex(query),
            project=_extract_project_regex(query),
            query_focus=_extract_query_focus(query),
        )
    except Exception as e:
        # Return empty entities on error
        return ExtractedEntities()


def resolve_username_for_platform(username: str, platform: str) -> str:
    """
    Resolve a username to the platform-specific version.
    
    Args:
        username: The extracted username
        platform: "jira" or "github"
        
    Returns:
        Platform-specific username
    """
    # Platform-specific mappings
    PLATFORM_MAPPINGS = {
        "justin": {
            "jira": "Justin Shi",
            "github": "Tianyue-Shi",
        },
        # Add more mappings as needed
    }
    
    username_lower = username.lower() if username else ""
    
    if username_lower in PLATFORM_MAPPINGS:
        return PLATFORM_MAPPINGS[username_lower].get(platform, username)
    
    return username
