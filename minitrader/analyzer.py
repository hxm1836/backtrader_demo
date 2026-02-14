"""Base analyzer abstractions for MiniTrader."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from .strategy import Strategy


class Analyzer(ABC):
    """Base analyzer that consumes strategy and equity curve."""

    def __init__(self, strategy: Strategy, equity_curve: list[tuple[Any, float]], **kwargs: Any) -> None:
        self.strategy = strategy
        self.equity_curve = equity_curve

    @abstractmethod
    def run(self) -> None:
        """Run analyzer calculation."""

    @abstractmethod
    def get_analysis(self) -> dict[str, Any]:
        """Return computed analysis dict."""

    def print_analysis(self) -> None:
        """Pretty print analysis results."""
        analysis = self.get_analysis()
        for key, value in analysis.items():
            print(f"{key}: {value}")
