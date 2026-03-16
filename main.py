import discord
from discord import app_commands
from discord.ext import commands
import os
import sys
import io
from dotenv import load_dotenv

# Ensure stdout handles UTF-8 (prevents crashes with non-ASCII characters in logs)
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Load environment variables from .env file
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

from music_handler import MusicPlayer
from lyrics_helper import get_lyrics

class MusicBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.voice_states = True
        super().__init__(command_prefix='!', intents=intents, help_command=None)
        self.music_players = {}  # Guild ID -> MusicPlayer

    def get_music_player(self, guild_id):
        if guild_id not in self.music_players:
            self.music_players[guild_id] = MusicPlayer(self)
        return self.music_players[guild_id]

    async def setup_hook(self):
        print(f"Logged in as {self.user} (ID: {self.user.id})")
        print("------")
        try:
            synced = await self.tree.sync()
            print(f"Synced {len(synced)} slash commands globally.")
        except Exception as e:
            print(f"Sync error in setup_hook: {e}")

bot = MusicBot()

# Manual sync command for the owner
@bot.command()
@commands.is_owner()
async def sync(ctx):
    """Force sync slash commands to the current guild for immediate visibility."""
    try:
        bot.tree.copy_global_to(guild=ctx.guild)
        synced = await bot.tree.sync(guild=ctx.guild)
        await ctx.send(f"✅ Synced {len(synced)} commands to this server!")
    except Exception as e:
        await ctx.send(f"❌ Sync failed: {e}")

@bot.tree.command(name="play", description="Play a song from YouTube")
@app_commands.describe(input="Search term or YouTube URL")
async def play(interaction: discord.Interaction, input: str):
    """Slash command to play music."""
    if not interaction.user.voice:
        return await interaction.response.send_message("❌ You must be in a voice channel!", ephemeral=True)

    await interaction.response.defer(ephemeral=False)

    try:
        player = bot.get_music_player(interaction.guild_id)
        await player.join(interaction.user.voice.channel)
        await player.add_to_queue(interaction, input)
    except Exception as e:
        import traceback
        traceback.print_exc()
        if not interaction.response.is_done():
            await interaction.response.send_message(f"❌ An error occurred: {e}")
        else:
            await interaction.followup.send(f"❌ An error occurred: {e}")

@bot.tree.command(name="lyrics", description="Get lyrics for the current song")
async def lyrics(interaction: discord.Interaction):
    """Slash command to get lyrics."""
    player = bot.get_music_player(interaction.guild_id)
    if not player.current_song:
        return await interaction.response.send_message("❌ No song is currently playing.", ephemeral=True)

    await interaction.response.defer()
    song_lyrics = await get_lyrics(player.current_song['title'])

    embed = discord.Embed(
        title=f"Lyrics for {player.current_song['title']}",
        description=song_lyrics,
        color=discord.Color.green()
    )
    await interaction.followup.send(embed=embed)

@bot.tree.command(name="help", description="Show all available commands")
async def help(interaction: discord.Interaction):
    """Slash command to show help message."""
    embed = discord.Embed(
        title="🎵 GMID Music Bot - Help Guide",
        description="Here are the available slash commands you can use:",
        color=discord.Color.gold()
    )
    embed.add_field(name="🚀 `/play <input>`", value="Play a song from YouTube. Provide a **search term** or a **direct YouTube URL**.", inline=False)
    embed.add_field(name="📜 `/lyrics`", value="Get the lyrics for the currently playing song using Genius AI.", inline=False)
    embed.add_field(name="❓ `/help`", value="Show this helpful list of commands.", inline=False)
    embed.set_footer(text="Enjoy the music! 🎧")
    await interaction.response.send_message(embed=embed)

if __name__ == "__main__":
    if TOKEN:
        bot.run(TOKEN)
    else:
        print("Error: DISCORD_TOKEN not found in .env file. Please create a .env file.")
