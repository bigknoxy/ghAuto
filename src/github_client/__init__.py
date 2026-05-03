"""GitHub API client module."""
import os
from typing import Any

import httpx


class GitHubClient:
    """Client for interacting with the GitHub API."""

    BASE_URL = "https://api.github.com"

    def __init__(self, token: str | None = None):
        self.token = token or os.getenv("GITHUB_TOKEN")
        self.headers = {
            "Accept": "application/vnd.github.v3+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }
        if self.token:
            self.headers["Authorization"] = f"Bearer {self.token}"

        self.client = httpx.AsyncClient(headers=self.headers, timeout=30.0)

    async def get(self, path: str, **kwargs) -> dict[str, Any] | list[Any]:
        """Make a GET request to the GitHub API."""
        url = f"{self.BASE_URL}{path}"
        response = await self.client.get(url, **kwargs)
        response.raise_for_status()
        return response.json()

    async def get_repository(self, owner: str, repo: str) -> dict[str, Any]:
        """Get repository details."""
        return await self.get(f"/repos/{owner}/{repo}")

    async def get_user_repositories(self, username: str, per_page: int = 100) -> list[dict]:
        """Get all repositories for a user."""
        repos = []
        page = 1
        while True:
            response = await self.get(
                f"/users/{username}/repos",
                params={"per_page": per_page, "page": page, "type": "all"},
            )
            if not response:
                break
            repos.extend(response)
            page += 1
        return repos

    async def get_organization_repositories(
        self, org: str, per_page: int = 100
    ) -> list[dict]:
        """Get all repositories for an organization."""
        repos = []
        page = 1
        while True:
            response = await self.get(
                f"/orgs/{org}/repos",
                params={"per_page": per_page, "page": page, "type": "all"},
            )
            if not response:
                break
            repos.extend(response)
            page += 1
        return repos

    async def get_repository_contents(
        self, owner: str, repo: str, path: str = ""
    ) -> list[dict] | dict:
        """Get repository file/directory contents."""
        return await self.get(f"/repos/{owner}/{repo}/contents/{path}")

    async def get_file_content(self, owner: str, repo: str, path: str) -> bytes | None:
        """Get raw file content."""
        try:
            result = await self.get(f"/repos/{owner}/{repo}/contents/{path}")
            import base64

            if isinstance(result, dict) and "content" in result:
                return base64.b64decode(result["content"])
        except httpx.HTTPStatusError:
            pass
        return None

    async def get_dependents(self, owner: str, repo: str) -> dict[str, Any]:
        """Get repository dependents (repositories that depend on this one)."""
        return await self.get(f"/repos/{owner}/{repo}/dependents")

    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()