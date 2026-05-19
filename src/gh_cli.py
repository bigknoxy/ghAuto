"""gh CLI integration for token discovery and command passthrough."""
import os
import platform
import subprocess
from pathlib import Path
from typing import Optional

import yaml


def get_gh_cli_config_path() -> Optional[Path]:
    """Get the path to gh CLI config file based on OS."""
    system = platform.system()
    
    if system == "Linux":
        # Check XDG_CONFIG_HOME first, then default
        xdg_config = os.environ.get("XDG_CONFIG_HOME")
        if xdg_config:
            path = Path(xdg_config) / "gh" / "hosts.yml"
            if path.exists():
                return path
        return Path.home() / ".config" / "gh" / "hosts.yml"
    elif system == "Darwin":  # macOS
        return Path.home() / "Library/Application Support/gh/hosts.yml"
    elif system == "Windows":
        return Path.home() / "AppData/Roaming/gh/hosts.yml"
    
    return None


def get_gh_cli_token() -> Optional[str]:
    """Extract GitHub token from gh CLI config.
    
    Works with both oauth_token and token fields in hosts.yml.
    Supports both personal tokens and fine-grained tokens.
    """
    config_path = get_gh_cli_config_path()
    if not config_path or not config_path.exists():
        return None
    
    try:
        with open(config_path) as f:
            config = yaml.safe_load(f)
        
        # Look for github.com section
        if "github.com" in config:
            host_config = config["github.com"]
            # oauth_token is the standard field
            token = host_config.get("oauth_token")
            if token:
                return token
            # token is an alternative field name
            token = host_config.get("token")
            if token:
                return token
        
        return None
    except (yaml.YAMLError, KeyError, IOError):
        return None


def is_gh_cli_installed() -> bool:
    """Check if gh CLI is installed and available in PATH."""
    try:
        result = subprocess.run(
            ["gh", "--version"],
            capture_output=True,
            text=True,
            timeout=5
        )
        return result.returncode == 0
    except (subprocess.SubprocessError, FileNotFoundError):
        return False


def get_gh_cli_username() -> Optional[str]:
    """Get the authenticated username from gh CLI."""
    try:
        result = subprocess.run(
            ["gh", "api", "user", "-q", ".login"],
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except (subprocess.SubprocessError, FileNotFoundError):
        pass
    return None


def check_gh_cli_auth() -> bool:
    """Check if gh CLI is authenticated."""
    if not is_gh_cli_installed():
        return False
    
    try:
        result = subprocess.run(
            ["gh", "auth", "status"],
            capture_output=True,
            text=True,
            timeout=10
        )
        return result.returncode == 0
    except (subprocess.SubprocessError, FileNotFoundError):
        return False


def get_gh_cli_token_with_scope() -> dict:
    """Get token and check its scopes.
    
    Returns dict with:
        - token: str | None
        - scopes: list[str]
        - host: str
    """
    token = get_gh_cli_token()
    if not token:
        return {"token": None, "scopes": [], "host": "github.com"}
    
    try:
        subprocess.run(
            ["gh", "api", "user", "-q", ".login"],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        # Get scopes from auth status
        auth_result = subprocess.run(
            ["gh", "auth", "status"],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        scopes = []
        if "Token scopes:" in auth_result.stdout:
            for line in auth_result.stdout.split("\n"):
                if "Token scopes:" in line:
                    # Extract scopes from line like "Token scopes: repo, read:org, ..."
                    scopes_str = line.split("Token scopes:")[1].strip()
                    scopes = [s.strip() for s in scopes_str.split(",")]
                    break
        
        return {
            "token": token,
            "scopes": scopes,
            "host": "github.com"
        }
    except (subprocess.SubprocessError, FileNotFoundError):
        return {"token": token, "scopes": [], "host": "github.com"}


def ensure_required_scopes(scopes: list[str]) -> bool:
    """Check if token has required scopes.
    
    Recommended minimum scopes for ghAuto:
    - repo: Full control of private repositories
    - read:org: Read org data (for organization analysis)
    - workflow: Update GitHub Actions
    """
    required = {"repo", "read:org", "workflow"}
    return bool(required.issubset(set(scopes)))


def recommend_scope_fix() -> str:
    """Return recommendation for fixing scopes."""
    return """To get the required scopes, run:
  gh auth refresh -s repo,read:org,workflow

Or re-authenticate with:
  gh auth logout
  gh auth login"""