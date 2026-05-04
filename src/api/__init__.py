"""REST API for the dashboard."""
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from db import (
    Analysis,
    Finding,
    Opportunity,
    Repository,
    ScheduledRun,
    get_session,
    init_db,
)

app = FastAPI(title="ghAuto API", version="0.1.0")

# Database path - defaults to ~/.ghauto/data/ghauto.db in db.py

# Enable CORS for dashboard
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class RepositoryResponse(BaseModel):
    id: int
    github_id: int
    name: str
    full_name: str
    description: str | None
    language: str | None
    stars: int
    forks: int
    open_issues: int
    health_score: float | None
    last_analyzed: datetime | None
    private: bool
    html_url: str


class FindingResponse(BaseModel):
    id: int
    repository_id: int
    category: str
    severity: str
    title: str
    description: str
    recommendation: str
    created_at: datetime


class OpportunityResponse(BaseModel):
    id: int
    type: str
    title: str
    description: str
    related_repositories: list[str]
    estimated_effort: str | None
    potential_impact: str | None
    created_at: datetime


class ScheduledRunResponse(BaseModel):
    id: int
    started_at: datetime
    completed_at: datetime | None
    status: str
    repositories_analyzed: int
    findings_count: int


@app.on_event("startup")
async def startup_event():
    """Initialize database on startup."""
    init_db()


@app.get("/api/repos", response_model=list[RepositoryResponse])
async def list_repositories():
    """List all repositories with their latest analysis."""
    session = get_session()
    repos = session.query(Repository).all()
    result = []

    for repo in repos:
        # Get latest analysis for health score
        latest_analysis = (
            session.query(Analysis)
            .filter_by(repository_id=repo.id)
            .order_by(Analysis.analyzed_at.desc())
            .first()
        )

        result.append(RepositoryResponse(
            id=repo.id,
            github_id=repo.github_id,
            name=repo.name,
            full_name=repo.full_name,
            description=repo.description,
            language=repo.language,
            stars=repo.stars,
            forks=repo.forks,
            open_issues=repo.open_issues,
            health_score=latest_analysis.health_score if latest_analysis else None,
            last_analyzed=latest_analysis.last_analyzed if latest_analysis else None,
            private=repo.private,
            html_url=repo.html_url,
        ))

    return result


@app.get("/api/repos/{repo_id}", response_model=dict)
async def get_repository(repo_id: int):
    """Get detailed repository information."""
    session = get_session()
    repo = session.query(Repository).get(repo_id)
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")

    analyses = (
        session.query(Analysis)
        .filter_by(repository_id=repo_id)
        .order_by(Analysis.analyzed_at.desc())
        .limit(5)
        .all()
    )

    findings = session.query(Finding).filter_by(repository_id=repo_id).all()

    return {
        "repository": RepositoryResponse(
            id=repo.id,
            github_id=repo.github_id,
            name=repo.name,
            full_name=repo.full_name,
            description=repo.description,
            language=repo.language,
            stars=repo.stars,
            forks=repo.forks,
            open_issues=repo.open_issues,
            health_score=analyses[0].health_score if analyses else None,
            last_analyzed=analyses[0].last_analyzed if analyses else None,
            private=repo.private,
            html_url=repo.html_url,
        ),
        "recent_analyses": [
            {
                "id": a.id,
                "analyzed_at": a.analyzed_at,
                "health_score": a.health_score,
                "has_readme": a.has_readme,
                "has_ci": a.has_ci,
                "has_tests": a.has_tests,
                "outdated_count": len(a.outdated_dependencies),
            }
            for a in analyses
        ],
        "findings": [
            FindingResponse(
                id=f.id,
                repository_id=f.repository_id,
                category=f.category,
                severity=f.severity,
                title=f.title,
                description=f.description,
                recommendation=f.recommendation,
                created_at=f.created_at,
            )
            for f in findings
        ],
    }


@app.get("/api/findings", response_model=list[FindingResponse])
async def list_findings(severity: str | None = None, category: str | None = None):
    """List all findings, optionally filtered."""
    session = get_session()
    query = session.query(Finding)

    if severity:
        query = query.filter_by(severity=severity)
    if category:
        query = query.filter_by(category=category)

    findings = query.order_by(Finding.created_at.desc()).all()

    return [
        FindingResponse(
            id=f.id,
            repository_id=f.repository_id,
            category=f.category,
            severity=f.severity,
            title=f.title,
            description=f.description,
            recommendation=f.recommendation,
            created_at=f.created_at,
        )
        for f in findings
    ]


@app.get("/api/opportunities", response_model=list[OpportunityResponse])
async def list_opportunities():
    """List all identified opportunities."""
    session = get_session()
    opportunities = session.query(Opportunity).order_by(Opportunity.created_at.desc()).all()

    return [
        OpportunityResponse(
            id=o.id,
            type=o.type,
            title=o.title,
            description=o.description,
            related_repositories=o.related_repositories,
            estimated_effort=o.estimated_effort,
            potential_impact=o.potential_impact,
            created_at=o.created_at,
        )
        for o in opportunities
    ]


@app.get("/api/runs", response_model=list[ScheduledRunResponse])
async def list_runs():
    """List scheduled run history."""
    session = get_session()
    runs = session.query(ScheduledRun).order_by(ScheduledRun.started_at.desc()).limit(20).all()

    return [
        ScheduledRunResponse(
            id=r.id,
            started_at=r.started_at,
            completed_at=r.completed_at,
            status=r.status,
            repositories_analyzed=r.repositories_analyzed,
            findings_count=r.findings_count,
        )
        for r in runs
    ]


@app.post("/api/analyze")
async def trigger_analysis(username: str, organizations: str | None = None):
    """Trigger a manual analysis run."""
    from scheduler import AnalysisScheduler

    orgs = [o.strip() for o in organizations.split(",")] if organizations else None

    scheduler = AnalysisScheduler()
    await scheduler.run_analysis_job(username, orgs)

    return {"status": "completed"}


@app.get("/api/stats")
async def get_stats():
    """Get overall statistics."""
    session = get_session()

    total_repos = session.query(Repository).count()
    total_findings = session.query(Finding).count()
    critical_findings = session.query(Finding).filter_by(severity="critical").count()
    opportunities = session.query(Opportunity).count()

    avg_health = session.query(Analysis.health_score).all()
    avg_health_score = sum(a[0] for a in avg_health) / len(avg_health) if avg_health else 0

    return {
        "total_repositories": total_repos,
        "total_findings": total_findings,
        "critical_findings": critical_findings,
        "opportunities": opportunities,
        "average_health_score": round(avg_health_score, 1),
    }


@app.get("/api/admin/config")
async def get_admin_config():
    """Get admin configuration."""
    session = get_session()
    from db import Config

    configs = session.query(Config).all()
    result = {}
    for c in configs:
        result[c.key] = c.value
    return result


@app.post("/api/admin/config")
async def update_admin_config(config: dict):
    """Update admin configuration."""
    session = get_session()
    from db import Config

    for key, value in config.items():
        cfg = session.query(Config).filter_by(key=key).first()
        if cfg:
            cfg.value = str(value)
        else:
            cfg = Config(key=key, value=str(value))
            session.add(cfg)
        session.commit()

    return {"status": "saved"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)