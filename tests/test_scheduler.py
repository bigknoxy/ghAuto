"""Tests for scheduler.py - AnalysisScheduler class."""
import sys
sys.path.insert(0, 'src')

import pytest
import tempfile
import os
from unittest.mock import patch, MagicMock, AsyncMock

from db import Repository, Analysis, Finding, ScheduledRun, get_session, init_db


class TestAnalysisScheduler:
    """Tests for AnalysisScheduler class."""

    @pytest.fixture
    def temp_db(self):
        """Create a temporary database for testing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test.db")
            init_db(db_path)
            yield db_path

    def test_scheduler_init(self, temp_db):
        """Test AnalysisScheduler initialization."""
        from scheduler import AnalysisScheduler
        scheduler = AnalysisScheduler(
            github_token="test_token",
            db_path=temp_db
        )
        assert scheduler.github_token == "test_token"
        assert scheduler.db_path == temp_db
        assert scheduler._running is False

    def test_scheduler_init_no_token(self, temp_db):
        """Test AnalysisScheduler initialization without token."""
        from scheduler import AnalysisScheduler
        scheduler = AnalysisScheduler(db_path=temp_db)
        assert scheduler.github_token is None

    @pytest.mark.asyncio
    async def test_run_analysis_job_success(self, temp_db):
        """Test successful analysis job execution."""
        from scheduler import AnalysisScheduler
        
        scheduler = AnalysisScheduler(github_token="test_token", db_path=temp_db)
        mock_repos = [
            {
                "id": 111,
                "name": "repo1",
                "full_name": "owner/repo1",
                "owner": {"login": "owner"},
                "description": "Test repo",
                "language": "Python",
                "stargazers_count": 10,
                "forks_count": 5,
                "open_issues_count": 2,
                "created_at": "2025-01-01T00:00:00Z",
                "updated_at": "2025-01-02T00:00:00Z",
                "private": False,
                "html_url": "https://github.com/owner/repo1"
            }
        ]

        with patch('scheduler.GitHubClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client
            mock_client.get_user_repositories = AsyncMock(return_value=mock_repos)
            
            mock_analysis = Analysis(
                repository_id=1,
                health_score=100.0
            )
            mock_findings = [
                Finding(
                    repository_id=1,
                    analysis_id=1,
                    category="opportunity",
                    severity="low",
                    title="Test finding"
                )
            ]
            
            with patch('scheduler.RepositoryAnalyzer') as mock_analyzer_class:
                mock_analyzer = MagicMock()
                mock_analyzer_class.return_value = mock_analyzer
                mock_analyzer.analyze_repository = AsyncMock(return_value=(mock_analysis, mock_findings))
                mock_analyzer.find_opportunities = AsyncMock(return_value=[])
                
                await scheduler.run_analysis_job("testuser")

        session = get_session(temp_db)
        repo = session.query(Repository).filter_by(github_id=111).first()
        assert repo is not None
        assert repo.name == "repo1"
        
        run = session.query(ScheduledRun).order_by(ScheduledRun.id.desc()).first()
        assert run.status == "completed"
        assert run.repositories_analyzed == 1
        session.close()

    def test_scheduler_stop_when_not_running(self, temp_db):
        """Test stopping scheduler when not running doesn't raise."""
        from scheduler import AnalysisScheduler
        scheduler = AnalysisScheduler(db_path=temp_db)
        scheduler.stop()  # Should not raise

    @pytest.mark.asyncio
    async def test_datetime_parsing_for_repo_storage(self, temp_db):
        """Test that datetime strings are properly parsed when storing repos."""
        from scheduler import AnalysisScheduler
        
        scheduler = AnalysisScheduler(github_token="test_token", db_path=temp_db)
        mock_repos = [
            {
                "id": 333,
                "name": "datetime-test",
                "full_name": "owner/datetime-test",
                "owner": {"login": "owner"},
                "stargazers_count": 0,
                "forks_count": 0,
                "open_issues_count": 0,
                "created_at": "2025-03-15T10:30:00Z",
                "updated_at": "2025-03-16T14:45:30Z",
                "private": True,
                "html_url": "https://github.com/owner/datetime-test"
            }
        ]

        with patch('scheduler.GitHubClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client
            mock_client.get_user_repositories = AsyncMock(return_value=mock_repos)
            
            with patch('scheduler.RepositoryAnalyzer') as mock_analyzer_class:
                mock_analyzer = MagicMock()
                mock_analyzer_class.return_value = mock_analyzer
                mock_analyzer.analyze_repository = AsyncMock(return_value=(Analysis(repository_id=1), []))
                mock_analyzer.find_opportunities = AsyncMock(return_value=[])
                
                await scheduler.run_analysis_job("testuser")

        session = get_session(temp_db)
        repo = session.query(Repository).filter_by(github_id=333).first()
        assert repo.created_at is not None
        assert repo.updated_at is not None
        assert repo.created_at.year == 2025
        assert repo.created_at.month == 3
        assert repo.created_at.day == 15
        session.close()


class TestSchedulerErrorHandling:
    """Tests for scheduler error handling."""

    @pytest.fixture
    def temp_db(self):
        """Create a temporary database for testing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test.db")
            init_db(db_path)
            yield db_path

    @pytest.mark.asyncio
    async def test_run_analysis_job_error_handling(self, temp_db):
        """Test analysis job handles errors gracefully."""
        from scheduler import AnalysisScheduler
        
        scheduler = AnalysisScheduler(github_token="test_token", db_path=temp_db)

        with patch('scheduler.GitHubClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client
            mock_client.get_user_repositories.side_effect = Exception("API Error")
            
            with pytest.raises(Exception):
                await scheduler.run_analysis_job("testuser")

        session = get_session(temp_db)
        run = session.query(ScheduledRun).order_by(ScheduledRun.id.desc()).first()
        assert run is not None
        assert run.status == "failed"
        session.close()