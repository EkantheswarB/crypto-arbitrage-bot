import streamlit as st
import pandas as pd
import time
import io
import uuid
from datetime import datetime, timezone
from aggregator import PriceAggregator
from detector import ArbitrageDetector
from executor import TradeExecutor
from notifier import Notifier
from config_loader import load_config


# Set Streamlit page config
st.set_page_config(page_title="Crypto Arbitrage Bot", layout="wide")
st.title("📈 Crypto Arbitrage Bot Dashboard")

# Load settings
config = load_config()
trade_amount = config['trade']['amount_usd']

# Initialize components
aggregator = PriceAggregator()
detector = ArbitrageDetector()
executor = TradeExecutor(trade_amount_usd=trade_amount)
notifier = Notifier()

# For charting
spread_history = []

placeholder = st.empty()

# Filter date inputs outside loop to avoid key conflict
start_date = st.sidebar.date_input("Start Date", key="unique_filter_start_date")
end_date = st.sidebar.date_input("End Date", key="unique_filter_end_date")

while True:
    with placeholder.container():
        # Fetch prices
        prices = aggregator.fetch_prices()

        # Track spread between Coinbase and Binance
        if 'coinbase' in prices and 'binance' in prices:
            cb_price = prices['coinbase']
            bn_price = prices['binance']
            spread_pct = ((bn_price - cb_price) / cb_price) * 100
            spread_history.append({
                "timestamp": datetime.now(),
                "spread_pct": spread_pct
            })

        st.subheader("🚱 Live Prices")
        st.write(prices)

        # Spread chart
        st.subheader("📉 Binance vs Coinbase Spread (%)")
        if len(spread_history) > 1:
            df = pd.DataFrame(spread_history)
            df.set_index("timestamp", inplace=True)
            st.line_chart(df["spread_pct"])
        else:
            st.info("Waiting for more data to show spread chart...")

        # Detect arbitrage
        opportunities = detector.find_opportunity(prices)

        st.subheader("🚨 Detected Opportunities")
        if opportunities:
            for opp in opportunities:
                st.success(f"{opp['buy_from']} → {opp['sell_to']}: "
                           f"${opp['buy_price']} → ${opp['sell_price']} | "
                           f"Spread: {opp['spread_pct']}% | "
                           f"Est. Profit: ${opp['estimated_profit_usd']}")

            # Notify top opportunity
            top = opportunities[0]
            msg = (
                f"🚀 *Arbitrage Opportunity Detected!*\n"
                f"Buy from: *{top['buy_from']}* at `${top['buy_price']}`\n"
                f"Sell to: *{top['sell_to']}* at `${top['sell_price']}`\n"
                f"Spread: *{top['spread_pct']}%*\n"
                f"Est. Profit: *${top['estimated_profit_usd']}*"
            )
            notifier.send_telegram(msg)

            # Simulate trade
            trade_result = executor.execute(opportunities)

            # Notify trade execution
            if trade_result:
                trade_msg = (
                    f"✅ *Trade Executed!*\n"
                    f"Bought from: *{trade_result['buy_from']}* at `${trade_result['buy_price']}`\n"
                    f"Sold to: *{trade_result['sell_to']}* at `${trade_result['sell_price']}`\n"
                    f"Profit: *${trade_result['profit_usd']}*\n"
                    f"New Balance: *${trade_result['balance_usd']}*"
                )
                notifier.send_telegram(trade_msg)

            st.subheader("✅ Last Trade Executed")
            st.json(trade_result)

        else:
            st.info("No profitable opportunities at the moment.")

        # Show current balance
        st.subheader("💰 Virtual USD Balance")
        st.metric(label="Current Balance", value=f"${executor.get_balance()}")

        # Show today's P&L
        history = executor.get_history()
        todays_profit = 0.0
        if history:
            today = datetime.now(timezone.utc).date()
            todays_trades = [
                trade for trade in history
                if datetime.fromisoformat(trade['timestamp']).date() == today
            ]
            todays_profit = sum(trade['profit_usd'] for trade in todays_trades)

        st.subheader("📅 Today's P&L")
        st.metric(label="Profit / Loss", value=f"${round(todays_profit, 2)}")

        # Show trade history
        st.subheader("📜 Trade History")
        if history:
            st.dataframe(history[::-1])
        else:
            st.write("No trades yet.")

        # Filter and download trade history
        st.subheader("📅 Filter & Download Trade History")
        filtered_trades = []
        if history:
            for trade in history:
                trade_date = datetime.fromisoformat(trade['timestamp']).date()
                if start_date <= trade_date <= end_date:
                    filtered_trades.append(trade)

            if filtered_trades:
                st.dataframe(filtered_trades[::-1])

                df_filtered = pd.DataFrame(filtered_trades)
                csv_buffer = io.StringIO()
                df_filtered.to_csv(csv_buffer, index=False)

                st.download_button(
                    label="Download Filtered Trade History",
                    data=csv_buffer.getvalue(),
                    file_name="filtered_trade_history.csv",
                    mime="text/csv",
                    key=f"filtered_trade_history_download_{uuid.uuid4()}"
                )
            else:
                st.info("No trades found in the selected range.")
        else:
            st.warning("No trade history available.")

    # Pause before next update
    time.sleep(aggregator.poll_interval)
