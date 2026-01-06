import logging
from logging.handlers import RotatingFileHandler
import sys
from datetime import datetime
import json


class TradingLogger:
    """Structured logging for trading bot"""
    
    def __init__(self, log_file: str = 'bot.log'):
        self.log_file = log_file
        self.setup_logger()
    
    def setup_logger(self):
        """Configure logging system"""
        # Create formatters
        detailed_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        # File handler with rotation
        file_handler = RotatingFileHandler(
            self.log_file,
            maxBytes=10485760,  # 10MB
            backupCount=5
        )
        file_handler.setFormatter(detailed_formatter)
        file_handler.setLevel(logging.INFO)
        
        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(detailed_formatter)
        console_handler.setLevel(logging.WARNING)
        
        # Get logger
        self.logger = logging.getLogger('TradingBot')
        self.logger.setLevel(logging.INFO)
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)
    
    def log(self, event_type: str, message: str, level: str = 'INFO', **kwargs):
        """
        Log structured trading event
        
        Args:
            event_type: Type of event (ORDER, ERROR, SYSTEM, etc.)
            message: Log message
            level: Log level (INFO, WARNING, ERROR, etc.)
            **kwargs: Additional structured data
        """
        log_entry = {
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'event_type': event_type,
            'level': level,
            'message': message,
            **kwargs
        }
        
        # Convert to JSON string for file logging
        log_message = json.dumps(log_entry)
        
        if level == 'ERROR':
            self.logger.error(log_message)
        elif level == 'WARNING':
            self.logger.warning(log_message)
        elif level == 'DEBUG':
            self.logger.debug(log_message)
        else:
            self.logger.info(log_message)
    
    def get_recent_logs(self, n: int = 100) -> list:
        """Get recent log entries"""
        try:
            with open(self.log_file, 'r') as f:
                lines = f.readlines()[-n:]
                logs = []
                for line in lines:
                    try:
                        logs.append(json.loads(line.strip()))
                    except:
                        logs.append({'raw': line.strip()})
                return logs
        except FileNotFoundError:
            return []
    
    def clear_logs(self):
        """Clear all logs"""
        open(self.log_file, 'w').close()
        self.log('SYSTEM', 'Logs cleared by user', level='INFO')
