"""
Main entry point for the Discord Voice Channel Bot
"""
import asyncio
import os
from bot import VoiceChannelBot
from utils.logger import setup_logger

def main():
    """Main function to start the Discord bot"""
    logger = setup_logger()
    
    # Check if bot token is available
    bot_token = os.getenv("DISCORD_BOT_TOKEN")
    if not bot_token:
        logger.error("DISCORD_BOT_TOKEN environment variable not found!")
        logger.error("Please create a .env file with your bot token or set the environment variable.")
        return
    
    # Create and run the bot
    bot = VoiceChannelBot()
    
    try:
        logger.info("Starting Discord Voice Channel Bot...")
        bot.run(bot_token)
    except Exception as e:
        logger.error(f"Failed to start bot: {e}")

if __name__ == "__main__":
    main()
