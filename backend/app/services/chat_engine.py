"""
Dual-Mode Chat Engine - The core of the Team Activity Monitor.
"""

import re
from typing import Optional
from pydantic import BaseModel

from app.services.jira_client import get_jira_client, JiraUserActivity
from app.services.github_client import get_github_client, GitHubUserActivity
from app.services.ai_providers import (
    get_ai_provider,
    Message,
    AIResponse,
    AVAILABLE_TOOLS,
)


# =============================================================================
# Username Alias Mapping (JIRA name → GitHub username)
# =============================================================================

# Maps display names to platform-specific usernames
# This handles cases where a user has different names across platforms
USERNAME_ALIASES = {
    # Real user - Justin Shi (connected JIRA + GitHub account)
    "justin": {
        "jira": "Justin Shi",       # JIRA display name (full name for search)
        "github": "Tianyue-Shi",    # GitHub username
        "display": "Justin Shi",    # For display purposes
        "is_real": True,            # Flag to indicate real user (use real APIs)
    },
    "justin shi": {
        "jira": "Justin Shi",
        "github": "Tianyue-Shi",
        "display": "Justin Shi",
        "is_real": True,
    },
    "shi": {
        "jira": "Justin Shi",
        "github": "Tianyue-Shi",
        "display": "Justin Shi",
        "is_real": True,
    },
    "tianyue-shi": {
        "jira": "Justin Shi",
        "github": "Tianyue-Shi",
        "display": "Justin Shi",
        "is_real": True,
    },
}

# Mock users (demo data, not real APIs)
MOCK_USERS = {"john", "sarah", "mike", "lisa"}

# Real user aliases (use real APIs)
REAL_USER_ALIASES = {"justin", "justin shi", "shi", "tianyue-shi"}


def resolve_username(username: str, platform: str) -> str:
    """
    Resolve a username to the platform-specific version.
    
    Args:
        username: The extracted username from query
        platform: "jira" or "github"
    
    Returns:
        Platform-specific username, or original if no alias found
    """
    username_lower = username.lower().strip()
    if username_lower in USERNAME_ALIASES:
        return USERNAME_ALIASES[username_lower].get(platform, username)
    return username


# =============================================================================
# Response Model
# =============================================================================

class ChatEngineResponse(BaseModel):
    """Response from the chat engine."""
    response: str                           # The AI's answer
    mode: str                               # "procedural" or "agent"
    ai_provider: str                        # "openai" or "claude"
    sources_consulted: list[str] = []       # ["jira", "github"]
    extracted_username: Optional[str] = None  # Username found in query
    debug_info: dict = {}                   # Extra info for debugging


# =============================================================================
# Query Parser - Extract usernames from natural language
# =============================================================================

def extract_username(query: str) -> Optional[str]:
    """
    Extract a username from a natural language query.
    """
    query_lower = query.lower()
    
    # First, check for multi-word real user names (higher priority)
    # This handles "Justin Shi" before regex extracts just "Justin"
    for alias in REAL_USER_ALIASES:
        if alias in query_lower:
            return alias
    
    # Pattern 1: "What is X working on" / "What has X been doing"
    # Updated to capture multi-word names with [\w\s]+
    patterns = [
        r"what (?:is|has) ([\w\s]+?) (?:working|doing|been)",
        r"show (?:me )?([\w\s]+?)'?s? (?:recent |current )?(?:activity|issues|work|tickets|commits|prs)",
        r"(?:activity|issues|work|tickets) (?:for|of) ([\w\s]+)",
        r"([\w\s]+?)'?s? (?:jira|github|activity|issues|work)",
        r"what (?:about|is) (\w+)",
    ]
    
    for pattern in patterns:
        match = re.search(pattern, query_lower)
        if match:
            username = match.group(1).strip()
            # Filter out common words that aren't usernames
            if username not in ["the", "a", "an", "my", "your", "their", "our", "they", "them"]:
                # Check if this matches a known alias
                if username in REAL_USER_ALIASES or username in MOCK_USERS:
                    return username
                # Check if it's a partial match for known users
                for alias in REAL_USER_ALIASES:
                    if username in alias or alias in username:
                        return alias
                return username
    
    # Pattern 2: Check for known usernames directly in query (mock users)
    for user in MOCK_USERS:
        if user in query_lower:
            return user
    
    return None


# =============================================================================
# Data Formatting - Convert API data to readable text
# =============================================================================

def format_jira_data(data: JiraUserActivity) -> str:
    """Format JIRA data into human-readable text for AI context."""
    if data.error:
        return f"JIRA Error: {data.error}"
    
    if not data.issues:
        return f"No JIRA issues found for {data.username}."
    
    lines = [f"JIRA Issues for {data.username} ({data.total_count} total):"]
    for issue in data.issues:
        lines.append(
            f"  - [{issue.key}] {issue.summary} "
            f"(Status: {issue.status}, Priority: {issue.priority})"
        )
    
    return "\n".join(lines)


def format_github_data(data: GitHubUserActivity) -> str:
    """Format GitHub data into human-readable text for AI context."""
    if data.error:
        return f"GitHub Error: {data.error}"
    
    lines = [f"GitHub Activity for {data.username}:"]
    
    if data.commits:
        lines.append(f"  Recent Commits ({data.total_commits} total):")
        for commit in data.commits[:5]:  # Show last 5
            lines.append(f"    - {commit.sha}: {commit.message} ({commit.repo})")
    else:
        lines.append("  No recent commits.")
    
    if data.pull_requests:
        open_prs = [pr for pr in data.pull_requests if pr.state == "open"]
        if open_prs:
            lines.append(f"  Open Pull Requests ({len(open_prs)}):")
            for pr in open_prs:
                lines.append(f"    - PR #{pr.number}: {pr.title} ({pr.repo})")
    
    if data.active_repos:
        lines.append(f"  Active Repositories: {', '.join(data.active_repos)}")
    
    return "\n".join(lines)


# =============================================================================
# PROCEDURAL MODE - Always fetch, then summarize
# =============================================================================

async def generate_procedural_response(
    query: str,
    ai_provider: str = "openai",
    system_prompt: str = "",
    selected_user: Optional[dict] = None,
) -> ChatEngineResponse:
    """
    Procedural/Standard mode: ALWAYS fetch data, then ask AI to summarize.
    
    Flow:
    1. Extract username from query (or use selected_user from dropdown)
    2. Fetch JIRA issues (always)
    3. Fetch GitHub activity (always)
    4. Concatenate into context string
    5. Send context + query to AI
    6. Return AI's response
    
    Pros: Deterministic, reliable, complete data
    Cons: Expensive (always fetches), slow, wasteful for simple queries
    """
    sources = []
    debug_info = {}
    
    # Step 1: Determine which user to query
    # Priority: selected_user from dropdown > extracted from query
    use_mock_data = False  # Flag to force mock data for demo users
    
    if selected_user:
        # Use the platform-specific identifiers from the dropdown selection
        jira_username = selected_user.jira_display_name or selected_user.display_name
        github_username = selected_user.github_username or selected_user.display_name
        username = selected_user.display_name
        debug_info["user_source"] = "dropdown"
        debug_info["selected_user_id"] = selected_user.id
        
        # Check if this is a mock/demo user - if so, force mock data
        if selected_user.source == "mock":
            use_mock_data = True
            debug_info["using_mock_data"] = True
    else:
        # Fall back to extracting from query
        username = extract_username(query)
        if username:
            jira_username = resolve_username(username, "jira")
            github_username = resolve_username(username, "github")
            # Check if the extracted username is a known mock user (NOT a real user alias)
            username_lower = username.lower()
            if username_lower in MOCK_USERS and username_lower not in REAL_USER_ALIASES:
                use_mock_data = True
                debug_info["using_mock_data"] = True
        else:
            jira_username = None
            github_username = None
        debug_info["user_source"] = "query_extraction"
    
    debug_info["extracted_username"] = username
    debug_info["jira_username"] = jira_username
    debug_info["github_username"] = github_username
    
    # Step 2 & 3: Fetch data from both sources
    jira_client = get_jira_client()
    github_client = get_github_client()
    
    # Temporarily override to use mock data for demo users
    original_jira_mock = jira_client._use_mock
    original_github_mock = github_client._use_mock
    
    if use_mock_data:
        jira_client._use_mock = True
        github_client._use_mock = True
    
    context_parts = []
    
    try:
        if jira_username or github_username:
            # Fetch JIRA
            if jira_username:
                jira_data = await jira_client.get_user_issues(jira_username)
                jira_text = format_jira_data(jira_data)
                context_parts.append(jira_text)
                sources.append("jira" + (" (mock)" if use_mock_data else ""))
                debug_info["jira_issues_count"] = jira_data.total_count
            
            # Fetch GitHub
            if github_username:
                github_data = await github_client.get_user_activity(github_username)
                github_text = format_github_data(github_data)
                context_parts.append(github_text)
                sources.append("github" + (" (mock)" if use_mock_data else ""))
                debug_info["github_commits_count"] = github_data.total_commits
        else:
            context_parts.append(
                "Note: No specific team member was mentioned in the query. "
                "Please select a user from the dropdown or mention a name in your question."
            )
    finally:
        # Restore original mock settings
        jira_client._use_mock = original_jira_mock
        github_client._use_mock = original_github_mock
    
    # Step 4: Build context for AI
    context = "\n\n".join(context_parts)
    
    # Step 5: Call AI
    ai = get_ai_provider(ai_provider)
    
    full_prompt = f"""Based on the following team activity data, answer the user's question.

{context}

User Question: {query}

Provide a helpful, concise response summarizing the relevant information."""
    
    response = await ai.generate(
        messages=[Message(role="user", content=full_prompt)],
        system_prompt=system_prompt or "You are a helpful technical program manager assistant.",
    )
    
    return ChatEngineResponse(
        response=response.content,
        mode="procedural",
        ai_provider=ai_provider,
        sources_consulted=sources,
        extracted_username=username,
        debug_info=debug_info,
    )


# =============================================================================
# AGENTIC MODE - AI decides when to fetch using Function Calling
# =============================================================================

async def execute_tool(tool_name: str, arguments: dict, use_mock_data: bool = False) -> str:
    """
    Execute a tool call and return the result as a string.
    
    This is called when the AI decides it needs data.
    Uses username alias resolution for cross-platform support.
    
    Args:
        tool_name: Name of the tool to execute
        arguments: Tool arguments
        use_mock_data: If True, force mock data (for demo users)
    """
    if tool_name == "get_jira_issues":
        username = arguments.get("username", "")
        # Resolve to JIRA-specific username
        jira_username = resolve_username(username, "jira")
        jira_client = get_jira_client()
        
        # Temporarily force mock data if needed
        original_mock = jira_client._use_mock
        if use_mock_data:
            jira_client._use_mock = True
        
        try:
            data = await jira_client.get_user_issues(jira_username)
            return format_jira_data(data)
        finally:
            jira_client._use_mock = original_mock
    
    elif tool_name == "get_github_activity":
        username = arguments.get("username", "")
        # Resolve to GitHub-specific username
        github_username = resolve_username(username, "github")
        github_client = get_github_client()
        
        # Temporarily force mock data if needed
        original_mock = github_client._use_mock
        if use_mock_data:
            github_client._use_mock = True
        
        try:
            data = await github_client.get_user_activity(github_username)
            return format_github_data(data)
        finally:
            github_client._use_mock = original_mock
    
    else:
        return f"Unknown tool: {tool_name}"


async def generate_agent_response(
    query: str,
    ai_provider: str = "openai",
    system_prompt: str = "",
    selected_user: Optional[dict] = None,
) -> ChatEngineResponse:
    """
    Agentic/Smart mode: AI DECIDES whether to fetch data using function calling.
    
    Flow:
    1. Send query to AI with available tools (enhanced with selected user context)
    2. AI returns either:
       a) Direct response (no data needed) → Done!
       b) Tool calls (needs data) → Execute tools, send results back
    3. AI generates final response based on tool results
    
    Pros: Efficient (only fetches when needed), smarter conversations
    Cons: Non-deterministic, AI might miss when it should fetch
    
    The key insight: If user says "Hello", AI should just say "Hi!" without
    wasting API calls to fetch JIRA/GitHub data.
    """
    sources = []
    debug_info = {"tool_calls": []}
    use_mock_data = False  # Flag to force mock data for demo users
    
    ai = get_ai_provider(ai_provider)
    
    # If a user is selected from dropdown, enhance the query with their info
    enhanced_query = query
    if selected_user:
        debug_info["user_source"] = "dropdown"
        debug_info["selected_user_id"] = selected_user.id
        # Add user context to the query so AI knows which user to query
        enhanced_query = f"""[Context: User selected '{selected_user.display_name}' from the dropdown. 
For JIRA queries, use: '{selected_user.jira_display_name or selected_user.display_name}'
For GitHub queries, use: '{selected_user.github_username or selected_user.display_name}']

User question: {query}"""
        
        # Check if this is a mock/demo user - if so, force mock data
        if selected_user.source == "mock":
            use_mock_data = True
            debug_info["using_mock_data"] = True
    else:
        debug_info["user_source"] = "query_extraction"
        # Check if query mentions a known mock user (NOT a real user alias)
        extracted = extract_username(query)
        if extracted:
            extracted_lower = extracted.lower()
            if extracted_lower in MOCK_USERS and extracted_lower not in REAL_USER_ALIASES:
                use_mock_data = True
                debug_info["using_mock_data"] = True
    
    # Enhanced system prompt for agentic mode
    agent_system_prompt = system_prompt or """You are a helpful technical program manager assistant for the Team Activity Monitor.

You have access to tools to fetch team member activity:
- get_jira_issues: Get JIRA tickets assigned to someone
- get_github_activity: Get recent GitHub commits and PRs

IMPORTANT:
- Only use tools when the user is asking about team member activity
- For greetings or general questions, respond directly without using tools
- When you do use tools, always specify the username parameter
- If a user is selected from dropdown (shown in [Context]), use the provided usernames

Available team members: Select from the dropdown for real users, or type names like john, sarah, mike, lisa (demo users)"""

    # Step 1: Initial call with tools
    initial_response = await ai.generate_with_tools(
        messages=[Message(role="user", content=enhanced_query)],
        tools=AVAILABLE_TOOLS,
        system_prompt=agent_system_prompt,
    )
    
    # Step 2a: If no tool calls, return direct response
    if not initial_response.tool_calls:
        return ChatEngineResponse(
            response=initial_response.content,
            mode="agent",
            ai_provider=ai_provider,
            sources_consulted=[],
            debug_info={"tool_calls": [], "direct_response": True},
        )
    
    # Step 2b: Execute tool calls
    # Include tool_calls in the assistant message (required by OpenAI API)
    messages = [
        Message(role="user", content=query),
        Message(
            role="assistant", 
            content=initial_response.content or "",
            tool_calls=initial_response.tool_calls,
        ),
    ]
    
    for tool_call in initial_response.tool_calls:
        debug_info["tool_calls"].append({
            "name": tool_call.name,
            "arguments": tool_call.arguments,
        })
        
        # Track which sources were consulted
        if tool_call.name == "get_jira_issues":
            sources.append("jira" + (" (mock)" if use_mock_data else ""))
        elif tool_call.name == "get_github_activity":
            sources.append("github" + (" (mock)" if use_mock_data else ""))
        
        # Execute the tool with mock data flag
        result = await execute_tool(tool_call.name, tool_call.arguments, use_mock_data)
        
        # Add tool result to conversation
        messages.append(Message(
            role="tool",
            content=result,
            tool_call_id=tool_call.id,
            name=tool_call.name,
        ))
    
    # Step 3: Final call to get AI's response with tool results
    final_response = await ai.generate_with_tools(
        messages=messages,
        tools=AVAILABLE_TOOLS,
        system_prompt=agent_system_prompt,
    )
    
    # Extract username from tool calls
    extracted_username = None
    for tc in initial_response.tool_calls:
        if "username" in tc.arguments:
            extracted_username = tc.arguments["username"]
            break
    
    return ChatEngineResponse(
        response=final_response.content,
        mode="agent",
        ai_provider=ai_provider,
        sources_consulted=list(set(sources)),  # Remove duplicates
        extracted_username=extracted_username,
        debug_info=debug_info,
    )


# =============================================================================
# Main Entry Point - Route to correct mode
# =============================================================================

async def generate_response(
    query: str,
    mode: str = "procedural",
    ai_provider: str = "openai",
    system_prompt: str = "",
    selected_user: Optional[dict] = None,
) -> ChatEngineResponse:
    """
    Main entry point for the chat engine.
    
    Routes to the appropriate mode based on the 'mode' parameter.
    
    Args:
        query: User's question
        mode: "procedural" or "agent"
        ai_provider: "openai" or "claude"
        system_prompt: Custom system prompt (optional)
        selected_user: User selected from dropdown (optional, overrides query extraction)
        
    Returns:
        ChatEngineResponse with the AI's answer and metadata
    """
    if mode == "agent":
        return await generate_agent_response(query, ai_provider, system_prompt, selected_user)
    else:
        return await generate_procedural_response(query, ai_provider, system_prompt, selected_user)
