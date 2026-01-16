"""
Username Extractor - Extracts usernames from queries using regex.

This module provides fast, regex-based username extraction.
No LLM calls - the AI router agent handles intent classification.
"""

import re
from typing import Optional


# =============================================================================
# Username Configuration
# =============================================================================

# Maps various ways users might refer to team members to canonical names
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

# Set of known usernames for validation
KNOWN_USERNAMES = {"justin", "john", "sarah", "mike", "lisa"}

# Regex patterns to extract usernames from natural language queries
USERNAME_PATTERNS = [
    r"what (?:is|has) (\w+(?:\s+\w+)?)\s+(?:working|doing|been)",
    r"show (?:me\s+)?(\w+(?:\s+\w+)?)'?s?\s+(?:recent\s+|current\s+)?(?:activity|issues|work|tickets|commits|prs)",
    r"(?:activity|issues|work|tickets)\s+(?:for|of)\s+(\w+(?:\s+\w+)?)",
    r"(\w+(?:\s+\w+)?)'?s?\s+(?:jira|github|activity|issues|work|commits|prs)",
    r"(?:for|about|of)\s+(\w+(?:\s+\w+)?)\??$",
    r"^(\w+)\s+(?:has|is|activity|status)",
]

# Words to filter out (not usernames)
FILTER_WORDS = {"the", "a", "an", "my", "your", "their", "our", "they", "them", "this", "that"}


# =============================================================================
# Username Extraction
# =============================================================================

def extract_username(query: str) -> Optional[str]:
    """
    Extract username from a query using regex patterns.
    
    This is a fast, no-LLM extraction that runs instantly.
    Returns the canonical username if found, None otherwise.
    
    Args:
        query: The user's query text
        
    Returns:
        Canonical username string or None
        
    Examples:
        >>> extract_username("What is John working on?")
        'john'
        >>> extract_username("Show me Justin's commits")
        'justin'
        >>> extract_username("Hello!")
        None
    """
    query_lower = query.lower()
    
    # First, check for known aliases directly in query
    for alias, canonical in USERNAME_ALIASES.items():
        if alias in query_lower:
            return canonical
    
    # Try regex patterns
    for pattern in USERNAME_PATTERNS:
        match = re.search(pattern, query_lower)
        if match:
            name = match.group(1).strip()
            # Filter out common words
            if name not in FILTER_WORDS:
                # Check if it matches a known alias
                if name in USERNAME_ALIASES:
                    return USERNAME_ALIASES[name]
                # Check if it's a known username
                if name in KNOWN_USERNAMES:
                    return name
                # Return as-is (might be a new user)
                return name
    
    return None


def is_known_user(username: str) -> bool:
    """Check if a username is in our known users list."""
    if not username:
        return False
    return username.lower() in KNOWN_USERNAMES


def get_platform_username(username: str, platform: str) -> str:
    """
    Get the platform-specific username for a user.
    
    Args:
        username: Canonical username
        platform: 'jira' or 'github'
        
    Returns:
        Platform-specific username
    """
    # Platform-specific mappings
    platform_map = {
        "justin": {
            "jira": "Justin Shi",
            "github": "Tianyue-Shi",
        }
    }
    
    if username in platform_map and platform in platform_map[username]:
        return platform_map[username][platform]
    
    # Default: return as-is (works for mock users)
    return username
