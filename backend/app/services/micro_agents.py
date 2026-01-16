"""
Micro-Agents

This module implements a 2-AI-agent call architecture:
1. Router Agent: Decides which tools to call, executes them
2. Response Agent: Formats the final response

Tool functions (called by Router Agent):
- jira_agent: Fetches JIRA data for a user
- github_agent: Fetches GitHub data for a user
"""

import json
from typing import Optional
from pydantic import BaseModel

from app.services.ai_providers import (
    get_ai_provider,
    Message,
    ToolDefinition,
    ToolParameter,
    ToolCall,
)
from app.services.jira_client import get_jira_client, JiraUserActivity
from app.services.github_client import get_github_client, GitHubUserActivity
from app.services.prompt_loader import get_prompt


# =============================================================================
# Result Models
# =============================================================================

class RouterResult(BaseModel):
    """Result from the router agent."""
    route: str  # 'jira', 'github', 'both', 'none'
    jira_data: Optional[dict] = None
    github_data: Optional[dict] = None
    message: Optional[str] = None  # For greetings/errors


# =============================================================================
# Tool Definitions (for AI function calling)
# =============================================================================

ROUTER_TOOLS = [
    ToolDefinition(
        name="jira_agent",
        description="Fetch JIRA tickets and issues for a team member. Use this when the user asks about tasks, tickets, bugs, stories, or JIRA-related work.",
        parameters=[
            ToolParameter(
                name="username",
                type="string",
                description="The team member's name (e.g., 'john', 'sarah', 'justin')",
                required=True,
            ),
        ],
    ),
    ToolDefinition(
        name="github_agent",
        description="Fetch GitHub commits and pull requests for a team member. Use this when the user asks about code, commits, PRs, or GitHub-related activity.",
        parameters=[
            ToolParameter(
                name="username",
                type="string",
                description="The team member's name (e.g., 'john', 'sarah', 'justin')",
                required=True,
            ),
        ],
    ),
]


# =============================================================================
# Tool Functions (executed when AI calls them)
# =============================================================================

async def jira_agent(username: str) -> dict:
    """
    Tool: Fetch JIRA data for a user.
    
    Called by the Router Agent via function calling.
    Returns raw data dict for the Response Agent to format.
    """
    # Resolve platform-specific username
    from app.services.intent_classifier import get_platform_username
    jira_username = get_platform_username(username, "jira")
    
    # Fetch data
    client = get_jira_client()
    data: JiraUserActivity = await client.get_user_issues(jira_username)
    
    # Convert to dict for JSON serialization
    return {
        "username": data.username,
        "total_count": data.total_count,
        "is_real_data": data.is_real_data,
        "error": data.error,
        "issues": [
            {
                "key": issue.key,
                "summary": issue.summary,
                "status": issue.status,
                "priority": issue.priority,
                "type": issue.issue_type,
            }
            for issue in data.issues
        ] if data.issues else [],
    }


async def github_agent(username: str) -> dict:
    """
    Tool: Fetch GitHub data for a user.
    
    Called by the Router Agent via function calling.
    Returns raw data dict for the Response Agent to format.
    """
    # Resolve platform-specific username
    from app.services.intent_classifier import get_platform_username
    github_username = get_platform_username(username, "github")
    
    # Fetch data
    client = get_github_client()
    data: GitHubUserActivity = await client.get_user_activity(github_username)
    
    # Convert to dict for JSON serialization
    return {
        "username": data.username,
        "total_commits": data.total_commits,
        "total_prs": data.total_prs,
        "active_repos": data.active_repos,
        "is_real_data": data.is_real_data,
        "error": data.error,
        "commits": [
            {
                "message": commit.message,
                "repo": commit.repo,
            }
            for commit in data.commits[:5]  # Limit to 5 commits
        ] if data.commits else [],
        "pull_requests": [
            {
                "number": pr.number,
                "title": pr.title,
                "repo": pr.repo,
                "state": pr.state,
            }
            for pr in data.pull_requests
        ] if data.pull_requests else [],
    }


# Tool execution map
TOOL_FUNCTIONS = {
    "jira_agent": jira_agent,
    "github_agent": github_agent,
}


async def execute_tool(tool_call: ToolCall) -> str:
    """Execute a tool call and return the result as JSON string."""
    func = TOOL_FUNCTIONS.get(tool_call.name)
    if not func:
        return json.dumps({"error": f"Unknown tool: {tool_call.name}"})
    
    try:
        result = await func(**tool_call.arguments)
        return json.dumps(result)
    except Exception as e:
        return json.dumps({"error": str(e)})


# =============================================================================
# Router Agent (AI Call 1)
# =============================================================================

async def router_agent(
    query: str,
    username: Optional[str],
    ai_provider: str = "openai",
) -> RouterResult:
    """
    AI Call 1: Decides which data sources to query and fetches the data.
    
    Uses function calling to invoke jira_agent and/or github_agent.
    For greetings or unclear queries, responds directly without tools.
    
    Args:
        query: User's question
        username: Pre-extracted username (from regex), may be None
        ai_provider: 'openai' or 'claude'
        
    Returns:
        RouterResult with route type and fetched data
    """
    ai = get_ai_provider(ai_provider)
    
    # Get system prompt
    try:
        system_prompt = get_prompt("router_agent")
    except Exception:
        system_prompt = """You are a helpful assistant that tracks team activity.
You have tools to fetch JIRA and GitHub data for team members.

Rules:
- For greetings (hi, hello, etc.): Respond directly without using tools
- For activity questions: Use the appropriate tool(s) to fetch data
- If no username is provided or unclear, ask for clarification
- You can call both tools if the user asks about general activity"""

    # Build user message with context
    user_content = query
    if username:
        user_content = f"[Context: The username '{username}' was detected in the query]\n\n{query}"
    
    messages = [Message(role="user", content=user_content)]
    
    # Call AI with tools
    response = await ai.generate_with_tools(
        messages=messages,
        tools=ROUTER_TOOLS,
        system_prompt=system_prompt,
    )
    
    # If no tool calls, return direct response
    if not response.tool_calls:
        return RouterResult(
            route="none",
            message=response.content,
        )
    
    # Execute tool calls and collect data
    jira_data = None
    github_data = None
    tool_results = []
    
    for tool_call in response.tool_calls:
        result_str = await execute_tool(tool_call)
        result_data = json.loads(result_str)
        
        if tool_call.name == "jira_agent":
            jira_data = result_data
        elif tool_call.name == "github_agent":
            github_data = result_data
        
        tool_results.append((tool_call, result_str))
    
    # Determine route type
    if jira_data and github_data:
        route = "both"
    elif jira_data:
        route = "jira"
    elif github_data:
        route = "github"
    else:
        route = "none"
    
    return RouterResult(
        route=route,
        jira_data=jira_data,
        github_data=github_data,
    )


# =============================================================================
# Response Agent (AI Call 2)
# =============================================================================

async def response_agent(
    query: str,
    data: RouterResult,
    ai_provider: str = "openai",
) -> str:
    """
    AI Call 2: Formats the data into a well-structured response.
    
    Takes the raw data from Router Agent and creates a clean,
    markdown-formatted response for the user.
    
    Args:
        query: Original user question
        data: RouterResult from router_agent
        ai_provider: 'openai' or 'claude'
        
    Returns:
        Formatted markdown response string
    """
    # If router returned a direct message (greeting, clarification)
    if data.route == "none" and data.message:
        return data.message
    
    ai = get_ai_provider(ai_provider)
    
    # Get system prompt
    try:
        system_prompt = get_prompt("response_agent")
    except Exception:
        system_prompt = """Format the data into a concise, well-structured markdown response.

Rules:
- Lead with a 1-sentence summary
- Use tables for 3+ items
- Max 5 bullet points per section
- Be direct, no fluff or filler text
- Use **bold** for emphasis on key items"""

    # Build context from data
    context_parts = []
    
    if data.jira_data:
        jira_str = _format_jira_context(data.jira_data)
        context_parts.append(f"JIRA Data:\n{jira_str}")
    
    if data.github_data:
        github_str = _format_github_context(data.github_data)
        context_parts.append(f"GitHub Data:\n{github_str}")
    
    if not context_parts:
        return "No data was found. Please specify a team member's name in your question."
    
    context = "\n\n".join(context_parts)
    
    user_message = f"""User Question: {query}

{context}

FORMAT (use bullet points, NO tables):
- Start with 2-3 sentence summary
- **JIRA Issues**: List each as "**TICKET** - Summary (Type, Status, Priority)"
- **GitHub Commits**: List each as "repo: message"
- **Pull Requests**: List each as "**PR #N** - Title (repo, state)"
- **Insights**: 3-4 bullets on themes, connections, workload

IMPORTANT: Only include sections for data provided above. If only JIRA data is shown, only include JIRA section. If only GitHub data is shown, only include GitHub sections. Do NOT add "No data available" messages for data sources not queried."""

    response = await ai.generate(
        messages=[Message(role="user", content=user_message)],
        system_prompt=system_prompt,
    )
    
    return response.content


def _format_jira_context(data: dict) -> str:
    """Format JIRA data for the response agent."""
    if data.get("error"):
        return f"Error: {data['error']}"
    
    lines = [
        f"Username: {data.get('username', 'unknown')}",
        f"Total Issues: {data.get('total_count', 0)}",
        f"Data Source: {'Real JIRA API' if data.get('is_real_data') else 'Demo Data'}",
    ]
    
    if data.get("issues"):
        lines.append("\nIssues (with details):")
        for issue in data["issues"]:
            issue_type = issue.get('type', 'Task')
            lines.append(f"- {issue['key']}: {issue['summary']}")
            lines.append(f"  Type: {issue_type} | Status: {issue['status']} | Priority: {issue['priority']}")
    
    return "\n".join(lines)


def _format_github_context(data: dict) -> str:
    """Format GitHub data for the response agent."""
    if data.get("error"):
        return f"Error: {data['error']}"
    
    lines = [
        f"Username: {data.get('username', 'unknown')}",
        f"Total Commits: {data.get('total_commits', 0)}",
        f"Total PRs: {data.get('total_prs', 0)}",
        f"Active Repos: {', '.join(data.get('active_repos', [])) or 'None'}",
        f"Data Source: {'Real GitHub API' if data.get('is_real_data') else 'Demo Data'}",
    ]
    
    if data.get("commits"):
        lines.append("\nRecent Commits (with repository):")
        for commit in data["commits"]:
            lines.append(f"- [{commit['repo']}] {commit['message']}")
    
    if data.get("pull_requests"):
        lines.append("\nPull Requests (with details):")
        for pr in data["pull_requests"]:
            lines.append(f"- PR #{pr['number']}: {pr['title']}")
            lines.append(f"  Repository: {pr['repo']} | State: {pr['state']}")
    
    return "\n".join(lines)
