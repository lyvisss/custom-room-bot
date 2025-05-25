# Discord Voice Channel Bot

A Python Discord bot that creates and manages temporary voice channels using slash commands. The bot automatically creates voice channels that delete themselves when empty, perfect for gaming sessions, study groups, or any temporary voice chat needs.

## Features

- ✅ **Slash Commands**: Modern Discord integration with `/` commands
- 🔊 **Temporary Voice Channels**: Create custom voice channels that auto-delete when empty
- 🛡️ **Permission Management**: Proper permission checks and user access control
- 🗂️ **Auto-Organization**: Channels are organized in a dedicated category
- 📝 **Logging**: Comprehensive logging for debugging and monitoring
- ⚡ **Real-time Cleanup**: Automatic monitoring and cleanup of empty channels

## Commands

| Command | Description |
|---------|-------------|
| `/create-voice [name]` | Create a temporary voice channel with optional custom name |
| `/delete-voice` | Delete a temporary voice channel you created |
| `/list-temp-channels` | Show all currently active temporary voice channels |
| `/voice-help` | Display help information for all commands |

## Setup Instructions

### 1. Bot Setup on Discord Developer Portal

1. Go to [Discord Developer Portal](https://discord.com/developers/applications)
2. Click "New Application" and give it a name
3. Go to the "Bot" section
4. Click "Add Bot"
5. Copy the bot token (you'll need this later)
6. Under "Privileged Gateway Intents", enable:
   - Server Members Intent (optional)
   - Message Content Intent (optional)

### 2. Bot Permissions

When inviting the bot to your server, make sure it has these permissions:
- `Manage Channels` - To create and delete voice channels
- `Connect` - To access voice channels
- `Use Slash Commands` - To register and use slash commands

**Permission Integer**: `16784384`

### 3. Installation

1. Clone or download this repository
2. Copy `.env.example` to `.env`
3. Edit `.env` and add your bot token:
   ```env
   DISCORD_BOT_TOKEN=your_actual_bot_token_here
   ```

4. Install dependencies:
   ```bash
   pip install discord.py python-dotenv
   ```

5. Run the bot:
   ```bash
   python main.py
   ```

## Configuration

All configuration is done through environment variables in the `.env` file:

| Variable | Default | Description |
|----------|---------|-------------|
| `DISCORD_BOT_TOKEN` | Required | Your Discord bot token |
| `DISCORD_GUILD_ID` | Optional | Specific server ID for faster command sync |
| `DEFAULT_CHANNEL_NAME` | "Temporary Channel" | Default name for channels |
| `MAX_CHANNEL_NAME_LENGTH` | 50 | Maximum allowed channel name length |
| `TEMP_CATEGORY_NAME` | "Temporary Channels" | Category name for organizing temp channels |
| `LOG_LEVEL` | "INFO" | Logging level (DEBUG, INFO, WARNING, ERROR) |
| `LOG_FILE` | Optional | File path for log output |

## Usage Examples

### Creating a Voice Channel
