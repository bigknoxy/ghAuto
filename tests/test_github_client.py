"""Tests for the GitHub client."""
import sys
sys.path.insert(0, 'src')

import pytest
from unittest.mock import patch, MagicMock

# Patch gh_cli functions BEFORE importing GitHubClient
with patch('gh_cli.check_gh_cli_auth', return_value=False):
    with patch('gh_cli.get_gh_cli_token', return_value=None):
        with patch('os.getenv', return_value=None):
            from github_client import GitHubClient


@pytest.mark.asyncio
async def test_github_client_init():
    """Test GitHub client initialization."""
    with patch('gh_cli.check_gh_cli_auth', return_value=False):
        with patch('gh_cli.get_gh_cli_token', return_value=None):
            with patch('os.getenv', return_value=None):
                from github_client import GitHubClient as GC
                client = GC(use_gh_cli=False)
                assert client.token is None
                await client.close()


@pytest.mark.asyncio
async def test_github_client_with_token():
    """Test GitHub client with token."""
    client = GitHubClient(token="test_token")
    assert client.token == "test_token"
    assert "Bearer test_token" in client.headers["Authorization"]
    await client.close()


@pytest.mark.asyncio
async def test_github_client_async_context_manager():
    """Test GitHub client as async context manager."""
    async with GitHubClient(token="test_token") as client:
        assert client.token == "test_token"
        assert "Bearer test_token" in client.headers["Authorization"]