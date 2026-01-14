"""
Routers package - API endpoint modules.

Each router handles a specific resource:
- chat: Main chat endpoint (/chat)
- prompts: System prompt management (/prompts)
"""

from app.routers.chat import router as chat_router
from app.routers.prompts import router as prompts_router

__all__ = ["chat_router", "prompts_router"]
