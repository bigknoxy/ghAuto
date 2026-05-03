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

## Quick Start

```bash
# Install
pip install ghauto

# Initialize configuration
ghauto init --token YOUR_GITHUB_TOKEN --username YOUR_USERNAME

# Run initial analysis
ghauto analyze

# Start the dashboard
ghauto serve
```

Or one-line install:
```bash
curl -fsSL https://raw.githubusercontent.com/ghAuto/install/main/install.sh | bash
```

## CLI Commands

| Command | Description |
|---------|-------------|
| `ghauto init` | Initialize configuration and database |
| `ghauto analyze` | Run repository analysis |
| `ghauto serve` | Start API and dashboard servers |
| `ghauto doctor` | Check system health |
| `ghauto config` | Manage configuration |

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