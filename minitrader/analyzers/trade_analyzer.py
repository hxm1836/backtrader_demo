"""Trade statistics analyzer."""

from __future__ import annotations

from typing import Any

import numpy as np

from ..analyzer import Analyzer


class TradeAnalyzer(Analyzer):
    """Analyze completed trade records from strategy.trades."""

    def __init__(self, strategy, equity_curve: list[tuple[Any, float]], **kwargs: Any) -> None:
        super().__init__(strategy=strategy, equity_curve=equity_curve, **kwargs)
        self._analysis: dict[str, Any] = {}

    def run(self) -> None:
        trades = list(getattr(self.strategy, "trades", []))
        pnls = np.asarray([float(t.get("pnl", 0.0)) for t in trades], dtype=float)
        durations = np.asarray([float(t.get("duration", 0.0)) for t in trades], dtype=float)

        total = int(len(trades))
        won_mask = pnls > 0.0
        lost_mask = pnls < 0.0
        won = int(np.sum(won_mask))
        lost = int(np.sum(lost_mask))

        avg_profit = float(np.mean(pnls[won_mask])) if won > 0 else 0.0
        avg_loss = float(np.mean(pnls[lost_mask])) if lost > 0 else 0.0

        gross_profit = float(np.sum(pnls[won_mask])) if won > 0 else 0.0
        gross_loss = float(np.sum(pnls[lost_mask])) if lost > 0 else 0.0
        if gross_loss < 0.0:
            profit_factor = float(gross_profit / abs(gross_loss)) if abs(gross_loss) > 0.0 else 0.0
        else:
            profit_factor = float("inf") if gross_profit > 0.0 else 0.0

        largest_win = float(np.max(pnls)) if total > 0 else 0.0
        largest_loss = float(np.min(pnls)) if total > 0 else 0.0
        avg_duration = float(np.mean(durations)) if durations.size > 0 else 0.0
        win_rate = float(won / total) if total > 0 else 0.0

        self._analysis = {
            "total_trades": total,
            "won": won,
            "lost": lost,
            "win_rate": win_rate,
            "avg_profit": avg_profit,
            "avg_loss": avg_loss,
            "profit_factor": profit_factor,
            "largest_win": largest_win,
            "largest_loss": largest_loss,
            "avg_trade_duration": avg_duration,
        }

    def get_analysis(self) -> dict[str, Any]:
        return self._analysis
