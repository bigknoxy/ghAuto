"""Scheduler for periodic repository analysis."""
import asyncio
import logging
from datetime import datetime

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

from analyzer import RepositoryAnalyzer
from github_client import GitHubClient
from db import Finding, Opportunity, Repository, ScheduledRun, get_session, parse_github_datetime

logger = logging.getLogger(__name__)


class AnalysisScheduler:
    """Schedules and runs periodic repository analysis."""

    def __init__(self, github_token: str | None = None, db_path: str = "data/ghauto.db"):
        self.github_token = github_token
        self.db_path = db_path
        self.scheduler = AsyncIOScheduler()
        self._running = False

    async def run_analysis_job(self, username: str, organizations: list[str] | None = None):
        """Run a full analysis of all repositories."""
        session = get_session(self.db_path)
        run_record = ScheduledRun(status="running", started_at=datetime.utcnow())
        session.add(run_record)
        session.commit()

        findings_count = 0
        repos_analyzed = 0

        try:
            async with GitHubClient(self.github_token) as client:
                analyzer = RepositoryAnalyzer(client)

                # Get user repositories
                repos = await client.get_user_repositories(username)
                logger.info(f"Found {len(repos)} repositories for user {username}")

                # Get organization repositories if specified
                if organizations:
                    for org in organizations:
                        try:
                            org_repos = await client.get_organization_repositories(org)
                            repos.extend(org_repos)
                            logger.info(f"Found {len(org_repos)} repositories for org {org}")
                        except Exception as e:
                            logger.error(f"Error fetching org {org} repos: {e}")

                # Analyze each repository
                for repo_data in repos:
                    try:
                        # Store/update repository
                        repo = session.query(Repository).filter_by(github_id=repo_data["id"]).first()
                        if not repo:
                            repo = Repository(
                                github_id=repo_data["id"],
                                name=repo_data["name"],
                                full_name=repo_data["full_name"],
                                owner=repo_data["owner"]["login"],
                                description=repo_data.get("description"),
                                language=repo_data.get("language"),
                                stars=repo_data.get("stargazers_count", 0),
                                forks=repo_data.get("forks_count", 0),
                                open_issues=repo_data.get("open_issues_count", 0),
                                created_at=parse_github_datetime(repo_data.get("created_at")),
                                updated_at=parse_github_datetime(repo_data.get("updated_at")),
                                private=repo_data.get("private", False),
                                html_url=repo_data.get("html_url"),
                            )
                            session.add(repo)
                        else:
                            repo.stars = repo_data.get("stargazers_count", 0)
                            repo.forks = repo_data.get("forks_count", 0)
                            repo.open_issues = repo_data.get("open_issues_count", 0)
                            repo.updated_at = parse_github_datetime(repo_data.get("updated_at"))

                        session.commit()

                        # Analyze repository
                        analysis, findings = await analyzer.analyze_repository(repo_data)
                        analysis.repository_id = repo.id
                        analysis.last_analyzed = datetime.utcnow()
                        session.add(analysis)
                        session.commit()

                        # Store findings
                        for finding in findings:
                            finding.repository_id = repo.id
                            finding.analysis_id = analysis.id
                            session.add(finding)
                            findings_count += 1

                        repos_analyzed += 1

                    except Exception as e:
                        logger.error(f"Error analyzing repo {repo_data.get('full_name')}: {e}")

                # Find opportunities across repositories
                db_repos = session.query(Repository).all()
                opportunities = analyzer.find_opportunities(db_repos)

                for opp in opportunities:
                    opportunity = Opportunity(
                        type=opp["type"],
                        title=opp["title"],
                        description=opp["description"],
                        related_repositories=opp.get("related_repositories", []),
                        estimated_effort=opp.get("estimated_effort"),
                        potential_impact=opp.get("potential_impact"),
                    )
                    session.add(opportunity)

                session.commit()

                run_record.status = "completed"
                run_record.repositories_analyzed = repos_analyzed
                run_record.findings_count = findings_count

        except Exception as e:
            logger.error(f"Analysis job failed: {e}")
            run_record.status = "failed"
            run_record.completed_at = datetime.utcnow()
            session.add(run_record)
            session.commit()
            raise

        run_record.completed_at = datetime.utcnow()
        session.add(run_record)
        session.commit()
        logger.info(f"Analysis complete: {repos_analyzed} repos, {findings_count} findings")

    def start(self, username: str, organizations: list[str] | None = None, interval_hours: int = 24):
        """Start the scheduler."""
        if self._running:
            return

        async def job():
            await self.run_analysis_job(username, organizations)

        self.scheduler.add_job(
            job,
            trigger=IntervalTrigger(hours=interval_hours),
            id="github_analysis",
            replace_existing=True,
        )
        self.scheduler.start()
        self._running = True
        logger.info(f"Scheduler started with {interval_hours}h interval")

    def stop(self):
        """Stop the scheduler."""
        if self._running:
            self.scheduler.shutdown()
            self._running = False

    def run_once(self, username: str, organizations: list[str] | None = None):
        """Run analysis once without scheduling."""
        asyncio.run(self.run_analysis_job(username, organizations))