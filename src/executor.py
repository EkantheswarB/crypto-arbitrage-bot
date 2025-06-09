import time
import json
import os
from datetime import datetime, timezone

class TradeExecutor:
    def __init__(self, initial_usd=10000, fee_pct=0.1, trade_amount_usd=1000):
        self.fee_pct = fee_pct  # percent fee per trade side
        self.trade_amount_usd = trade_amount_usd
        self.state_file = "state/trade_state.json"

        # Load from file or set defaults
        if os.path.exists(self.state_file):
            self._load_state()
        else:
            self.usd_balance = initial_usd
            self.total_fees = 0.0
            self.trade_history = []
            self._save_state()

    def execute(self, opportunity: dict):
        if not opportunity:
            return None

        trade = opportunity[0]

        # Check required fields
        required_keys = ['buy_from', 'sell_to', 'buy_price', 'sell_price']
        if not all(k in trade for k in required_keys):
            print(f"[SKIP] Incomplete trade object: {trade}")
            return None

        amount_usd = min(self.usd_balance, self.trade_amount_usd)  # respect config cap
        buy_price = trade['buy_price']
        sell_price = trade['sell_price']

        # Simulate trade with detailed fee tracking
        btc_bought = amount_usd / buy_price
        btc_fee = btc_bought * (self.fee_pct / 100)
        btc_after_fee = btc_bought - btc_fee

        usd_gained = btc_after_fee * sell_price
        usd_fee = usd_gained * (self.fee_pct / 100)
        usd_after_fee = usd_gained - usd_fee

        profit = usd_after_fee - amount_usd

        # Track total fees (converted BTC fee to USD for tracking)
        total_trade_fee = (btc_fee * buy_price) + usd_fee
        self.total_fees += total_trade_fee

        self.usd_balance += profit

        trade_record = {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'buy_from': trade['buy_from'],
            'sell_to': trade['sell_to'],
            'buy_price': buy_price,
            'sell_price': sell_price,
            'amount_usd': amount_usd,
            'profit_usd': round(profit, 2),
            'balance_usd': round(self.usd_balance, 2),
            'fees_paid_usd': round(total_trade_fee, 4)
        }

        self.trade_history.append(trade_record)
        self._save_state()
        print(f"[TRADE EXECUTED] {trade_record}")
        return trade_record

    def get_balance(self):
        return round(self.usd_balance, 2)

    def get_history(self):
        return self.trade_history

    def get_total_fees(self):
        return round(self.total_fees, 2)

    def _save_state(self):
        os.makedirs(os.path.dirname(self.state_file), exist_ok=True)
        state = {
            'usd_balance': self.usd_balance,
            'total_fees': self.total_fees,
            'trade_history': self.trade_history
        }
        with open(self.state_file, 'w') as f:
            json.dump(state, f, indent=2)

    def _load_state(self):
        with open(self.state_file, 'r') as f:
            state = json.load(f)
            self.usd_balance = state.get('usd_balance', 10000)
            self.total_fees = state.get('total_fees', 0.0)
            self.trade_history = state.get('trade_history', [])


if __name__ == "__main__":
    executor = TradeExecutor(trade_amount_usd=10000)

    dummy_opportunity = [{
        'buy_from': 'coinbase',
        'sell_to': 'binance',
        'buy_price': 64000,
        'sell_price': 64500,
        'spread_pct': 0.78,
        'estimated_profit_usd': 7.5
    }]

    executor.execute(dummy_opportunity)
