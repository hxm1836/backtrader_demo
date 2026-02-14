from datetime import datetime

from minitrader.broker import Broker
from minitrader.order import Direction, Order, OrderStatus, OrderType


def _bar(open_: float, high: float, low: float, close: float) -> dict[str, float]:
    return {"open": open_, "high": high, "low": low, "close": close}


def test_market_order_executes():
    broker = Broker(cash=10000, commission=0.001)
    order = Order(data_name="AAPL", order_type=OrderType.MARKET, direction=Direction.BUY, size=10)
    broker.submit_order(order)
    broker.execute_pending_orders({"AAPL": _bar(100, 101, 99, 100)}, datetime(2024, 1, 1))
    assert order.status == OrderStatus.COMPLETED
    assert order.executed_price == 100
    assert broker.positions["AAPL"].size == 10


def test_limit_order_executes_when_price_matches():
    broker = Broker(cash=10000, commission=0.001)
    order = Order(data_name="AAPL", order_type=OrderType.LIMIT, direction=Direction.BUY, size=5, price=98)
    broker.submit_order(order)
    broker.execute_pending_orders({"AAPL": _bar(100, 105, 97, 103)}, datetime(2024, 1, 1))
    assert order.status == OrderStatus.COMPLETED
    assert order.executed_price == 98


def test_limit_order_stays_pending_when_price_not_met():
    broker = Broker(cash=10000, commission=0.001)
    order = Order(data_name="AAPL", order_type=OrderType.LIMIT, direction=Direction.BUY, size=5, price=95)
    broker.submit_order(order)
    broker.execute_pending_orders({"AAPL": _bar(100, 105, 96, 103)}, datetime(2024, 1, 1))
    assert order.status == OrderStatus.ACCEPTED


def test_buy_rejected_when_cash_insufficient():
    broker = Broker(cash=50, commission=0.001)
    order = Order(data_name="AAPL", order_type=OrderType.MARKET, direction=Direction.BUY, size=1)
    broker.submit_order(order)
    broker.execute_pending_orders({"AAPL": _bar(100, 101, 99, 100)}, datetime(2024, 1, 1))
    assert order.status == OrderStatus.REJECTED
    assert broker.cash == 50


def test_commission_calculation():
    broker = Broker(cash=10000, commission=0.001)
    order = Order(data_name="AAPL", order_type=OrderType.MARKET, direction=Direction.BUY, size=10)
    broker.submit_order(order)
    broker.execute_pending_orders({"AAPL": _bar(100, 101, 99, 100)}, datetime(2024, 1, 1))
    assert order.commission == 1.0
    assert broker.cash == 10000 - 1000 - 1.0
