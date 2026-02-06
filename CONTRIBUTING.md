# Contributing to mcp-bcrp

Thank you for your interest in contributing! This project follows a simple contribution workflow.

## Development Setup

```bash
# Clone the repository
git clone https://github.com/MaykolMedrano/mcp-bcrp.git
cd mcp-bcrp

# Create virtual environment
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac

# Install in development mode with test dependencies
pip install -e ".[dev]"
```

## Running Tests

```bash
pytest tests/ -v
```

## Code Style

- Use type hints where possible
- Follow PEP 8 conventions
- Keep functions focused and document complex logic

## Pull Request Process

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## Reporting Issues

Please use GitHub Issues and include:
- Clear description of the problem
- Steps to reproduce
- Expected vs actual behavior
- Python version and OS
