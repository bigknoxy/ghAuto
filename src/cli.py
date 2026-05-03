"""ghAuto CLI - Command line interface for GitHub repository management."""
import os
import sys
from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from db import get_session, init_db
from scheduler import AnalysisScheduler
from github_client import GitHubClient

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
    """Get GitHub token from environment or config."""
    return os.getenv("GITHUB_TOKEN")


def get_github_username() -> str | None:
    """Get GitHub username from environment or config."""
    return os.getenv("GITHUB_USERNAME")


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
    
    # Get token
    if not token:
        token = get_github_token()
        if not token:
            token = typer.prompt("Enter GitHub Personal Access Token", hide_input=True)
    
    # Get username
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


if __name__ == "__main__":
    app()