# Analysis of strat_backtest Python Backtesting Framework

## Executive Summary

The strat_backtest framework is a sophisticated Python backtesting library built around abstract classes and modular components. It follows a clean architecture pattern with separate concerns for signal generation, trade execution, position management, and risk control.

## 1. Abstract Classes and Architecture (`src/strat_backtest/base/`)

### Core Abstract Classes:
- **EntryStruct**: Defines how new positions are opened (single vs multiple positions)
- **ExitStruct & HalfExitStruct**: Manage position closing strategies (FIFO, LIFO, take-all, etc.)
- **SignalEvaluator**: Evaluates entry/exit conditions over multiple periods
- **TradeSignal** (EntrySignal & ExitSignal): Generate buy/sell/wait signals
- **GenTrades**: Main orchestrator that coordinates all components

### Data Models:
- **StockTrade**: Pydantic model for individual trades with computed fields (profit/loss, returns, etc.)
- **TradingConfig & RiskConfig**: Configuration dataclasses for strategy parameters

## 2. TradingStrategy Orchestration

The `TradingStrategy` class acts as the main coordinator:
1. Takes EntrySignal, ExitSignal, and GenTrades instances
2. Processes OHLCV data through signal generation pipeline
3. Generates completed trades and updated signals
4. Follows a clean composition pattern

## 3. Concrete Implementations

### Entry Methods (`src/strat_backtest/entry_method/`):
- **SingleEntry**: Only one position at a time
- **MultiEntry**: Multiple overlapping positions allowed
- **MultiHalfEntry**: Partial position management

### Exit Methods (`src/strat_backtest/exit_method/`):
- **FIFOExit/LIFOExit**: First/Last-in-first-out closing
- **HalfFIFOExit/HalfLIFOExit**: Partial position closing
- **TakeAllExit**: Close all positions
- **FixedExit**: Predetermined exit levels

### Signal Evaluators (`src/strat_backtest/signal_evaluator/`):
- **OpenEvaluator**: Execute at market open next day
- **BreakoutEvaluator**: Wait for price confirmation over multiple days

### Stop Methods (`src/strat_backtest/stop_method/`):
- **LatestLoss**: Stop price based on percentage loss from latest open position
- **NearestLoss**: Stop price closest to current trading price (highest for long, lowest for short)
- **PercentLoss**: Stop price calculated to limit total portfolio loss to specified percentage

### Trail Methods (`src/strat_backtest/trail_method/`):
- **FirstTrail**: Trailing profit based on first open position as reference price

## 4. Dependency and Initialization Patterns

The framework uses several sophisticated patterns:

### Dynamic Class Loading:
- `get_module_paths()` maps class names to module paths
- `get_class_instance()` uses importlib for dynamic instantiation
- Instance caching prevents repeated object creation

### Configuration-Driven Architecture:
- TradingConfig and RiskConfig dataclasses centralize parameters
- String-based method selection enables flexible strategy combinations
- Type-safe enums define valid strategy options

## 5. Data Flow Architecture

```
OHLCV Data → EntrySignal → ExitSignal → GenTrades → Completed Trades
                                            ↓
                           SignalEvaluator ← Entry/Exit Methods
                                            ↓
                                    Risk Management (Stops/Trails)
```

### Key Flow Steps:
1. **Signal Generation**: EntrySignal and ExitSignal process OHLCV data
2. **Signal Evaluation**: SignalEvaluator confirms conditions over multiple periods
3. **Position Management**: Entry/Exit methods handle trade execution
4. **Risk Control**: Stop-loss and trailing profit mechanisms
5. **Trade Completion**: Generates final trade records with performance metrics

## 6. External User Implementation Pattern

Users would implement strategies by:

1. **Define Custom Signals** (inheriting from EntrySignal/ExitSignal):
   ```python
   class MyEntrySignal(EntrySignal):
       def gen_entry_signal(self, df: pd.DataFrame) -> pd.DataFrame:
           # Custom logic to add 'entry_signal' column
           return df
   ```

2. **Configure Strategy Components**:
   ```python
   trading_cfg = TradingConfig(
       entry_struct="SingleEntry",
       exit_struct="FIFOExit",
       num_lots=10,
       monitor_close=True
   )

   risk_cfg = RiskConfig(
       sig_eval_method="OpenEvaluator",
       percent_loss=0.05,
       stop_method="PercentLoss"
   )
   ```

3. **Assemble Complete Strategy**:
   ```python
   strategy = TradingStrategy(
       entry_signal=MyEntrySignal("long"),
       exit_sig=MyExitSignal("long"),
       trades=GenTrades(trading_cfg, risk_cfg)
   )

   df_trades, df_signals = strategy(df_ohlcv)
   ```

## 7. Key Strengths

- **Modularity**: Clean separation of concerns allows easy customization
- **Type Safety**: Strong typing with Pydantic models and type hints
- **Extensibility**: Abstract base classes enable new strategy implementations
- **Risk Management**: Built-in stop-loss and trailing profit mechanisms
- **Performance**: Efficient position tracking with deque data structures
- **Testing**: Comprehensive test suite with fixtures for all components

This framework provides a robust foundation for implementing and backtesting complex trading strategies with professional-grade risk management and performance tracking capabilities.