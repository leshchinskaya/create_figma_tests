import logging
import sys # Import sys for StreamHandler's default stream

# Define SUCCESS log level
SUCCESS_LEVEL_NUM = 25  # Arbitrary number between INFO (20) and WARNING (30)
logging.addLevelName(SUCCESS_LEVEL_NUM, "SUCCESS")
# Make it available as an attribute on the logging module, which EmojiFormatter uses
logging.SUCCESS = SUCCESS_LEVEL_NUM

class EmojiFormatter(logging.Formatter):
    EMOJIS = {
        logging.DEBUG: "🐛",
        logging.INFO: "ℹ️",
        logging.WARNING: "⚠️",
        logging.ERROR: "❌",
        logging.CRITICAL: "💥",
        logging.SUCCESS: "✅",
    }

    LOG_COLORS = {
        logging.DEBUG: "\033[94m",  # Blue
        logging.INFO: "\033[92m",  # Green
        logging.WARNING: "\033[93m",  # Yellow
        logging.ERROR: "\033[91m",  # Red
        logging.CRITICAL: "\033[91m\033[1m",  # Bold Red
        logging.SUCCESS: "\033[92m\033[1m",  # Bold Green
        "RESET": "\033[0m",
    }

    def format(self, record):
        emoji = self.EMOJIS.get(record.levelno, "")
        
        # Color for console, not for file
        if hasattr(record, 'stream') and record.stream is sys.stdout: # Crude check for console stream
             color = self.LOG_COLORS.get(record.levelno, "")
             reset_color = self.LOG_COLORS.get("RESET", "")
             record.msg = f"{color}{emoji} {record.msg}{reset_color}"
        else:
            record.msg = f"{emoji} {record.msg}"
            
        return super().format(record)

# Add success method to Logger class
# This allows logger.success("message") to be called
def success_method(self, message, *args, **kws):
    if self.isEnabledFor(logging.SUCCESS):
        # The logger._log method expects args to be a tuple.
        self._log(logging.SUCCESS, message, args, **kws)

logging.Logger.success = success_method

def setup_logger(name: str = __name__, log_file: str = "figma_to_jira.log", level: int = logging.INFO) -> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.propagate = False # To avoid duplicate logs if root logger is also configured

    # Clear existing handlers to avoid duplication if this function is called multiple times
    if logger.hasHandlers():
        logger.handlers.clear()

    # Create a stream handler for console output
    stream_handler = logging.StreamHandler(sys.stdout) # Explicitly use sys.stdout
    stream_formatter = EmojiFormatter('%(asctime)s - %(levelname)s - %(message)s')
    stream_handler.setFormatter(stream_formatter)
    logger.addHandler(stream_handler)

    # Create a file handler for outputting to a file
    try:
        file_handler = logging.FileHandler(log_file, mode='a', encoding='utf-8')
        file_formatter = EmojiFormatter('%(asctime)s - %(levelname)s - %(message)s') # File formatter without colors
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)
    except IOError as e:
        # Fallback to console if file cannot be opened
        print(f"Error setting up file handler for logging: {e}. Logging to console only for errors.", file=sys.stderr)


    return logger

# Optionally, provide a default logger instance for easy import
# logger = setup_logger() 