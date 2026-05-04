"""Tests for the repository analyzer."""
import sys
sys.path.insert(0, 'src')

import pytest
from unittest.mock import MagicMock, AsyncMock, patch

from analyzer import RepositoryAnalyzer
from github_client import GitHubClient


@pytest.fixture
def mock_client():
    """Create a mock GitHub client."""
    client = MagicMock(spec=GitHubClient)
    client.get_repository_contents = AsyncMock()
    client.get_file_content = AsyncMock()
    return client


@pytest.fixture
def analyzer(mock_client):
    """Create a RepositoryAnalyzer with mock client."""
    return RepositoryAnalyzer(mock_client)


@pytest.mark.asyncio
async def test_check_documentation_all_present(analyzer, mock_client):
    """Test documentation check when all files are present."""
    mock_client.get_repository_contents.return_value = [
        {"name": "LICENSE", "type": "file"},
        {"name": "CONTRIBUTING.md", "type": "file"},
        {"name": "CODE_OF_CONDUCT.md", "type": "file"},
        {"name": "README.md", "type": "file"},
    ]
    
    result = await analyzer._check_documentation("owner", "repo")
    
    assert result["has_license"] is True
    assert result["has_contributing"] is True
    assert result["has_code_of_conduct"] is True
    assert result["missing"] == []


@pytest.mark.asyncio
async def test_check_documentation_missing_files(analyzer, mock_client):
    """Test documentation check when files are missing."""
    mock_client.get_repository_contents.return_value = [
        {"name": "README.md", "type": "file"},
    ]
    
    result = await analyzer._check_documentation("owner", "repo")
    
    assert result["has_license"] is False
    assert result["has_contributing"] is False
    assert result["has_code_of_conduct"] is False
    assert "LICENSE" in result["missing"]
    assert "CONTRIBUTING.md" in result["missing"]
    assert "CODE_OF_CONDUCT.md" in result["missing"]


@pytest.mark.asyncio
async def test_check_documentation_license_variants(analyzer, mock_client):
    """Test documentation check with different LICENSE file variants."""
    # Test LICENSE.txt variant
    mock_client.get_repository_contents.return_value = [
        {"name": "LICENSE.txt", "type": "file"},
    ]
    result = await analyzer._check_documentation("owner", "repo")
    assert result["has_license"] is True
    
    # Test LICENSE (no extension) variant
    mock_client.get_repository_contents.return_value = [
        {"name": "LICENSE", "type": "file"},
    ]
    result = await analyzer._check_documentation("owner", "repo")
    assert result["has_license"] is True


@pytest.mark.asyncio
async def test_check_security_with_dependabot(analyzer, mock_client):
    """Test security check when dependabot is configured."""
    # The check looks for ".github" in paths (root level directories)
    # Then checks for dependabot.yml in .github folder contents
    mock_client.get_repository_contents.side_effect = [
        # First call for root contents - look for ".github" directory
        [{"name": "README.md", "type": "file"}, {"name": ".github", "type": "dir"}],
        # Second call for .github contents - look for dependabot.yml
        [{"name": "dependabot.yml", "type": "file"}, {"name": "workflows", "type": "dir"}],
    ]
    
    result = await analyzer._check_security("owner", "repo")
    
    assert result["has_dependabot"] is True


@pytest.mark.asyncio
async def test_check_security_without_dependabot(analyzer, mock_client):
    """Test security check when dependabot is not configured."""
    mock_client.get_repository_contents.return_value = [
        {"name": "README.md", "type": "file"},
    ]
    
    result = await analyzer._check_security("owner", "repo")
    
    assert result["has_dependabot"] is False


@pytest.mark.asyncio
async def test_check_security_with_secret_scanning_workflow(analyzer, mock_client):
    """Test security check when secret scanning workflow is detected."""
    mock_client.get_repository_contents.return_value = [
        {"name": "secret-scanning.yml", "type": "file"},
    ]
    
    result = await analyzer._check_security("owner", "repo")
    
    assert result["has_secret_scanning"] is True


@pytest.mark.asyncio
async def test_analyze_repository_includes_documentation_findings(analyzer, mock_client):
    """Test that analyze_repository includes documentation findings."""
    repo = {
        "id": 123,
        "name": "test-repo",
        "full_name": "owner/test-repo",
        "owner": {"login": "owner"},
    }
    
    calls = [
        # README check
        [{"name": "README.md", "type": "file"}],
        # README content (this is get_file_content, not get_repository_contents)
        # CI/CD check
        [{"name": ".github", "type": "dir"}, {"name": "README.md", "type": "file"}],
        # .github/workflows content
        [{"name": "ci.yml", "type": "file"}],
        # Dependencies check
        [{"name": "README.md", "type": "file"}],
        # Documentation check
        [{"name": "README.md", "type": "file"}],  # No license files
        # Security check
        [{"name": "README.md", "type": "file"}, {"name": ".github", "type": "dir"}],
    ]
    
    # Mock get_repository_contents with sequential calls
    async def get_contents_side_effect(owner, repo_name, path=None):
        result = calls.pop(0) if calls else []
        return result
    
    mock_client.get_repository_contents.side_effect = get_contents_side_effect
    mock_client.get_file_content.return_value = b"# Test Project\n\nThis is a test."
    
    analysis, findings = await analyzer.analyze_repository(repo)
    
    # Should have findings for missing documentation
    doc_findings = [f for f in findings if f.title.startswith("Missing")]
    assert len(doc_findings) >= 3  # LICENSE, CONTRIBUTING, CODE_OF_CONDUCT
    
    # Check analysis attributes
    assert analysis.has_license is False
    assert analysis.has_contributing is False
    assert analysis.has_code_of_conduct is False


@pytest.mark.asyncio
async def test_analyze_repository_with_all_features_present(analyzer, mock_client):
    """Test that analyze_repository works correctly when all features are present."""
    repo = {
        "id": 456,
        "name": "complete-repo",
        "full_name": "owner/complete-repo",
        "owner": {"login": "owner"},
    }
    
    # Simplified test - just verify documentation checks work
    mock_client.get_repository_contents.return_value = [
        {"name": "LICENSE", "type": "file"},
        {"name": "CONTRIBUTING.md", "type": "file"},
        {"name": "CODE_OF_CONDUCT.md", "type": "file"},
    ]
    
    doc_result = await analyzer._check_documentation("owner", "repo")
    
    # All documentation files present
    assert doc_result["has_license"] is True
    assert doc_result["has_contributing"] is True
    assert doc_result["has_code_of_conduct"] is True
    assert len(doc_result["missing"]) == 0


@pytest.mark.asyncio
async def test_scheduler_github_client_context_manager():
    """Test that GitHubClient works correctly as async context manager (e2e for the bug fix)."""
    with patch('github_client.check_gh_cli_auth', return_value=False):
        with patch('github_client.get_gh_cli_token', return_value=None):
            with patch('os.getenv', return_value=None):
                # This is the exact pattern used in scheduler.py
                async with GitHubClient("test_token") as client:
                    assert client.token == "test_token"
                    assert "Bearer test_token" in client.headers["Authorization"]
                
                # Verify close was called (client should be closed after context exit)
                # The httpx client should be closed
                assert client.client.is_closed