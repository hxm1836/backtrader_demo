from pathlib import Path

import minitrader as mt


class MultiIndicatorStrategy(mt.Strategy):
    def __init__(self, datas, broker, **kwargs):
        super().__init__(datas, broker, **kwargs)
        self.macd = mt.ind.MACD(self.data.close)
        self.rsi = mt.ind.RSI(self.data.close, period=14)
        self.bb = mt.ind.BollingerBands(self.data.close, period=20, devfactor=2.0)
        self.macd_cross = mt.ind.CrossOver(self.macd.macd, self.macd.signal)

    def next(self):
        price = self.data.close[0]
        buy_cond = self.macd_cross[0] > 0 and self.rsi[0] < 50 and price <= self.bb.bot[0] * 1.01
        sell_cond = self.macd_cross[0] < 0 or self.rsi[0] > 70 or price >= self.bb.top[0] * 0.99

        if buy_cond and self.position.size == 0:
            self.buy(size=30)
        elif sell_cond and self.position.size > 0:
            self.close()


def main():
    csv_path = Path(__file__).resolve().parent / "sample_data.csv"
    cerebro = mt.Cerebro()
    cerebro.broker.setcash(100000)
    cerebro.broker.setcommission(0.001)
    cerebro.adddata(mt.CSVFeed(csv_path, date_col="Date"), name="SAMPLE")
    cerebro.addstrategy(MultiIndicatorStrategy)
    results = cerebro.run()
    print(f"Final equity: {cerebro.broker.value:.2f}")
    cerebro.plot(strategy=results[0], price_mode="candlestick")


if __name__ == "__main__":
    main()
