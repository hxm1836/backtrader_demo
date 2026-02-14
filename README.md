# MiniTrader

MiniTrader is a lightweight Python backtesting framework for strategy development, indicator research, performance analysis, and visualization.

## Installation

```bash
pip install -e .
```

## Quick Start (SMA Cross, 10 lines)

```python
import minitrader as mt
c=mt.Cerebro(); c.adddata(mt.CSVFeed("examples/sample_data.csv", date_col="Date"))
class S(mt.Strategy):
    params={"f":10,"s":30}
    def __init__(self,datas,broker,**k): super().__init__(datas,broker,**k); self.a=mt.ind.SMA(self.data.close,self.p.f); self.b=mt.ind.SMA(self.data.close,self.p.s); self.x=mt.ind.CrossOver(self.a,self.b)
    def next(self): self.buy(size=10) if self.x[0]>0 and self.position.size==0 else (self.close() if self.x[0]<0 and self.position.size>0 else None)
c.addstrategy(S); c.run(); c.plot()
```

## Supported Indicators

- `SMA`
- `EMA`
- `RSI`
- `MACD`
- `BollingerBands`
- `ATR`
- `CrossOver`
- `Stochastic`

## Supported Analyzers

- `ReturnsAnalyzer`
- `SharpeAnalyzer`
- `DrawdownAnalyzer`
- `TradeAnalyzer`

## Optimization

Grid-search optimization is supported:

```python
cerebro.optstrategy(MyStrategy, fast_period=range(5, 20), slow_period=range(20, 40))
results = cerebro.run()  # sorted by final_value desc, prints top 10
```
