# FixedTimeExit Integration Plan

## Overview

This document outlines the plan to integrate FixedTimeExit into the GenTrades class, allowing time-based position exits to work independently alongside existing exit methods.

## Key Insight: Independent Exit Mechanisms

FixedTimeExit should be **independent** of the `exit_struct` attribute since:
- Users can combine **FixedTimeExit (time-based)** with **any exit method (price-based)**
- Time-based exits should run **regardless** of the configured exit method
- This allows strategies like: "Use FIFO exit for signals, but also auto-close after 10 days"

## 1. Configuration Updates (RiskConfig)

**Add to RiskConfig dataclass:**
```python
@dataclass
class RiskConfig:
    """Risk management and stop loss configuration."""

    sig_eval_method: SigEvalMethod = "OpenEvaluator"
    trigger_percent: float | None = None
    percent_loss: float = 0.05
    stop_method: StopMethod = "no_stop"
    trail_method: TrailMethod = "no_trail"
    trigger_trail: float = 0.2
    step: float | None = None
    time_period: int | None = None  # NEW: Optional time period for FixedTimeExit
```

**Rationale:**
- Makes `time_period` optional like `step` and `trigger_percent`
- `None` indicates no time-based exit constraint
- Only used when time-based exits are desired

## 2. GenTrades Class Updates

### A. Update __init__ method:
```python
def __init__(self, trading_cfg: TradingConfig, risk_cfg: RiskConfig) -> None:
    # Existing code...

    # Risk configuration
    self.sig_eval_method = risk_cfg.sig_eval_method or "OpenEvaluator"
    self.trigger_percent = convert_to_decimal(risk_cfg.trigger_percent)
    self.percent_loss = risk_cfg.percent_loss
    self.stop_method = risk_cfg.stop_method
    self.trail_method = risk_cfg.trail_method
    self.trigger_trail = convert_to_decimal(risk_cfg.trigger_trail)
    self.step = convert_to_decimal(risk_cfg.step)
    self.time_period = risk_cfg.time_period  # NEW: Can be None
```

### B. Update class docstring:
```python
class GenTrades:
    """Abstract class to generate completed trades for given strategy.

    Usage:
        >>> trading_cfg = TradingConfig(
                entry_struct, exit_struct, num_lots, monitor_close
            )
        >>> risk_cfg = RiskConfig(
                percent_loss, stop_method, trigger_trail, step, time_period
            )
        >>> trades = GenTrades(trading_cfg, risk_cfg)
        >>> df_trades, df_signals = trades.gen_trades(df_signals)

    Args:
        trading_cfg (TradingConfig):
            Instance of 'TradingConfig' dataclass containing 'entry_struct',
            'exit_struct', 'num_lots' and 'monitor_close' attributes.
        risk_cfg (RiskConfig):
            Instance of 'RiskConfig' dataclass containing 'percent_loss',
            'stop_method', 'trigger_trail', 'step' and 'time_period' attributes.

    Attributes:
        # ... existing attributes ...
        step (Decimal):
            If provided, percent profit increment to trail profit. If None,
            increment set to current high - trigger_trail_level.
        time_period (int | None):
            If provided, number of trading days to hold position before automatic
            exit via time-based mechanism. Works independently of exit_struct method.
            If None, no time-based exit applied.
        # ... rest of existing attributes ...
    """
```

## 3. Integration in check_stop_loss Method

**Key Change: Use `time_period` for execution logic instead of `exit_struct`**

```python
def check_stop_loss(self, completed_list, record):
    """Check if stop loss condition met

    Args:
        completed_list (CompletedTrades):
            List of dictionary containing required fields to generate DataFrame.
        record (Record):
            Dictionary mapping required attributes to its values.

    Returns:
        completed_list (CompletedTrades):
            List of dictionary containing required fields to generate DataFrame.
    """

    # Return 'completed_list' unamended if no net position or no stop loss set
    if len(self.open_trades) == 0 or self.stop_method == "no_stop":
        return completed_list

    # NEW: Check time-based exits FIRST (independent of exit_struct)
    if self.time_period is not None:
        fixed_time_exit = self._get_inst_from_cache(
            "FixedTimeExit", time_period=self.time_period
        )
        self.open_trades, completed_list = fixed_time_exit.close_pos(
            self.open_trades, record["date"], record["close"]
        )
        # Continue to other exit checks even after time-based exits
        # (in case some positions remain open)

    # Existing FixedExit logic (unchanged)
    if self.exit_struct == "FixedExit":
        fixed_exit = self._get_inst_from_cache(
            "FixedExit", monitor_close=self.monitor_close
        )
        self.open_trades, completed_list = fixed_exit.check_all_stop(
            self.open_trades, completed_list, record
        )
        return completed_list

    # Existing generic stop-loss logic (unchanged)
    # Compute stop loss price based on 'self.stop_method'
    stop_price = self.cal_stop_price()

    # Check if stop loss triggered; and update 'completed_list' accordingly
    completed_list, trigger_info = self._update_trigger_status(
        completed_list, record, stop_price, exit_type="stop"
    )

    # Update 'self.stop_info_list' with trigger_info
    self.stop_info_list.append(trigger_info)

    return completed_list
```

## 4. Key Integration Benefits

### Execution Logic Changes:
- ✅ **Use `if self.time_period is not None:`** instead of `if self.exit_struct == "FixedTimeExit"`
- ✅ **Continue processing** after time-based exits (don't return immediately)
- ✅ **Independent operation** - time-based exits work with any exit method

### Behavioral Benefits:
- ✅ **Composable strategies** - combine time limits with any exit method
- ✅ **Flexible risk management** - multiple exit conditions can coexist
- ✅ **Proper precedence** - time-based exits happen first, then price-based

### Framework Benefits:
- ✅ Uses **only existing methods** (close_pos)
- ✅ Follows existing **configuration patterns**
- ✅ **Zero changes** needed to FixedTimeExit class
- ✅ Maintains **backward compatibility**

## 5. Example Use Cases

```python
# FIFO exit + 7-day time limit
trading_cfg = TradingConfig(exit_struct="FIFOExit", ...)
risk_cfg = RiskConfig(time_period=7, ...)

# FixedExit + 10-day time limit
trading_cfg = TradingConfig(exit_struct="FixedExit", ...)
risk_cfg = RiskConfig(time_period=10, ...)

# No time limit, just LIFO
trading_cfg = TradingConfig(exit_struct="LIFOExit", ...)
risk_cfg = RiskConfig(time_period=None, ...)
```

## 6. Implementation Steps

1. **Update RiskConfig** - Add `time_period: int | None = None` parameter
2. **Update GenTrades.__init__()** - Store `self.time_period = risk_cfg.time_period`
3. **Update GenTrades docstrings** - Document new time_period attribute
4. **Update check_stop_loss()** - Add time-based exit check using `time_period` condition
5. **Test integration** - Verify FixedTimeExit works independently with all exit methods

## 7. Technical Approach

This approach makes FixedTimeExit a **risk management tool** rather than an exclusive exit method, allowing maximum flexibility for strategy design. Time-based exits operate as an additional layer of risk control that works alongside any configured exit method.