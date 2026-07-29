
import unittest
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from collections import deque
import time
from typing import Protocol, Dict, Optional

# Real event types — WindowManager now uses EventType enum
from market_data.events import MarketEvent, Exchange, EventType, Timestamps

# --- T3 Code to Verify ---
from features.windows import SymbolWindowState, WindowManager, DefaultWindowManager
from features.models import SymbolFeatureState
from features import handlers

# --- Verification Tests ---

def _ts():
    return Timestamps.now()


class TestT3Implementation(unittest.TestCase):

    def test_1_symbol_window_state_is_pure_dataclass(self):
        """Verify SymbolWindowState is a dataclass with slots (no instance dict)."""
        self.assertTrue(hasattr(SymbolWindowState, '__dataclass_fields__'), "Must be a dataclass.")
        self.assertTrue(hasattr(SymbolWindowState, '__slots__'), "Must use slots.")
        self.assertFalse(hasattr(SymbolWindowState(*(None,)*4), '__dict__'), "Instance must not have __dict__.")

    def test_2_default_window_manager_instantiation(self):
        """Verify DefaultWindowManager can be instantiated."""
        try:
            manager = DefaultWindowManager()
            self.assertIsInstance(manager, DefaultWindowManager)
        except Exception as e:
            self.fail(f"DefaultWindowManager instantiation failed: {e}")

    def _trade_event(self, exch="BINANCE", sym="BTC/USDT"):
        return MarketEvent(event_type=EventType.TRADE, timestamps=_ts(), exchange=Exchange.BINANCE, symbol=sym, data={"price": 50000, "volume": 0.5})

    def _candle_event(self, sym="BTC/USDT"):
        return MarketEvent(event_type=EventType.CANDLE_1M, timestamps=_ts(), exchange=Exchange.BINANCE, symbol=sym, data={"close": 50000})

    def _oi_event(self, sym="BTC/USDT"):
        return MarketEvent(event_type=EventType.OPEN_INTEREST, timestamps=_ts(), exchange=Exchange.BINANCE, symbol=sym, data={"open_interest": 100000})

    def _funding_event(self, sym="BTC/USDT"):
        return MarketEvent(event_type=EventType.FUNDING, timestamps=_ts(), exchange=Exchange.BINANCE, symbol=sym, data={"funding_rate": 0.0001})

    def test_3_data_appending(self):
        """Verify data is appended to the correct deques."""
        manager = DefaultWindowManager()

        manager.append_trade(self._trade_event())
        manager.append_candle(self._candle_event())
        manager.append_open_interest(self._oi_event())
        manager.append_funding(self._funding_event())

        state = manager.get_state("BINANCE", "BTC/USDT")
        self.assertEqual(len(state.trades_1m), 1)
        self.assertEqual(len(state.candles_1m), 1)
        self.assertEqual(len(state.oi_1h), 1)
        self.assertEqual(len(state.funding_8h), 1)

    def test_4_deque_max_length(self):
        """Verify deques respect their maxlen."""
        manager = DefaultWindowManager(max_trades=2)
        for _ in range(3):
            manager.append_trade(self._trade_event())

        state = manager.get_state("BINANCE", "BTC/USDT")
        self.assertEqual(len(state.trades_1m), 2)

    def test_5_state_isolation(self):
        """Verify state is isolated between different symbols."""
        manager = DefaultWindowManager()
        manager.append_trade(self._trade_event(sym="BTC/USDT"))
        manager.append_trade(self._trade_event(sym="ETH/USDT"))

        btc_state = manager.get_state("BINANCE", "BTC/USDT")
        eth_state = manager.get_state("BINANCE", "ETH/USDT")

        self.assertEqual(len(btc_state.trades_1m), 1)
        self.assertEqual(len(eth_state.trades_1m), 1)
        self.assertNotEqual(btc_state, eth_state)

    def test_6_package_imports(self):
        """Verify all necessary components can be imported."""
        try:
            from features import (
                FeatureDefinition,
                FeatureId,
                FEATURE_REGISTRY,
                SymbolFeatureState,
                FeatureHandler,
                WindowManager,
                DefaultWindowManager,
                SymbolWindowState,
                TickerHandler,
                TradeHandler,
                OpenInterestHandler,
            )
        except ImportError as e:
            self.fail(f"Failed to import from features package: {e}")

if __name__ == '__main__':
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestT3Implementation))
    runner = unittest.TextTestRunner()
    result = runner.run(suite)
    if result.wasSuccessful():
        print("T3 Implementation Verification PASSED")
    else:
        import sys
        sys.exit(1)
