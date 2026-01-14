"""
JIRA API Client - Supports both mock and real JIRA API.
"""

from datetime import datetime, timedelta
from typing import Optional
from pydantic import BaseModel
import httpx
import base64


# =============================================================================
# Response Models (What we return to callers)
# =============================================================================

class JiraIssue(BaseModel):
    """A single JIRA issue/ticket."""
    key: str                    # e.g., "PROJ-123"
    summary: str                # Issue title
    status: str                 # e.g., "In Progress", "Code Review"
    priority: str               # e.g., "High", "Medium", "Low"
    issue_type: str             # e.g., "Bug", "Story", "Task"
    updated: datetime           # Last update time
    assignee: str               # Username
    url: str = ""               # Link to issue


class JiraUserActivity(BaseModel):
    """All JIRA activity for a user."""
    username: str
    issues: list[JiraIssue]
    total_count: int
    error: Optional[str] = None
    is_real_data: bool = False  # True if from real API


# =============================================================================
# Mock Data - Realistic team activity (fallback)
# =============================================================================

MOCK_JIRA_DATA: dict[str, list[dict]] = {
    "john": [
        {
            "key": "PROJ-142",
            "summary": "Implement OAuth2 authentication flow",
            "status": "In Progress",
            "priority": "High",
            "issue_type": "Story",
            "updated": datetime.now() - timedelta(hours=2),
        },
        {
            "key": "PROJ-138",
            "summary": "Fix session timeout bug",
            "status": "Code Review",
            "priority": "Medium",
            "issue_type": "Bug",
            "updated": datetime.now() - timedelta(days=1),
        },
        {
            "key": "PROJ-155",
            "summary": "Add rate limiting to API endpoints",
            "status": "To Do",
            "priority": "Medium",
            "issue_type": "Task",
            "updated": datetime.now() - timedelta(days=3),
        },
    ],
    "sarah": [
        {
            "key": "PROJ-147",
            "summary": "Design new dashboard UI components",
            "status": "In Progress",
            "priority": "High",
            "issue_type": "Story",
            "updated": datetime.now() - timedelta(hours=5),
        },
        {
            "key": "PROJ-151",
            "summary": "Optimize database queries for reports",
            "status": "In Progress",
            "priority": "High",
            "issue_type": "Task",
            "updated": datetime.now() - timedelta(hours=8),
        },
    ],
    "mike": [
        {
            "key": "PROJ-149",
            "summary": "Set up CI/CD pipeline for staging",
            "status": "Done",
            "priority": "High",
            "issue_type": "Task",
            "updated": datetime.now() - timedelta(days=1),
        },
        {
            "key": "PROJ-156",
            "summary": "Investigate memory leak in worker service",
            "status": "In Progress",
            "priority": "Critical",
            "issue_type": "Bug",
            "updated": datetime.now() - timedelta(hours=3),
        },
    ],
    "lisa": [
        {
            "key": "PROJ-144",
            "summary": "Write API documentation for v2 endpoints",
            "status": "In Progress",
            "priority": "Medium",
            "issue_type": "Task",
            "updated": datetime.now() - timedelta(hours=1),
        },
        {
            "key": "PROJ-152",
            "summary": "Implement webhook notifications",
            "status": "Code Review",
            "priority": "Medium",
            "issue_type": "Story",
            "updated": datetime.now() - timedelta(days=2),
        },
        {
            "key": "PROJ-158",
            "summary": "Add unit tests for payment module",
            "status": "To Do",
            "priority": "Low",
            "issue_type": "Task",
            "updated": datetime.now() - timedelta(days=4),
        },
    ],
}


# =============================================================================
# JIRA Client Class
# =============================================================================

class JiraClient:
    """
    Client for fetching JIRA data.
    """
    
    def __init__(self, base_url: str = "", email: str = "", api_token: str = ""):
        """
        Initialize JIRA client.
        
        Args:
            base_url: JIRA instance URL (e.g., https://company.atlassian.net)
            email: User email for authentication
            api_token: JIRA API token
        """
        self.base_url = base_url.rstrip("/") if base_url else ""
        self.email = email
        self.api_token = api_token
        # Use real API if all credentials are provided
        self._use_mock = not all([base_url, email, api_token])
        self._client: Optional[httpx.AsyncClient] = None
    
    def _get_auth_header(self) -> str:
        """Generate Basic Auth header value."""
        credentials = f"{self.email}:{self.api_token}"
        encoded = base64.b64encode(credentials.encode()).decode()
        return f"Basic {encoded}"
    
    def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client with auth headers."""
        if self._client is None:
            headers = {
                "Authorization": self._get_auth_header(),
                "Accept": "application/json",
                "Content-Type": "application/json",
            }
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                headers=headers,
                timeout=30.0,
            )
        return self._client
    
    async def test_connection(self) -> dict:
        """
        Test JIRA API connection and authentication.
        
        Returns:
            Dict with connection status and user info
        """
        if not all([self.base_url, self.email, self.api_token]):
            return {
                "connected": False,
                "authenticated": False,
                "error": "JIRA credentials not fully configured (need base_url, email, api_token)",
                "using_mock": True,
            }
        
        try:
            client = self._get_client()
            # Test with /myself endpoint - returns current user info
            response = await client.get("/rest/api/3/myself")
            
            if response.status_code == 200:
                user_data = response.json()
                return {
                    "connected": True,
                    "authenticated": True,
                    "account_id": user_data.get("accountId"),
                    "display_name": user_data.get("displayName"),
                    "email": user_data.get("emailAddress"),
                    "using_mock": False,
                }
            elif response.status_code == 401:
                return {
                    "connected": True,
                    "authenticated": False,
                    "error": "Invalid credentials (check email and API token)",
                    "using_mock": True,
                }
            elif response.status_code == 404:
                return {
                    "connected": False,
                    "authenticated": False,
                    "error": "JIRA instance not found (check base URL)",
                    "using_mock": True,
                }
            else:
                return {
                    "connected": False,
                    "authenticated": False,
                    "error": f"JIRA API returned {response.status_code}: {response.text}",
                    "using_mock": True,
                }
        except Exception as e:
            return {
                "connected": False,
                "authenticated": False,
                "error": str(e),
                "using_mock": True,
            }
    
    async def get_all_users(self) -> list[dict]:
        """
        Fetch all users from the JIRA instance.
        
        Returns:
            List of user dictionaries with account_id, display_name, email, active
        """
        if self._use_mock:
            # Return mock user list
            return [
                {"account_id": "mock_john", "display_name": "John", "email": "john@example.com", "active": True},
                {"account_id": "mock_sarah", "display_name": "Sarah", "email": "sarah@example.com", "active": True},
                {"account_id": "mock_mike", "display_name": "Mike", "email": "mike@example.com", "active": True},
                {"account_id": "mock_lisa", "display_name": "Lisa", "email": "lisa@example.com", "active": True},
            ]
        
        try:
            client = self._get_client()
            # Use user search API to get all accessible users
            response = await client.get(
                "/rest/api/3/users/search",
                params={"maxResults": 50}  # Limit to 50 users
            )
            
            if response.status_code != 200:
                print(f"JIRA users API error: {response.status_code}")
                return []
            
            users_data = response.json()
            users = []
            
            for user in users_data:
                # Filter out system/app users (they don't have email usually)
                account_type = user.get("accountType", "")
                if account_type == "atlassian":  # Real human users
                    users.append({
                        "account_id": user.get("accountId"),
                        "display_name": user.get("displayName"),
                        "email": user.get("emailAddress"),
                        "active": user.get("active", True),
                    })
            
            return users
        except Exception as e:
            print(f"Error fetching JIRA users: {e}")
            return []
    
    async def get_user_issues(self, username: str) -> JiraUserActivity:
        """
        Get all issues assigned to a user.
        
        Args:
            username: The username/display name to look up (case-insensitive)
            
        Returns:
            JiraUserActivity with issues or error message
        """
        username_lower = username.lower().strip()
        
        if self._use_mock:
            return await self._get_mock_issues(username_lower)
        else:
            try:
                return await self._get_real_issues(username_lower)
            except Exception as e:
                # Fallback to mock on error
                print(f"JIRA API error, falling back to mock: {e}")
                result = await self._get_mock_issues(username_lower)
                result.error = f"API error (using mock): {str(e)}"
                return result
    
    async def _get_mock_issues(self, username: str) -> JiraUserActivity:
        """Return mock data for testing."""
        
        if username not in MOCK_JIRA_DATA:
            return JiraUserActivity(
                username=username,
                issues=[],
                total_count=0,
                error=f"User '{username}' not found in JIRA",
                is_real_data=False,
            )
        
        issues = [
            JiraIssue(
                key=issue["key"],
                summary=issue["summary"],
                status=issue["status"],
                priority=issue["priority"],
                issue_type=issue["issue_type"],
                updated=issue["updated"],
                assignee=username,
            )
            for issue in MOCK_JIRA_DATA[username]
        ]
        
        return JiraUserActivity(
            username=username,
            issues=issues,
            total_count=len(issues),
            is_real_data=False,
        )
    
    async def _get_real_issues(self, username: str) -> JiraUserActivity:
        """
        Fetch real issues from JIRA API.
        
        Uses JQL to search for issues where:
        - assignee matches the user
        - OR reporter/creator matches
        
        Note: JIRA Cloud requires accountId for reliable searches.
        We first look up the user, then search by accountId.
        Uses the new /rest/api/3/search/jql endpoint (old /search was deprecated).
        """
        client = self._get_client()
        
        # Step 1: Look up user by display name to get accountId
        user_response = await client.get(
            "/rest/api/3/user/search",
            params={"query": username, "maxResults": 5}
        )
        
        if user_response.status_code != 200:
            return JiraUserActivity(
                username=username,
                issues=[],
                total_count=0,
                error=f"Failed to search for user: {user_response.status_code}",
                is_real_data=True,
            )
        
        users = user_response.json()
        
        # Find exact or best match
        account_id = None
        for user in users:
            display_name = user.get("displayName", "").lower()
            if display_name == username.lower() or username.lower() in display_name:
                account_id = user.get("accountId")
                break
        
        if not account_id and users:
            # Use first result if no exact match
            account_id = users[0].get("accountId")
        
        if not account_id:
            return JiraUserActivity(
                username=username,
                issues=[],
                total_count=0,
                error=f"User '{username}' not found in JIRA",
                is_real_data=True,
            )
        
        # Step 2: Search issues by accountId
        jql = f'(assignee = "{account_id}" OR reporter = "{account_id}") ORDER BY updated DESC'
        
        # Use POST with JSON body for the new search/jql endpoint
        request_body = {
            "jql": jql,
            "maxResults": 20,
            "fields": ["key", "summary", "status", "priority", "issuetype", "updated", "assignee", "reporter"],
        }
        
        response = await client.post("/rest/api/3/search/jql", json=request_body)
        
        if response.status_code == 400:
            # JQL error - user might not exist or invalid query
            error_data = response.json()
            error_msg = error_data.get("errorMessages", ["Unknown error"])[0]
            return JiraUserActivity(
                username=username,
                issues=[],
                total_count=0,
                error=f"JIRA search error: {error_msg}",
                is_real_data=True,
            )
        
        if response.status_code != 200:
            raise Exception(f"JIRA API error: {response.status_code} - {response.text}")
        
        data = response.json()
        issues_data = data.get("issues", [])
        
        issues = []
        for issue in issues_data:
            fields = issue.get("fields", {})
            
            # Extract status name
            status = fields.get("status", {})
            status_name = status.get("name", "Unknown") if status else "Unknown"
            
            # Extract priority name
            priority = fields.get("priority", {})
            priority_name = priority.get("name", "Medium") if priority else "Medium"
            
            # Extract issue type
            issue_type = fields.get("issuetype", {})
            type_name = issue_type.get("name", "Task") if issue_type else "Task"
            
            # Extract assignee display name
            assignee = fields.get("assignee", {})
            assignee_name = assignee.get("displayName", username) if assignee else username
            
            # Parse updated timestamp
            updated_str = fields.get("updated", "")
            try:
                updated = datetime.fromisoformat(updated_str.replace("Z", "+00:00"))
            except:
                updated = datetime.now()
            
            issues.append(JiraIssue(
                key=issue.get("key", ""),
                summary=fields.get("summary", ""),
                status=status_name,
                priority=priority_name,
                issue_type=type_name,
                updated=updated,
                assignee=assignee_name,
                url=f"{self.base_url}/browse/{issue.get('key', '')}",
            ))
        
        return JiraUserActivity(
            username=username,
            issues=issues,
            total_count=data.get("total", len(issues)),
            is_real_data=True,
        )
    
    async def get_all_users(self) -> list[dict]:
        """
        Get all users that can be assigned issues.
        
        Useful for autocomplete and validation.
        """
        if self._use_mock:
            return [
                {"username": name, "displayName": name.title()}
                for name in MOCK_JIRA_DATA.keys()
            ]
        
        try:
            client = self._get_client()
            response = await client.get(
                "/rest/api/3/users/search",
                params={"maxResults": 50}
            )
            
            if response.status_code == 200:
                users = response.json()
                return [
                    {
                        "account_id": u.get("accountId"),
                        "display_name": u.get("displayName"),
                        "email": u.get("emailAddress"),
                        "active": u.get("active", True),
                    }
                    for u in users
                ]
            return []
        except:
            return []
    
    async def close(self):
        """Close the HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None


# =============================================================================
# Singleton Instance
# =============================================================================

_client: Optional[JiraClient] = None


def get_jira_client() -> JiraClient:
    """Get the JIRA client instance."""
    global _client
    if _client is None:
        from app.config import get_settings
        settings = get_settings()
        _client = JiraClient(
            base_url=settings.jira_base_url,
            email=settings.jira_email,
            api_token=settings.jira_api_token,
        )
    return _client


def reset_jira_client():
    """Reset the client (useful for testing or config changes)."""
    global _client
    _client = None
