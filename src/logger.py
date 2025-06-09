import logging
import os
from config_loader import load_config

def setup_logger(name=__name__,config_path="config/settings.yaml" ):
    config = load_config(config_path)
    log_config = config.get('logging',{})
    log_level = getattr(logging,log_config.get('level','INFO').upper(),logging.INFO)
    log_file = log_config.get('file','data/logs/arb_bot.log')

    # Ensure log directory exists

    os.makedirs(os.path.dirname(log_file),exist_ok=True)

    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(log_level)

    # Prevent duplicate handlers
    if not logger.handlers:
        # Console handler
        ch = logging.StreamHandler()
        ch.setLevel(log_level)
        ch_formatter = logging.Formatter('[%(asctime)s][%(levelname)s] %(message)s')
        ch.setFormatter(ch_formatter)

        # File handler
        fh = logging.FileHandler(log_file)
        fh.setLevel(log_level)
        fh.setFormatter(ch_formatter)

        # Add both handlers
        logger.addHandler(ch)
        logger.addHandler(fh)


    return logger

# Example usage

if __name__ == "__main__":
    logger = setup_logger("arb-bot")
    logger.info("Logger initialized successfully")
    logger.debug("This is a debug message")
    logger.error("This is an error")

