"""Repository analyzer module."""
import json
import re
from typing import Any

from github_client import GitHubClient
from db import Analysis, Finding, Repository


class RepositoryAnalyzer:
    """Analyzes GitHub repositories for improvements and opportunities."""

    def __init__(self, client: GitHubClient):
        self.client = client

    async def analyze_repository(self, repo: dict[str, Any]) -> tuple[Analysis, list[Finding]]:
        """Analyze a repository and return analysis and findings."""
        owner = repo["owner"]["login"]
        name = repo["name"]
        full_name = repo["full_name"]

        findings = []
        analysis = Analysis(
            repository_id=repo["id"],
            health_score=100.0,
            analysis_data={},
        )

        # Check for README
        readme_result = await self._check_readme(owner, name)
        analysis.has_readme = readme_result["exists"]
        analysis.readme_quality_score = readme_result["quality_score"]
        if not readme_result["exists"]:
            findings.append(Finding(
                repository_id=repo["id"],
                analysis_id=0,
                category="critical",
                severity="high",
                title="Missing README",
                description="Repository is missing a README file.",
                recommendation="Add a README.md file with project description, installation instructions, and usage examples.",
            ))

        # Check for CI/CD
        ci_result = await self._check_ci_cd(owner, name)
        analysis.has_ci = ci_result["has_ci"]
        if not ci_result["has_ci"]:
            findings.append(Finding(
                repository_id=repo["id"],
                analysis_id=0,
                category="improvement",
                severity="medium",
                title="No CI/CD detected",
                description="No continuous integration configuration found.",
                recommendation="Add GitHub Actions workflow for automated testing and deployment.",
            ))

        # Check for tests
        analysis.has_tests = ci_result["has_tests"]
        if not ci_result["has_tests"]:
            findings.append(Finding(
                repository_id=repo["id"],
                analysis_id=0,
                category="improvement",
                severity="medium",
                title="No test configuration detected",
                description="No test configuration files found in the repository.",
                recommendation="Add test framework and write unit/integration tests.",
            ))

        # Check dependencies
        dep_result = await self._check_dependencies(owner, name)
        analysis.dependencies = dep_result["dependencies"]
        analysis.outdated_dependencies = dep_result["outdated"]

        # Check documentation files (LICENSE, CONTRIBUTING, CODE_OF_CONDUCT)
        doc_result = await self._check_documentation(owner, name)
        analysis.has_license = doc_result["has_license"]
        analysis.has_contributing = doc_result["has_contributing"]
        analysis.has_code_of_conduct = doc_result["has_code_of_conduct"]
        
        for missing in doc_result["missing"]:
            findings.append(Finding(
                repository_id=repo["id"],
                analysis_id=0,
                category="improvement",
                severity="low",
                title=f"Missing {missing}",
                description=f"Repository is missing a {missing} file.",
                recommendation=f"Add a {missing} file to improve project documentation and community guidelines.",
            ))

        # Check security features (dependabot, secret scanning)
        sec_result = await self._check_security(owner, name)
        analysis.has_dependabot = sec_result["has_dependabot"]
        analysis.has_secret_scanning = sec_result["has_secret_scanning"]
        analysis.security_findings = sec_result["findings"]
        
        if not sec_result["has_dependabot"]:
            findings.append(Finding(
                repository_id=repo["id"],
                analysis_id=0,
                category="improvement",
                severity="medium",
                title="No Dependabot configuration",
                description="Repository does not have Dependabot alerts enabled.",
                recommendation="Enable Dependabot in your repository settings or add a dependabot.yml file.",
            ))

        # Calculate health score
        if not analysis.has_readme:
            analysis.health_score -= 20
        if not analysis.has_ci:
            analysis.health_score -= 15
        if not analysis.has_tests:
            analysis.health_score -= 15
        if dep_result["outdated"]:
            analysis.health_score -= len(dep_result["outdated"]) * 2
        if not analysis.has_license:
            analysis.health_score -= 5
        if not analysis.has_dependabot:
            analysis.health_score -= 5

        analysis.analysis_data["readme"] = readme_result
        analysis.analysis_data["ci"] = ci_result
        analysis.analysis_data["dependencies"] = dep_result
        analysis.analysis_data["documentation"] = doc_result
        analysis.analysis_data["security"] = sec_result

        return analysis, findings

    async def _check_readme(self, owner: str, repo: str) -> dict[str, Any]:
        """Check for README file and analyze its quality."""
        try:
            contents = await self.client.get_repository_contents(owner, repo)
            readme_files = [f for f in contents if "readme" in f.get("name", "").lower()]

            if not readme_files:
                return {"exists": False, "quality_score": 0.0}

            # Get README content
            readme_content = await self.client.get_file_content(owner, repo, readme_files[0]["name"])
            if readme_content:
                text = readme_content.decode("utf-8", errors="ignore")
                score = self._calculate_readme_quality(text)
                return {"exists": True, "quality_score": score, "length": len(text)}

        except Exception:
            pass
        return {"exists": False, "quality_score": 0.0}

    def _calculate_readme_quality(self, content: str) -> float:
        """Calculate README quality score based on content."""
        score = 0.0
        sections = ["install", "usage", "example", "api", "contribut", "license"]

        content_lower = content.lower()
        for section in sections:
            if section in content_lower:
                score += 15

        # Bonus for length
        if len(content) > 500:
            score += 10
        if len(content) > 1000:
            score += 10

        return min(score, 100.0)

    async def _check_ci_cd(self, owner: str, repo: str) -> dict[str, Any]:
        """Check for CI/CD configuration files."""
        ci_indicators = [
            ".github/workflows",
            ".travis.yml",
            ".circleci/config.yml",
            "azure-pipelines.yml",
            "Jenkinsfile",
        ]
        test_indicators = ["pytest", "jest", "mocha", "junit", "test", "spec"]

        has_ci = False
        has_tests = False

        try:
            contents = await self.client.get_repository_contents(owner, repo)
            paths = ["/" + f["name"] for f in contents]

            # Check for .github/workflows
            if ".github" in paths:
                try:
                    workflow_contents = await self.client.get_repository_contents(owner, repo, ".github/workflows")
                    if workflow_contents and len(workflow_contents) > 0:
                        has_ci = True
                except Exception:
                    pass

            # Check for other CI files
            for ci_file in [".travis.yml", "azure-pipelines.yml", "Jenkinsfile"]:
                if ci_file in paths:
                    has_ci = True

            # Check for CircleCI
            if ".circleci" in paths:
                has_ci = True

            # Check for test files
            for f in contents:
                name_lower = f["name"].lower()
                for test_ind in test_indicators:
                    if test_ind in name_lower:
                        has_tests = True
                        break

        except Exception:
            pass

        return {"has_ci": has_ci, "has_tests": has_tests}

    async def _check_dependencies(self, owner: str, repo: str) -> dict[str, Any]:
        """Check for dependency files and identify outdated packages."""
        dependencies = {}
        outdated = []

        dep_files = {
            "package.json": "npm",
            "requirements.txt": "pip",
            "pyproject.toml": "pip",
            "Gemfile": "ruby",
            "go.mod": "go",
            "Cargo.toml": "rust",
        }

        try:
            contents = await self.client.get_repository_contents(owner, repo)
            files = {f["name"]: f for f in contents}

            for dep_file, pkg_manager in dep_files.items():
                if dep_file in files:
                    content = await self.client.get_file_content(owner, repo, dep_file)
                    if content:
                        dependencies[dep_file] = {
                            "package_manager": pkg_manager,
                            "raw_content": content.decode("utf-8", errors="ignore")[:1000],
                        }

                        # Check for outdated versions (basic check)
                        outdated.extend(self._find_outdated_deps(dep_file, content))

        except Exception:
            pass

        return {"dependencies": dependencies, "outdated": outdated}

    async def _check_documentation(self, owner: str, repo: str) -> dict[str, Any]:
        """Check for documentation files (LICENSE, CONTRIBUTING, CODE_OF_CONDUCT)."""
        doc_files = {
            "LICENSE": "has_license",
            "LICENSE.md": "has_license",
            "LICENSE.txt": "has_license",
            "CONTRIBUTING.md": "has_contributing",
            "CONTRIBUTING": "has_contributing",
            "CODE_OF_CONDUCT.md": "has_code_of_conduct",
            "CODE_OF_CONDUCT": "has_code_of_conduct",
        }
        
        has_license = False
        has_contributing = False
        has_code_of_conduct = False
        missing = []
        
        try:
            contents = await self.client.get_repository_contents(owner, repo)
            file_names = [f["name"] for f in contents]
            
            for doc_file, attr in doc_files.items():
                if doc_file in file_names:
                    if attr == "has_license":
                        has_license = True
                    elif attr == "has_contributing":
                        has_contributing = True
                    elif attr == "has_code_of_conduct":
                        has_code_of_conduct = True
        except Exception:
            pass
        
        if not has_license:
            missing.append("LICENSE")
        if not has_contributing:
            missing.append("CONTRIBUTING.md")
        if not has_code_of_conduct:
            missing.append("CODE_OF_CONDUCT.md")
        
        return {
            "has_license": has_license,
            "has_contributing": has_contributing,
            "has_code_of_conduct": has_code_of_conduct,
            "missing": missing,
        }

    async def _check_security(self, owner: str, repo: str) -> dict[str, Any]:
        """Check for security configuration (dependabot, secret scanning)."""
        has_dependabot = False
        has_secret_scanning = False
        findings = []
        
        try:
            contents = await self.client.get_repository_contents(owner, repo)
            file_names = [f["name"] for f in contents]
            
            # Check for .github/dependabot.yml
            if ".github" in file_names:
                try:
                    dg_contents = await self.client.get_repository_contents(owner, repo, ".github")
                    dg_files = [f["name"] for f in dg_contents]
                    if "dependabot.yml" in dg_files or "dependabot.yaml" in dg_files:
                        has_dependabot = True
                except Exception:
                    pass
            
            # Note: Secret scanning is enabled at repo level, not file-based
            # We can detect if there's a secret-scanning-related workflow
            for f in contents:
                if "secret" in f["name"].lower() and (f["name"].endswith(".yml") or f["name"].endswith(".yaml")):
                    has_secret_scanning = True
                    
        except Exception:
            pass
        
        return {
            "has_dependabot": has_dependabot,
            "has_secret_scanning": has_secret_scanning,
            "findings": findings,
        }

    def _find_outdated_deps(self, filename: str, content: bytes) -> list[dict]:
        """Simple check for potentially outdated dependencies."""
        outdated = []
        text = content.decode("utf-8", errors="ignore")

        # Look for pinned old versions
        if filename == "package.json":
            # Simple regex to find version patterns
            version_pattern = r'"([^"]+)":\s*"([^"]+)"'
            for match in re.finditer(version_pattern, text):
                pkg_name, version = match.groups()
                if version.startswith("^") or version.startswith("~"):
                    # Consider major versions 0.x as potentially unstable
                    if version.startswith("^0."):
                        outdated.append({"package": pkg_name, "current": version, "issue": "Stable version recommended"})

        return outdated

    async def find_opportunities(self, repositories: list[Repository]) -> list[dict]:
        """Identify opportunities for new apps or improvements across repositories."""
        opportunities = []

        # Group by language
        lang_groups: dict[str, list] = {}
        for repo in repositories:
            lang = repo.language or "Unknown"
            if lang not in lang_groups:
                lang_groups[lang] = []
            lang_groups[lang].append(repo)

        # Find languages with multiple repositories
        for lang, repos in lang_groups.items():
            if len(repos) >= 3:
                opportunities.append({
                    "type": "new_app",
                    "title": f"Potential {lang} application suite",
                    "description": f"You have {len(repos)} {lang} repositories. Consider building a unified application or CLI tool.",
                    "related_repositories": [r.full_name for r in repos],
                    "estimated_effort": "medium",
                    "potential_impact": "high",
                })

        # Check for duplicate functionality
        repo_names = [r.name.lower() for r in repositories]
        duplicate_patterns = [
            (r"api.*", "API duplicate pattern detected"),
            (r"cli.*", "CLI duplicate pattern detected"),
        ]

        for pattern, desc in duplicate_patterns:
            matches = [r.full_name for r in repositories if re.match(pattern, r.name.lower())]
            if len(matches) >= 2:
                opportunities.append({
                    "type": "consolidation",
                    "title": desc,
                    "description": f"Multiple similar repositories found. Consider consolidating: {', '.join(matches)}",
                    "related_repositories": matches,
                    "estimated_effort": "high",
                    "potential_impact": "medium",
                })

        return opportunities