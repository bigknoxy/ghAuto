# ghAuto 🚀

> GitHub Repository Management and Analysis Tool

ghAuto is a comprehensive tool that analyzes your GitHub repositories to identify improvements, detect opportunities for new features, and provide actionable insights. It runs periodic checks and provides a dashboard for monitoring.

## Features

- 🔍 **Repository Analysis** - Automated checks for README quality, CI/CD configuration, tests, and dependencies
- 📊 **Health Scoring** - Each repository gets a health score based on best practices
- 💡 **Opportunity Detection** - Identifies gaps for new features and applications
- ⏱️ **Scheduled Analysis** - Runs periodic checks (configurable interval)
- 🌐 **Web Dashboard** - Beautiful React-based UI for monitoring
- 🔐 **CLI Interface** - Easy-to-use command line tool
- 🔐 **Authentication** - JWT-based auth with optional admin password protection
- 🔗 **gh CLI Integration** - Automatically uses your GitHub CLI token

## Quick Start

### Option 1: One-Line Install (Recommended)

```bash
# Install via script
curl -fsSL https://raw.githubusercontent.com/bigknoxy/ghAuto/main/install.sh | bash

# Initialize - will auto-detect your gh CLI token!
ghauto init

# Run initial analysis
ghauto analyze

# Start the dashboard
ghauto serve
```

### Option 2: From Source

```bash
# Clone and install
git clone https://github.com/bigknoxy/ghAuto.git
cd ghAuto
pip install -e .

# Initialize with explicit token (or use gh CLI token auto-detection)
ghauto init

# Run analysis
ghauto analyze
ghauto serve
```

### Option 3: Development Setup

```bash
# Clone for development
git clone https://github.com/bigknoxy/ghAuto.git
cd ghAuto
pip install -e ".[dev]"

# Run tests
pytest

# Start development servers
ghauto serve
```

## CLI Commands

| Command | Description |
|---------|-------------|
| `ghauto init` | Initialize configuration and database (auto-detects gh CLI token) |
| `ghauto analyze` | Run repository analysis |
| `ghauto daemon` | Run periodic analysis daemon (--once or --start) |
| `ghauto serve` | Start API and dashboard servers |
| `ghauto doctor` | Check system health |
| `ghauto config` | Manage configuration |

## gh CLI Integration

ghAuto integrates seamlessly with the GitHub CLI (`gh`). If you have `gh` installed and authenticated, ghAuto will automatically:

- ✅ Use your existing GitHub token from `~/.config/gh/hosts.yml`
- ✅ Detect your username from `gh api user`
- ✅ Check required token scopes and warn if missing

### Setup gh CLI (if not already done)

```bash
# Install gh CLI (if needed)
# macOS: brew install gh
# Linux: sudo apt install gh
# Windows: winget install gh

# Authenticate
gh auth login

# Refresh token with required scopes for ghAuto
gh auth refresh -s repo,read:org,workflow
```

### Required Token Scopes

For full functionality, your GitHub token needs these scopes:
- `repo` - Full control of private repositories
- `read:org` - Read organization data
- `workflow` - Update GitHub Actions workflows

## Dashboard

The web dashboard provides:
- **Overview** - Statistics and health summary
- **Repositories** - List with health scores and findings
- **Opportunities** - New app/feature suggestions
- **Admin** - Configuration management

## Configuration

```yaml
# ~/.ghauto/config.yaml
version: 1

github:
  username: your_username
  token: your_token

schedule:
  interval_hours: 24

dashboard:
  port: 3000
```

## What It Analyzes

- ✅ README presence and quality
- ✅ CI/CD workflow configuration
- ✅ Test files and configuration
- ✅ Dependencies and outdated packages
- ✅ Code quality patterns

## What It Suggests

- 📦 **New Apps** - When you have multiple repos in the same language
- 🔧 **Feature Gaps** - Missing standard files (LICENSE, CONTRIBUTING, etc.)
- 🔄 **Consolidation Opportunities** - Duplicate functionality across repos
- ⚡ **Improvement Ideas** - Based on repository patterns

## Development

```bash
# Clone
git clone https://github.com/bigknoxy/ghAuto.git
cd ghAuto

# Install dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Start development servers
ghauto serve
```

## License

MIT License - see [LICENSE](LICENSE) for details.

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## Support

- 📧 Issues: [GitHub Issues](https://github.com/bigknoxy/ghAuto/issues)
- 📖 Documentation: Coming soon
- 💬 Discussions: [GitHub Discussions](https://github.com/bigknoxy/ghAuto/discussions)

## Uninstall

```bash
# Run the uninstall script
curl -fsSL https://raw.githubusercontent.com/bigknoxy/ghAuto/main/scripts/uninstall.sh | bash
```

Or manually:
```bash
rm -rf ~/.ghauto
pip uninstall ghauto
# Remove PATH entry from ~/.zshrc or ~/.bashrc
```