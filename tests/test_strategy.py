import numpy as np
import pandas as pd

import minitrader as mt
from minitrader.order import Direction, OrderStatus


class SMACrossStrategy(mt.Strategy):
    params = {"fast_period": 5, "slow_period": 20}

    def __init__(self, datas, broker, **kwargs):
        super().__init__(datas, broker, **kwargs)
        self.sma_fast = mt.ind.SMA(self.data.close, period=self.p.fast_period)
        self.sma_slow = mt.ind.SMA(self.data.close, period=self.p.slow_period)
        self.cross = mt.ind.CrossOver(self.sma_fast, self.sma_slow)

    def next(self):
        signal = self.cross[0]
        if signal > 0 and self.position.size == 0:
            self.buy(size=10)
        elif signal < 0 and self.position.size > 0:
            self.sell(size=10)


def test_sma_cross_end_to_end():
    n = 140
    x = np.arange(n, dtype=float)
    close = 100.0 + 0.12 * x + 4.0 * np.sin(x / 6.0)
    df = pd.DataFrame(
        {
            "datetime": pd.date_range("2020-01-01", periods=n, freq="D"),
            "open": close + np.sin(x / 7.0) * 0.3,
            "high": close + 1.0,
            "low": close - 1.0,
            "close": close,
            "volume": 1000 + (x * 2).astype(int),
        }
    )

    cerebro = mt.Cerebro()
    cerebro.broker.setcash(10000)
    cerebro.adddata(mt.PandasFeed(df), name="TEST")
    cerebro.addstrategy(SMACrossStrategy)
    results = cerebro.run()
    strategy = results[0]

    completed = {}
    for o in strategy.orders:
        if o.status == OrderStatus.COMPLETED:
            completed[o.ref] = o

    completed_orders = list(completed.values())
    assert any(o.direction == Direction.BUY for o in completed_orders)
    assert any(o.direction == Direction.SELL for o in completed_orders)
    assert 7000 < cerebro.broker.value < 20000


def test_optstrategy_returns_sorted_results():
    n = 80
    x = np.arange(n, dtype=float)
    close = 100.0 + 0.1 * x + 3.0 * np.sin(x / 4.0)
    df = pd.DataFrame(
        {
            "datetime": pd.date_range("2021-01-01", periods=n, freq="D"),
            "open": close,
            "high": close + 1.0,
            "low": close - 1.0,
            "close": close,
            "volume": 1000,
        }
    )

    cerebro = mt.Cerebro()
    cerebro.broker.setcash(10000)
    cerebro.adddata(mt.PandasFeed(df), name="TEST")
    cerebro.optstrategy(SMACrossStrategy, fast_period=range(3, 5), slow_period=range(6, 8))
    results = cerebro.run()

    assert len(results) == 4
    assert all("params" in r and "final_value" in r for r in results)
    vals = [r["final_value"] for r in results]
    assert vals == sorted(vals, reverse=True)
