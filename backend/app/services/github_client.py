"""
GitHub API Client - Supports both mock and real GitHub API.
"""

from datetime import datetime, timedelta
from typing import Optional
from pydantic import BaseModel
import httpx


# =============================================================================
# Response Models
# =============================================================================

class GitHubCommit(BaseModel):
    """A single commit."""
    sha: str                    # Short SHA (7 chars)
    message: str                # Commit message
    repo: str                   # Repository name
    date: datetime              # Commit timestamp
    additions: int = 0          # Lines added
    deletions: int = 0          # Lines removed


class GitHubPullRequest(BaseModel):
    """A pull request."""
    number: int                 # PR number
    title: str                  # PR title
    repo: str                   # Repository name
    state: str                  # "open", "closed", "merged"
    created_at: datetime
    updated_at: datetime
    url: str = ""               # Link to PR


class GitHubUserActivity(BaseModel):
    """All GitHub activity for a user."""
    username: str
    commits: list[GitHubCommit]
    pull_requests: list[GitHubPullRequest]
    active_repos: list[str]     # Repos user contributed to recently
    total_commits: int
    total_prs: int
    error: Optional[str] = None
    is_real_data: bool = False  # True if from real API


# =============================================================================
# Mock Data - Realistic GitHub activity (fallback)
# =============================================================================

MOCK_GITHUB_DATA: dict[str, dict] = {
    "john": {
        "commits": [
            {
                "sha": "a1b2c3d",
                "message": "feat: implement JWT token validation",
                "repo": "backend-api",
                "date": datetime.now() - timedelta(hours=3),
                "additions": 145,
                "deletions": 23,
            },
            {
                "sha": "e4f5g6h",
                "message": "fix: resolve token refresh race condition",
                "repo": "backend-api",
                "date": datetime.now() - timedelta(hours=8),
                "additions": 32,
                "deletions": 15,
            },
            {
                "sha": "i7j8k9l",
                "message": "test: add auth middleware unit tests",
                "repo": "backend-api",
                "date": datetime.now() - timedelta(days=1),
                "additions": 89,
                "deletions": 0,
            },
        ],
        "pull_requests": [
            {
                "number": 234,
                "title": "Add OAuth2 authentication support",
                "repo": "backend-api",
                "state": "open",
                "created_at": datetime.now() - timedelta(days=2),
                "updated_at": datetime.now() - timedelta(hours=3),
            },
        ],
        "active_repos": ["backend-api", "shared-utils"],
    },
    "sarah": {
        "commits": [
            {
                "sha": "m1n2o3p",
                "message": "feat: add responsive dashboard grid layout",
                "repo": "frontend-app",
                "date": datetime.now() - timedelta(hours=2),
                "additions": 234,
                "deletions": 45,
            },
            {
                "sha": "q4r5s6t",
                "message": "style: update color palette for dark mode",
                "repo": "frontend-app",
                "date": datetime.now() - timedelta(hours=6),
                "additions": 67,
                "deletions": 52,
            },
            {
                "sha": "u7v8w9x",
                "message": "refactor: extract chart components",
                "repo": "frontend-app",
                "date": datetime.now() - timedelta(days=1),
                "additions": 312,
                "deletions": 189,
            },
            {
                "sha": "y1z2a3b",
                "message": "perf: optimize re-renders in data table",
                "repo": "frontend-app",
                "date": datetime.now() - timedelta(days=2),
                "additions": 28,
                "deletions": 41,
            },
        ],
        "pull_requests": [
            {
                "number": 189,
                "title": "Redesign dashboard with new UI components",
                "repo": "frontend-app",
                "state": "open",
                "created_at": datetime.now() - timedelta(days=3),
                "updated_at": datetime.now() - timedelta(hours=2),
            },
            {
                "number": 185,
                "title": "Fix chart rendering on mobile devices",
                "repo": "frontend-app",
                "state": "merged",
                "created_at": datetime.now() - timedelta(days=5),
                "updated_at": datetime.now() - timedelta(days=2),
            },
        ],
        "active_repos": ["frontend-app", "design-system"],
    },
    "mike": {
        "commits": [
            {
                "sha": "c4d5e6f",
                "message": "ci: add automated deployment to staging",
                "repo": "infra-config",
                "date": datetime.now() - timedelta(hours=5),
                "additions": 156,
                "deletions": 12,
            },
            {
                "sha": "g7h8i9j",
                "message": "fix: resolve container memory limits",
                "repo": "worker-service",
                "date": datetime.now() - timedelta(hours=12),
                "additions": 8,
                "deletions": 3,
            },
            {
                "sha": "k1l2m3n",
                "message": "docs: update deployment runbook",
                "repo": "infra-config",
                "date": datetime.now() - timedelta(days=1),
                "additions": 89,
                "deletions": 23,
            },
        ],
        "pull_requests": [
            {
                "number": 56,
                "title": "Implement blue-green deployment strategy",
                "repo": "infra-config",
                "state": "merged",
                "created_at": datetime.now() - timedelta(days=4),
                "updated_at": datetime.now() - timedelta(days=1),
            },
            {
                "number": 78,
                "title": "Debug memory leak in worker pods",
                "repo": "worker-service",
                "state": "open",
                "created_at": datetime.now() - timedelta(hours=6),
                "updated_at": datetime.now() - timedelta(hours=3),
            },
        ],
        "active_repos": ["infra-config", "worker-service", "monitoring-stack"],
    },
    "lisa": {
        "commits": [
            {
                "sha": "o4p5q6r",
                "message": "docs: add OpenAPI specs for v2 endpoints",
                "repo": "backend-api",
                "date": datetime.now() - timedelta(hours=1),
                "additions": 445,
                "deletions": 0,
            },
            {
                "sha": "s7t8u9v",
                "message": "feat: implement Stripe webhook handler",
                "repo": "payment-service",
                "date": datetime.now() - timedelta(days=1),
                "additions": 234,
                "deletions": 12,
            },
            {
                "sha": "w1x2y3z",
                "message": "test: add payment flow integration tests",
                "repo": "payment-service",
                "date": datetime.now() - timedelta(days=2),
                "additions": 178,
                "deletions": 0,
            },
        ],
        "pull_requests": [
            {
                "number": 312,
                "title": "Add comprehensive API documentation",
                "repo": "backend-api",
                "state": "open",
                "created_at": datetime.now() - timedelta(days=1),
                "updated_at": datetime.now() - timedelta(hours=1),
            },
            {
                "number": 89,
                "title": "Implement webhook notification system",
                "repo": "payment-service",
                "state": "open",
                "created_at": datetime.now() - timedelta(days=3),
                "updated_at": datetime.now() - timedelta(days=1),
            },
        ],
        "active_repos": ["backend-api", "payment-service"],
    },
}

# User with no recent activity (for testing edge case)
MOCK_GITHUB_DATA["inactive_user"] = {
    "commits": [],
    "pull_requests": [],
    "active_repos": [],
}


# =============================================================================
# GitHub Client Class
# =============================================================================

class GitHubClient:
    """
    Client for fetching GitHub data.
    
    Supports both mock data and real GitHub API.
    Uses personal access token for authentication.
    """
    
    BASE_URL = "https://api.github.com"
    
    def __init__(self, token: str = ""):
        """
        Initialize GitHub client.
        
        Args:
            token: GitHub personal access token
        """
        self.token = token
        # Use real API if token is provided, otherwise use mock
        self._use_mock = not bool(token)
        self._client: Optional[httpx.AsyncClient] = None
    
    def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client with auth headers."""
        if self._client is None:
            headers = {
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": "2022-11-28",
            }
            if self.token:
                headers["Authorization"] = f"Bearer {self.token}"
            
            self._client = httpx.AsyncClient(
                base_url=self.BASE_URL,
                headers=headers,
                timeout=30.0,
            )
        return self._client
    
    async def test_connection(self) -> dict:
        """
        Test GitHub API connection and authentication.
        
        Returns:
            Dict with connection status and user info
        """
        if not self.token:
            return {
                "connected": False,
                "authenticated": False,
                "error": "No GitHub token configured",
                "using_mock": True,
            }
        
        try:
            client = self._get_client()
            response = await client.get("/user")
            
            if response.status_code == 200:
                user_data = response.json()
                return {
                    "connected": True,
                    "authenticated": True,
                    "user": user_data.get("login"),
                    "name": user_data.get("name"),
                    "rate_limit_remaining": response.headers.get("x-ratelimit-remaining"),
                    "using_mock": False,
                }
            elif response.status_code == 401:
                return {
                    "connected": True,
                    "authenticated": False,
                    "error": "Invalid or expired token",
                    "using_mock": True,
                }
            else:
                return {
                    "connected": False,
                    "authenticated": False,
                    "error": f"GitHub API returned {response.status_code}",
                    "using_mock": True,
                }
        except Exception as e:
            return {
                "connected": False,
                "authenticated": False,
                "error": str(e),
                "using_mock": True,
            }
    
    async def get_user_activity(self, username: str) -> GitHubUserActivity:
        """
        Get recent activity for a GitHub user.
        
        Args:
            username: GitHub username (case-insensitive)
            
        Returns:
            GitHubUserActivity with commits, PRs, and repos
        """
        username_lower = username.lower().strip()
        
        if self._use_mock:
            return await self._get_mock_activity(username_lower)
        else:
            try:
                return await self._get_real_activity(username_lower)
            except Exception as e:
                # Fallback to mock on error
                print(f"GitHub API error, falling back to mock: {e}")
                result = await self._get_mock_activity(username_lower)
                result.error = f"API error (using mock): {str(e)}"
                return result
    
    async def _get_mock_activity(self, username: str) -> GitHubUserActivity:
        """Return mock data for testing."""
        
        if username not in MOCK_GITHUB_DATA:
            return GitHubUserActivity(
                username=username,
                commits=[],
                pull_requests=[],
                active_repos=[],
                total_commits=0,
                total_prs=0,
                error=f"User '{username}' not found on GitHub",
                is_real_data=False,
            )
        
        data = MOCK_GITHUB_DATA[username]
        
        commits = [
            GitHubCommit(
                sha=c["sha"],
                message=c["message"],
                repo=c["repo"],
                date=c["date"],
                additions=c.get("additions", 0),
                deletions=c.get("deletions", 0),
            )
            for c in data["commits"]
        ]
        
        prs = [
            GitHubPullRequest(
                number=pr["number"],
                title=pr["title"],
                repo=pr["repo"],
                state=pr["state"],
                created_at=pr["created_at"],
                updated_at=pr["updated_at"],
            )
            for pr in data["pull_requests"]
        ]
        
        return GitHubUserActivity(
            username=username,
            commits=commits,
            pull_requests=prs,
            active_repos=data["active_repos"],
            total_commits=len(commits),
            total_prs=len(prs),
            is_real_data=False,
        )
    
    async def _get_real_activity(self, username: str) -> GitHubUserActivity:
        """
        Fetch real activity from GitHub API.
        
        Uses multiple endpoints:
        - /users/{username} - verify user exists
        - /users/{username}/events - recent activity (commits via PushEvents)
        - /search/issues - pull requests
        """
        client = self._get_client()
        
        # Step 1: Verify user exists
        user_response = await client.get(f"/users/{username}")
        if user_response.status_code == 404:
            return GitHubUserActivity(
                username=username,
                commits=[],
                pull_requests=[],
                active_repos=[],
                total_commits=0,
                total_prs=0,
                error=f"User '{username}' not found on GitHub",
                is_real_data=True,
            )
        elif user_response.status_code != 200:
            raise Exception(f"GitHub API error: {user_response.status_code}")
        
        # Step 2: Fetch recent events (includes push events with commits)
        events_response = await client.get(
            f"/users/{username}/events",
            params={"per_page": 100}  # Get more events to find commits
        )
        
        commits: list[GitHubCommit] = []
        active_repos: set[str] = set()
        
        if events_response.status_code == 200:
            events = events_response.json()
            
            for event in events:
                repo_name = event.get("repo", {}).get("name", "").split("/")[-1]
                
                # Extract commits from PushEvents
                if event.get("type") == "PushEvent":
                    payload = event.get("payload", {})
                    event_commits = payload.get("commits", [])
                    
                    for commit in event_commits[:5]:  # Limit commits per push
                        commits.append(GitHubCommit(
                            sha=commit.get("sha", "")[:7],
                            message=commit.get("message", "").split("\n")[0],  # First line
                            repo=repo_name,
                            date=datetime.fromisoformat(
                                event.get("created_at", "").replace("Z", "+00:00")
                            ),
                        ))
                        active_repos.add(repo_name)
                
                # Track repos from other events
                elif event.get("type") in ["PullRequestEvent", "IssuesEvent", "CreateEvent"]:
                    active_repos.add(repo_name)
        
        # Step 3: Fetch pull requests via search API
        prs_response = await client.get(
            "/search/issues",
            params={
                "q": f"author:{username} type:pr",
                "sort": "updated",
                "order": "desc",
                "per_page": 20,
            }
        )
        
        pull_requests: list[GitHubPullRequest] = []
        
        if prs_response.status_code == 200:
            prs_data = prs_response.json()
            
            for pr in prs_data.get("items", []):
                # Extract repo name from URL
                repo_url = pr.get("repository_url", "")
                repo_name = repo_url.split("/")[-1] if repo_url else "unknown"
                
                # Determine state (open, closed, or merged)
                state = pr.get("state", "open")
                if state == "closed" and pr.get("pull_request", {}).get("merged_at"):
                    state = "merged"
                
                pull_requests.append(GitHubPullRequest(
                    number=pr.get("number", 0),
                    title=pr.get("title", ""),
                    repo=repo_name,
                    state=state,
                    created_at=datetime.fromisoformat(
                        pr.get("created_at", "").replace("Z", "+00:00")
                    ),
                    updated_at=datetime.fromisoformat(
                        pr.get("updated_at", "").replace("Z", "+00:00")
                    ),
                    url=pr.get("html_url", ""),
                ))
                active_repos.add(repo_name)
        
        # Sort and limit results
        commits = sorted(commits, key=lambda c: c.date, reverse=True)[:10]
        pull_requests = sorted(pull_requests, key=lambda p: p.updated_at, reverse=True)[:10]
        
        return GitHubUserActivity(
            username=username,
            commits=commits,
            pull_requests=pull_requests,
            active_repos=list(active_repos)[:10],
            total_commits=len(commits),
            total_prs=len(pull_requests),
            is_real_data=True,
        )
    
    async def close(self):
        """Close the HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None


# =============================================================================
# Singleton Instance
# =============================================================================

_client: Optional[GitHubClient] = None


def get_github_client() -> GitHubClient:
    """Get the GitHub client instance."""
    global _client
    if _client is None:
        from app.config import get_settings
        settings = get_settings()
        _client = GitHubClient(token=settings.github_token)
    return _client


def reset_github_client():
    """Reset the client (useful for testing or config changes)."""
    global _client
    _client = None
