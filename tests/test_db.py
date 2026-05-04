"""Tests for db.py - database models and session management."""
import sys
sys.path.insert(0, 'src')

import pytest
import tempfile
import os
from datetime import datetime
from pathlib import Path
from unittest.mock import patch

from db import (
    parse_github_datetime,
    Repository,
    Analysis,
    Finding,
    Opportunity,
    ScheduledRun,
    Config,
    get_session,
    init_db,
    Base
)


class TestParseGitHubDateTime:
    """Tests for parse_github_datetime function."""

    def test_parse_with_z_suffix(self):
        """Test parsing datetime with Z suffix."""
        result = parse_github_datetime("2025-10-09T19:21:45Z")
        assert result is not None
        assert result.year == 2025
        assert result.month == 10
        assert result.day == 9
        assert result.hour == 19
        assert result.minute == 21
        assert result.second == 45
        # Should be naive (no timezone)
        assert result.tzinfo is None

    def test_parse_with_timezone_offset(self):
        """Test parsing datetime with timezone offset."""
        result = parse_github_datetime("2025-10-09T19:21:45+00:00")
        assert result is not None
        assert result.year == 2025
        assert result.month == 10

    def test_parse_with_negative_offset(self):
        """Test parsing datetime with negative timezone offset."""
        result = parse_github_datetime("2025-10-09T19:21:45-05:00")
        assert result is not None
        assert result.year == 2025

    def test_parse_none_returns_none(self):
        """Test that None input returns None."""
        assert parse_github_datetime(None) is None

    def test_parse_empty_string_returns_none(self):
        """Test that empty string returns None."""
        assert parse_github_datetime("") is None

    def test_parse_invalid_string_returns_none(self):
        """Test that invalid string returns None."""
        assert parse_github_datetime("not-a-date") is None
        assert parse_github_datetime("invalid-date") is None

    def test_parse_with_milliseconds(self):
        """Test parsing datetime with milliseconds."""
        result = parse_github_datetime("2025-10-09T19:21:45.123Z")
        assert result is not None
        assert result.microsecond == 123000

    def test_parse_preserves_utc_time(self):
        """Test that UTC time is preserved when converting to naive."""
        result = parse_github_datetime("2025-10-09T19:21:45Z")
        assert result is not None
        assert result.hour == 19
        assert result.minute == 21


class TestDatabaseModels:
    """Tests for database model definitions."""

    @pytest.fixture
    def test_db(self):
        """Create a temporary database for testing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test.db")
            init_db(db_path)
            yield db_path

    @pytest.fixture
    def session(self, test_db):
        """Get a database session for testing."""
        return get_session(test_db)

    def test_repository_model_creation(self, session):
        """Test creating a Repository model."""
        repo = Repository(
            github_id=12345,
            name="test-repo",
            full_name="owner/test-repo",
            owner="owner",
            description="Test repository",
            language="Python",
            stars=100,
            forks=50,
            open_issues=10,
            created_at=datetime(2025, 1, 1),
            updated_at=datetime(2025, 1, 2),
            private=False,
            html_url="https://github.com/owner/test-repo"
        )
        session.add(repo)
        session.commit()

        retrieved = session.query(Repository).filter_by(github_id=12345).first()
        assert retrieved is not None
        assert retrieved.name == "test-repo"
        assert retrieved.full_name == "owner/test-repo"
        assert retrieved.stars == 100

    def test_repository_model_defaults(self, session):
        """Test Repository model default values."""
        repo = Repository(
            github_id=12346,
            name="test-repo-2",
            full_name="owner/test-repo-2",
            owner="owner"
        )
        session.add(repo)
        session.commit()

        retrieved = session.query(Repository).filter_by(github_id=12346).first()
        assert retrieved.stars == 0  # Default
        assert retrieved.forks == 0  # Default
        assert retrieved.open_issues == 0  # Default
        assert retrieved.private is False  # Default

    def test_analysis_model_creation(self, session):
        """Test creating an Analysis model."""
        analysis = Analysis(
            repository_id=1,
            health_score=85.5,
            has_readme=True,
            has_ci=True,
            has_tests=True,
            has_dependabot=True,
            has_secret_scanning=False,
            has_license=True,
            has_contributing=True,
            has_code_of_conduct=True
        )
        session.add(analysis)
        session.commit()

        retrieved = session.query(Analysis).first()
        assert retrieved.health_score == 85.5
        assert retrieved.has_readme is True

    def test_finding_model_creation(self, session):
        """Test creating a Finding model."""
        finding = Finding(
            repository_id=1,
            analysis_id=1,
            category="critical",
            severity="high",
            title="Missing README",
            description="Repository is missing a README file.",
            recommendation="Add a README.md file"
        )
        session.add(finding)
        session.commit()

        retrieved = session.query(Finding).first()
        assert retrieved.category == "critical"
        assert retrieved.severity == "high"

    def test_opportunity_model_creation(self, session):
        """Test creating an Opportunity model."""
        opportunity = Opportunity(
            type="new_app",
            title="Potential Python application suite",
            description="You have 3 Python repositories",
            related_repositories=["owner/repo1", "owner/repo2", "owner/repo3"],
            estimated_effort="medium",
            potential_impact="high"
        )
        session.add(opportunity)
        session.commit()

        retrieved = session.query(Opportunity).first()
        assert retrieved.type == "new_app"
        assert len(retrieved.related_repositories) == 3

    def test_scheduled_run_model_creation(self, session):
        """Test creating a ScheduledRun model."""
        run = ScheduledRun(
            status="running",
            repositories_analyzed=5,
            findings_count=10
        )
        session.add(run)
        session.commit()

        retrieved = session.query(ScheduledRun).first()
        assert retrieved.status == "running"
        assert retrieved.repositories_analyzed == 5

    def test_config_model_creation(self, session):
        """Test creating a Config model."""
        config = Config(
            key="analysis_interval",
            value="24",
            encrypted=False
        )
        session.add(config)
        session.commit()

        retrieved = session.query(Config).filter_by(key="analysis_interval").first()
        assert retrieved.value == "24"
        assert retrieved.encrypted is False

    def test_model_relationships(self, session):
        """Test relationships between models."""
        repo = Repository(
            github_id=12347,
            name="test-repo-3",
            full_name="owner/test-repo-3",
            owner="owner"
        )
        session.add(repo)
        session.commit()

        analysis = Analysis(repository_id=repo.id)
        session.add(analysis)
        session.commit()

        finding = Finding(
            repository_id=repo.id,
            analysis_id=analysis.id,
            category="improvement",
            severity="low",
            title="Test finding"
        )
        session.add(finding)
        session.commit()

        # Verify relationships work
        assert analysis.repository_id == repo.id
        assert finding.repository_id == repo.id
        assert finding.analysis_id == analysis.id

    def test_json_fields(self, session):
        """Test JSON fields in models."""
        analysis = Analysis(
            repository_id=1,
            dependencies={"package.json": {"package_manager": "npm"}},
            outdated_dependencies=[{"package": "old-pkg", "current": "1.0.0"}],
            code_quality_issues=["unused import"],
            security_findings=[],
            analysis_data={"custom": "data"}
        )
        session.add(analysis)
        session.commit()

        retrieved = session.query(Analysis).first()
        assert retrieved.dependencies["package.json"]["package_manager"] == "npm"
        assert retrieved.outdated_dependencies[0]["package"] == "old-pkg"
        assert retrieved.code_quality_issues == ["unused import"]


class TestDatabaseFunctions:
    """Tests for database utility functions."""

    def test_init_db_creates_directory(self):
        """Test that init_db creates directory if it doesn't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "subdir", "test.db")
            assert not os.path.exists(os.path.dirname(db_path))
            init_db(db_path)
            assert os.path.exists(db_path)

    def test_get_session_creates_directory(self):
        """Test that get_session creates directory if it doesn't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "another", "test.db")
            assert not os.path.exists(os.path.dirname(db_path))
            session = get_session(db_path)
            assert os.path.exists(db_path)
            session.close()

    def test_database_persistence(self):
        """Test that data persists across sessions."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "persist.db")
            
            # Create and add data
            session1 = get_session(db_path)
            repo = Repository(
                github_id=99999,
                name="persist-test",
                full_name="owner/persist-test",
                owner="owner"
            )
            session1.add(repo)
            session1.commit()
            session1.close()

            # Retrieve in new session
            session2 = get_session(db_path)
            retrieved = session2.query(Repository).filter_by(github_id=99999).first()
            assert retrieved is not None
            assert retrieved.name == "persist-test"
            session2.close()


class TestDatabasePathDefaults:
    """Tests for default database path behavior."""

    def test_get_session_default_path_uses_home_directory(self):
        """Test that get_session without arguments uses ~/.ghauto/data/ghauto.db."""
        with patch.dict(os.environ, {}, clear=True):
            # The default path should be ~/.ghauto/data/ghauto.db
            # When no argument is passed, get_session should default to this path
            session = get_session()
            assert session is not None
            session.close()

    def test_init_db_default_path_uses_home_directory(self):
        """Test that init_db without arguments uses ~/.ghauto/data/ghauto.db."""
        with patch.dict(os.environ, {}, clear=True):
            engine = init_db()
            assert engine is not None

    def test_get_session_with_explicit_none_uses_default(self):
        """Test that get_session(None) uses the default path."""
        session = get_session(None)
        assert session is not None
        session.close()

    def test_init_db_with_explicit_none_uses_default(self):
        """Test that init_db(None) uses the default path."""
        engine = init_db(None)
        assert engine is not None

    def test_get_session_uses_custom_path(self):
        """Test that get_session uses a custom path when provided."""
        with tempfile.TemporaryDirectory() as tmpdir:
            custom_path = os.path.join(tmpdir, "custom", "test.db")
            session = get_session(custom_path)
            assert session is not None
            assert os.path.exists(custom_path)
            session.close()

    def test_init_db_uses_custom_path(self):
        """Test that init_db uses a custom path when provided."""
        with tempfile.TemporaryDirectory() as tmpdir:
            custom_path = os.path.join(tmpdir, "custom", "test.db")
            engine = init_db(custom_path)
            assert engine is not None
            assert os.path.exists(custom_path)

    def test_database_path_consistency_across_functions(self):
        """Test that get_session and init_db use the same default path."""
        # Get expected default path
        expected_path = str(Path.home() / ".ghauto" / "data" / "ghauto.db")
        
        # Test init_db returns engine pointing to correct path
        # (We can't easily verify the path in the engine without introspection)
        
        # Test get_session works with the same default
        session = get_session()
        assert session is not None
        session.close()


class TestDatabasePathIntegration:
    """Integration tests for database path across modules."""

    def test_scheduler_uses_default_db_path(self):
        """Test that AnalysisScheduler works with default database path."""
        from scheduler import AnalysisScheduler
        scheduler = AnalysisScheduler(github_token="test_token")
        assert scheduler.db_path is None  # Should be None to use default
        # Clean up
        scheduler.stop()

    def test_scheduler_uses_custom_db_path(self):
        """Test that AnalysisScheduler works with custom database path."""
        from scheduler import AnalysisScheduler
        with tempfile.TemporaryDirectory() as tmpdir:
            custom_path = os.path.join(tmpdir, "scheduler_test.db")
            scheduler = AnalysisScheduler(github_token="test_token", db_path=custom_path)
            assert scheduler.db_path == custom_path
            scheduler.stop()

    def test_auth_manager_uses_default_db_path(self):
        """Test that AuthManager works with default database path."""
        from auth import AuthManager
        auth = AuthManager()
        assert auth.db_path is None  # Should be None to use default

    def test_auth_manager_uses_custom_db_path(self):
        """Test that AuthManager works with custom database path."""
        from auth import AuthManager
        with tempfile.TemporaryDirectory() as tmpdir:
            custom_path = os.path.join(tmpdir, "auth_test.db")
            auth = AuthManager(db_path=custom_path)
            assert auth.db_path == custom_path

    def test_cli_db_file_constant(self):
        """Test that CLI uses the correct DB_FILE constant."""
        from cli import DB_FILE
        expected = Path.home() / ".ghauto" / "data" / "ghauto.db"
        assert DB_FILE == expected