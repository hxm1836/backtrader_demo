"""Core backtesting engine for MiniTrader."""

from __future__ import annotations

from datetime import datetime
from itertools import product
from typing import Any

from .broker import Broker
from .feed import DataFeed, PandasFeed
from .sizer import Sizer
from .strategy import Strategy


class Cerebro:
    """Coordinate datas, strategy, broker, and analyzers."""

    def __init__(self) -> None:
        """Initialize an empty backtest engine."""
        self.datas: list[DataFeed] = []
        self._strategy_specs: list[tuple[type[Strategy], dict[str, Any]]] = []
        self._sizer_spec: tuple[type[Sizer], dict[str, Any]] | None = None
        self._analyzer_specs: list[tuple[type[Any], dict[str, Any]]] = []
        self._opt_strategy_spec: tuple[type[Strategy], dict[str, Any]] | None = None
        self.broker: Broker = Broker(cash=10000.0, commission=0.001)
        self._equity_curve: list[tuple[datetime | Any, float]] = []
        self._last_strategies: list[Strategy] = []
        self._opt_results: list[dict[str, Any]] = []

    def adddata(self, data: DataFeed, name: str | None = None) -> DataFeed:
        """Add a data feed to the engine."""
        idx = len(self.datas)
        data_name = name or f"data{idx}"
        setattr(data, "_name", data_name)
        self.datas.append(data)
        return data

    def addstrategy(self, strategy_cls: type[Strategy], **kwargs: Any) -> None:
        """Register a strategy class and its init kwargs."""
        self._strategy_specs.append((strategy_cls, kwargs))
        self._opt_strategy_spec = None

    def optstrategy(self, strategy_cls: type[Strategy], **kwargs: Any) -> None:
        """Register parameter-grid optimization for one strategy class."""
        self._opt_strategy_spec = (strategy_cls, kwargs)
        self._strategy_specs = []

    def addsizer(self, sizer_cls: type[Sizer], **kwargs: Any) -> None:
        """Set the global sizer for all strategy instances."""
        self._sizer_spec = (sizer_cls, kwargs)

    def addanalyzer(self, analyzer_cls: type[Any], **kwargs: Any) -> None:
        """Register analyzer class and kwargs."""
        self._analyzer_specs.append((analyzer_cls, kwargs))

    def run(self) -> list[Any]:
        """Run backtest or optimization and return strategy/results list."""
        if self._opt_strategy_spec is not None:
            return self._run_optimization()

        if not self.datas:
            raise ValueError("No data feed added. Call adddata() before run().")
        if not self._strategy_specs:
            raise ValueError("No strategy added. Call addstrategy() before run().")

        # Step 1: create broker instance from configured values.
        broker = Broker(cash=self.broker.cash, commission=self.broker.commission)
        self.broker = broker

        strategies: list[Strategy] = []
        for strategy_cls, kwargs in self._strategy_specs:
            strat = strategy_cls(datas=self.datas, broker=broker, **kwargs)
            if self._sizer_spec is not None:
                sizer_cls, sizer_kwargs = self._sizer_spec
                strat.sizer = sizer_cls(**sizer_kwargs)
            strategies.append(strat)

        for strat in strategies:
            strat.start()

        min_bars = min(len(data) for data in self.datas)
        if min_bars <= 0:
            for strat in strategies:
                strat.stop()
            return strategies

        warmup = max((self._compute_warmup_period(strat) for strat in strategies), default=0)
        self._equity_curve = []

        for bar_index in range(min_bars):
            for data in self.datas:
                data.advance()

            dt = self._current_dt()
            self._update_indicators(strategies)
            current_data = {self._get_data_name(data): data for data in self.datas}
            broker.execute_pending_orders(current_data=current_data, dt=dt)
            self._dispatch_broker_notifications(strategies)

            if (bar_index + 1) >= max(1, warmup):
                for strat in strategies:
                    strat.next()
                self._dispatch_broker_notifications(strategies)

            current_prices = {}
            for data in self.datas:
                try:
                    current_prices[self._get_data_name(data)] = float(data.close[0])
                except Exception:
                    continue
            broker.value = broker.get_value(current_prices)
            self._equity_curve.append((dt, broker.value))

        for strat in strategies:
            strat.stop()

        self._run_analyzers(strategies)
        self._last_strategies = strategies
        self._opt_results = []
        return strategies

    def plot(self, **kwargs: Any) -> Any:
        """Delegate plotting to plot module."""
        if not self._last_strategies:
            raise ValueError("No strategy result found. Run cerebro.run() before plot().")
        from .plot import MiniPlot

        strategy = kwargs.pop("strategy", None) or self._last_strategies[0]
        savefig = kwargs.pop("savefig", None)
        return MiniPlot(strategy=strategy, equity_curve=self._equity_curve, **kwargs).plot(savefig=savefig)

    @staticmethod
    def _get_data_name(data: DataFeed) -> str:
        name = getattr(data, "_name", None)
        if not name:
            raise ValueError("Data feed name is missing. Use adddata(..., name=...).")
        return str(name)

    def _current_dt(self) -> datetime | Any:
        primary = self.datas[0]
        try:
            return primary.datetime[0]
        except Exception:
            return datetime.utcnow()

    def _update_indicators(self, strategies: list[Strategy]) -> None:
        for strat in strategies:
            for indicator in self._collect_indicator_like(strat):
                update_fn = getattr(indicator, "update", None)
                if callable(update_fn):
                    update_fn()

    def _compute_warmup_period(self, strategy: Strategy) -> int:
        max_period = 0
        for indicator in self._collect_indicator_like(strategy):
            period = getattr(indicator, "period", 0)
            if isinstance(period, int) and period > max_period:
                max_period = period
        return max_period

    def _collect_indicator_like(self, strategy: Strategy) -> list[Any]:
        indicators: list[Any] = []
        for value in strategy.__dict__.values():
            if hasattr(value, "period") or hasattr(value, "update"):
                indicators.append(value)
            elif isinstance(value, (list, tuple)):
                for item in value:
                    if hasattr(item, "period") or hasattr(item, "update"):
                        indicators.append(item)
            elif isinstance(value, dict):
                for item in value.values():
                    if hasattr(item, "period") or hasattr(item, "update"):
                        indicators.append(item)
        return indicators

    def _run_analyzers(self, strategies: list[Strategy]) -> None:
        if not self._analyzer_specs:
            return
        for strat in strategies:
            analyzers: dict[str, Any] = {}
            for analyzer_cls, kwargs in self._analyzer_specs:
                analyzer = self._build_analyzer(analyzer_cls, strat, self._equity_curve, kwargs)
                run_fn = getattr(analyzer, "run", None)
                if callable(run_fn):
                    run_fn()
                analyzers[analyzer_cls.__name__] = analyzer
            strat.analyzers = analyzers

    @staticmethod
    def _build_analyzer(
        analyzer_cls: type[Any],
        strategy: Strategy,
        equity_curve: list[tuple[Any, float]],
        kwargs: dict[str, Any],
    ) -> Any:
        try:
            return analyzer_cls(strategy=strategy, equity_curve=equity_curve, **kwargs)
        except TypeError:
            try:
                return analyzer_cls(strategy, equity_curve, **kwargs)
            except TypeError:
                return analyzer_cls(**kwargs)

    def _dispatch_broker_notifications(self, strategies: list[Strategy]) -> None:
        """Dispatch broker order/trade updates to all strategy callbacks."""
        orders = self.broker.consume_order_updates()
        trades = self.broker.consume_trade_updates()

        if not orders and not trades:
            return

        for strat in strategies:
            for order in orders:
                strat.orders.append(order)
                strat.notify_order(order)
            for trade in trades:
                strat.trades.append(trade)
                strat.notify_trade(trade)

    def _run_optimization(self) -> list[dict[str, Any]]:
        """Run parameter grid search and return results sorted by final value."""
        if not self.datas:
            raise ValueError("No data feed added. Call adddata() before run().")
        if self._opt_strategy_spec is None:
            return []

        strategy_cls, grid_kwargs = self._opt_strategy_spec
        param_names, value_lists = self._expand_grid(grid_kwargs)
        combos = [dict(zip(param_names, values)) for values in product(*value_lists)]
        results: list[dict[str, Any]] = []

        for params in combos:
            datas = self._clone_datas()
            broker = Broker(cash=self.broker.cash, commission=self.broker.commission)
            strat = strategy_cls(datas=datas, broker=broker, **params)
            if self._sizer_spec is not None:
                sizer_cls, sizer_kwargs = self._sizer_spec
                strat.sizer = sizer_cls(**sizer_kwargs)

            strat.start()
            min_bars = min(len(data) for data in datas)
            warmup = self._compute_warmup_period(strat)
            equity_curve: list[tuple[datetime | Any, float]] = []

            for bar_index in range(min_bars):
                for data in datas:
                    data.advance()

                current_data = {self._get_data_name(data): data for data in datas}
                dt = datas[0].datetime[0]
                self._update_indicators([strat])
                broker.execute_pending_orders(current_data=current_data, dt=dt)
                self._dispatch_broker_notifications([strat])

                if (bar_index + 1) >= max(1, warmup):
                    strat.next()
                    self._dispatch_broker_notifications([strat])

                prices = {self._get_data_name(data): float(data.close[0]) for data in datas}
                broker.value = broker.get_value(prices)
                equity_curve.append((dt, broker.value))

            strat.stop()
            self._equity_curve = equity_curve
            self._run_analyzers([strat])
            results.append({"params": params, "final_value": float(broker.value), "strategy": strat})

        results.sort(key=lambda x: x["final_value"], reverse=True)
        self._opt_results = results
        self._last_strategies = [r["strategy"] for r in results]
        self._print_top_optimization(results)
        return results

    @staticmethod
    def _expand_grid(grid_kwargs: dict[str, Any]) -> tuple[list[str], list[list[Any]]]:
        """Normalize optimization kwargs into parameter names and value lists."""
        names = list(grid_kwargs.keys())
        values: list[list[Any]] = []
        for name in names:
            raw = grid_kwargs[name]
            if isinstance(raw, range):
                values.append(list(raw))
            elif isinstance(raw, (list, tuple, set)):
                values.append(list(raw))
            else:
                values.append([raw])
        return names, values

    def _clone_datas(self) -> list[DataFeed]:
        """Deep clone currently added data feeds for isolated optimization runs."""
        clones: list[DataFeed] = []
        for idx, data in enumerate(self.datas):
            cloned = PandasFeed(data._df.copy(), date_col="datetime")
            setattr(cloned, "_name", getattr(data, "_name", f"data{idx}"))
            clones.append(cloned)
        return clones

    @staticmethod
    def _print_top_optimization(results: list[dict[str, Any]], topn: int = 10) -> None:
        """Print top-N optimization parameter combinations."""
        print("\nOptimization Top Results")
        print("-" * 60)
        for i, row in enumerate(results[:topn], start=1):
            print(f"{i:>2}. final_value={row['final_value']:.2f} params={row['params']}")
