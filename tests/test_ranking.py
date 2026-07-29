"""
Unit tests for ADR-007 Ranking Engine.
"""
import sys, os, time, asyncio, unittest
sys.path.insert(0, os.path.abspath('.'))

from market_data.events import Exchange
from features.models import NormalizedFeature, MarketBreadth, RankedSymbol
from features.registry import FeatureId
from features.ranking import RankingStore, RankingEngine, WEIGHTS

# Dummy classes for isolation
class MockBus:
    def subscribe(self, h): pass
class MockNorm:
    def __init__(self): self.states = {}
    def get_all_states(self): return self.states

class TestRankingEngine(unittest.TestCase):
    
    def setUp(self):
        """Set up a fresh engine for each test."""
        self.ranking_store = RankingStore(top_n=5)
        self.mock_norm = MockNorm()
        self.ranking_engine = RankingEngine(
            bus=MockBus(), norm=self.mock_norm, store=self.ranking_store
        )
        self.now = time.monotonic()

    def test_score_calculation(self):
        """T7.1: Verify base score formula."""
        norm_state = {
            FeatureId.RSI_14_1M: NormalizedFeature('EX', 'S1', FeatureId.RSI_14_1M, 0, 90, 0, 1, self.now),
            FeatureId.VOLUME_1M: NormalizedFeature('EX', 'S1', FeatureId.VOLUME_1M, 0, 80, 0, 1, self.now),
            FeatureId.OI:        NormalizedFeature('EX', 'S1', FeatureId.OI, 0, 70, 0, 1, self.now),
        }
        # No breadth context
        self.ranking_engine._last_breadth = None
        
        score, _ = self.ranking_engine._compute_score(norm_state)
        
        expected_breadth_score = 0.0
        expected_base_score = (90 * WEIGHTS['rsi'] + 80 * WEIGHTS['volume'] + 70 * WEIGHTS['oi'])
        expected_final = expected_base_score * (1 - WEIGHTS['breadth']) + expected_breadth_score * WEIGHTS['breadth']
        
        self.assertAlmostEqual(score, expected_final, 2)

    def test_breadth_multiplier(self):
        """T7.2: Verify breadth multiplier correctly adjusts score."""
        norm_state = {
            FeatureId.RSI_14_1M: NormalizedFeature('EX', 'S1', FeatureId.RSI_14_1M, 0, 90, 0, 1, self.now),
            FeatureId.VOLUME_1M: NormalizedFeature('EX', 'S1', FeatureId.VOLUME_1M, 0, 80, 0, 1, self.now),
            FeatureId.OI:        NormalizedFeature('EX', 'S1', FeatureId.OI, 0, 70, 0, 1, self.now),
        }
        # Strong breadth context
        self.ranking_engine._last_breadth = MarketBreadth(self.now, 0.8, 0.8, 0.8, 0.8, 1)

        score, _ = self.ranking_engine._compute_score(norm_state)
        
        expected_breadth_score = 80.0 # (0.8*4)/4 * 100
        expected_base_score = (90 * WEIGHTS['rsi'] + 80 * WEIGHTS['volume'] + 70 * WEIGHTS['oi'])
        expected_final = expected_base_score * (1 - WEIGHTS['breadth']) + expected_breadth_score * WEIGHTS['breadth']
        
        self.assertAlmostEqual(score, expected_final, 2)
        # Check that score with breadth is higher
        score_no_breadth, _ = self.ranking_engine._compute_score(norm_state)
        self.ranking_engine._last_breadth = None
        score_no_breadth, _ = self.ranking_engine._compute_score(norm_state)
        self.assertGreater(score, score_no_breadth)

    def test_ranking_order(self):
        """T7.3: Verify RankingStore sorts symbols correctly."""
        async def run():
            self.mock_norm.states[Exchange.BINANCE] = {
                'S1': { # High score
                    FeatureId.RSI_14_1M: NormalizedFeature('EX', 'S1', FeatureId.RSI_14_1M, 0, 90, 0, 1, self.now),
                    FeatureId.VOLUME_1M: NormalizedFeature('EX', 'S1', FeatureId.VOLUME_1M, 0, 90, 0, 1, self.now),
                    FeatureId.OI:        NormalizedFeature('EX', 'S1', FeatureId.OI, 0, 90, 0, 1, self.now),
                },
                'S2': { # Low score
                    FeatureId.RSI_14_1M: NormalizedFeature('EX', 'S2', FeatureId.RSI_14_1M, 0, 10, 0, 1, self.now),
                    FeatureId.VOLUME_1M: NormalizedFeature('EX', 'S2', FeatureId.VOLUME_1M, 0, 10, 0, 1, self.now),
                    FeatureId.OI:        NormalizedFeature('EX', 'S2', FeatureId.OI, 0, 10, 0, 1, self.now),
                },
            }
            await self.ranking_engine._re_rank_all()
            
            top = self.ranking_store.get_top_n()
            self.assertEqual(len(top), 2)
            self.assertEqual(top[0].symbol, 'S1')
            self.assertEqual(top[0].rank, 1)
            self.assertEqual(top[1].symbol, 'S2')
            self.assertEqual(top[1].rank, 2)
        asyncio.run(run())
        
    def test_missing_features(self):
        """T7.4: Verify symbols with incomplete features are not ranked."""
        async def run():
            self.mock_norm.states[Exchange.BINANCE] = {
                'S1': { # Complete
                    FeatureId.RSI_14_1M: NormalizedFeature('EX', 'S1', FeatureId.RSI_14_1M, 0, 90, 0, 1, self.now),
                    FeatureId.VOLUME_1M: NormalizedFeature('EX', 'S1', FeatureId.VOLUME_1M, 0, 90, 0, 1, self.now),
                    FeatureId.OI:        NormalizedFeature('EX', 'S1', FeatureId.OI, 0, 90, 0, 1, self.now),
                },
                'S2': { # Missing OI
                    FeatureId.RSI_14_1M: NormalizedFeature('EX', 'S2', FeatureId.RSI_14_1M, 0, 10, 0, 1, self.now),
                    FeatureId.VOLUME_1M: NormalizedFeature('EX', 'S2', FeatureId.VOLUME_1M, 0, 10, 0, 1, self.now),
                },
            }
            await self.ranking_engine._re_rank_all()
            
            top = self.ranking_store.get_top_n()
            self.assertEqual(len(top), 1)
            self.assertEqual(top[0].symbol, 'S1')
        asyncio.run(run())

    def test_top_n_truncation(self):
        """T7.5: Verify RankingStore only stores top N symbols."""
        async def run():
            states = {}
            for i in range(10): # Create 10 symbols
                states[f'S{i}'] = {
                    FeatureId.RSI_14_1M: NormalizedFeature('EX', f'S{i}', FeatureId.RSI_14_1M, 0, 100-i*10, 0, 1, self.now),
                    FeatureId.VOLUME_1M: NormalizedFeature('EX', f'S{i}', FeatureId.VOLUME_1M, 0, 100-i*10, 0, 1, self.now),
                    FeatureId.OI:        NormalizedFeature('EX', f'S{i}', FeatureId.OI, 0, 100-i*10, 0, 1, self.now),
                }
            self.mock_norm.states[Exchange.BINANCE] = states
            
            await self.ranking_engine._re_rank_all()
            
            top = self.ranking_store.get_top_n()
            stats = self.ranking_store.stats()
            
            self.assertEqual(len(top), 5) # top_n=5
            self.assertEqual(stats['ranked_symbols'], 5)
            self.assertEqual(top[0].symbol, 'S0') # Highest score
            self.assertEqual(top[4].symbol, 'S4') # 5th highest
        asyncio.run(run())

if __name__ == '__main__':
    unittest.main()
