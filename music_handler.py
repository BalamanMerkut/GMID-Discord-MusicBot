import discord
import yt_dlp
import asyncio
import random
import os
from discord.ext import commands

# yt-dlp options for high-quality audio extraction
YTDL_OPTIONS = {
    'format': 'bestaudio/best',
    'extractaudio': True,
    'audioformat': 'mp3',
    'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
    'restrictfilenames': True,
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'ytsearch',
    'source_address': '0.0.0.0',
    'postprocessors': [{
        'key': 'FFmpegExtractAudio',
        'preferredcodec': 'mp3',
        'preferredquality': '192',
    }],
}

FFMPEG_OPTIONS = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
    'options': '-vn',
}

ytdl = yt_dlp.YoutubeDL(YTDL_OPTIONS)

class YTDLSource(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=0.5):
        super().__init__(source, volume)
        self.data = data
        self.title = data.get('title')
        self.url = data.get('url')

    @classmethod
    async def from_url(cls, url, *, loop=None, stream=False):
        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=not stream))

        if 'entries' in data:
            data = data['entries'][0]

        filename = data['url'] if stream else ytdl.prepare_filename(data)
        return cls(discord.FFmpegPCMAudio(filename, **FFMPEG_OPTIONS), data=data)

class MusicPlayer:
    def __init__(self, bot):
        self.bot = bot
        self.queue = []
        self.current_song = None
        self.voice_client = None
        self.loop = False
        self.shuffle = False
        self.assets_path = os.path.join(os.path.dirname(__file__), "assets")

    def get_state_file(self, state):
        """Returns a discord.File for the current state icon."""
        filename = f"{state}.png"
        path = os.path.join(self.assets_path, filename)
        if os.path.exists(path):
            return discord.File(path, filename=filename)
        return None

    def is_paused(self):
        return self.voice_client and self.voice_client.is_paused()

    async def join(self, channel):
        try:
            if self.voice_client and self.voice_client.is_connected():
                await self.voice_client.move_to(channel)
            else:
                self.voice_client = await asyncio.wait_for(channel.connect(), timeout=15.0)
        except asyncio.TimeoutError:
            raise Exception("Voice channel connection timed out (15s).")
        except Exception as e:
            raise e

    async def play_next(self, interaction):
        if len(self.queue) > 0:
            if self.loop and self.current_song:
                self.queue.insert(0, self.current_song)

            if self.shuffle and len(self.queue) > 1:
                idx = random.randint(0, len(self.queue) - 1)
                self.current_song = self.queue.pop(idx)
            else:
                self.current_song = self.queue.pop(0)

            url = self.current_song['url']
            try:
                player = await asyncio.wait_for(
                    YTDLSource.from_url(url, loop=self.bot.loop, stream=True),
                    timeout=20.0
                )
            except asyncio.TimeoutError:
                await interaction.channel.send(f"❌ Timeout loading song: **{self.current_song['title']}**")
                return await self.play_next(interaction)
            except Exception as e:
                await interaction.channel.send(f"❌ Error loading song: {e}")
                return await self.play_next(interaction)

            try:
                self.voice_client.play(
                    player,
                    after=lambda e: asyncio.run_coroutine_threadsafe(
                        self.play_next(interaction), self.bot.loop
                    ) if not e else print(f"Player error: {e}")
                )
            except Exception as e:
                await interaction.channel.send(f"❌ Could not start playback: {e}")
                return

            from ui_components import MusicControlView
            view = MusicControlView(self)

            state_file = self.get_state_file("play")
            embed = discord.Embed(
                title="Now Playing",
                description=f"[{player.title}]({url})",
                color=discord.Color.blue()
            )

            if state_file:
                embed.set_thumbnail(url="attachment://play.png")

            if interaction.response.is_done():
                if state_file:
                    await interaction.channel.send(file=state_file, embed=embed, view=view)
                else:
                    await interaction.channel.send(embed=embed, view=view)
            else:
                if state_file:
                    await interaction.followup.send(file=state_file, embed=embed, view=view)
                else:
                    await interaction.followup.send(embed=embed, view=view)
        else:
            self.current_song = None

    async def add_to_queue(self, interaction, search_query):
        # URL Detection
        is_url = search_query.startswith(('http://', 'https://', 'www.'))

        if is_url:
            refined_query = search_query
            search_prefix = ""
        else:
            # AI refinement for searches
            from ai_helper import refine_query
            try:
                refined_query = await asyncio.wait_for(refine_query(search_query), timeout=10.0)
                search_prefix = "ytsearch:"
            except asyncio.TimeoutError:
                refined_query = search_query
                search_prefix = "ytsearch:"

        # Search or direct URL extraction
        try:
            data = await asyncio.wait_for(
                self.bot.loop.run_in_executor(
                    None,
                    lambda: ytdl.extract_info(f"{search_prefix}{refined_query}", download=False)
                ),
                timeout=20.0
            )
        except asyncio.TimeoutError:
            return await interaction.followup.send(f"❌ YouTube operation timed out for: **{refined_query}**")
        except Exception as e:
            return await interaction.followup.send(f"❌ Could not find or load: **{refined_query}** (Error: {e})")

        if 'entries' in data and len(data['entries']) > 0:
            song_info = data['entries'][0]
        elif 'url' in data:
            song_info = data
        else:
            return await interaction.followup.send(f"❌ Song not found for: **{refined_query}**")

        self.queue.append({
            'title': song_info.get('title'),
            'url': song_info.get('webpage_url', song_info.get('url'))
        })

        if self.voice_client is None or (not self.voice_client.is_playing() and not self.voice_client.is_paused()):
            await self.play_next(interaction)
        else:
            msg = f"✅ Added to queue: **{song_info.get('title')}**"
            if not is_url:
                msg += f" (Refined from: *{search_query}*)"
            await interaction.followup.send(msg)

    async def pause(self, interaction):
        if self.voice_client and self.voice_client.is_playing():
            self.voice_client.pause()
            await interaction.response.send_message("⏸️ Paused", ephemeral=True)

    async def resume(self, interaction):
        if self.voice_client and self.voice_client.is_paused():
            self.voice_client.resume()
            await interaction.response.send_message("▶️ Resumed", ephemeral=True)

    async def stop(self, interaction):
        self.queue = []
        if self.voice_client:
            await self.voice_client.disconnect()
            self.voice_client = None
        await interaction.response.send_message("⏹️ Stopped and disconnected", ephemeral=True)

    async def skip(self, interaction):
        if self.voice_client and self.voice_client.is_playing():
            self.voice_client.stop()
            await interaction.response.send_message("⏭️ Skipped", ephemeral=True)

    async def toggle_loop(self, interaction):
        self.loop = not self.loop
        status = "enabled" if self.loop else "disabled"
        await interaction.response.send_message(f"🔁 Loop {status}", ephemeral=True)

    async def shuffle_queue(self, interaction):
        self.shuffle = not self.shuffle
        status = "enabled" if self.shuffle else "disabled"
        await interaction.response.send_message(f"🔀 Shuffle {status}", ephemeral=True)
