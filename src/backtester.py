import ccxt
import pandas as pd
from datetime import datetime, timedelta, timezone
import time
from detector import ArbitrageDetector
from executor import TradeExecutor
from config_loader import load_config


def fetch_historical_prices(exchange, symbol, timeframe='5m', since_minutes=43200):  # 30 days
    end_time = int(datetime.now().timestamp() * 1000)
    since = int((datetime.now() - timedelta(minutes=since_minutes)).timestamp() * 1000)
    all_data = []

    print(f"Fetching historical candles for {symbol} from {exchange.id}...")

    while since < end_time:
        try:
            batch = exchange.fetch_ohlcv(symbol, timeframe=timeframe, since=since, limit=1000)
            if not batch:
                break

            all_data += batch
            since = batch[-1][0] + 1  # move past the last timestamp

            # Be nice to the API
            time.sleep(exchange.rateLimit / 1000)

        except Exception as e:
            print(f"Error fetching batch: {e}")
            break

    df = pd.DataFrame(all_data, columns=["timestamp", "open", "high", "low", "close", "volume"])
    df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
    df.set_index("timestamp", inplace=True)
    return df


if __name__ == "__main__":
    coinbase = ccxt.coinbase()
    binanceus = ccxt.binanceus()

    config = load_config()
    trade_amount = config['trade']['amount_usd']
    initial_balance = config['trade'].get('initial_usd', 10000)

    print("Fetching Coinbase data...")
    df_cb = fetch_historical_prices(coinbase, "BTC/USD", since_minutes=129600)  # 30 days

    print("Fetching BinanceUS data...")
    df_bn = fetch_historical_prices(binanceus, "BTC/USDT", since_minutes=129600)  # 30 days

    if not df_cb.empty and not df_bn.empty:
        cb_close = df_cb[['close']].rename(columns={"close": "close_coinbase"})
        bn_close = df_bn[['close']].rename(columns={"close": "close_binance"})
        merged = pd.merge(cb_close, bn_close, left_index=True, right_index=True)
        print(merged.head())

        # Init detector + executor
        detector = ArbitrageDetector()
        executor = TradeExecutor(trade_amount_usd=trade_amount)

        # Stats
        trade_count = 0
        wins = 0
        losses = 0
        print("Running backtest...")

        for timestamp, row in merged.iterrows():
            prices = {
                'coinbase': row['close_coinbase'],
                'binance': row['close_binance']
            }

            opportunities = detector.find_opportunity(prices)
            if opportunities:
                trade = executor.execute(opportunities)
                print(f"Trade object: {trade}")
                if trade and all(k in trade for k in ['buy_from', 'sell_to', 'profit_usd']):
                    trade['timestamp'] = timestamp.isoformat()
                    print(f"[{timestamp}] Trade executed: Profit = ${trade['profit_usd']}")
                    trade_count += 1

                    if trade['profit_usd'] > 0:
                        wins += 1
                    else:
                        losses += 1
                else:
                    print(f"[{timestamp}] Trade execution returned an incomplete object: {trade}")

        # Summary
        print("Backtest complete")
        print(f"Total Trades: {trade_count}")
        print(f"Winning Trades: {wins}")
        print(f"Losing Trades: {losses}")
        print(f"Final Virtual Balance: ${executor.get_balance()}")

        # Total Profit Earned
        total_profit = executor.get_balance() - initial_balance
        print(f"\U0001f4b0 Total Profit Earned: ${round(total_profit, 2)}")

        # Total Fees Paid
        print(f"Total Fees Paid: ${executor.get_total_fees()}")

        # Save history
        history = executor.get_history()
        if history:
            # Average profit margin per trade
            profit_margins = [
                (trade['profit_usd'] / trade['amount_usd']) * 100
                for trade in history if trade['amount_usd'] > 0
            ]
            avg_profit_margin = sum(profit_margins) / len(profit_margins)
            print(f"\U0001f4ca Average Profit Margin per Trade: {round(avg_profit_margin, 4)}%")

            pd.DataFrame(history).to_csv("backtest_trade_history.csv", index=False)
            print("Trade history saved to backtest_trade_history.csv")
        else:
            print("No trades were executed. History not saved.")

    else:
        print("Could not fetch both data sources.")
