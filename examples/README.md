# strat_backtest Examples

This directory contains examples demonstrating how to use the `strat_backtest` trading strategy backtesting framework.

## Installation

To use the `strat_backtest` library, install it using UV from GitHub:

```bash
# Install the package directly from GitHub
uv add git+https://github.com/CKAbundant/strat_backtest.git

# Or if working with the development version from source
uv sync
```

## Framework Overview

The `strat_backtest` framework provides a modular architecture for building and backtesting trading strategies:

- **EntrySignal**: Generates buy/sell/wait signals to open new positions
- **ExitSignal**: Generates signals to close existing positions for profit
- **GenTrades**: Orchestrates trade execution with risk management
- **TradingStrategy**: Main coordinator that combines all components

The framework supports:
- Long, short, and long/short trading strategies
- Multiple position management methods (FIFO, LIFO, take-all)
- Risk management with stop-loss and trailing profit mechanisms
- Configurable signal evaluation methods

## Configuration Options

The framework provides multiple concrete implementations for each component. Configure them in your `TradingConfig` and `RiskConfig`:

### Entry Methods
- **`"SingleEntry"`**: Only one position at a time. Use for simple strategies that avoid overlapping trades.
- **`"MultiEntry"`**: Multiple overlapping positions allowed. Use when you want to scale into positions.
- **`"MultiHalfEntry"`**: Partial position management. Use for gradual position building.

```python
trading_cfg = TradingConfig(entry_struct="MultiEntry", ...)
```

### Exit Methods
- **`"FIFOExit"`**: First-in-first-out closing. Use for tax optimization or simple position management.
- **`"LIFOExit"`**: Last-in-first-out closing. Use when recent positions should close first.
- **`"TakeAllExit"`**: Close all positions simultaneously. Use for quick market exit strategies.
- **`"FixedExit"`**: Predetermined exit levels. Use when you have specific price targets.

```python
trading_cfg = TradingConfig(exit_struct="TakeAllExit", ...)
```

### Signal Evaluators
- **`"OpenEvaluator"`**: Execute trades at market open next day. Use for standard daily strategies.
- **`"BreakoutEvaluator"`**: Wait for price confirmation over multiple days. Use for momentum strategies requiring validation.

```python
risk_cfg = RiskConfig(sig_eval_method="BreakoutEvaluator", ...)
```

### Stop Methods (Portfolio Risk Protection)
All open positions close when stop condition is met. You define the portfolio loss percentage (e.g., 5%):

- **`"LatestLoss"`**: Uses most recent position to set stop level. Protects against trend reversals.
- **`"NearestLoss"`**: Uses position closest to current price. Provides tightest risk control.
- **`"PercentLoss"`**: Calculates stop to limit total portfolio loss to exact percentage. Ensures absolute loss control.
- **`"no_stop"`**: No automatic stops. Rely purely on your exit signal logic.

```python
risk_cfg = RiskConfig(stop_method="PercentLoss", percent_loss=0.05, ...)
```

### Trail Methods (Profit Protection)
Locks in portfolio gains while allowing continued upside participation:

- **`"FirstTrail"`**: Trails stops upward using first position as reference. Protects accumulated gains across all positions.
- **`"no_trail"`**: No trailing stops. Exit timing controlled entirely by your exit signals.

```python
risk_cfg = RiskConfig(trail_method="FirstTrail", trigger_trail=0.2, ...)
```

## Examples

### Simple RSI Strategy

The `simple_rsi_strategy.py` file demonstrates a basic RSI (Relative Strength Index) momentum trading strategy.

**To run the example:**

1. Use the provided sample data or prepare your own OHLCV data (see data format requirements below)
2. Run the strategy:

```bash
uv run python examples/simple_rsi_strategy.py
```

**What this example demonstrates:**
- Creating custom EntrySignal and ExitSignal classes
- Configuring trading and risk management parameters
- Using the TradingStrategy coordinator
- Processing OHLCV data through the backtesting pipeline
- Generating completed trades and performance metrics

## Data Format Requirements

The framework expects OHLCV data with ticker information. All column names should be in lowercase:

| Column | Description | Type |
|--------|-------------|------|
| date | Trading date (index) | datetime |
| ticker | Stock ticker symbol | string |
| open | Opening price | Decimal |
| high | Highest price | Decimal |
| low | Lowest price | Decimal |
| close | Closing price | Decimal |
| volume | Trading volume | Decimal |

**Sample data**: A sample parquet file is provided at `examples/data/sample_ohlcv.parquet` that you can use to test the framework. All numeric data uses Decimal type for precision.

**Loading the sample data:**
```python
import pandas as pd

# Load the sample data
df = pd.read_parquet('examples/data/sample_ohlcv.parquet')
```

## Getting Started

1. **Prepare your data**: Use the sample data or format your market data according to the requirements above
2. **Define your signals**: Create custom EntrySignal and ExitSignal classes
3. **Configure strategy**: Set up TradingConfig and RiskConfig parameters
4. **Run backtest**: Use TradingStrategy to execute the complete pipeline
5. **Analyze results**: Review the generated trades and performance metrics

For detailed implementation examples, see the individual strategy files in this directory.