# CLAUDE.md

## Project Overview
Python development project focused on production-ready code with comprehensive testing and documentation.

## Technology Stack
- **Language**: Python 3.x
- **Dependency Manager**: UV (never use pip)
- **Testing**: pytest
- **Linting**: pylint
- **Version Control**: Git with conventional commits

## Development Environment

This project uses UV for dependency management. **ALWAYS use these commands:**

- `uv add <package>` - Add new dependency
- `uv sync` - Install/update dependencies  
- `uv run python <file>` - Run Python scripts (never use `python3`)
- `uv run pytest` - Run all tests
- `uv run pytest --cov=src` - Run tests with coverage
- `uv run pytest <path/to/test_file>` - Run specific test file
- `uv run pylint src/` - Lint code for quality issues

**Never use system Python commands like `python3`, `python`, or `pytest` directly.**

## Environment Setup
- Use UV exclusively - never use pip or virtualenv commands
- Activate: `source .venv/bin/activate` or use `uv run`

## Security & File Protection
- **Never access**: Environment files (`.env*`) - contain sensitive credentials
- **Never modify**: `.git/`, `.venv/`, `__pycache__/`, `.pytest_cache/`
- Protection enforced via `~/.claude/settings.json` deny rules
- **Safe to edit**: `src/`, `tests/`, `docs/`, `README.md`

## Code Style Standards
- Use Python 3.10+ union syntax: `str | None` not `Optional[str]`
- Avoid nested if statements - use early returns for validation
- Follow PEP 8 formatting standards
- Include type hints for functions and returns

## Class Documentation Standards
- Document `__init__` parameters in class docstring (not in `__init__` method)
- Include both Args (initialization parameters) and Attributes (resulting class state)
- Structure: brief purpose, Args section, Attributes section
- Focus on clear parameter descriptions over examples

## Code Generation Requirements
- Run pytest on generated code to ensure functionality
- Focus on maintainable, readable solutions

## Git Workflow
- **Branch naming**: `feature/description`, `fix/issue-description`
- **Commit format**: `type(scope): description` (conventional commits)
- Create feature branches, never commit directly to main

## Analysis Preferences
- Exclude `__pycache__`, `.pytest_cache`, `.git`, `.venv` directories from analysis
- When using tree/ls commands, always exclude these directories with -I flag
- Focus on source code and meaningful project files only
