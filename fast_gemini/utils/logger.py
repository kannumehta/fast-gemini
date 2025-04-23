import logging
import os
import sys
from logging.handlers import RotatingFileHandler
from typing import Optional

class FastGeminiLogger:
    _instance: Optional['FastGeminiLogger'] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(FastGeminiLogger, cls).__new__(cls)
            cls._instance._initialize_logger()
        return cls._instance
    
    def _initialize_logger(self):
        self.logger = logging.getLogger('fast_gemini')
        
        # Get log level from environment variable, default to INFO
        log_level = os.getenv('FAST_GEMINI_LOG_LEVEL', 'INFO').upper()
        self.logger.setLevel(getattr(logging, log_level))
        
        # Create formatters
        console_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s'
        )
        
        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(console_formatter)
        self.logger.addHandler(console_handler)
        
        # File handler
        log_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'logs')
        os.makedirs(log_dir, exist_ok=True)
        file_handler = RotatingFileHandler(
            os.path.join(log_dir, 'fast_gemini.log'),
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5
        )
        file_handler.setFormatter(file_formatter)
        self.logger.addHandler(file_handler)
    
    @classmethod
    def get_logger(cls) -> logging.Logger:
        return cls().logger

# Convenience functions
def get_logger() -> logging.Logger:
    return FastGeminiLogger.get_logger()

def debug(msg: str, *args, **kwargs):
    get_logger().debug(msg, *args, **kwargs)

def info(msg: str, *args, **kwargs):
    get_logger().info(msg, *args, **kwargs)

def warning(msg: str, *args, **kwargs):
    get_logger().warning(msg, *args, **kwargs)

def error(msg: str, *args, **kwargs):
    get_logger().error(msg, *args, **kwargs)

def critical(msg: str, *args, **kwargs):
    get_logger().critical(msg, *args, **kwargs) 