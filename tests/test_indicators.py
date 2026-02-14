import numpy as np
import pandas as pd

import minitrader as mt


def _feed_from_close(close: list[float]) -> mt.PandasFeed:
    n = len(close)
    df = pd.DataFrame(
        {
            "datetime": pd.date_range("2024-01-01", periods=n, freq="D"),
            "open": close,
            "high": [x + 1.0 for x in close],
            "low": [x - 1.0 for x in close],
            "close": close,
            "volume": [100] * n,
        }
    )
    feed = mt.PandasFeed(df)
    for _ in range(n):
        feed.advance()
    return feed


def _ema_manual(values: np.ndarray, period: int) -> np.ndarray:
    alpha = 2.0 / (period + 1.0)
    out = np.zeros_like(values, dtype=float)
    out[0] = values[0]
    for i in range(1, len(values)):
        out[i] = alpha * values[i] + (1.0 - alpha) * out[i - 1]
    return out


def test_sma_known_values():
    feed = _feed_from_close([1, 2, 3, 4, 5])
    sma = mt.ind.SMA(feed.close, period=3)
    expected = np.array([np.nan, np.nan, 2.0, 3.0, 4.0])
    np.testing.assert_allclose(sma.sma.values, expected, equal_nan=True)


def test_ema_known_values():
    vals = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
    feed = _feed_from_close(vals.tolist())
    ema = mt.ind.EMA(feed.close, period=3)
    expected = _ema_manual(vals, period=3)
    np.testing.assert_allclose(ema.ema.values, expected, atol=1e-12)


def test_rsi_macd_and_other_indicators():
    close = np.array([1, 2, 3, 2, 2.5, 3.5, 3, 4], dtype=float)
    feed = _feed_from_close(close.tolist())

    rsi = mt.ind.RSI(feed.close, period=3)
    delta = np.diff(close, prepend=close[0])
    gains = np.where(delta > 0.0, delta, 0.0)
    losses = np.where(delta < 0.0, -delta, 0.0)
    alpha = 2.0 / 4.0
    avg_gain = _ema_manual(gains, period=3)
    avg_loss = _ema_manual(losses, period=3)
    rs = np.divide(avg_gain, avg_loss, out=np.full_like(avg_gain, np.inf), where=avg_loss != 0.0)
    expected_rsi = 100.0 - (100.0 / (1.0 + rs))
    np.testing.assert_allclose(rsi.rsi.values, expected_rsi, atol=1e-12)

    macd = mt.ind.MACD(feed.close, fast_period=3, slow_period=5, signal_period=2)
    fast = _ema_manual(close, period=3)
    slow = _ema_manual(close, period=5)
    expected_macd = fast - slow
    expected_signal = _ema_manual(expected_macd, period=2)
    np.testing.assert_allclose(macd.macd.values, expected_macd, atol=1e-12)
    np.testing.assert_allclose(macd.signal.values, expected_signal, atol=1e-12)
    np.testing.assert_allclose(macd.histogram.values, expected_macd - expected_signal, atol=1e-12)

    bb = mt.ind.BollingerBands(feed.close, period=3, devfactor=2.0)
    assert np.isnan(bb.mid.values[1])
    assert np.isfinite(bb.mid.values[-1])

    atr = mt.ind.ATR(feed, period=3)
    assert np.isnan(atr.atr.values[1])
    assert np.isfinite(atr.atr.values[-1])

    stoch = mt.ind.Stochastic(feed, k_period=3, d_period=2)
    assert np.isnan(stoch.k.values[1])
    assert np.isfinite(stoch.k.values[-1])

    sma_short = mt.ind.SMA(feed.close, period=2)
    sma_long = mt.ind.SMA(feed.close, period=3)
    cross = mt.ind.CrossOver(sma_short, sma_long)
    assert set(np.unique(np.nan_to_num(cross.cross.values))).issubset({-1.0, 0.0, 1.0})
