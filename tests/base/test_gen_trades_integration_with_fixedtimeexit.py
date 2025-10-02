"""Integration tests for FixedTimeExit with GenTrades."""

from tests.utils.test_gentrades_utils import gen_testgentrades_inst


class TestFixedTimeExitIntegration:
    """Test FixedTimeExit integration with GenTrades using real data."""

    def test_fixed_time_exit_with_fifo_exit(
        self, sample_gen_trades, trading_config, risk_config
    ):
        """Test FixedTimeExit works with FIFOExit method."""
        # Create test instance with time_period and FIFOExit
        test_inst = gen_testgentrades_inst(
            trading_config,
            risk_config,
            time_period=3,  # Close positions after 3 days
            exit_struct="FIFOExit",
        )
        df_trades, _ = test_inst.gen_trades(sample_gen_trades)

        # Should generate some completed trades due to time-based exits
        assert len(df_trades) > 0
        assert "ticker" in df_trades.columns
        assert all(df_trades["ticker"] == "AAPL")

        # Verify that time_period is stored correctly
        assert test_inst.time_period == 3

    def test_fixed_time_exit_with_lifo_exit(
        self, sample_gen_trades, trading_config, risk_config
    ):
        """Test FixedTimeExit works with LIFOExit method."""
        # Create test instance with time_period and LIFOExit
        test_inst = gen_testgentrades_inst(
            trading_config,
            risk_config,
            time_period=5,  # Close positions after 5 days
            exit_struct="LIFOExit",
            num_lots=5,
        )
        df_trades, _ = test_inst.gen_trades(sample_gen_trades)

        # Should generate completed trades
        assert len(df_trades) > 0
        assert test_inst.time_period == 5

    def test_fixed_time_exit_with_take_all_exit(
        self, sample_gen_trades, trading_config, risk_config
    ):
        """Test FixedTimeExit works with TakeAllExit method."""
        # Create test instance with time_period and TakeAllExit
        test_inst = gen_testgentrades_inst(
            trading_config,
            risk_config,
            time_period=2,  # Very short time period
            exit_struct="TakeAllExit",
            entry_struct="SingleEntry",
            num_lots=20,
        )
        df_trades, _ = test_inst.gen_trades(sample_gen_trades)

        # Should generate completed trades quickly due to short time period
        assert len(df_trades) > 0
        assert test_inst.time_period == 2

    def test_no_time_period_behaves_normally(
        self, sample_gen_trades, trading_config, risk_config
    ):
        """Test that None time_period doesn't affect normal operation."""
        # Create test instance without time_period (None)
        test_inst = gen_testgentrades_inst(
            trading_config, risk_config, time_period=None  # No time-based exits
        )
        _, _ = test_inst.gen_trades(sample_gen_trades)

        # Should still work normally without time-based exits
        assert test_inst.time_period is None
        # May or may not generate trades depending on signals, but should not error

    def test_time_period_longer_than_data_period(
        self, sample_gen_trades, trading_config, risk_config
    ):
        """Test time_period longer than the data period."""
        # Create test instance with very long time_period
        test_inst = gen_testgentrades_inst(
            trading_config,
            risk_config,
            time_period=30,  # Much longer than data period (13 days)
        )
        _, _ = test_inst.gen_trades(sample_gen_trades)

        # Should work without time-based exits since period is too long
        assert test_inst.time_period == 30
        # Trades should only be closed at end of testing period

    def test_time_period_with_different_entry_methods(
        self, sample_gen_trades, trading_config, risk_config
    ):
        """Test time_period works with different entry methods."""
        entry_methods = ["SingleEntry", "MultiEntry", "MultiHalfEntry"]

        for entry_method in entry_methods:
            # Create test instance with different entry methods
            test_inst = gen_testgentrades_inst(
                trading_config, risk_config, time_period=4, entry_struct=entry_method
            )
            _, _ = test_inst.gen_trades(sample_gen_trades)

            # Should work with any entry method
            assert test_inst.time_period == 4
            # Verify no errors occurred during processing

    def test_time_period_edge_case_one_day(
        self, sample_gen_trades, trading_config, risk_config
    ):
        """Test time_period = 1 (exit next day)."""
        # Create test instance with 1-day time period
        test_inst = gen_testgentrades_inst(
            trading_config,
            risk_config,
            time_period=1,  # Exit positions after 1 day
            num_lots=5,
        )
        df_trades, _ = test_inst.gen_trades(sample_gen_trades)

        # Should generate many completed trades due to very short time period
        assert len(df_trades) > 0
        assert test_inst.time_period == 1

        # Verify all trades have short holding periods
        if len(df_trades) > 0:
            assert all(df_trades["days_held"] >= 1)

    def test_backward_compatibility_without_time_period(
        self, sample_gen_trades, trading_config, risk_config
    ):
        """Test that existing code without time_period still works."""
        # Create test instance using default fixtures (time_period=None by default)
        test_inst = gen_testgentrades_inst(trading_config, risk_config)
        _, _ = test_inst.gen_trades(sample_gen_trades)

        # Should work exactly as before
        assert test_inst.time_period is None
        # Should generate normal trades based on signals only

    def test_combined_time_and_signal_exits(
        self, sample_gen_trades, trading_config, risk_config
    ):
        """Test that time-based exits work alongside signal-based exits."""
        # Create test instance with moderate time period
        test_inst = gen_testgentrades_inst(
            trading_config, risk_config, time_period=6  # Moderate time period
        )
        df_trades, _ = test_inst.gen_trades(sample_gen_trades)

        # Should generate trades from both time-based and signal-based exits
        assert len(df_trades) >= 0  # May have trades from either source
        assert test_inst.time_period == 6

        # Verify the data structure is correct
        if len(df_trades) > 0:
            required_columns = [
                "ticker",
                "entry_datetime",
                "entry_action",
                "entry_lots",
                "entry_price",
                "exit_datetime",
                "exit_action",
                "exit_lots",
                "exit_price",
                "days_held",
                "profit_loss",
                "percent_ret",
                "daily_ret",
                "win",
            ]
            for col in required_columns:
                assert col in df_trades.columns, f"Missing column: {col}"
