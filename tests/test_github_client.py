"""Tests for the GitHub client."""
import sys
sys.path.insert(0, 'src')

import pytest

from github_client import GitHubClient


@pytest.mark.asyncio
async def test_github_client_init():
    """Test GitHub client initialization."""
    client = GitHubClient()
    assert client.token is None
    await client.close()


@pytest.mark.asyncio
async def test_github_client_with_token():
    """Test GitHub client with token."""
    client = GitHubClient(token="test_token")
    assert client.token == "test_token"
    assert "Bearer test_token" in client.headers["Authorization"]
    await client.close()