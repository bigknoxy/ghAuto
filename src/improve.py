from typing import Optional


class AIProvider:
    """Base class for AI providers."""
    
    async def complete(self, repo: str, findings: dict) -> str:
        """Generate completion for a prompt."""
        raise NotImplementedError


class HeuristicProvider(AIProvider):
    """Rule-based provider that works without external AI."""
    
    async def complete(self, repo: str, findings: dict) -> str:
        """Generate fixes based on simple heuristics."""
        suggestions = []
        
        if findings.get("missing_readme"):
            suggestions.append({
                "type": "add_readme",
                "title": "Add README.md",
                "description": "Create a basic README with project description",
                "file": "README.md"
            })
        
        if findings.get("missing_license"):
            suggestions.append({
                "type": "add_license",
                "title": "Add LICENSE",
                "description": "Add MIT license file",
                "file": "LICENSE"
            })
        
        if findings.get("missing_ci"):
            suggestions.append({
                "type": "add_ci",
                "title": "Add CI workflow",
                "description": "Create basic GitHub Actions workflow",
                "file": ".github/workflows/ci.yml"
            })
        
        return self._format_suggestions(suggestions)
    
    def _format_suggestions(self, suggestions: list) -> str:
        """Format suggestions as readable text."""
        if not suggestions:
            return "No improvements needed."
        
        lines = ["## Suggested Improvements:\n"]
        for i, s in enumerate(suggestions, 1):
            lines.append(f"{i}. **{s['title']}**")
            lines.append(f"   - {s['description']}")
            lines.append(f"   - File: `{s['file']}`\n")
        
        return "\n".join(lines)


class OpenRouterProvider(AIProvider):
    """OpenRouter API provider for enhanced suggestions."""
    
    def __init__(self, api_key: str, model: str = "anthropic/claude-3-sonnet"):
        self.api_key = api_key
        self.model = model
    
    async def complete(self, prompt: str, **kwargs) -> str:
        """Call OpenRouter API for enhanced suggestions."""
        try:
            import aiohttp
        except ImportError:
            return "AI enhancement requested but aiohttp not installed. Run 'ghauto update' to install all dependencies."
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    "https://openrouter.ai/api/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": self.model,
                        "messages": [{"role": "user", "content": prompt}]
                    }
                ) as response:
                    data = await response.json()
                    return data.get("choices", [{}])[0].get("message", {}).get("content", "")
        except Exception as e:
            return f"Error calling OpenRouter API: {e}"


class RepoImprover:
    """Main class for improving repositories."""
    
    def __init__(self, github_client=None, ai_provider: Optional[AIProvider] = None):
        self.github = github_client
        self.ai = ai_provider or HeuristicProvider()
    
    async def improve_repo(self, repo: str, use_ai: bool = False) -> dict:
        """Analyze and improve a repository."""
        # Get current findings
        findings = await self._get_findings(repo)
        
        # Generate improvements
        if use_ai and isinstance(self.ai, OpenRouterProvider):
            # Use AI-enhanced suggestions
            prompt = f"Analyze repository {repo} and suggest improvements. Current findings: {findings}"
            improvements = await self.ai.complete(prompt=prompt)
            # Fall back to heuristic if AI returns empty/dud response
            if not improvements or improvements.startswith("Error") or "not installed" in improvements:
                # Create a new heuristic provider for fallback
                heuristic = HeuristicProvider()
                improvements = await heuristic.complete(repo, findings)
        else:
            # Use heuristic-based suggestions
            improvements = await self._generate_heuristic_fixes(repo, findings)
        
        # In real implementation, would create PR here
        return {
            "repo": repo,
            "improvements": improvements,
            "findings": findings
        }
    
    async def _get_findings(self, repo: str) -> dict:
        """Get repository findings (simplified)."""
        # Placeholder - would use actual analyzer
        return {
            "missing_readme": True,
            "missing_license": True,
            "missing_ci": True
        }
    
    async def _generate_heuristic_fixes(self, repo: str, findings: dict) -> str:
        """Generate fixes using heuristic provider."""
        # Always use HeuristicProvider for fallback, regardless of current ai_provider
        heuristic = HeuristicProvider()
        return await heuristic.complete(repo, findings)