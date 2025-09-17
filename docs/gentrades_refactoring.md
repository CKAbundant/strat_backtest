# GenTrades Refactoring Plan

**Date:** September 17, 2025  
**Objective:** Convert `GenTrades` from abstract to concrete while maintaining 100% backward compatibility

## 🎯 **Objective**
Convert `GenTrades` from abstract to concrete while maintaining **100% backward compatibility** with existing tests and API.

## 📊 **Current State Analysis**

**Current Abstract Method:**
```python
@abstractmethod
def gen_trades(self, df_signals: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Generate DataFrame containing completed trades for given strategy."""
    ...
```

**Current Concrete Helper:**
```python
def iterate_df(self, ticker: str, df_signals: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Iterate through DataFrame containing buy and sell signals..."""
```

**Key Problem:** `iterate_df()` requires `ticker: str` parameter, but `gen_trades()` doesn't have it.

## 🔧 **Solution Strategy**

**Extract ticker from DataFrame** - The sample data shows DataFrames contain a `ticker` column with values like `'AAPL'`. We'll extract the ticker from this column.

## 📝 **Detailed Changes**

### **1. Remove Abstract Decorator & Implement Method**

**File:** `src/strat_backtest/base/gen_trades.py`

**Before:**
```python
@abstractmethod
def gen_trades(self, df_signals: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Generate DataFrame containing completed trades for given strategy.

    Args:
        df_signals (pd.DataFrame):
            DataFrame containing entry and exit signals for specific ticker.

    Returns:
        df_trades (pd.DataFrame):
            DataFrame containing completed trades.
        df_signals (pd.DataFrame):
            DataFrame containing updated exit signals price-related stops.
    """
    ...
```

**After:**
```python
def gen_trades(self, df_signals: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Generate DataFrame containing completed trades for given strategy.

    Args:
        df_signals (pd.DataFrame):
            DataFrame containing entry and exit signals for specific ticker.
            Must include a 'ticker' column.

    Returns:
        df_trades (pd.DataFrame):
            DataFrame containing completed trades.
        df_signals (pd.DataFrame):
            DataFrame containing updated exit signals price-related stops.

    Raises:
        ValueError: If 'ticker' column is missing or contains multiple tickers.
    """
    # Validate ticker column exists
    if "ticker" not in df_signals.columns:
        raise ValueError("DataFrame must contain a 'ticker' column")
    
    # Extract unique ticker(s) and validate single ticker
    unique_tickers = df_signals["ticker"].unique()
    if len(unique_tickers) != 1:
        raise ValueError(
            f"DataFrame must contain exactly one ticker. Found: {unique_tickers}"
        )
    
    ticker = str(unique_tickers[0])
    
    # Delegate to existing iterate_df method
    return self.iterate_df(ticker, df_signals)
```

### **2. Remove ABC Import Statement**

**File:** `src/strat_backtest/base/gen_trades.py`

**Before:**
```python
from abc import ABC, abstractmethod
```

**After:**
```python
# Remove entire ABC import - no longer needed for concrete class
```

### **3. Update Class Declaration**

**File:** `src/strat_backtest/base/gen_trades.py`

**Before:**
```python
class GenTrades(ABC):
```

**After:**
```python
class GenTrades:
```

**Rationale:** Remove ABC inheritance since no abstract methods remain.

### **4. Clean Up Test Infrastructure**

**File:** `tests/utils/test_gentrades_utils.py`

**Remove entire `GenTradesTest` class:**
```python
# DELETE THIS CLASS - NO LONGER NEEDED
class GenTradesTest(GenTrades):
    """Concrete implementation for testing 'GenTrades' abstract class"""
    def gen_trades(self, df_signals: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
        return pd.DataFrame(), pd.DataFrame()
```

**Update factory function:**
```python
def gen_testgentrades_inst(
    trading_cfg: TradingConfig, risk_cfg: RiskConfig, **kwargs: Any
) -> GenTrades:  # Changed return type from GenTradesTest to GenTrades
    """Generate instance of 'GenTrades' class.

    Args:
        trading_cfg (TradingConfig):
            Instance of 'TradingConfig' dataclass.
        risk_cfg (RiskConfig):
            Instance of 'RiskConfig' dataclass.
        **kwargs (Any):
            Additional keyword arguments to set as attributes on the
            created instance. Only existing attributes will be modified.

    Returns:
        GenTrades:  # Updated return type
            Instance of 'GenTrades' class with specified configuration and
            any additional attributes set via kwargs.
    """
    
    # Create instance of 'GenTrades' directly (was GenTradesTest)
    gen_trades = GenTrades(trading_cfg, risk_cfg)
    
    # Set additional attributes if provided
    for attr_name, attr_value in kwargs.items():
        if not hasattr(gen_trades, attr_name):
            raise AttributeError(f"'{attr_name}' is not a valid attribute for 'GenTrades'.")
        setattr(gen_trades, attr_name, attr_value)

    return gen_trades
```

### **5. Update Test Imports**

**File:** `tests/base/test_gen_trades.py`

**Before:**
```python
from tests.utils.test_gentrades_utils import (
    # ... other imports ...
    gen_testgentrades_inst,
)
```

**After:** ✅ **No changes needed** - factory function still exists, just returns `GenTrades` instead.

## 🔍 **Compatibility Analysis**

### ✅ **What Remains Compatible:**

1. **Public API**: All imports continue to work
2. **TradingStrategy**: Calls `self.trades.gen_trades(df_pa)` unchanged  
3. **Method Signature**: `gen_trades(df_signals: pd.DataFrame)` unchanged
4. **Return Types**: Same tuple return type
5. **Test Framework**: Existing tests just use `GenTrades` directly

### 📋 **New Requirements:**

1. **DataFrame must include `ticker` column** - This is already true based on sample data
2. **Single ticker per DataFrame** - Existing usage pattern already follows this

## 🚨 **Risk Assessment**

### **Low Risk:**
- ✅ No breaking changes to public interface
- ✅ All existing tests will pass (just use `GenTrades` instead of `GenTradesTest`)
- ✅ `TradingStrategy` continues to work unchanged

### **Medium Risk:**
- ⚠️ New validation requirements might catch edge cases
- ⚠️ Error messages will be more descriptive (could change test assertions)

## 📊 **Implementation Order**

1. **Update `GenTrades` class** (remove abstract, implement method)
2. **Update test utilities** (remove `GenTradesTest`, update factory)
3. **Run tests** to verify compatibility
4. **Update documentation** to reflect concrete nature

## 🧪 **Testing Strategy**

**Before implementing:**
```bash
uv run pytest tests/base/test_gen_trades.py -v  # Should pass with current setup
```

**After implementing:**
```bash
uv run pytest tests/base/test_gen_trades.py -v  # Should still pass
uv run pytest --cov=src # Verify coverage
```

## 📈 **Expected Benefits**

1. **Simplified User Experience**: Users can instantiate `GenTrades` directly without creating subclasses
2. **Reduced Boilerplate**: Eliminates need for minimal concrete implementations
3. **Better Test Coverage**: Can test `GenTrades` directly, improving coverage from 95% to near 100%
4. **Cleaner Architecture**: Removes unnecessary abstraction layer
5. **Enhanced Usability**: Makes the library more accessible to new users

## 🔄 **Migration Path for Users**

### **Before (Abstract):**
```python
class MyGenTrades(GenTrades):
    def gen_trades(self, df_signals):
        return self.iterate_df("AAPL", df_signals)

# Usage
strategy = MyGenTrades(trading_cfg, risk_cfg)
```

### **After (Concrete):**
```python
# Direct usage - no subclass needed!
strategy = GenTrades(trading_cfg, risk_cfg)
```

## 📋 **Files to Modify**

1. **`src/strat_backtest/base/gen_trades.py`** - Main implementation
2. **`tests/utils/test_gentrades_utils.py`** - Remove test class, update factory
3. **Documentation updates** (if any exist)

## ✅ **Success Criteria**

- [ ] All existing tests pass without modification
- [ ] `GenTrades` can be instantiated directly
- [ ] `TradingStrategy` integration works unchanged
- [ ] Test coverage improves for `gen_trades` method
- [ ] No breaking changes to public API

---

*This refactoring maintains backward compatibility while significantly improving the developer experience by making GenTrades concrete and directly usable.*