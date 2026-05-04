"""ghAuto CLI - Command line interface for GitHub repository management."""
import os
import subprocess
import sys
from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from db import get_session, init_db
from scheduler import AnalysisScheduler
from github_client import GitHubClient
from gh_cli import (
    get_gh_cli_token,
    check_gh_cli_auth,
    get_gh_cli_username,
    get_gh_cli_token_with_scope,
    ensure_required_scopes,
    recommend_scope_fix,
)

# Version
__version__ = "0.2.2"

# Configuration directory
CONFIG_DIR = Path.home() / ".ghauto"
CONFIG_FILE = CONFIG_DIR / "config.yaml"
DB_FILE = CONFIG_DIR / "data" / "ghauto.db"

console = Console()
app = typer.Typer(
    name="ghAuto",
    help="GitHub Repository Management and Analysis Tool",
)


def get_github_token() -> str | None:
    """Get GitHub token from environment, config, or gh CLI."""
    # Check environment first
    token = os.getenv("GITHUB_TOKEN")
    if token:
        return token
    
    # Check gh CLI
    if check_gh_cli_auth():
        gh_token = get_gh_cli_token()
        if gh_token:
            return gh_token
    
    # Check config file
    if CONFIG_FILE.exists():
        import yaml
        config = yaml.safe_load(CONFIG_FILE.read_text())
        return config.get("github", {}).get("token")
    
    return None


def get_github_username() -> str | None:
    """Get GitHub username from environment, config, or gh CLI."""
    # Check environment first
    username = os.getenv("GITHUB_USERNAME")
    if username:
        return username
    
    # Check config file
    if CONFIG_FILE.exists():
        import yaml
        config = yaml.safe_load(CONFIG_FILE.read_text())
        username = config.get("github", {}).get("username")
        if username:
            return username
    
    # Check gh CLI
    if check_gh_cli_auth():
        return get_gh_cli_username()
    
    return None


@app.command()
def init(
    token: str = typer.Option(None, "--token", "-t", help="GitHub Personal Access Token"),
    username: str = typer.Option(None, "--username", "-u", help="GitHub username"),
    force: bool = typer.Option(False, "--force", "-f", help="Overwrite existing config"),
):
    """Initialize ghAuto configuration."""
    console.print(Panel("🚀 Initializing ghAuto", style="bold blue"))
    
    if CONFIG_FILE.exists() and not force:
        console.print("[yellow]Config already exists. Use --force to overwrite.[/yellow]")
        return
    
    # Create config directory
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    (CONFIG_DIR / "data").mkdir(parents=True, exist_ok=True)
    
    # Check for gh CLI authentication
    gh_cli_auth = check_gh_cli_auth()
    if gh_cli_auth:
        console.print("[green]✓[/green] gh CLI authenticated")
    
    # Get token - prioritize gh CLI
    if not token:
        if gh_cli_auth:
            token_info = get_gh_cli_token_with_scope()
            if token_info["token"]:
                token = token_info["token"]
                console.print("[green]✓[/green] Using token from gh CLI")
                if token_info["scopes"]:
                    scopes_ok = ensure_required_scopes(token_info["scopes"])
                    if not scopes_ok:
                        console.print("[yellow]⚠[/yellow] Token may be missing required scopes")
                        console.print(f"  {recommend_scope_fix()}")
        else:
            token = typer.prompt("Enter GitHub Personal Access Token", hide_input=True)
    
    # Get username - try gh CLI if not provided
    if not username:
        username = get_github_username()
        if not username:
            username = typer.prompt("Enter GitHub username")
    
    # Create config file
    config_content = f"""# ghAuto Configuration
version: 1

github:
  username: {username}
  token: {token}

schedule:
  interval_hours: 24

dashboard:
  port: 3000
"""
    CONFIG_FILE.write_text(config_content)
    
    # Initialize database
    init_db(str(DB_FILE))
    
    console.print(f"[green]✓[/green] Configuration created at {CONFIG_FILE}")
    console.print(f"[green]✓[/green] Database initialized at {DB_FILE}")
    console.print("\n[bold]Next steps:[/bold]")
    console.print("  ghauto analyze  - Run initial analysis")
    console.print("  ghauto serve    - Start the dashboard")


@app.command()
def analyze(
    username: str = typer.Option(None, "--username", "-u", help="GitHub username"),
    orgs: str = typer.Option(None, "--orgs", "-o", help="Comma-separated organizations"),
    once: bool = typer.Option(True, "--once", help="Run once without scheduling"),
):
    """Run repository analysis."""
    import asyncio
    
    token = get_github_token()
    user = username or get_github_username()
    
    if not token:
        console.print("[red]Error:[/red] GITHUB_TOKEN not set")
        raise typer.Exit(1)
    
    if not user:
        console.print("[red]Error:[/red] GITHUB_USERNAME not set")
        raise typer.Exit(1)
    
    org_list = [o.strip() for o in orgs.split(",")] if orgs else None
    
    console.print(Panel(f"🔍 Analyzing repositories for {user}", style="bold blue"))
    
    scheduler = AnalysisScheduler(github_token=token, db_path=str(DB_FILE))
    
    with console.status("[spinner]Running analysis..."):
        asyncio.run(scheduler.run_analysis_job(user, org_list))
    
    # Show results
    session = get_session(str(DB_FILE))
    from db import Finding, Repository
    
    repo_count = session.query(Repository).count()
    finding_count = session.query(Finding).count()
    
    console.print(f"\n[green]✓[/green] Analysis complete!")
    console.print(f"  Repositories analyzed: {repo_count}")
    console.print(f"  Findings: {finding_count}")


@app.command()
def daemon(
    interval: int = typer.Option(24, "--interval", "-i", help="Analysis interval in hours"),
    once: bool = typer.Option(False, "--once", help="Run once and exit"),
    start_daemon: bool = typer.Option(False, "--start", help="Start background daemon"),
):
    """Run repository analysis daemon for periodic checks."""
    import asyncio
    
    token = get_github_token()
    user = get_github_username()
    
    if not token:
        console.print("[red]Error:[/red] No GitHub token available. Run 'ghauto init' first.")
        raise typer.Exit(1)
    
    if not user:
        console.print("[red]Error:[/red] No GitHub username configured. Run 'ghauto init' first.")
        raise typer.Exit(1)
    
    console.print(Panel(f"🤖 ghAuto Daemon for {user}", style="bold blue"))
    
    scheduler = AnalysisScheduler(github_token=token, db_path=str(DB_FILE))
    
    if once:
        # Run once and exit
        asyncio.run(scheduler.run_once(user))
        console.print("[green]✓[/green] One-time analysis complete")
    elif start_daemon:
        # Start background daemon
        scheduler.run_once(user)  # Initial run
        scheduler.start(user, interval_hours=interval)
        
        console.print(f"[green]✓[/green] Daemon started with {interval}h interval")
        console.print("[green]✓[/green] Initial analysis complete")
        console.print("\nPress Ctrl+C to stop")
        
        try:
            asyncio.get_event_loop().run_forever()
        except KeyboardInterrupt:
            scheduler.stop()
            console.print("\n[yellow]Daemon stopped[/yellow]")
    else:
        # Default: run once with option to start daemon
        console.print("Use --once to run once, or --start to start daemon")


@app.command()
def serve(
    host: str = typer.Option("0.0.0.0", "--host", "-h"),
    port: int = typer.Option(8000, "--port", "-p"),
    dashboard_port: int = typer.Option(3000, "--dashboard-port"),
):
    """Start the dashboard and API server."""
    import subprocess
    import threading
    import time
    
    console.print(Panel("🌐 Starting ghAuto servers", style="bold blue"))
    
    # Start API server
    console.print(f"[green]✓[/green] Starting API server on {host}:{port}")
    
    # Start dashboard if npm is available
    dashboard_path = Path(__file__).parent.parent / "dashboard"
    if dashboard_path.exists():
        console.print(f"[green]✓[/green] Starting dashboard on port {dashboard_port}")
    
    console.print("\nPress Ctrl+C to stop")
    
    try:
        import uvicorn
        uvicorn.run("api:app", host=host, port=port)
    except KeyboardInterrupt:
        console.print("\n[yellow]Shutting down...[/yellow]")


@app.command()
def doctor():
    """Check system health and configuration."""
    console.print(Panel("🏥 ghAuto Doctor", style="bold blue"))
    
    table = Table(title="System Status")
    table.add_column("Check", style="cyan")
    table.add_column("Status", style="bold")
    
    # Check gh CLI
    gh_cli_installed = False
    gh_cli_auth = False
    try:
        import subprocess
        result = subprocess.run(["gh", "--version"], capture_output=True, timeout=5)
        gh_cli_installed = result.returncode == 0
        if gh_cli_installed:
            gh_cli_auth = check_gh_cli_auth()
    except Exception:
        pass
    
    table.add_row("gh CLI installed", "[green]✓ Yes[/green]" if gh_cli_installed else "[yellow]✗ No[/yellow]")
    table.add_row("gh CLI authenticated", "[green]✓ Yes[/green]" if gh_cli_auth else "[red]✗ No[/red]")
    
    # Check config
    config_ok = CONFIG_FILE.exists()
    table.add_row("Config file", "[green]✓ OK[/green]" if config_ok else "[red]✗ Missing[/red]")
    
    # Check database
    db_ok = DB_FILE.exists()
    table.add_row("Database", "[green]✓ OK[/green]" if db_ok else "[red]✗ Missing[/red]")
    
    # Check token
    token = get_github_token()
    table.add_row("GitHub Token", "[green]✓ Set[/green]" if token else "[red]✗ Not set[/red]")
    
    # Check username
    user = get_github_username()
    table.add_row("GitHub Username", "[green]✓ Set[/green]" if user else "[red]✗ Not set[/red]")
    
    console.print(table)
    
    if db_ok:
        session = get_session(str(DB_FILE))
        from db import Finding, Repository
        repo_count = session.query(Repository).count()
        finding_count = session.query(Finding).count()
        
        console.print(f"\n[bold]Statistics:[/bold]")
        console.print(f"  Repositories tracked: {repo_count}")
        console.print(f"  Findings recorded: {finding_count}")
    
    # Show recommendation if gh CLI auth is missing
    if gh_cli_installed and not gh_cli_auth:
        console.print("\n[yellow]Recommendation:[/yellow] Run 'gh auth login' to authenticate gh CLI")
    elif not gh_cli_installed:
        console.print("\n[yellow]Recommendation:[/yellow] Install gh CLI from https://cli.github.com")


@app.command()
def config(
    show: bool = typer.Option(False, "--show", help="Show current configuration"),
    reset: bool = typer.Option(False, "--reset", help="Reset configuration"),
):
    """Manage configuration."""
    if show:
        if CONFIG_FILE.exists():
            console.print(CONFIG_FILE.read_text())
        else:
            console.print("[yellow]No configuration found. Run 'ghauto init' first.[/yellow]")
    
    if reset:
        if CONFIG_FILE.exists():
            CONFIG_FILE.unlink()
            console.print("[green]✓ Configuration reset[/green]")
        else:
            console.print("[yellow]No configuration to reset[/yellow]")


@app.callback(invoke_without_command=True)
def main_callback(
    ctx: typer.Context,
    version: bool = typer.Option(False, "--version", "-v", help="Show version and exit"),
):
    """ghAuto - GitHub Repository Management and Analysis Tool."""
    if version:
        console.print(f"ghAuto {__version__}")
        raise typer.Exit()
    
    # If no command is provided, show help
    if ctx.invoked_subcommand is None:
        console.print(ctx.get_help())


@app.command()
def version():
    """Show version information."""
    console.print(f"ghAuto {__version__}")


@app.command()
def update(
    force: bool = typer.Option(False, "--force", "-f", help="Force reinstall even if up to date"),
):
    """Update ghAuto to the latest version."""
    import shutil
    
    console.print(Panel("🔄 Updating ghAuto", style="bold blue"))
    
    GHAUTO_SRC = Path.home() / ".ghauto" / "src"
    
    if not GHAUTO_SRC.exists() or not (GHAUTO_SRC / ".git").exists():
        console.print("[yellow]ghAuto not installed via script. Use install script to update.[/yellow]")
        return
    
    try:
        # Pull latest changes
        result = subprocess.run(
            ["git", "pull"],
            cwd=GHAUTO_SRC,
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            console.print(f"[red]Failed to pull updates:[/red] {result.stderr}")
            raise typer.Exit(1)
        
        if "Already up to date" in result.stdout or "up to date" in result.stdout.lower():
            console.print("[green]✓ Already up to date[/green]")
        else:
            console.print("[green]✓ Updated to latest version[/green]")
        
        # Reinstall in case of dependency changes
        GHAUTO_VENV = Path.home() / ".ghauto" / "venv"
        if GHAUTO_VENV.exists():
            pip_path = GHAUTO_VENV / "bin" / "pip"
            if pip_path.exists():
                console.print("Reinstalling dependencies...")
                result = subprocess.run(
                    [str(pip_path), "install", "-e", str(GHAUTO_SRC), "--quiet"],
                    capture_output=True
                )
                if result.returncode == 0:
                    console.print("[green]✓ Dependencies updated[/green]")
                else:
                    console.print("[yellow]Warning: Failed to update dependencies[/yellow]")
        
        console.print("\n[bold]Update complete![/bold]")
        
    except subprocess.SubprocessError as e:
        console.print(f"[red]Update failed:[/red] {e}")
        raise typer.Exit(1)


if __name__ == "__main__":
    app()