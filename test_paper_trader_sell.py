import pytest

from paper_trader import PaperTrader


def test_sell_option_reduces_position_and_updates_balance():
    trader = PaperTrader(initial_balance=1000)
    option = {
        'price': 2.0,
        'option_type': 'call',
        'strike': 100,
        'expiry_days': 30,
    }
    trader.buy_option(option, quantity=1)
    initial_cash_after_buy = trader.balance

    sell_row = dict(option, price=3.5)
    trader.sell_option(sell_row, quantity=1)

    assert trader.balance == pytest.approx(initial_cash_after_buy + 3.5 * 100)
    assert trader.positions == []

    sell_log = trader.transaction_history[-1]
    assert sell_log['action'] == 'SELL'
    assert sell_log['quantity'] == 1
    assert sell_log['price'] == 3.5
    assert sell_log['realized_pnl'] == pytest.approx((3.5 - 2.0) * 100)
