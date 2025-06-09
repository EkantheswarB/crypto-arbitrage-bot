import requests
from config_loader import load_config

class Notifier:
    def __init__(self,config_path = "config/settings.yaml"):
        self.config = load_config(config_path)
        tg_config = self.config.get('notifier',{}).get('telegram',{})
        self.enabled = tg_config.get('enabled', False)
        self.bot_token = tg_config.get('bot_token')
        self.chat_id = tg_config.get('chat_id')

    def send_telegram(self, message:str):
        if not self.enabled or not self.bot_token or not self.chat_id:
            return
        url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
        payload = {
            'chat_id': self.chat_id,
            'text':message,
            'parse_mode':'Markdown'
        }

        try:
            response = requests.post(url=url,json=payload)
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            print(f"Telegram notification failed: {e}")

# Example test

if __name__ == '__main__':
    notifier = Notifier()
    notifier.send_telegram("Test message from your Crypto Arbitrage Bot :)")