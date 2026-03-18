import discord
from discord import app_commands
from discord.ext import commands
import os
import sys
import io
from dotenv import load_dotenv

# Ensure stdout handles UTF-8 (prevents crashes with Turkish characters in logs)
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Load environment variables
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
        self.music_players = {} # Guild ID -> MusicPlayer

    def get_music_player(self, guild_id):
        if guild_id not in self.music_players:
            self.music_players[guild_id] = MusicPlayer(self)
        return self.music_players[guild_id]

    async def setup_hook(self):
        print(f"Logged in as {self.user} (ID: {self.user.id})")
        print("------")
        # Global sync can take up to 24 hours. We sync locally for immediate results if needed, 
        # but setup_hook should generally stay simple.
        try:
            synced = await self.tree.sync()
            print(f"Synced {len(synced)} slash commands globally.")
        except Exception as e:
            print(f"Sync error in setup_hook: {e}")

bot = MusicBot()

@bot.event
async def on_voice_state_update(member: discord.Member, before: discord.VoiceState, after: discord.VoiceState):
    """Herkes çıkınca bot otomatik olarak odadan ayrılır."""
    # Bot'un kendisinin state değişikliğini yoksay
    if member.id == bot.user.id:
        return

    player = bot.music_players.get(member.guild.id)
    if not player or not player.voice_client or not player.voice_client.is_connected():
        return

    voice_channel = player.voice_client.channel
    # Kanalda bot dışında insan var mı?
    human_members = [m for m in voice_channel.members if not m.bot]
    if len(human_members) == 0:
        print(f"DEBUG: Kanalda kimse kalmadı ({voice_channel.name}), bot ayrılıyor.")
        await player.stop(None)
        # Kullanıcıya bilgi ver (kanalda son mesaj atılan yer bilinmiyor, text kanalı bilinmiyor)
        # Yeterince bilgi var, sessizce ayrılıyoruz.

# Manual sync command for the owner
@bot.command()
@commands.is_owner()
async def sync(ctx):
    """Force sync slash commands to the current guild for immediate visibility."""
    try:
        # Syncing to the current guild is much faster for testing
        bot.tree.copy_global_to(guild=ctx.guild)
        synced = await bot.tree.sync(guild=ctx.guild)
        await ctx.send(f"✅ Synced {len(synced)} commands to this server! (Try typing `/` now)")
    except Exception as e:
        await ctx.send(f"❌ Sync failed: {e}")

@bot.tree.command(name="play", description="Play a song from YouTube")
@app_commands.describe(input="Search term or YouTube URL")
async def play(interaction: discord.Interaction, input: str):
    """Slash command to play music."""
    print(f"DEBUG: /play command received for: '{input}'")
    if not interaction.user.voice:
        print("DEBUG: User not in voice channel.")
        return await interaction.response.send_message("❌ You must be in a voice channel!", ephemeral=True)

    print("DEBUG: Deferring interaction response...")
    await interaction.response.defer(ephemeral=False)
    
    try:
        player = bot.get_music_player(interaction.guild_id)
        print(f"DEBUG: Found/Created MusicPlayer for guild: {interaction.guild_id}")
        
        print(f"DEBUG: Attempting to join voice channel: {interaction.user.voice.channel.name}")
        await player.join(interaction.user.voice.channel)
        print("DEBUG: Successfully joined or already in voice channel.")
        
        print(f"DEBUG: Adding to queue: '{input}'")
        await player.add_to_queue(interaction, input)
        print("DEBUG: Finished add_to_queue call.")
        
    except Exception as e:
        print(f"DEBUG: ERROR in /play command: {e}")
        import traceback
        traceback.print_exc()
        if not interaction.response.is_done():
            await interaction.response.send_message(f"❌ An error occurred: {e}")
        else:
            await interaction.followup.send(f"❌ An error occurred: {e}")

@bot.tree.command(name="again", description="Replay the last played song")
async def again(interaction: discord.Interaction):
    """Slash command to replay the last song."""
    player = bot.get_music_player(interaction.guild_id)
    if not player.last_playing:
        return await interaction.response.send_message("❌ No previous song found to replay.", ephemeral=True)
    
    if not interaction.user.voice:
        return await interaction.response.send_message("❌ You must be in a voice channel!", ephemeral=True)

    await interaction.response.defer()
    await player.join(interaction.user.voice.channel)
    # Add the last song back to the queue
    song = player.last_playing
    player.queue.insert(0, song)
    if player.voice_client is None or (not player.voice_client.is_playing() and not player.voice_client.is_paused()):
        await player.play_next(interaction)
    else:
        await interaction.edit_original_response(content=f"🔄 Replaying: **{song['title']}**")

@bot.tree.command(name="lyrics", description="Get lyrics for the current song")
async def lyrics(interaction: discord.Interaction):
    """Slash command to get lyrics."""
    player = bot.get_music_player(interaction.guild_id)
    player.reset_idle_timer()
    if not player.current_song:
        return await interaction.response.send_message("❌ No song is currently playing.", ephemeral=True)

    await interaction.response.defer()
    song_lyrics = await get_lyrics(player.current_song['title'])
    
    embed = discord.Embed(title=f"Lyrics for {player.current_song['title']}", description=song_lyrics, color=discord.Color.green())
    await interaction.followup.send(embed=embed)

@bot.tree.command(name="help", description="Show all available commands")
async def help(interaction: discord.Interaction):
    """Slash command to show help message."""
    player = bot.get_music_player(interaction.guild_id)
    player.reset_idle_timer()
    embed = discord.Embed(
        title="🎵 GMID Music Bot - Help Guide",
        description="Here are the available slash commands you can use:",
        color=discord.Color.gold()
    )
    
    embed.add_field(
        name="🚀 `/play <input>`", 
        value="Play a song from YouTube. You can provide a **search term** or a **direct YouTube URL**.", 
        inline=False
    )
    embed.add_field(
        name="📜 `/lyrics`", 
        value="Get the lyrics for the currently playing song using Genius AI.", 
        inline=False
    )
    embed.add_field(
        name="❓ `/help`", 
        value="Show this helpful list of commands.", 
        inline=False
    )
    
    embed.set_footer(text="Enjoy the music! 🎧")
    await interaction.response.send_message(embed=embed)

if __name__ == "__main__":
    if TOKEN:
        bot.run(TOKEN)
    else:
        print("Error: DISCORD_TOKEN not found in .env file.")
