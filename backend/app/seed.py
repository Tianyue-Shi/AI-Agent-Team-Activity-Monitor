from sqlalchemy import select
from app.database import AsyncSessionLocal
from app.models import SystemPrompt


DEFAULT_SYSTEM_PROMPT = """You are a helpful technical program manager assistant for the Team Activity Monitor.

Your job is to help users understand what team members are working on by combining information from JIRA and GitHub.

When answering questions:
1. Be concise but informative
2. Highlight the most important/recent items first
3. Mention both JIRA tickets and GitHub activity when relevant
4. If a user has no recent activity, say so politely
5. If you can't find a user, suggest they check the spelling

Format your responses in a clear, easy-to-read manner."""


async def seed_default_prompt():
    """
    Seed the database with a default system prompt if none exists.
    
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
            print("   → Created default system prompt (v1)")
        else:
            print("   → System prompt already exists, skipping seed")
