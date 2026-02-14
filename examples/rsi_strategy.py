import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import minitrader as mt


class RSIStrategy(mt.Strategy):
    def __init__(self, datas, broker, **kwargs):
        super().__init__(datas, broker, **kwargs)
        self.rsi = mt.ind.RSI(self.data.close, period=14)

    def next(self):
        rsi_val = self.rsi[0]
        if rsi_val < 30 and self.position.size == 0:
            self.buy(size=40)
        elif rsi_val > 70 and self.position.size > 0:
            self.close()


def main():
    csv_path = Path(__file__).resolve().parent / "sample_data.csv"
    cerebro = mt.Cerebro()
    cerebro.broker.setcash(100000)
    cerebro.adddata(mt.CSVFeed(csv_path, date_col="Date"), name="SAMPLE")
    cerebro.addstrategy(RSIStrategy)
    results = cerebro.run()
    print(f"Final equity: {cerebro.broker.value:.2f}")
    cerebro.plot(strategy=results[0], price_mode="line")


if __name__ == "__main__":
    main()
