# agent.md

## Project Context

This document describes the agents and AI assistance approach for the ghAuto project.

## Architecture Agents

### 1. Backend Agent
**Responsibilities:**
- GitHub API integration and rate limiting
- Repository analysis algorithms
- Database schema and ORM
- Authentication and authorization

**Key Files:**
- `src/github_client/` - API wrapper
- `src/analyzer/` - Analysis logic
- `src/db.py` - Database models
- `src/auth.py` - Authentication

### 2. CLI Agent
**Responsibilities:**
- Command parsing and validation
- User interaction and prompts
- Progress reporting
- Configuration management

**Key Files:**
- `src/cli.py` - Typer CLI implementation

### 3. Frontend Agent
**Responsibilities:**
- React component architecture
- State management
- API integration
- Styling and responsive design

**Key Files:**
- `dashboard/src/pages/` - Page components
- `dashboard/src/main.jsx` - App entry point

### 4. Scheduler Agent
**Responsibilities:**
- Periodic job scheduling
- Task distribution
- Failure handling and retries
- Run history tracking

**Key Files:**
- `src/scheduler/` - Job orchestration

## AI-Assisted Development

### Code Generation Patterns

1. **Repository Analysis**
   - Pattern: Analyze file patterns → Score → Suggest
   - AI helps identify common anti-patterns
   - Suggest improvements based on best practices

2. **Opportunity Detection**
   - Pattern: Group similar repos → Find gaps → Recommend
   - AI identifies consolidation opportunities
   - Suggests new app ideas from existing patterns

3. **Health Scoring**
   - Pattern: Weighted metrics → Score aggregation
   - AI tunes weights based on successful repositories

### Future AI Features

- **Natural Language Queries**: "Show me repos with bad CI"
- **Auto-generated Recommendations**: AI-suggested improvements
- **Anomaly Detection**: Unusual patterns in repo changes
- **Predictive Analysis**: Forecast maintenance needs

## Development Workflow

### Testing Strategy
```
- Unit tests for analyzers
- Integration tests for API endpoints
- E2E tests for dashboard flows
- Mock tests for GitHub API
```

### Deployment Considerations
- Docker containerization
- GitHub Actions for CI
- Automated health checks
- Self-hosted option

## Configuration as Code

The AI agents should understand:
- Repository health patterns
- Common improvement opportunities
- Configuration best practices
- Security considerations

## Agent Communication

Agents communicate through:
1. Database shared state
2. File-based configuration
3. API endpoints
4. Event-driven updates

## gh CLI Integration Agent

### Responsibilities
- Token discovery from gh CLI config (`~/.config/gh/hosts.yml`)
- Username auto-detection via `gh api user`
- Token scope validation and recommendations
- Cross-platform config path resolution (Linux, macOS, Windows)

### Key Files
- `src/gh_cli.py` - Token discovery and validation
- `src/github_client/__init__.py` - Token fallback in GitHubClient
- `src/cli.py` - Integration with init and doctor commands

### Token Priority Order
1. Explicitly provided token (CLI flag or env var)
2. gh CLI stored token (if authenticated)
3. Generated token from environment variable

### Platform Config Paths
- Linux: `~/.config/gh/hosts.yml`
- macOS: `~/Library/Application Support/gh/hosts.yml`
- Windows: `~/AppData/Roaming/gh/hosts.yml`