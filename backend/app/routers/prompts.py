"""
Prompts Router - Version-controlled system prompts.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import (
    SystemPrompt,
    PromptCreate,
    PromptResponse,
    PromptHistoryResponse,
)

router = APIRouter()


# =============================================================================
# GET /prompts/current - Get the active prompt
# =============================================================================

@router.get("/current", response_model=PromptResponse)
async def get_current_prompt(db: AsyncSession = Depends(get_db)):
    """
    Get the currently active system prompt.
    
    There should always be exactly one active prompt.
    Returns the prompt with is_active=True.
    """
    result = await db.execute(
        select(SystemPrompt).where(SystemPrompt.is_active == True)
    )
    prompt = result.scalar_one_or_none()
    
    if not prompt:
        raise HTTPException(
            status_code=404,
            detail="No active prompt found. Database may not be seeded."
        )
    
    return prompt


# =============================================================================
# POST /prompts/update - Create a new prompt version
# =============================================================================

@router.post("/update", response_model=PromptResponse)
async def update_prompt(
    prompt_data: PromptCreate,
    db: AsyncSession = Depends(get_db),
):
    """
    Create a new prompt version.
    
    We NEVER delete or update existing rows - only append.
    """
    # Step 1: Get current max version
    result = await db.execute(
        select(func.max(SystemPrompt.version))
    )
    max_version = result.scalar() or 0
    new_version = max_version + 1
    
    # Step 2: Deactivate all existing prompts
    result = await db.execute(select(SystemPrompt))
    all_prompts = result.scalars().all()
    for p in all_prompts:
        p.is_active = False
    
    # Step 3: Create new prompt version
    new_prompt = SystemPrompt(
        prompt_text=prompt_data.prompt_text,
        version=new_version,
        is_active=True,
    )
    db.add(new_prompt)
    
    # Commit is handled by the get_db dependency
    await db.flush()
    await db.refresh(new_prompt)
    
    return new_prompt


# =============================================================================
# GET /prompts/history - Get all prompt versions
# =============================================================================

@router.get("/history", response_model=PromptHistoryResponse)
async def get_prompt_history(db: AsyncSession = Depends(get_db)):
    """
    Get all prompt versions (for audit trail / "blame" feature).
    
    Returns prompts ordered by version descending (newest first).
    This lets the admin see what changed and when.
    """
    result = await db.execute(
        select(SystemPrompt).order_by(SystemPrompt.version.desc())
    )
    prompts = result.scalars().all()
    
    return PromptHistoryResponse(
        prompts=prompts,
        total_versions=len(prompts),
    )


# =============================================================================
# POST /prompts/rollback/{version} - Rollback to a previous version
# =============================================================================

@router.post("/rollback/{version}", response_model=PromptResponse)
async def rollback_prompt(
    version: int,
    db: AsyncSession = Depends(get_db),
):
    """
    Rollback to a previous prompt version.
    
    This doesn't delete anything - it creates a NEW version
    with the same text as the specified old version.
    
    Example:
    - v1: "Be helpful" (active)
    - v2: "Be rude" (oops!)
    - Rollback to v1 creates:
    - v3: "Be helpful" (active, copy of v1)
    """
    # Find the version to rollback to
    result = await db.execute(
        select(SystemPrompt).where(SystemPrompt.version == version)
    )
    old_prompt = result.scalar_one_or_none()
    
    if not old_prompt:
        raise HTTPException(
            status_code=404,
            detail=f"Prompt version {version} not found"
        )
    
    # Create new version with old text (reuse update logic)
    return await update_prompt(
        PromptCreate(prompt_text=old_prompt.prompt_text),
        db=db,
    )


# =============================================================================
# GET /prompts/{version} - Get a specific version
# =============================================================================

@router.get("/{version}", response_model=PromptResponse)
async def get_prompt_version(
    version: int,
    db: AsyncSession = Depends(get_db),
):
    """
    Get a specific prompt version.
    
    Useful for comparing versions or previewing before rollback.
    """
    result = await db.execute(
        select(SystemPrompt).where(SystemPrompt.version == version)
    )
    prompt = result.scalar_one_or_none()
    
    if not prompt:
        raise HTTPException(
            status_code=404,
            detail=f"Prompt version {version} not found"
        )
    
    return prompt
