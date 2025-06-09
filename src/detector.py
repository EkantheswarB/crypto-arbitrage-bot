from config_loader import load_config

class ArbitrageDetector:
    def __init__(self, config_path = "config/settings.yaml"):
        self.config = load_config(config_path)
        self.min_spread_pct = self.config['arbitrage']['min_spread_percentage']
        self.trade_amount_usd = self.config['trade']['amount_usd']
        self.fee_pct = self.config['trade']['fee_percentage']

    def find_opportunity(self, prices:dict):
        if len(prices) < 2:
            return None  # Need atleast 2 exchanges to compare
        
        opportunities = []


        #compare all exchange pairs
        exchanges = list(prices.keys())
        for i in range(len(exchanges)):
            for j in range(i+1,len(exchanges)):
                ex_a = exchanges[i]
                ex_b = exchanges[j]
                price_a = prices[ex_a]
                price_b = prices[ex_b]

                #check both directions

                for buy_ex, sell_ex, buy_price, sell_price in [
                    (ex_a,ex_b,price_a,price_b),
                    (ex_b,ex_a,price_b,price_a)
                ]:
                    spread_pct = ((sell_price - buy_price)/buy_price)*100
                    if spread_pct >=self.min_spread_pct:
                        est_profit = (sell_price - buy_price) * (1 - self.fee_pct / 100) * (self.trade_amount_usd / buy_price)
                        opportunities.append({
                            'buy_from': buy_ex,
                            'sell_to':sell_ex,
                            'buy_price':buy_price,
                            'sell_price':sell_price,
                            'spread_pct':round(spread_pct,2),
                            'estimated_profit_usd':round(est_profit,2)
                        })
        return opportunities if opportunities else None
    

# For standalone test

if __name__ == "__main__":
    sample_prices = {
        'coinbase': 64500,
        'binance': 64800
    }

    detector = ArbitrageDetector()
    opps = detector.find_opportunity(sample_prices)
    print("Opportunities: ", opps)