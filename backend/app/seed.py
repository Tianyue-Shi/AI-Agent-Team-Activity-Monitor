from sqlalchemy import select
from app.database import AsyncSessionLocal
from app.models import SystemPrompt


# NOTE: This legacy prompt is kept for backwards compatibility with the database.
# The actual prompts used by the new intelligent pipeline are in prompts.yaml
# and loaded via prompt_loader.py at startup.
DEFAULT_SYSTEM_PROMPT = """You are a helpful technical program manager assistant for the Team Activity Monitor.

Your job is to help users understand what team members are working on by combining information from JIRA and GitHub.

When answering questions:
1. Be concise but informative
2. Highlight the most important/recent items first
3. Mention both JIRA tickets and GitHub activity when relevant
4. If a user has no recent activity, say so politely
5. If you can't find a user, suggest they check the spelling

Format your responses in a clear, easy-to-read manner.

NOTE: This prompt is from the legacy database storage. The new intelligent pipeline 
uses specialized prompts from prompts.yaml for different agents (classifier, 
jira_agent, github_agent, summary_agent, etc.)."""


async def seed_default_prompt():
    """
    Seed the database with a default system prompt if none exists.
    
    NOTE: The new intelligent pipeline uses prompts from prompts.yaml instead
    of the database. This function is kept for backwards compatibility and
    for the admin panel's prompt history feature.
    
    This is idempotent - safe to call multiple times.
    """
    async with AsyncSessionLocal() as session:
        # Check if any prompts exist
        result = await session.execute(
            select(SystemPrompt).limit(1)
        )
        existing = result.scalar_one_or_none()
        
        if existing is None:
            # No prompts exist, create the default
            default_prompt = SystemPrompt(
                prompt_text=DEFAULT_SYSTEM_PROMPT,
                version=1,
                is_active=True
            )
            session.add(default_prompt)
            await session.commit()
            print("   → Created default system prompt (v1) [legacy - see prompts.yaml]")
        else:
            print("   → System prompt already exists, skipping seed")
    
    # Validate YAML prompts are loadable
    try:
        from app.services.prompt_loader import load_prompts
        prompts = load_prompts()
        print(f"   → Loaded {len(prompts)} prompt categories from YAML")
    except Exception as e:
        print(f"   ⚠ Warning: Failed to load prompts.yaml: {e}")
