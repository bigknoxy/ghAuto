# Contributing to ghAuto

Thank you for your interest in contributing to ghAuto! This document provides guidelines and instructions for contributing.

## Code of Conduct

By participating in this project, you agree to maintain a respectful and inclusive environment. Please be kind and constructive in all interactions.

## How to Contribute

### Reporting Bugs

1. Check the [issues](https://github.com/bigknoxy/ghAuto/issues) to see if the bug has already been reported.
2. If not, create a new issue with a clear description, including:
   - Steps to reproduce
   - Expected behavior
   - Actual behavior
   - Your environment (Python version, OS, etc.)

### Suggesting Features

1. Open an issue describing the feature you'd like to see.
2. Explain the problem it solves and how you envision it working.

### Pull Requests

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Run tests (`pytest`)
5. Commit your changes (`git commit -m 'Add amazing feature'`)
6. Push to the branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

## Development Setup

```bash
# Clone the repository
git clone https://github.com/bigknoxy/ghAuto.git
cd ghAuto

# Install development dependencies
pip install -e ".[dev]"

# Run tests
pytest
```

## Coding Standards

- Follow PEP 8 style guidelines
- Add docstrings to new functions and classes
- Write tests for new functionality
- Keep commits focused and atomic

## Questions?

Feel free to open an issue for any questions about contributing!