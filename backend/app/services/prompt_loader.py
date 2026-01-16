"""
Prompt Loader - Loads prompts from YAML file at startup and caches in memory.

This module provides prompts for the 2-AI-call architecture:
- router_agent: Decides which tools to call
- response_agent: Formats the final response
"""

from functools import lru_cache
from pathlib import Path

import yaml


# Path to the prompts file
PROMPTS_FILE = Path(__file__).parent.parent / "prompts.yaml"


class PromptNotFoundError(Exception):
    """Raised when a requested prompt is not found."""
    pass


@lru_cache(maxsize=1)
def _load_prompts_from_file() -> dict:
    """
    Load prompts from YAML file (cached).
    
    Returns:
        dict: All prompts from the YAML file
    """
    if not PROMPTS_FILE.exists():
        raise FileNotFoundError(f"Prompts file not found at {PROMPTS_FILE}")
    
    with open(PROMPTS_FILE, "r", encoding="utf-8") as f:
        prompts = yaml.safe_load(f)
    
    return prompts


def load_prompts() -> dict:
    """Get all prompts (cached)."""
    return _load_prompts_from_file()


def get_prompt(category: str, key: str = "system") -> str:
    """
    Get a specific prompt by category and key.
    
    Args:
        category: The prompt category (e.g., "router_agent", "response_agent")
        key: The key within the category (default: "system")
        
    Returns:
        str: The prompt text
    """
    prompts = load_prompts()
    
    if category not in prompts:
        raise PromptNotFoundError(f"Prompt '{category}' not found")
    
    category_prompts = prompts[category]
    
    if key not in category_prompts:
        raise PromptNotFoundError(f"Key '{key}' not found in '{category}'")
    
    return category_prompts[key]


def get_router_agent_prompt() -> str:
    """Get the router agent system prompt."""
    return get_prompt("router_agent", "system")


def get_response_agent_prompt() -> str:
    """Get the response agent system prompt."""
    return get_prompt("response_agent", "system")


def reload_prompts() -> dict:
    """Force reload prompts from file (clears cache)."""
    _load_prompts_from_file.cache_clear()
    return load_prompts()


# Validate prompts on module load
def _validate_prompts():
    """Validate required prompts exist."""
    required = ["router_agent", "response_agent"]
    
    try:
        prompts = load_prompts()
        missing = [cat for cat in required if cat not in prompts]
        if missing:
            print(f"WARNING: Missing prompts: {missing}")
    except FileNotFoundError:
        print(f"WARNING: Prompts file not found at {PROMPTS_FILE}")
    except Exception as e:
        print(f"WARNING: Error loading prompts: {e}")


_validate_prompts()
