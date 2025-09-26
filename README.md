# Strategy Backtesting Library

A Python library for backtesting trading strategies, including deep learning model integration and comprehensive technical analysis capabilities.

## Features

- Advanced backtesting engine for trading strategies
- Deep learning model integration
- Technical analysis indicators via TA-Lib
- Performance metrics and visualization
- Modern Python development with UV package management

## Library Architecture

The framework follows a clean composition pattern:
- **EntrySignal & ExitSignal**: Generate buy/sell/wait signals from OHLCV data
- **GenTrades**: Orchestrates position management with configurable entry/exit methods
- **TradingStrategy**: Main coordinator that processes signals into completed trades
- **Risk Management**: Built-in stop-loss and trailing profit mechanisms

## Prerequisites

- Python 3.10+
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

## Main Components

Import the core classes directly from the package:

```python
from strat_backtest import TradingStrategy, EntrySignal, ExitSignal, GenTrades, TradingConfig, RiskConfig
```

## Quick Start Example

Here's a simple RSI-based strategy implementation:

```python
import pandas as pd
from strat_backtest import TradingStrategy, EntrySignal, ExitSignal, GenTrades, TradingConfig, RiskConfig

# Custom entry signal using RSI
class RSIEntrySignal(EntrySignal):
    def gen_entry_signal(self, df: pd.DataFrame) -> pd.DataFrame:
        # Calculate RSI and generate buy signals when RSI < 30
        # Add 'entry_signal' column with 1 (buy), -1 (sell), 0 (wait)
        return df

# Simple exit after N days
class TimeExitSignal(ExitSignal):
    def gen_exit_signal(self, df: pd.DataFrame) -> pd.DataFrame:
        # Add 'exit_signal' column based on holding period
        return df

# Configure strategy
trading_cfg = TradingConfig(
    entry_struct="SingleEntry",
    exit_struct="FIFOExit",
    num_lots=100
)

risk_cfg = RiskConfig(
    sig_eval_method="OpenEvaluator",
    percent_loss=0.05,
    stop_method="PercentLoss"
)

# Create and run strategy
strategy = TradingStrategy(
    entry_signal=RSIEntrySignal("long"),
    exit_sig=TimeExitSignal("long"),
    trades=GenTrades(trading_cfg, risk_cfg)
)

# Process OHLCV data
df_trades, df_signals = strategy(ohlcv_data)
print(f"Generated {len(df_trades)} trades")
```

Run your strategy:

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





