"""
Discord Voice Channel Bot
Manages temporary voice channels with slash commands
"""
import discord
from discord.ext import commands, tasks
import asyncio
from config import BotConfig
from commands.voice_channels import VoiceChannelCommands
from utils.logger import setup_logger

class VoiceChannelBot(commands.Bot):
    def __init__(self):
        # Set up intents
        intents = discord.Intents.default()
        intents.voice_states = True
        intents.guilds = True
        
        super().__init__(
            command_prefix='!',  # Fallback prefix, we'll use slash commands
            intents=intents,
            help_command=None
        )
        
        self.config = BotConfig()
        self.logger = setup_logger()
        self.temp_channels = {}  # Track temporary channels {channel_id: creator_id}
        
    async def setup_hook(self):
        """Setup hook called when bot is starting"""
        # Add voice channel commands
        await self.add_cog(VoiceChannelCommands(self))
        
        # Start the cleanup task
        self.channel_cleanup.start()
        
        # Sync slash commands
        try:
            synced = await self.tree.sync()
            self.logger.info(f"Synced {len(synced)} slash commands")
        except Exception as e:
            self.logger.error(f"Failed to sync slash commands: {e}")
    
    async def on_ready(self):
        """Called when bot is ready and connected"""
        self.logger.info(f'{self.user} has connected to Discord!')
        self.logger.info(f'Bot is in {len(self.guilds)} servers')
        
        # Set bot activity
        activity = discord.Activity(
            type=discord.ActivityType.listening,
            name="for /voice commands"
        )
        await self.change_presence(activity=activity)
    
    async def on_voice_state_update(self, member, before, after):
        """Monitor voice state changes to clean up empty channels"""
        # Check if someone left a voice channel
        if before.channel and before.channel.id in self.temp_channels:
            await self.check_and_cleanup_channel(before.channel)
    
    async def check_and_cleanup_channel(self, channel):
        """Check if a temporary channel is empty and delete it"""
        if not channel or channel.id not in self.temp_channels:
            return
        
        # Wait 10 seconds before checking if channel is empty
        await asyncio.sleep(10)
        
        try:
            # Refresh channel data
            channel = self.get_channel(channel.id)
            if not channel:
                # Channel already deleted
                self.temp_channels.pop(channel.id, None)
                return
            
            # Check if channel is empty (no members)
            if len(channel.members) == 0:
                self.logger.info(f"Deleting empty temporary channel: {channel.name}")
                await channel.delete(reason="Temporary channel is empty")
                self.temp_channels.pop(channel.id, None)
                
        except discord.NotFound:
            # Channel already deleted
            self.temp_channels.pop(channel.id, None)
        except discord.Forbidden:
            self.logger.error(f"No permission to delete channel: {channel.name}")
        except Exception as e:
            channel_name = channel.name if channel else "Unknown"
            self.logger.error(f"Error cleaning up channel {channel_name}: {e}")
    
    @tasks.loop(minutes=5)
    async def channel_cleanup(self):
        """Periodic cleanup task to remove empty temporary channels"""
        channels_to_remove = []
        
        for channel_id in list(self.temp_channels.keys()):
            channel = self.get_channel(channel_id)
            if channel:
                await self.check_and_cleanup_channel(channel)
            else:
                # Channel doesn't exist anymore
                channels_to_remove.append(channel_id)
        
        # Clean up tracked channels that no longer exist
        for channel_id in channels_to_remove:
            self.temp_channels.pop(channel_id, None)
    
    @channel_cleanup.before_loop
    async def before_cleanup(self):
        """Wait for bot to be ready before starting cleanup task"""
        await self.wait_until_ready()
    
    async def on_command_error(self, ctx, error):
        """Global error handler"""
        if isinstance(error, commands.CommandNotFound):
            return  # Ignore unknown commands
        
        self.logger.error(f"Command error: {error}")
        
        if ctx.interaction:
            try:
                await ctx.interaction.followup.send(
                    f"An error occurred: {str(error)}", 
                    ephemeral=True
                )
            except:
                pass
