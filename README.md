# Strategy Backtesting Library

A Python library for backtesting trading strategies, including deep learning model integration and comprehensive technical analysis capabilities.

## Features

- Advanced backtesting engine for trading strategies
- Deep learning model integration
- Technical analysis indicators via TA-Lib
- Performance metrics and visualization
- Modern Python development with UV package management

## Prerequisites

- Python 3.8+
- Linux/Unix environment (Ubuntu/Debian recommended)
- Administrative privileges for system dependencies

## Installation

### 1. Install UV Package Manager

UV is a fast Python package manager that replaces pip and virtualenv. Install it using the official installer:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

**For Windows users:** See the [official UV installation guide](https://docs.astral.sh/uv/getting-started/installation/) for platform-specific instructions.

### 2. Install System Dependencies

The project requires TA-Lib C library and development tools. Install the necessary system packages:

```bash
sudo apt update && sudo apt install build-essential python3-dev
```

> **Note:** Use `build-essential` (not `build-essentials`) for the correct package name.

### 3. Install TA-Lib C Library

TA-Lib provides technical analysis functions and must be installed at the system level before the Python wrapper.

1. Download the appropriate Debian package from the [TA-Lib releases page](https://github.com/ta-lib/ta-lib/releases):

   ```bash
   wget https://github.com/ta-lib/ta-lib/releases/download/v0.6.4/ta-lib_0.6.4_amd64.deb
   ```

2. Install the package:

   ```bash
   sudo dpkg -i ta-lib_0.6.4_amd64.deb
   ```

**For Windows users:** Refer to the [TA-Lib installation guide](https://ta-lib.org/install/) for Windows-specific instructions.

### 4. Synchronize Python Dependencies

The TA-Lib Python wrapper version in `uv.lock` may not match your system installation, which can cause sync issues. Update the package to ensure compatibility:

```bash
uv lock --upgrade-package ta-lib
uv sync
```

This ensures the Python TA-Lib wrapper matches your system TA-Lib installation version.

## Quick Start

After installation, activate the environment and run your backtests:

```bash
# Activate the UV environment
source .venv/bin/activate

# Or run directly with UV
uv run python your_strategy.py
```

## Project Structure

```
strat_backtest/
├── src/           # Source code
├── tests/         # Test files
├── docs/          # Documentation
├── pyproject.toml # Project configuration
└── uv.lock        # Locked dependencies
```

## Development

This project uses modern Python development practices:

- **UV** for dependency management (never use pip)
- **pytest** for testing
- **pylint** for code quality
- **Type hints** for better code documentation

### Common Commands

```bash
# Install new dependencies
uv add package-name

# Run tests
uv run pytest

# Run tests with coverage
uv run pytest --cov=src

# Lint code
uv run pylint src/

# Sync dependencies
uv sync
```

## Troubleshooting

### TA-Lib Installation Issues

If you encounter TA-Lib related errors:

1. Verify system TA-Lib installation: `dpkg -l | grep ta-lib`
2. Ensure build tools are installed: `gcc --version`
3. Update the Python wrapper: `uv lock --upgrade-package ta-lib && uv sync`

### UV Sync Problems

If `uv sync` fails:

1. Check your `uv.lock` file is not corrupted
2. Try regenerating the lock file: `uv lock --refresh`
3. Ensure system dependencies are properly installed

## Contributing

1. Create a feature branch: `git checkout -b feature/your-feature`
2. Make your changes with proper type hints and docstrings
3. Run tests: `uv run pytest`
4. Lint your code: `uv run pylint src/`
5. Commit using conventional commits: `feat(scope): description`

## License

[Add your license information here]





