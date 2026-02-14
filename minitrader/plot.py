"""Visualization utilities for MiniTrader."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


@dataclass
class MiniPlot:
    """TradingView-like multi-panel plot for one strategy result."""

    strategy: Any
    equity_curve: list[tuple[Any, float]]
    price_mode: str = "candlestick"

    BG = "#1a1a2e"
    FG = "#ffffff"
    GRID = (0.7, 0.7, 0.7, 0.2)
    UP = "#4caf50"
    DOWN = "#ef5350"

    def plot(self, savefig: str | None = None) -> None:
        """Render full report plot and optionally save figure."""
        data = self.strategy.data0
        n = len(self.equity_curve)
        if n <= 0:
            raise ValueError("No equity curve data to plot. Run backtest first.")

        dates = pd.to_datetime(np.asarray(data.datetime.values[:n]))
        opens = np.asarray(data.open.values[:n], dtype=float)
        highs = np.asarray(data.high.values[:n], dtype=float)
        lows = np.asarray(data.low.values[:n], dtype=float)
        closes = np.asarray(data.close.values[:n], dtype=float)
        volumes = np.asarray(data.volume.values[:n], dtype=float)
        equity = np.asarray([v for _, v in self.equity_curve], dtype=float)
        dd_base = np.maximum.accumulate(equity)

        plt.style.use("default")
        fig = plt.figure(figsize=(16, 10), facecolor=self.BG, constrained_layout=True)
        gs = fig.add_gridspec(10, 1, hspace=0.05)
        ax_price = fig.add_subplot(gs[0:6, 0])
        ax_vol = fig.add_subplot(gs[6:7, 0], sharex=ax_price)
        ax_ind = fig.add_subplot(gs[7:8, 0], sharex=ax_price)
        ax_eq = fig.add_subplot(gs[8:10, 0], sharex=ax_price)

        for ax in (ax_price, ax_vol, ax_ind, ax_eq):
            ax.set_facecolor(self.BG)
            ax.grid(True, color=self.GRID)
            ax.tick_params(colors=self.FG, labelsize=9)
            for spine in ax.spines.values():
                spine.set_color((1, 1, 1, 0.15))

        x = mdates.date2num(dates.to_pydatetime())
        self._plot_price(ax_price, x, opens, highs, lows, closes)
        self._plot_ma_indicators(ax_price, x, n)
        self._plot_signals(ax_price, x)

        vol_colors = np.where(closes >= opens, self.UP, self.DOWN)
        ax_vol.bar(x, volumes, color=vol_colors, width=0.7, alpha=0.75)
        ax_vol.set_ylabel("Vol", color=self.FG)

        self._plot_separate_indicators(ax_ind, x, n)
        ax_ind.set_ylabel("Ind", color=self.FG)

        ax_eq.plot(x, equity, color="#40c4ff", linewidth=1.8, label="Equity")
        ax_eq.fill_between(x, equity, dd_base, where=equity < dd_base, color=self.DOWN, alpha=0.22, label="Drawdown")
        ax_eq.set_ylabel("Equity", color=self.FG)
        ax_eq.legend(loc="upper left", facecolor=self.BG, edgecolor=(1, 1, 1, 0.2), labelcolor=self.FG)

        locator = mdates.AutoDateLocator(minticks=6, maxticks=12)
        formatter = mdates.ConciseDateFormatter(locator)
        ax_eq.xaxis.set_major_locator(locator)
        ax_eq.xaxis.set_major_formatter(formatter)
        plt.setp(ax_price.get_xticklabels(), visible=False)
        plt.setp(ax_vol.get_xticklabels(), visible=False)
        plt.setp(ax_ind.get_xticklabels(), visible=False)

        ax_price.set_title("MiniTrader Backtest Report", color=self.FG, loc="left", fontsize=13)
        if savefig:
            fig.savefig(savefig, dpi=150, facecolor=self.BG)
            plt.close(fig)
            return
        plt.show()

    def _plot_price(self, ax: Any, x: np.ndarray, opens: np.ndarray, highs: np.ndarray, lows: np.ndarray, closes: np.ndarray) -> None:
        if self.price_mode == "line":
            ax.plot(x, closes, color="#80cbc4", linewidth=1.6, label="Close")
            ax.legend(loc="upper left", facecolor=self.BG, edgecolor=(1, 1, 1, 0.2), labelcolor=self.FG)
            return

        width = 0.65
        for xi, o, h, l, c in zip(x, opens, highs, lows, closes):
            color = self.UP if c >= o else self.DOWN
            ax.vlines(xi, l, h, color=color, linewidth=1.0, alpha=0.9)
            body_bottom = min(o, c)
            body_height = abs(c - o)
            if body_height == 0.0:
                body_height = 1e-6
            rect = plt.Rectangle((xi - width / 2.0, body_bottom), width, body_height, color=color, alpha=0.9)
            ax.add_patch(rect)

    def _plot_ma_indicators(self, ax: Any, x: np.ndarray, n: int) -> None:
        for ind in self._collect_indicators():
            name = ind.__class__.__name__
            if name == "SMA":
                ax.plot(x, ind.sma.values[:n], linewidth=1.2, color="#ffca28", label="SMA")
            elif name == "EMA":
                ax.plot(x, ind.ema.values[:n], linewidth=1.2, color="#26c6da", label="EMA")
            elif name == "BollingerBands":
                mid = ind.mid.values[:n]
                top = ind.top.values[:n]
                bot = ind.bot.values[:n]
                ax.plot(x, mid, linewidth=1.1, color="#b39ddb", label="BB Mid")
                ax.plot(x, top, linewidth=0.9, color="#9575cd", alpha=0.9, label="BB Top")
                ax.plot(x, bot, linewidth=0.9, color="#9575cd", alpha=0.9, label="BB Bot")

        handles, labels = ax.get_legend_handles_labels()
        if handles:
            ax.legend(loc="upper left", facecolor=self.BG, edgecolor=(1, 1, 1, 0.2), labelcolor=self.FG, ncol=2, fontsize=8)

    def _plot_signals(self, ax: Any, x: np.ndarray) -> None:
        date_to_x = {pd.Timestamp(d).to_pydatetime(): xi for d, xi in zip(pd.to_datetime(np.asarray(self.strategy.data0.datetime.values[: len(x)])), x)}
        buy_x: list[float] = []
        buy_y: list[float] = []
        sell_x: list[float] = []
        sell_y: list[float] = []
        seen_refs: set[int] = set()

        for order in getattr(self.strategy, "orders", []):
            ref = getattr(order, "ref", None)
            if isinstance(ref, int) and ref in seen_refs:
                continue
            if getattr(order, "status", None) is None or str(order.status.value) != "COMPLETED":
                continue
            if getattr(order, "data_name", None) != getattr(self.strategy.data0, "_name", "data0"):
                continue
            dt = getattr(order, "executed_dt", None)
            px = getattr(order, "executed_price", None)
            if dt is None or px is None:
                continue
            key = pd.Timestamp(dt).to_pydatetime()
            xi = date_to_x.get(key)
            if xi is None:
                continue
            if order.isbuy():
                buy_x.append(xi)
                buy_y.append(float(px))
            else:
                sell_x.append(xi)
                sell_y.append(float(px))
            if isinstance(ref, int):
                seen_refs.add(ref)

        if buy_x:
            ax.scatter(buy_x, buy_y, marker="^", color=self.UP, s=50, zorder=5, label="Buy")
        if sell_x:
            ax.scatter(sell_x, sell_y, marker="v", color=self.DOWN, s=50, zorder=5, label="Sell")

    def _plot_separate_indicators(self, ax: Any, x: np.ndarray, n: int) -> None:
        has_rsi = False
        for ind in self._collect_indicators():
            name = ind.__class__.__name__
            if name == "RSI":
                has_rsi = True
                ax.plot(x, ind.rsi.values[:n], color="#ffd54f", linewidth=1.1, label="RSI")
            elif name == "Stochastic":
                ax.plot(x, ind.k.values[:n], color="#4dd0e1", linewidth=1.0, label="%K")
                ax.plot(x, ind.d.values[:n], color="#ff8a65", linewidth=1.0, label="%D")

        if has_rsi:
            ax.axhline(70, color=self.DOWN, linestyle="--", linewidth=0.9, alpha=0.7)
            ax.axhline(30, color=self.UP, linestyle="--", linewidth=0.9, alpha=0.7)
            ax.set_ylim(0, 100)

        handles, labels = ax.get_legend_handles_labels()
        if handles:
            ax.legend(loc="upper left", facecolor=self.BG, edgecolor=(1, 1, 1, 0.2), labelcolor=self.FG, fontsize=8)

    def _collect_indicators(self) -> list[Any]:
        indicators: list[Any] = []
        for value in self.strategy.__dict__.values():
            if hasattr(value, "lines") and hasattr(value, "period"):
                indicators.append(value)
            elif isinstance(value, (list, tuple)):
                for item in value:
                    if hasattr(item, "lines") and hasattr(item, "period"):
                        indicators.append(item)
            elif isinstance(value, dict):
                for item in value.values():
                    if hasattr(item, "lines") and hasattr(item, "period"):
                        indicators.append(item)
        return indicators


def plot(strategy: Any, equity_curve: list[tuple[Any, float]], **kwargs: Any) -> None:
    """Convenience function for cerebro.plot delegation."""
    savefig = kwargs.pop("savefig", None)
    MiniPlot(strategy=strategy, equity_curve=equity_curve, **kwargs).plot(savefig=savefig)
