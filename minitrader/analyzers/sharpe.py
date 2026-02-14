"""Sharpe ratio analyzer."""

from __future__ import annotations

from typing import Any

import numpy as np

from ..analyzer import Analyzer


class SharpeAnalyzer(Analyzer):
    """Analyze annualized Sharpe ratio."""

    def __init__(
        self,
        strategy,
        equity_curve: list[tuple[Any, float]],
        risk_free_rate: float = 0.02,
        **kwargs: Any,
    ) -> None:
        super().__init__(strategy=strategy, equity_curve=equity_curve, **kwargs)
        self.risk_free_rate = float(risk_free_rate)
        self._analysis: dict[str, Any] = {"sharpe_ratio": 0.0}

    def run(self) -> None:
        values = np.asarray([v for _, v in self.equity_curve], dtype=float)
        if values.size < 2 or values[0] == 0.0:
            self._analysis = {"sharpe_ratio": 0.0}
            return

        daily_returns = (values[1:] / values[:-1]) - 1.0
        periods = len(daily_returns)
        if periods < 2:
            self._analysis = {"sharpe_ratio": 0.0}
            return

        total_return = (values[-1] / values[0]) - 1.0
        annual_return = (1.0 + total_return) ** (252.0 / periods) - 1.0
        annual_vol = float(np.std(daily_returns, ddof=1) * np.sqrt(252.0))
        if annual_vol == 0.0:
            self._analysis = {"sharpe_ratio": 0.0}
            return

        sharpe_ratio = float((annual_return - self.risk_free_rate) / annual_vol)
        self._analysis = {"sharpe_ratio": sharpe_ratio}

    def get_analysis(self) -> dict[str, Any]:
        return self._analysis
