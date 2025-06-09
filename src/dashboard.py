import pandas as pd
import streamlit as st
import time
from datetime import datetime, timezone
from aggregator import PriceAggregator
from detector import ArbitrageDetector
from executor import TradeExecutor
from notifier import Notifier


spread_history = []  # Stores spread % over time

# Set Streamlit page config
st.set_page_config(page_title = "Crypto Arbitrage Bot", layout = "wide")
st.title("Crypto Arbitrage Bot Dashboard")

# Initialize components
aggregator = PriceAggregator()
detector = ArbitrageDetector()
executor = TradeExecutor()
notifier = Notifier()

placeholder = st.empty()

while True:
    with placeholder.container():

        # Fetch prices
        prices = aggregator.fetch_prices()

        if 'coinbase' in prices and 'binance' in prices:
            cb_price = prices['coinbase']
            bn_price = prices['binance']
            spread_pct = ((bn_price - cb_price) / cb_price) * 100
            spread_history.append({
                "timestamp": datetime.now(),
                "spread_pct": spread_pct
            })

        st.subheader("Live prices")
        st.write(prices)

        st.subheader("📉 Binance vs Coinbase Spread (%)")

        if len(spread_history) > 1:
            df = pd.DataFrame(spread_history)
            df.set_index("timestamp", inplace=True)
            st.line_chart(df["spread_pct"])
        else:
            st.info("Waiting for more data to show spread chart...")


        # Detect arbitrage
        opportunities = detector.find_opportunity(prices)

        st.subheader("Detected opportunities")
        if opportunities:
            for opp in opportunities:
                st.success(f"{opp['buy_from']} -> {opp['sell_to']}:"
                           f"${opp['buy_price']} -> {opp['sell_price']}"
                           f"Spread: {opp['spread_pct']}% | "
                           f"Est. Profit: $ {opp['estimated_profit_usd']}")
            top = opportunities[0]
            message = (
                f"🚀 Arbitrage Opportunity Detected!\n"
                f"Buy from: {top['buy_from']} at ${top['buy_price']}\n"
                f"Sell to: {top['sell_to']} at ${top['sell_price']}\n"
                f"Spread: {top['spread_pct']}%\n"
                f"Est. Profit: ${top['estimated_profit_usd']}"

            )
            notifier.send_telegram(message=message)
                
        else:
            st.info("No profitable opportunities at the moment")

        
        # Simulate the execution

        if opportunities:
            trade_result = executor.execute(opportunities)
            if trade_result:
                trade_msg = (
                    f"✅ Trade Executed!\n"
                    f"Bought from: {trade_result['buy_from']} at ${trade_result['buy_price']}\n"
                    f"Sold to: {trade_result['sell_to']} at ${trade_result['sell_price']}\n"
                    f"Profit: ${trade_result['profit_usd']}\n"
                    f"New Balance: ${trade_result['balance_usd']}"
                )
                notifier.send_telegram(trade_msg)
            st.subheader("Last Trade Executed")
            st.json(trade_result)
        # Filter trades executed today
        today = datetime.now(timezone.utc).date()
        todays_trades = [
            trade for trade in executor.get_history()
            if datetime.fromisoformat(trade['timestamp']).date() == today
        ]

        # Calculate today's profit
        todays_profit = sum(trade['profit_usd'] for trade in todays_trades)


        # Show balance
        st.subheader("Virtual USD balance")
        st.metric(label="Current Balance", value = f"${executor.get_balance()}")

        # Today's P&L
        st.subheader("📅 Today's P&L")
        st.metric(label="Profit / Loss", value=f"${round(todays_profit, 2)}")

        # Trade history

        st.subheader("Trade History")
        history = executor.get_history()
        if history:
            st.dataframe(history[::-1])  # Latest first
        else:
            st.write("No trades yet")

    # Pause before next update
    time.sleep(aggregator.poll_interval)
