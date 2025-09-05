# CLAUDE.md

## Project Overview
Python development project focused on production-ready code with comprehensive testing and documentation.

## Technology Stack
- **Language**: Python 3.x
- **Dependency Manager**: UV (never use pip)
- **Testing**: pytest
- **Linting**: pylint
- **Version Control**: Git with conventional commits

## Commands
- `uv add <package>`: Add new dependency
- `uv sync`: Install/update dependencies
- `uv run pytest`: Run all tests (run from repo root, not from inside `tests` directory)
- `uv run pytest --cov=src`: Run tests with coverage
- `uv run pytest tests/test_specific.py`: Run specific test file
- `uv run pylint src/`: Lint code for quality issues
- `uv run python script.py`: Run Python scripts

## Environment Setup
- This project uses UV - do not use pip or virtualenv commands
- Activate environment: `source .venv/bin/activate` or use `uv run`
- Python version managed by UV

## File Boundaries
- **Safe to edit**: `src/`, `tests/`, `docs/`, `README.md`
- **Never touch**: `.venv/`, `__pycache__/`, `.pytest_cache/`, `.git/`

## Code Style Rules
- Use type hints for all function parameters and returns
- Prefer simple functions over classes when possible
- Keep variable names descriptive but concise
- Follow PEP 8 formatting standards
- Add docstrings to all public functions and classes

## Git Workflow
- **Branch naming**: `feature/description`, `fix/issue-description`
- **Commit format**: `type(scope): description` (conventional commits)
- **Always**: Create feature branches, never commit directly to main
- **Before committing**: Run tests and linting

## Safety Rules
- Always ask permission before modifying existing files
- Show proposed changes before implementing
- Run tests after any code modifications
- Use UV commands exclusively for Python operations

## Available Specialists
- **python-code-quality**: For SOLID principles and PEP compliance
- **python-test-specialist**: For comprehensive pytest generation
- **python-performance-optimizer**: For memory/speed/security optimization

## Project-Specific Notes
- Focus on human-readable code over complex abstractions
- Address technical debt, not just "working" solutions
- Search for latest best practices before implementing changes