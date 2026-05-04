"""Database models and session management."""
from datetime import datetime
from pathlib import Path

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    Float,
    Integer,
    String,
    Text,
    create_engine,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

Base = declarative_base()


def parse_github_datetime(date_str: str | None) -> datetime | None:
    """Parse GitHub API datetime string to Python datetime.
    
    GitHub returns dates in ISO 8601 format (e.g., '2025-10-09T19:21:45Z').
    SQLAlchemy DateTime columns require Python datetime objects.
    """
    if not date_str:
        return None
    # Handle both 'Z' suffix and '+00:00' format
    if date_str.endswith('Z'):
        date_str = date_str[:-1] + '+00:00'
    try:
        parsed = datetime.fromisoformat(date_str)
        # Convert to naive UTC datetime for SQLite compatibility
        return parsed.replace(tzinfo=None)
    except (ValueError, TypeError):
        return None


class Repository(Base):
    """GitHub repository information."""

    __tablename__ = "repositories"

    id = Column(Integer, primary_key=True)
    github_id = Column(Integer, unique=True, nullable=False)
    name = Column(String, nullable=False)
    full_name = Column(String, nullable=False)
    owner = Column(String, nullable=False)
    description = Column(Text)
    language = Column(String)
    stars = Column(Integer, default=0)
    forks = Column(Integer, default=0)
    open_issues = Column(Integer, default=0)
    created_at = Column(DateTime)
    updated_at = Column(DateTime)
    last_analyzed = Column(DateTime, default=datetime.utcnow)
    private = Column(Boolean, default=False)
    html_url = Column(String)


class Analysis(Base):
    """Repository analysis results."""

    __tablename__ = "analyses"

    id = Column(Integer, primary_key=True)
    repository_id = Column(Integer, nullable=False)
    analyzed_at = Column(DateTime, default=datetime.utcnow)
    last_analyzed = Column(DateTime, default=datetime.utcnow)

    # Health score (0-100)
    health_score = Column(Float, default=0.0)

    # README analysis
    has_readme = Column(Boolean, default=False)
    readme_quality_score = Column(Float, default=0.0)

    # CI/CD analysis
    has_ci = Column(Boolean, default=False)
    has_tests = Column(Boolean, default=False)

    # Dependency analysis
    dependencies = Column(JSON, default={})
    outdated_dependencies = Column(JSON, default=[])

    # Code quality metrics
    code_quality_issues = Column(JSON, default=[])

    # Security analysis
    has_dependabot = Column(Boolean, default=False)
    has_secret_scanning = Column(Boolean, default=False)
    security_findings = Column(JSON, default=[])

    # Documentation analysis
    has_license = Column(Boolean, default=False)
    has_contributing = Column(Boolean, default=False)
    has_code_of_conduct = Column(Boolean, default=False)

    # Raw analysis data
    analysis_data = Column(JSON, default={})


class Finding(Base):
    """Individual findings from repository analysis."""

    __tablename__ = "findings"

    id = Column(Integer, primary_key=True)
    repository_id = Column(Integer, nullable=False)
    analysis_id = Column(Integer, nullable=False)
    category = Column(String)  # critical, improvement, opportunity
    severity = Column(String)  # low, medium, high, critical
    title = Column(String)
    description = Column(Text)
    recommendation = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)


class Opportunity(Base):
    """New app/feature opportunities identified."""

    __tablename__ = "opportunities"

    id = Column(Integer, primary_key=True)
    type = Column(String)  # new_app, feature, consolidation
    title = Column(String)
    description = Column(Text)
    related_repositories = Column(JSON, default=[])
    estimated_effort = Column(String)
    potential_impact = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)


class ScheduledRun(Base):
    """Scheduled analysis run tracking."""

    __tablename__ = "scheduled_runs"

    id = Column(Integer, primary_key=True)
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime)
    status = Column(String)  # pending, running, completed, failed
    repositories_analyzed = Column(Integer, default=0)
    findings_count = Column(Integer, default=0)


class Config(Base):
    """Key-value configuration storage."""

    __tablename__ = "config"

    id = Column(Integer, primary_key=True)
    key = Column(String, unique=True, nullable=False)
    value = Column(Text)
    encrypted = Column(Boolean, default=False)
    updated_at = Column(DateTime, default=datetime.utcnow)


def get_session(db_path: str = "data/ghauto.db"):
    """Get a database session."""
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    engine = create_engine(f"sqlite:///{db_path}")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    return Session()


def init_db(db_path: str = "data/ghauto.db"):
    """Initialize the database."""
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    engine = create_engine(f"sqlite:///{db_path}")
    Base.metadata.create_all(engine)
    return engine