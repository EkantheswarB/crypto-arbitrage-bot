import ccxt
import time
from config_loader import load_config

class PriceAggregator:
    def __init__(self, config_path="config/settings.yaml"):
        self.config = load_config(config_path)
        self.poll_interval = self.config["poll_interval"]
        self.exchanges= {}

        if self.config['exchanges']['coinbase']['enabled']:
            self.exchanges['coinbase'] = ccxt.coinbase()
        
        if self.config['exchanges']['binance']['enabled']:
            self.exchanges['binance']=ccxt.binanceus()
    
    def fetch_prices(self,symbol='BTC/USD'):
        prices={}
        for name, exchange in self.exchanges.items():
            try:
                ticker = exchange.fetch_ticker(symbol)
                prices[name]=ticker['last']
            except Exception as e:
                print(f"Error fetching price from {name}:{e}")
        return prices

# For standalone testing

if __name__ == "__main__":
    aggregator = PriceAggregator()
    while True:
        prices = aggregator.fetch_prices()
        print(f"Prices:{prices}")
        time.sleep(aggregator.poll_interval)
        