"""
Logging configuration for the Discord Voice Channel Bot
"""
import logging
import os
from datetime import datetime

def setup_logger(name="VoiceChannelBot", level=None):
    """Setup and configure logger for the bot"""
    
    # Get log level from environment or default to INFO
    if level is None:
        level = os.getenv("LOG_LEVEL", "INFO").upper()
    
    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level, logging.INFO))
    
    # Clear existing handlers to avoid duplicates
    logger.handlers.clear()
    
    # Create formatters
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # File handler (optional)
    log_file = os.getenv("LOG_FILE")
    if log_file:
        try:
            file_handler = logging.FileHandler(log_file, encoding='utf-8')
            file_handler.setLevel(logging.DEBUG)
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
        except Exception as e:
            logger.warning(f"Could not create file handler: {e}")
    
    return logger

def log_command_usage(logger, user, command, guild=None):
    """Log command usage for monitoring"""
    guild_info = f" in {guild.name}" if guild else ""
    logger.info(f"Command '{command}' used by {user}{guild_info}")

def log_error(logger, error, context=""):
    """Log errors with context"""
    context_str = f" ({context})" if context else ""
    logger.error(f"Error{context_str}: {error}")
