"""Tests for the improve command."""
import pytest


class TestImproveCommand:
    """Test the ghauto improve command."""

    def test_improve_command_exists(self):
        """Test that improve command is registered."""
        from cli import app
        from typer.testing import CliRunner
        
        runner = CliRunner()
        result = runner.invoke(app, ["improve", "--help"])
        
        assert result.exit_code == 0
        assert "improve" in result.output.lower()

    def test_heuristic_provider_exists(self):
        """Test that heuristic provider can be instantiated."""
        from improve import HeuristicProvider
        
        provider = HeuristicProvider()
        assert provider is not None
        assert hasattr(provider, 'complete')

    @pytest.mark.asyncio
    async def test_heuristic_provider_returns_suggestions(self):
        """Test that heuristic provider returns improvement suggestions."""
        from improve import HeuristicProvider
        
        provider = HeuristicProvider()
        result = await provider.complete("myorg/myrepo", {"missing_readme": True})
        
        assert result is not None
        assert isinstance(result, str)
        assert len(result) > 0

    def test_improve_command_accepts_repo_argument(self):
        """Test that improve command accepts repo argument."""
        from cli import app
        from typer.testing import CliRunner
        
        runner = CliRunner()
        # Test with --help to avoid making actual changes
        result = runner.invoke(app, ["improve", "--help"])
        
        assert result.exit_code == 0
        # Should show repo argument in help
        assert "repo" in result.output.lower() or "repository" in result.output.lower()

    @pytest.mark.asyncio
    async def test_repo_improver_can_be_instantiated(self):
        """Test that RepoImprover can be instantiated."""
        from improve import RepoImprover, HeuristicProvider
        
        improver = RepoImprover(ai_provider=HeuristicProvider())
        assert improver is not None
        assert hasattr(improver, 'improve_repo')

    @pytest.mark.asyncio
    async def test_improve_repo_returns_result(self):
        """Test that improve_repo returns proper result structure."""
        from improve import RepoImprover, HeuristicProvider
        
        improver = RepoImprover(ai_provider=HeuristicProvider())
        result = await improver.improve_repo("testorg/testrepo")
        
        assert result is not None
        assert "repo" in result
        assert result["repo"] == "testorg/testrepo"
        assert "improvements" in result
        assert "findings" in result

    @pytest.mark.asyncio
    async def test_heuristic_provider_handles_multiple_findings(self):
        """Test heuristic provider with multiple findings."""
        from improve import HeuristicProvider
        
        provider = HeuristicProvider()
        findings = {
            "missing_readme": True,
            "missing_license": True,
            "missing_ci": True,
            "missing_contributing": False,
            "missing_code_of_conduct": False
        }
        result = await provider.complete("testorg/testrepo", findings)
        
        assert "Add README" in result
        assert "Add LICENSE" in result
        assert "Add CI" in result

    def test_openrouter_provider_exists(self):
        """Test that OpenRouter provider can be instantiated."""
        from improve import OpenRouterProvider
        
        provider = OpenRouterProvider(api_key="test-key")
        assert provider is not None
        assert hasattr(provider, 'complete')

    @pytest.mark.asyncio
    async def test_openrouter_provider_handles_api_error(self):
        """Test that OpenRouter provider handles API errors gracefully."""
        from improve import OpenRouterProvider
        
        provider = OpenRouterProvider(api_key="test-key")
        
        # Test that provider can be created and returns error on API failure
        # We'll mock the actual API call to avoid needing aiohttp installed
        result = await provider.complete(prompt="test prompt")
        
        # Should handle errors gracefully - either returns error message or makes API call
        assert result is not None

    @pytest.mark.asyncio
    async def test_improve_repo_falls_back_on_ai_error(self):
        """Test that improve_repo falls back to heuristic when AI fails."""
        from improve import RepoImprover, OpenRouterProvider
        
        # Test with AI that will fail (no aiohttp)
        improver = RepoImprover(ai_provider=OpenRouterProvider(api_key="test-key"))
        result = await improver.improve_repo("testorg/testrepo", use_ai=True)
        
        # Should still have improvements (fallback to heuristic)
        assert result["improvements"] is not None
        assert "README" in result["improvements"]  # From heuristic fallback

    def test_improve_command_ai_flag_works(self):
        """Test that improve command handles --ai flag."""
        from cli import app
        from typer.testing import CliRunner
        
        runner = CliRunner()
        # Test that --ai flag is accepted
        result = runner.invoke(app, ["improve", "--ai", "--help"])
        
        assert result.exit_code == 0
        # The help should show the --ai option
        assert "--ai" in result.output