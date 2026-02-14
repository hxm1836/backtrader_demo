import pandas as pd
import pytest

from minitrader.feed import CSVFeed, PandasFeed


def test_csvfeed_loads_csv(tmp_path):
    csv_file = tmp_path / "bars.csv"
    csv_file.write_text(
        "Date,Open,High,Low,Close,Volume\n"
        "2024-01-01,10,11,9,10.5,1000\n"
        "2024-01-02,10.5,12,10,11,1200\n",
        encoding="utf-8",
    )

    feed = CSVFeed(csv_file, date_col="Date")
    assert len(feed) == 2
    assert feed.advance() is True
    assert feed.close[0] == 10.5


def test_pandasfeed_from_dataframe():
    df = pd.DataFrame(
        {
            "datetime": ["2024-01-01", "2024-01-02"],
            "open": [1, 2],
            "high": [2, 3],
            "low": [0.5, 1.5],
            "close": [1.5, 2.5],
            "volume": [100, 110],
        }
    )
    feed = PandasFeed(df)
    assert len(feed) == 2
    feed.advance()
    assert feed.open[0] == 1


def test_lineseries_relative_indexing():
    df = pd.DataFrame(
        {
            "datetime": ["2024-01-01", "2024-01-02", "2024-01-03"],
            "open": [1, 2, 3],
            "high": [1, 2, 3],
            "low": [1, 2, 3],
            "close": [1, 2, 3],
            "volume": [10, 20, 30],
        }
    )
    feed = PandasFeed(df)
    feed.advance()
    feed.advance()
    assert feed.close[0] == 2
    assert feed.close[-1] == 1


def test_lineseries_future_access_raises():
    df = pd.DataFrame(
        {
            "datetime": ["2024-01-01", "2024-01-02"],
            "open": [1, 2],
            "high": [1, 2],
            "low": [1, 2],
            "close": [1, 2],
            "volume": [10, 20],
        }
    )
    feed = PandasFeed(df)
    feed.advance()
    with pytest.raises(IndexError):
        _ = feed.close[1]
