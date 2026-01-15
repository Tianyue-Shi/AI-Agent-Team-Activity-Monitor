"""
Prompt Loader - Loads prompts from YAML file at startup and caches in memory.

This replaces the database-based prompt storage for better performance.
Prompts are loaded once when the module is imported and cached using lru_cache.
"""

import os
from functools import lru_cache
from pathlib import Path
from typing import Optional

import yaml


# Path to the prompts file (relative to the app directory)
PROMPTS_FILE = Path(__file__).parent.parent / "prompts.yaml"


class PromptNotFoundError(Exception):
    """Raised when a requested prompt is not found."""
    pass


@lru_cache(maxsize=1)
def _load_prompts_from_file() -> dict:
    """
    Load prompts from YAML file.
    
    This is cached with lru_cache to ensure the file is only read once.
    The cache persists for the lifetime of the application.
    
    Returns:
        dict: All prompts loaded from the YAML file
        
    Raises:
        FileNotFoundError: If prompts.yaml doesn't exist
        yaml.YAMLError: If the YAML is invalid
    """
    if not PROMPTS_FILE.exists():
        raise FileNotFoundError(
            f"Prompts file not found at {PROMPTS_FILE}. "
            "Please ensure prompts.yaml exists in the app directory."
        )
    
    with open(PROMPTS_FILE, "r", encoding="utf-8") as f:
        prompts = yaml.safe_load(f)
    
    return prompts


def load_prompts() -> dict:
    """
    Get all prompts.
    
    This is the main entry point for accessing prompts.
    Returns the cached prompts dictionary.
    
    Returns:
        dict: All prompts
    """
    return _load_prompts_from_file()


def get_prompt(category: str, key: str = "system") -> str:
    """
    Get a specific prompt by category and key.
    
    Args:
        category: The prompt category (e.g., "classifier", "jira_agent")
        key: The key within the category (default: "system")
        
    Returns:
        str: The prompt text
        
    Raises:
        PromptNotFoundError: If the category or key doesn't exist
    """
    prompts = load_prompts()
    
    if category not in prompts:
        raise PromptNotFoundError(
            f"Prompt category '{category}' not found. "
            f"Available categories: {list(prompts.keys())}"
        )
    
    category_prompts = prompts[category]
    
    if key not in category_prompts:
        raise PromptNotFoundError(
            f"Prompt key '{key}' not found in category '{category}'. "
            f"Available keys: {list(category_prompts.keys())}"
        )
    
    return category_prompts[key]


def get_classifier_prompt() -> str:
    """Get the intent classifier system prompt."""
    return get_prompt("classifier", "system")


def get_entity_extractor_prompt() -> str:
    """Get the entity extractor system prompt."""
    return get_prompt("entity_extractor", "system")


def get_jira_agent_prompt() -> str:
    """Get the JIRA agent system prompt."""
    return get_prompt("jira_agent", "system")


def get_github_agent_prompt() -> str:
    """Get the GitHub agent system prompt."""
    return get_prompt("github_agent", "system")


def get_summary_agent_prompt() -> str:
    """Get the summary agent system prompt."""
    return get_prompt("summary_agent", "system")


def get_direct_response_prompt() -> str:
    """Get the direct response agent system prompt."""
    return get_prompt("direct_response", "system")


def reload_prompts() -> dict:
    """
    Force reload prompts from file.
    
    This clears the cache and reloads from disk.
    Useful for development or hot-reloading prompts.
    
    Returns:
        dict: Freshly loaded prompts
    """
    _load_prompts_from_file.cache_clear()
    return load_prompts()


# Validate prompts on module load (fail fast if there's an issue)
def _validate_prompts():
    """Validate that all required prompts exist."""
    required_categories = [
        "classifier",
        "entity_extractor", 
        "jira_agent",
        "github_agent",
        "summary_agent",
        "direct_response",
    ]
    
    try:
        prompts = load_prompts()
        missing = [cat for cat in required_categories if cat not in prompts]
        if missing:
            print(f"WARNING: Missing prompt categories: {missing}")
    except FileNotFoundError:
        # Don't fail on import, but warn
        print(f"WARNING: Prompts file not found at {PROMPTS_FILE}")
    except Exception as e:
        print(f"WARNING: Error loading prompts: {e}")


# Run validation on module import
_validate_prompts()
