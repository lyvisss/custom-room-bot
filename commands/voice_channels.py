"""
Voice Channel Management Commands
"""
import discord
from discord.ext import commands
from discord import app_commands
import re

class PlatformSelect(discord.ui.Select):
    def __init__(self, platforms):
        options = [
            discord.SelectOption(label=platform, value=platform, emoji="🎮")
            for platform in platforms
        ]
        super().__init__(placeholder="Choose your platform...", options=options)

    async def callback(self, interaction: discord.Interaction):
        selected_platform = self.values[0]
        modal = ChannelCreationModal(selected_platform)
        await interaction.response.send_modal(modal)

class ChannelCreationModal(discord.ui.Modal, title='Create Gaming Voice Channel'):
    def __init__(self, platform):
        super().__init__()
        self.selected_platform = platform
    
    game_name = discord.ui.TextInput(
        label='Game Name',
        placeholder='Mobile Legends, Dota2, LOL, Valorant, or custom game name',
        required=True,
        max_length=50
    )
    
    max_users = discord.ui.TextInput(
        label='Max Users (2-99)',
        placeholder='Enter maximum number of users (default: 10)',
        required=False,
        max_length=2
    )

    async def on_submit(self, interaction: discord.Interaction):
        # Get the voice channel commands cog from the bot
        cog = interaction.client.get_cog('VoiceChannelCommands')
        if cog:
            await cog.create_gaming_channel(interaction, self.selected_platform, self.game_name.value, self.max_users.value)

class ChannelCreationView(discord.ui.View):
    def __init__(self, platforms):
        super().__init__(timeout=300)
        self.add_item(PlatformSelect(platforms))

class VoiceChannelCommands(commands.Cog):
    """Cog for voice channel management commands"""
    
    def __init__(self, bot):
        self.bot = bot
        self.logger = bot.logger
        # Default platforms - can be modified with commands
        self.platforms = ["PC", "Mobile", "Console", "Switch", "PlayStation", "Xbox"]
        # Track channel numbers per platform
        self.platform_counters = {}
        # Track banned users per channel
        self.channel_bans = {}  # {channel_id: [user_ids]}
    
    def sanitize_channel_name(self, name):
        """Sanitize channel name to meet Discord requirements"""
        # Remove invalid characters and limit length
        name = re.sub(r'[^\w\s-]', '', name)
        name = name.strip()
        if len(name) > self.bot.config.MAX_CHANNEL_NAME_LENGTH:
            name = name[:self.bot.config.MAX_CHANNEL_NAME_LENGTH]
        
        # Ensure name is not empty
        if not name:
            name = self.bot.config.DEFAULT_CHANNEL_NAME
        
        return name
    
    async def get_or_create_platform_category(self, guild, platform):
        """Get or create a platform-specific category"""
        category_name = f"🎮 {platform} Gaming"
        
        # Look for existing category
        category = discord.utils.get(guild.categories, name=category_name)
        
        if not category:
            try:
                category = await guild.create_category(
                    category_name,
                    reason=f"Category for {platform} gaming channels"
                )
                self.logger.info(f"Created platform category: {category_name}")
            except discord.Forbidden:
                self.logger.error("No permission to create category")
                return None
            except Exception as e:
                self.logger.error(f"Error creating category: {e}")
                return None
        
        return category

    async def get_or_create_temp_category(self, guild):
        """Get or create the temporary channels category (legacy)"""
        category_name = self.bot.config.TEMP_CATEGORY_NAME
        
        # Look for existing category
        category = discord.utils.get(guild.categories, name=category_name)
        
        if not category:
            try:
                category = await guild.create_category(
                    category_name,
                    reason="Category for temporary voice channels"
                )
                self.logger.info(f"Created temporary channels category: {category_name}")
            except discord.Forbidden:
                self.logger.error("No permission to create category")
                return None
            except Exception as e:
                self.logger.error(f"Error creating category: {e}")
                return None
        
        return category
    
    def check_permissions(self, member, guild):
        """Check if user has required permissions"""
        permissions = member.guild_permissions
        
        required_perms = [
            permissions.connect,
            permissions.speak
        ]
        
        # Check if user has manage_channels or is in a voice channel
        has_manage_channels = permissions.manage_channels
        is_in_voice = member.voice is not None
        
        return all(required_perms) and (has_manage_channels or is_in_voice)
    
    @app_commands.command(name="gaming-channel", description="Create a gaming voice channel with platform and game selection")
    async def gaming_channel_setup(self, interaction: discord.Interaction):
        """Create an interactive gaming voice channel setup"""
        # Check permissions
        if not self.check_permissions(interaction.user, interaction.guild):
            await interaction.response.send_message(
                "❌ You need to be in a voice channel or have 'Manage Channels' permission to create temporary channels.",
                ephemeral=True
            )
            return
        
        # Create embed
        embed = discord.Embed(
            title="🎮 Create Gaming Voice Channel",
            description="Click the button below to set up your gaming voice channel with platform, game, and user limit options!",
            color=discord.Color.blue()
        )
        embed.add_field(
            name="📋 What you'll set:",
            value="• Platform (PC, Mobile, Console)\n• Game name\n• Maximum users\n• Auto-cleanup when empty",
            inline=False
        )
        embed.set_footer(text="Channel will be named: {Platform} - {Game} - {Your Name}")
        
        view = ChannelCreationView(self.platforms)
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

    async def create_gaming_channel(self, interaction: discord.Interaction, platform: str, game_name: str, max_users_str: str):
        """Create the actual gaming voice channel from modal data"""
        await interaction.response.defer()
        
        try:
            # Validate and process max users
            max_users = 10  # default
            if max_users_str and max_users_str.strip():
                try:
                    max_users = int(max_users_str.strip())
                    if max_users < 2:
                        max_users = 2
                    elif max_users > 99:
                        max_users = 99
                except ValueError:
                    max_users = 10
            
            # Sanitize inputs
            platform = self.sanitize_channel_name(platform)
            game_name = self.sanitize_channel_name(game_name)
            
            # Get next room number for this platform
            if platform not in self.platform_counters:
                self.platform_counters[platform] = 0
            self.platform_counters[platform] += 1
            room_number = self.platform_counters[platform]
            
            # Create channel name format: #{Number} - {Game}'s {Owner}
            channel_name = f"#{room_number} - {game_name}'s {interaction.user.display_name}"
            
            # Get or create platform-specific category
            category = await self.get_or_create_platform_category(interaction.guild, platform)
            
            # Enhanced permissions for channel creator
            overwrites = {
                interaction.guild.default_role: discord.PermissionOverwrite(connect=True),
                interaction.user: discord.PermissionOverwrite(
                    connect=True,
                    speak=True,
                    manage_channels=True,
                    move_members=True,
                    mute_members=True,
                    deafen_members=True,
                    priority_speaker=True
                )
            }
            
            voice_channel = await interaction.guild.create_voice_channel(
                channel_name,
                category=category,
                overwrites=overwrites,
                user_limit=max_users,
                reason=f"Gaming voice channel created by {interaction.user}"
            )
            
            # Track the temporary channel
            self.bot.temp_channels[voice_channel.id] = interaction.user.id
            
            self.logger.info(f"Created gaming voice channel: {channel_name} by {interaction.user}")
            
            # Success embed with clickable channel link
            success_embed = discord.Embed(
                title="✅ Gaming Channel Created!",
                description=f"🎮 **Click here to join:** <#{voice_channel.id}>",
                color=discord.Color.green()
            )
            success_embed.add_field(name="📱 Platform", value=platform, inline=True)
            success_embed.add_field(name="🎲 Game", value=game_name, inline=True)
            success_embed.add_field(name="👥 Max Users", value=str(max_users), inline=True)
            success_embed.add_field(name="🛡️ Owner Powers", value="Use `/kick-user`, `/mute-user`, `/ban-user`, `/transfer-owner`", inline=False)
            success_embed.add_field(name="🗑️ Auto-cleanup", value="Channel deletes after 10 seconds when empty", inline=False)
            
            await interaction.followup.send(embed=success_embed, ephemeral=True)
            
        except discord.Forbidden:
            await interaction.followup.send(
                "❌ I don't have permission to create voice channels. Please contact a server administrator.",
                ephemeral=True
            )
        except Exception as e:
            self.logger.error(f"Error creating gaming voice channel: {e}")
            await interaction.followup.send(
                f"❌ An error occurred while creating the voice channel: {str(e)}",
                ephemeral=True
            )

    @app_commands.command(name="create-voice", description="Create a simple temporary voice channel")
    @app_commands.describe(name="Name for the temporary voice channel")
    async def create_voice_channel(self, interaction: discord.Interaction, name: str = None):
        """Create a simple temporary voice channel (legacy command)"""
        await interaction.response.defer()
        
        try:
            # Check permissions
            if not self.check_permissions(interaction.user, interaction.guild):
                await interaction.followup.send(
                    "❌ You need to be in a voice channel or have 'Manage Channels' permission to create temporary channels.",
                    ephemeral=True
                )
                return
            
            # Sanitize channel name
            if not name:
                name = f"{interaction.user.display_name}'s Channel"
            
            channel_name = self.sanitize_channel_name(name)
            
            # Get or create temporary category
            category = await self.get_or_create_temp_category(interaction.guild)
            
            # Create the voice channel
            overwrites = {
                interaction.guild.default_role: discord.PermissionOverwrite(connect=True),
                interaction.user: discord.PermissionOverwrite(
                    connect=True,
                    speak=True,
                    manage_channels=True,
                    move_members=True,
                    mute_members=True
                )
            }
            
            voice_channel = await interaction.guild.create_voice_channel(
                channel_name,
                category=category,
                overwrites=overwrites,
                reason=f"Temporary voice channel created by {interaction.user}"
            )
            
            # Track the temporary channel
            self.bot.temp_channels[voice_channel.id] = interaction.user.id
            
            self.logger.info(f"Created temporary voice channel: {channel_name} by {interaction.user}")
            
            await interaction.followup.send(
                f"✅ Created temporary voice channel: **{channel_name}**\n"
                f"🔗 <#{voice_channel.id}>\n"
                f"📝 The channel will be automatically deleted when empty.",
                ephemeral=True
            )
            
        except discord.Forbidden:
            await interaction.followup.send(
                "❌ I don't have permission to create voice channels. Please contact a server administrator.",
                ephemeral=True
            )
        except Exception as e:
            self.logger.error(f"Error creating voice channel: {e}")
            await interaction.followup.send(
                f"❌ An error occurred while creating the voice channel: {str(e)}",
                ephemeral=True
            )
    
    @app_commands.command(name="delete-voice", description="Delete a temporary voice channel you created")
    async def delete_voice_channel(self, interaction: discord.Interaction):
        """Delete a temporary voice channel"""
        await interaction.response.defer()
        
        try:
            user_id = interaction.user.id
            user_channels = [
                channel_id for channel_id, creator_id in self.bot.temp_channels.items()
                if creator_id == user_id
            ]
            
            if not user_channels:
                await interaction.followup.send(
                    "❌ You don't have any temporary voice channels to delete.",
                    ephemeral=True
                )
                return
            
            # If user is in a voice channel and it's their temp channel, delete it
            if interaction.user.voice and interaction.user.voice.channel:
                current_channel = interaction.user.voice.channel
                if current_channel.id in user_channels:
                    channel_name = current_channel.name
                    await current_channel.delete(reason=f"Deleted by creator: {interaction.user}")
                    self.bot.temp_channels.pop(current_channel.id, None)
                    
                    await interaction.followup.send(
                        f"✅ Deleted temporary voice channel: **{channel_name}**",
                        ephemeral=True
                    )
                    return
            
            # Otherwise, delete the first channel they created
            channel_id = user_channels[0]
            channel = self.bot.get_channel(channel_id)
            
            if channel:
                channel_name = channel.name
                await channel.delete(reason=f"Deleted by creator: {interaction.user}")
                self.bot.temp_channels.pop(channel_id, None)
                
                await interaction.followup.send(
                    f"✅ Deleted temporary voice channel: **{channel_name}**",
                    ephemeral=True
                )
            else:
                # Channel doesn't exist anymore
                self.bot.temp_channels.pop(channel_id, None)
                await interaction.followup.send(
                    "❌ Channel not found. It may have already been deleted.",
                    ephemeral=True
                )
                
        except discord.Forbidden:
            await interaction.followup.send(
                "❌ I don't have permission to delete voice channels.",
                ephemeral=True
            )
        except Exception as e:
            self.logger.error(f"Error deleting voice channel: {e}")
            await interaction.followup.send(
                f"❌ An error occurred while deleting the voice channel: {str(e)}",
                ephemeral=True
            )
    
    @app_commands.command(name="list-temp-channels", description="List all temporary voice channels")
    async def list_temp_channels(self, interaction: discord.Interaction):
        """List all temporary voice channels"""
        await interaction.response.defer()
        
        if not self.bot.temp_channels:
            await interaction.followup.send(
                "📝 No temporary voice channels are currently active.",
                ephemeral=True
            )
            return
        
        embed = discord.Embed(
            title="🔊 Temporary Voice Channels",
            color=discord.Color.blue()
        )
        
        for channel_id, creator_id in self.bot.temp_channels.items():
            channel = self.bot.get_channel(channel_id)
            creator = self.bot.get_user(creator_id)
            
            if channel:
                member_count = len(channel.members)
                embed.add_field(
                    name=f"🔗 {channel.name}",
                    value=f"👤 Created by: {creator.mention if creator else 'Unknown'}\n"
                          f"👥 Members: {member_count}",
                    inline=True
                )
        
        if not embed.fields:
            embed.description = "No active temporary channels found."
        
        await interaction.followup.send(embed=embed, ephemeral=True)
    
    @app_commands.command(name="voice-help", description="Show help for voice channel commands")
    async def voice_help(self, interaction: discord.Interaction):
        """Show help for voice channel commands"""
        embed = discord.Embed(
            title="🔊 Voice Channel Bot Help",
            description="Manage temporary voice channels with these commands:",
            color=discord.Color.green()
        )
        
        embed.add_field(
            name="/create-voice [name]",
            value="Create a temporary voice channel with an optional custom name. "
                  "The channel will be automatically deleted when empty.",
            inline=False
        )
        
        embed.add_field(
            name="/delete-voice",
            value="Delete a temporary voice channel you created.",
            inline=False
        )
        
        embed.add_field(
            name="/list-temp-channels",
            value="Show all currently active temporary voice channels.",
            inline=False
        )
        
        embed.add_field(
            name="/voice-help",
            value="Show this help message.",
            inline=False
        )
        
        embed.add_field(
            name="📋 Requirements",
            value="• You must be in a voice channel OR have 'Manage Channels' permission\n"
                  "• Channel names are automatically sanitized\n"
                  "• Channels auto-delete when empty",
            inline=False
        )
        
        embed.set_footer(text="Bot created for temporary voice channel management")
        
        await interaction.response.send_message(embed=embed, ephemeral=True)



    @app_commands.command(name="kick-user", description="Kick a user from your voice channel")
    @app_commands.describe(user="User to kick from the channel")
    async def kick_user(self, interaction: discord.Interaction, user: discord.Member):
        """Kick a user from the owner's voice channel"""
        await interaction.response.defer()
        
        # Check if user is in a voice channel they own
        if not interaction.user.voice or not interaction.user.voice.channel:
            await interaction.followup.send("❌ You must be in a voice channel to use this command.", ephemeral=True)
            return
        
        channel = interaction.user.voice.channel
        if channel.id not in self.bot.temp_channels or self.bot.temp_channels[channel.id] != interaction.user.id:
            await interaction.followup.send("❌ You can only kick users from channels you created.", ephemeral=True)
            return
        
        if user.voice and user.voice.channel == channel:
            try:
                await user.move_to(None)
                await interaction.followup.send(f"✅ Kicked {user.mention} from the channel.", ephemeral=True)
                self.logger.info(f"{interaction.user} kicked {user} from {channel.name}")
            except discord.Forbidden:
                await interaction.followup.send("❌ I don't have permission to move members.", ephemeral=True)
        else:
            await interaction.followup.send(f"❌ {user.mention} is not in your channel.", ephemeral=True)

    @app_commands.command(name="ban-user", description="Ban a user from joining your voice channel")
    @app_commands.describe(user="User to ban from the channel")
    async def ban_user(self, interaction: discord.Interaction, user: discord.Member):
        """Ban a user from the owner's voice channel"""
        await interaction.response.defer()
        
        # Check if user is in a voice channel they own
        if not interaction.user.voice or not interaction.user.voice.channel:
            await interaction.followup.send("❌ You must be in a voice channel to use this command.", ephemeral=True)
            return
        
        channel = interaction.user.voice.channel
        if channel.id not in self.bot.temp_channels or self.bot.temp_channels[channel.id] != interaction.user.id:
            await interaction.followup.send("❌ You can only ban users from channels you created.", ephemeral=True)
            return
        
        # Add to ban list
        if channel.id not in self.channel_bans:
            self.channel_bans[channel.id] = []
        
        if user.id not in self.channel_bans[channel.id]:
            self.channel_bans[channel.id].append(user.id)
            
            # Update channel permissions
            try:
                await channel.set_permissions(user, connect=False, reason=f"Banned by channel owner {interaction.user}")
                
                # Kick if currently in channel
                if user.voice and user.voice.channel == channel:
                    await user.move_to(None)
                
                await interaction.followup.send(f"✅ Banned {user.mention} from the channel.", ephemeral=True)
                self.logger.info(f"{interaction.user} banned {user} from {channel.name}")
            except discord.Forbidden:
                await interaction.followup.send("❌ I don't have permission to manage channel permissions.", ephemeral=True)
        else:
            await interaction.followup.send(f"❌ {user.mention} is already banned from your channel.", ephemeral=True)

    @app_commands.command(name="mute-user", description="Server mute a user in your voice channel")
    @app_commands.describe(user="User to mute in the channel")
    async def mute_user(self, interaction: discord.Interaction, user: discord.Member):
        """Mute a user in the owner's voice channel"""
        await interaction.response.defer()
        
        # Check if user is in a voice channel they own
        if not interaction.user.voice or not interaction.user.voice.channel:
            await interaction.followup.send("❌ You must be in a voice channel to use this command.", ephemeral=True)
            return
        
        channel = interaction.user.voice.channel
        if channel.id not in self.bot.temp_channels or self.bot.temp_channels[channel.id] != interaction.user.id:
            await interaction.followup.send("❌ You can only mute users in channels you created.", ephemeral=True)
            return
        
        if user.voice and user.voice.channel == channel:
            try:
                await user.edit(mute=not user.voice.mute)
                action = "unmuted" if user.voice.mute else "muted"
                await interaction.followup.send(f"✅ {action.capitalize()} {user.mention} in the channel.", ephemeral=True)
                self.logger.info(f"{interaction.user} {action} {user} in {channel.name}")
            except discord.Forbidden:
                await interaction.followup.send("❌ I don't have permission to mute members.", ephemeral=True)
        else:
            await interaction.followup.send(f"❌ {user.mention} is not in your channel.", ephemeral=True)

    @app_commands.command(name="transfer-owner", description="Transfer ownership of your voice channel")
    @app_commands.describe(user="User to transfer ownership to")
    async def transfer_owner(self, interaction: discord.Interaction, user: discord.Member):
        """Transfer ownership of the voice channel"""
        await interaction.response.defer()
        
        # Check if user is in a voice channel they own
        if not interaction.user.voice or not interaction.user.voice.channel:
            await interaction.followup.send("❌ You must be in a voice channel to use this command.", ephemeral=True)
            return
        
        channel = interaction.user.voice.channel
        if channel.id not in self.bot.temp_channels or self.bot.temp_channels[channel.id] != interaction.user.id:
            await interaction.followup.send("❌ You can only transfer ownership of channels you created.", ephemeral=True)
            return
        
        if not (user.voice and user.voice.channel == channel):
            await interaction.followup.send(f"❌ {user.mention} must be in the channel to receive ownership.", ephemeral=True)
            return
        
        try:
            # Update ownership tracking
            self.bot.temp_channels[channel.id] = user.id
            
            # Update permissions
            await channel.set_permissions(interaction.user, overwrite=None)  # Remove old owner perms
            await channel.set_permissions(user, connect=True, speak=True, manage_channels=True, 
                                        move_members=True, mute_members=True, deafen_members=True, 
                                        priority_speaker=True)
            
            await interaction.followup.send(f"✅ Transferred channel ownership to {user.mention}.", ephemeral=True)
            self.logger.info(f"{interaction.user} transferred ownership of {channel.name} to {user}")
        except discord.Forbidden:
            await interaction.followup.send("❌ I don't have permission to manage channel permissions.", ephemeral=True)
