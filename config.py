"""
Configuration settings for the Discord Voice Channel Bot
"""
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class BotConfig:
    """Bot configuration class"""
    
    def __init__(self):
        # Bot settings
        self.BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")
        self.GUILD_ID = os.getenv("DISCORD_GUILD_ID")  # Optional: for guild-specific commands
        
        # Voice channel settings
        self.DEFAULT_CHANNEL_NAME = os.getenv("DEFAULT_CHANNEL_NAME", "Temporary Channel")
        self.MAX_CHANNEL_NAME_LENGTH = int(os.getenv("MAX_CHANNEL_NAME_LENGTH", "50"))
        self.TEMP_CATEGORY_NAME = os.getenv("TEMP_CATEGORY_NAME", "Temporary Channels")
        
        # Permission settings
        self.REQUIRED_PERMISSIONS = [
            "manage_channels",
            "connect",
            "speak"
        ]
        
        # Logging settings
        self.LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
        self.LOG_FILE = os.getenv("LOG_FILE", "bot.log")
    
    def validate_config(self):
        """Validate required configuration"""
        if not self.BOT_TOKEN:
            raise ValueError("DISCORD_BOT_TOKEN is required")
        
        return True
