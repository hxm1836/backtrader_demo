from pathlib import Path

import minitrader as mt


class SMACrossStrategy(mt.Strategy):
    def __init__(self, datas, broker, **kwargs):
        super().__init__(datas, broker, **kwargs)
        self.sma_fast = mt.ind.SMA(self.data.close, period=10)
        self.sma_slow = mt.ind.SMA(self.data.close, period=30)
        self.cross = mt.ind.CrossOver(self.sma_fast, self.sma_slow)

    def next(self):
        signal = self.cross[0]
        if signal > 0 and self.position.size == 0:
            self.buy(size=50)
        elif signal < 0 and self.position.size > 0:
            self.close()


def main():
    csv_path = Path(__file__).resolve().parent / "sample_data.csv"
    cerebro = mt.Cerebro()
    cerebro.broker.setcash(100000)
    cerebro.broker.setcommission(0.001)
    cerebro.adddata(mt.CSVFeed(csv_path, date_col="Date"), name="SAMPLE")
    cerebro.addstrategy(SMACrossStrategy)
    results = cerebro.run()
    print(f"Final equity: {cerebro.broker.value:.2f}")
    cerebro.plot(strategy=results[0], price_mode="candlestick")


if __name__ == "__main__":
    main()
