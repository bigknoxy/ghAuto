"""Tests for gh CLI integration."""
import sys
sys.path.insert(0, 'src')

from unittest.mock import patch, MagicMock
from pathlib import Path

from gh_cli import (
    get_gh_cli_config_path,
    get_gh_cli_token,
    is_gh_cli_installed,
    check_gh_cli_auth,
    get_gh_cli_username,
    get_gh_cli_token_with_scope,
    ensure_required_scopes,
)


class TestGetGhCliConfigPath:
    """Tests for config path detection."""
    
    def test_linux_path(self):
        """Test Linux config path detection."""
        with patch('platform.system', return_value='Linux'):
            with patch.dict('os.environ', {'XDG_CONFIG_HOME': ''}, clear=True):
                path = get_gh_cli_config_path()
                assert 'gh' in str(path)
                assert 'hosts.yml' in str(path)
    
    def test_macos_path(self):
        """Test macOS config path detection."""
        with patch('platform.system', return_value='Darwin'):
            path = get_gh_cli_config_path()
            assert 'Library/Application Support/gh' in str(path)
            assert 'hosts.yml' in str(path)
    
    def test_windows_path(self):
        """Test Windows config path detection."""
        with patch('platform.system', return_value='Windows'):
            path = get_gh_cli_config_path()
            assert 'AppData/Roaming/gh' in str(path)
            assert 'hosts.yml' in str(path)


class TestGetGhCliToken:
    """Tests for token extraction."""
    
    def test_no_config_file(self):
        """Test when config file doesn't exist."""
        with patch('gh_cli.get_gh_cli_config_path') as mock_path:
            mock_path.return_value = Path('/nonexistent/path')
            token = get_gh_cli_token()
            assert token is None
    
    def test_oauth_token(self):
        """Test extracting oauth_token from config."""
        mock_path = MagicMock()
        mock_path.exists.return_value = True
        
        with patch('gh_cli.get_gh_cli_config_path', return_value=mock_path):
            with patch('builtins.open', MagicMock()):
                import yaml
                with patch.object(yaml, 'safe_load', return_value={
                    'github.com': {'oauth_token': 'gho_testtoken123'}
                }):
                    token = get_gh_cli_token()
                    assert token == 'gho_testtoken123'
    
    def test_token_field(self):
        """Test extracting token field from config."""
        mock_path = MagicMock()
        mock_path.exists.return_value = True
        
        with patch('gh_cli.get_gh_cli_config_path', return_value=mock_path):
            import yaml
            with patch.object(yaml, 'safe_load', return_value={
                'github.com': {'token': 'ghp_testtoken456'}
            }):
                token = get_gh_cli_token()
                assert token == 'ghp_testtoken456'
    
    def test_no_token_in_config(self):
        """Test when no token in config."""
        with patch('gh_cli.get_gh_cli_config_path') as mock_path:
            mock_path.return_value = Path('/fake/path')
            with patch('builtins.open', MagicMock()):
                import yaml
                with patch.object(yaml, 'safe_load', return_value={
                    'github.com': {'user': 'test'}
                }):
                    token = get_gh_cli_token()
                    assert token is None


class TestIsGhCliInstalled:
    """Tests for gh CLI installation check."""
    
    def test_installed(self):
        """Test when gh is installed."""
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="gh version 2.0.0")
            assert is_gh_cli_installed() is True
    
    def test_not_installed(self):
        """Test when gh is not installed."""
        with patch('subprocess.run', side_effect=FileNotFoundError):
            assert is_gh_cli_installed() is False


class TestCheckGhCliAuth:
    """Tests for gh CLI authentication check."""
    
    def test_authenticated(self):
        """Test when gh CLI is authenticated."""
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="Logged in as testuser")
            assert check_gh_cli_auth() is True
    
    def test_not_authenticated(self):
        """Test when gh CLI is not authenticated."""
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(returncode=1, stdout="Not logged in")
            assert check_gh_cli_auth() is False


class TestGetGhCliUsername:
    """Tests for username retrieval."""
    
    def test_get_username(self):
        """Test successful username retrieval."""
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="testuser\n")
            username = get_gh_cli_username()
            assert username == "testuser"
    
    def test_get_username_failed(self):
        """Test when username retrieval fails."""
        with patch('subprocess.run', side_effect=FileNotFoundError):
            username = get_gh_cli_username()
            assert username is None


class TestGetGhCliTokenWithScope:
    """Tests for token with scope info."""
    
    def test_token_with_scopes(self):
        """Test token retrieval with scopes."""
        with patch('gh_cli.get_gh_cli_token', return_value='test_token'):
            with patch('subprocess.run') as mock_run:
                # Mock gh api user
                mock_run.side_effect = [
                    MagicMock(returncode=0, stdout="testuser\n"),
                    MagicMock(returncode=0, stdout="Token scopes: repo, read:org\n")
                ]
                result = get_gh_cli_token_with_scope()
                assert result['token'] == 'test_token'
                assert 'repo' in result['scopes']
    
    def test_no_token(self):
        """Test when no token available."""
        with patch('gh_cli.get_gh_cli_token', return_value=None):
            result = get_gh_cli_token_with_scope()
            assert result['token'] is None


class TestEnsureRequiredScopes:
    """Tests for scope checking."""
    
    def test_has_required_scopes(self):
        """Test when all required scopes are present."""
        scopes = ['repo', 'read:org', 'workflow', 'delete_repo']
        assert ensure_required_scopes(scopes) is True
    
    def test_missing_scopes(self):
        """Test when scopes are missing."""
        scopes = ['repo']
        assert ensure_required_scopes(scopes) is False
    
    def test_empty_scopes(self):
        """Test with empty scopes."""
        assert ensure_required_scopes([]) is False


class TestGhCliIntegration:
    """Integration tests for gh CLI with GitHubClient."""
    
    def test_client_uses_gh_cli_token(self):
        """Test that GitHubClient can use gh CLI token."""
        # Patch at module level before import
        with patch('gh_cli.check_gh_cli_auth', return_value=True):
            with patch('gh_cli.get_gh_cli_token', return_value='gh_test_token'):
                # Force reimport to pick up patches
                import importlib
                import github_client
                importlib.reload(github_client)
                GitHubClient = github_client.GitHubClient
                
                client = GitHubClient(use_gh_cli=True)
                assert client.token == 'gh_test_token'
                assert client.headers['Authorization'] == 'Bearer gh_test_token'
                import asyncio
                asyncio.run(client.close())
    
    def test_client_explicit_token_bypasses_gh_cli(self):
        """Test that explicit token takes priority."""
        with patch('gh_cli.check_gh_cli_auth', return_value=True):
            with patch('gh_cli.get_gh_cli_token', return_value='gh_token'):
                import importlib
                import github_client
                importlib.reload(github_client)
                GitHubClient = github_client.GitHubClient
                
                client = GitHubClient(token='explicit_token', use_gh_cli=True)
                assert client.token == 'explicit_token'
                import asyncio
                asyncio.run(client.close())
    
    def test_client_no_gh_cli_fallback(self):
        """Test that use_gh_cli=False skips gh CLI."""
        with patch('gh_cli.check_gh_cli_auth', return_value=True):
            with patch('gh_cli.get_gh_cli_token', return_value='gh_token'):
                import importlib
                import github_client
                importlib.reload(github_client)
                GitHubClient = github_client.GitHubClient
                
                client = GitHubClient(use_gh_cli=False)
                assert client.token is None
                import asyncio
                asyncio.run(client.close())