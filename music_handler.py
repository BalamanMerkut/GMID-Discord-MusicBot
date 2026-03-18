import discord
import yt_dlp
import asyncio
import random
import os
from discord.ext import commands

# yt-dlp options — tekli şarkı için
YTDL_OPTIONS = {
    'format': 'bestaudio/best',
    'extractaudio': True,
    'audioformat': 'mp3',
    'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
    'restrictfilenames': True,
    'noplaylist': True,          # Tekil şarkı: playlist'i yoksay
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

# yt-dlp options — playlist için (noplaylist=False)
YTDL_PLAYLIST_OPTIONS = {
    'format': 'bestaudio/best',
    'extractaudio': True,
    'audioformat': 'mp3',
    'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
    'restrictfilenames': True,
    'noplaylist': False,         # Playlist: tüm şarkıları al
    'nocheckcertificate': True,
    'ignoreerrors': True,        # Hatalı/özel şarkıları atla
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'source_address': '0.0.0.0',
    'extract_flat': True,        # Hızlı: ses indirmeden sadece metadata al
}

FFMPEG_OPTIONS = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
    'options': '-vn',
}

ytdl = yt_dlp.YoutubeDL(YTDL_OPTIONS)
ytdl_playlist = yt_dlp.YoutubeDL(YTDL_PLAYLIST_OPTIONS)

class YTDLSource(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=0.5):
        super().__init__(source, volume)
        self.data = data
        self.title = data.get('title')
        self.url = data.get('url')

    @classmethod
    async def from_url(cls, url, *, loop=None, stream=False):
        loop = loop or asyncio.get_event_loop()
        print(f"DEBUG: Extracting info for {url}")
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=not stream))

        if 'entries' in data:
            data = data['entries'][0]

        filename = data['url'] if stream else ytdl.prepare_filename(data)
        print(f"DEBUG: FFmpeg playing from {filename[:50]}...")
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
        self.now_playing_msg = None
        self.text_channel = None
        self.idle_task = None
        self.last_playing = None # Stores the metadata of the last started song

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
        print(f"DEBUG: MusicPlayer.join called for channel: {channel.name}")
        try:
            if self.voice_client and self.voice_client.is_connected():
                print(f"DEBUG: Already connected to {self.voice_client.channel.name}. Moving...")
                await self.voice_client.move_to(channel)
            else:
                print(f"DEBUG: Connecting to {channel.name}...")
                self.voice_client = await asyncio.wait_for(channel.connect(), timeout=15.0)
                print(f"DEBUG: Connected to {channel.name}")
        except asyncio.TimeoutError:
            print(f"DEBUG: Timeout connecting to voice channel {channel.name}")
            raise Exception("Voice channel connection timed out (15s).")
        except Exception as e:
            print(f"DEBUG: Error in MusicPlayer.join: {e}")
            raise e

    def start_idle_timer(self):
        """Starts the 5-minute idle timer."""
        self.stop_idle_timer()
        print("DEBUG: Starting 5-minute idle timer.")
        self.idle_task = self.bot.loop.create_task(self.idle_timeout())

    def stop_idle_timer(self):
        """Stops the idle timer."""
        if self.idle_task:
            print("DEBUG: Stopping idle timer.")
            self.idle_task.cancel()
            self.idle_task = None

    def reset_idle_timer(self):
        """Resets the idle timer if the bot is not playing music."""
        if self.voice_client and not self.voice_client.is_playing() and not self.voice_client.is_paused():
            self.start_idle_timer()
        else:
            self.stop_idle_timer()

    async def idle_timeout(self):
        """Disconnects the bot after 5 minutes of inactivity."""
        try:
            await asyncio.sleep(300) # 5 minutes
            print("DEBUG: 5 minutes idle timeout reached. Disconnecting.")
            if self.voice_client:
                # Cleanup UI before leaving
                await self.cleanup_now_playing()
                await self.voice_client.disconnect()
                self.voice_client = None
        except asyncio.CancelledError:
            pass

    async def cleanup_now_playing(self):
        """Deletes the 'Now Playing' message if it exists."""
        if self.now_playing_msg:
            try:
                await self.now_playing_msg.delete()
            except Exception as e:
                print(f"DEBUG: Error deleting now_playing_msg: {e}")
            self.now_playing_msg = None

    async def play_next(self, interaction=None):
        self.stop_idle_timer()
        
        # If loop is enabled and there is a current song, replay it directly
        if self.loop and self.current_song:
            song_to_play = self.current_song
        elif len(self.queue) > 0:
            if self.shuffle and len(self.queue) > 1:
                idx = random.randint(0, len(self.queue) - 1)
                song_to_play = self.queue.pop(idx)
            else:
                song_to_play = self.queue.pop(0)
            self.current_song = song_to_play
        else:
            self.current_song = None
            print("DEBUG: Queue empty. Starting idle timer.")
            await self.cleanup_now_playing()
            self.start_idle_timer()
            return

        url = song_to_play['url']
        print(f"DEBUG: Processing song: {song_to_play['title']} (loop={'on' if self.loop else 'off'})")
        try:
            player = await asyncio.wait_for(
                YTDLSource.from_url(url, loop=self.bot.loop, stream=True),
                timeout=20.0
            )
        except asyncio.TimeoutError:
            print(f"DEBUG: Timeout extracting song info for: {url}")
            await self.text_channel.send(f"❌ Timeout loading song: **{song_to_play['title']}**")
            # On timeout during loop, still continue to next song
            if self.loop:
                self.loop = False
            return await self.play_next(interaction)
        except Exception as e:
            print(f"DEBUG: Error loading song: {e}")
            await self.text_channel.send(f"❌ Error loading song: {e}")
            if self.loop:
                self.loop = False
            return await self.play_next(interaction)

        print(f"DEBUG: Starting playback for {player.title}")
        try:
            self.last_playing = song_to_play # Track for /again command
            self.voice_client.play(
                player,
                after=lambda e: (
                    print(f"DEBUG: Player error: {e}") if e
                    else asyncio.run_coroutine_threadsafe(self.play_next(), self.bot.loop)
                )
            )
        except Exception as e:
            print(f"DEBUG: Fatal error starting voice_client playback: {e}")
            await self.text_channel.send(f"❌ Could not start playback: {e}")
            self.start_idle_timer()
            return

        from ui_components import MusicControlView
        view = MusicControlView(self)

        state_file = self.get_state_file("play")
        embed = discord.Embed(
            title="🔁 Now Playing (Loop)" if self.loop else "Now Playing",
            description=f"[{player.title}]({url})",
            color=discord.Color.green() if self.loop else discord.Color.blue()
        )
        if state_file:
            embed.set_thumbnail(url="attachment://play.png")

        # Persistent Message Logic
        try:
            if interaction:
                # Clear thinking status by editing original response
                if state_file:
                    self.now_playing_msg = await interaction.edit_original_response(embed=embed, view=view, attachments=[state_file])
                else:
                    self.now_playing_msg = await interaction.edit_original_response(embed=embed, view=view)
                self.text_channel = interaction.channel
            elif self.now_playing_msg:
                # Update existing message for next song
                try:
                    # In an edit, we usually only update embed and view to stay safe
                    await self.now_playing_msg.edit(embed=embed, view=view)
                except discord.NotFound:
                    if state_file:
                        self.now_playing_msg = await self.text_channel.send(embed=embed, view=view, file=state_file)
                    else:
                        self.now_playing_msg = await self.text_channel.send(embed=embed, view=view)
            else:
                if state_file:
                    self.now_playing_msg = await self.text_channel.send(embed=embed, view=view, file=state_file)
                else:
                    self.now_playing_msg = await self.text_channel.send(embed=embed, view=view)
        except Exception as e:
            print(f"DEBUG: Error updating now playing message: {e}")
            # Fallback to followup if edit fails
            if interaction:
                if state_file:
                    self.now_playing_msg = await interaction.followup.send(embed=embed, view=view, file=state_file)
                else:
                    self.now_playing_msg = await interaction.followup.send(embed=embed, view=view)

    async def add_to_queue(self, interaction, search_query):
        # 1. URL Detection
        is_url = search_query.startswith(('http://', 'https://', 'www.'))

        # 2. Playlist detection (list= parametresi var mı?)
        is_playlist = is_url and ('list=' in search_query)

        if is_playlist:
            # --- PLAYLIST MODU ---
            # URL'den list= ID'sini çıkar ve temiz playlist URL'si oluştur
            # Örnek: ?v=xxx&list=PL_abc → https://www.youtube.com/playlist?list=PL_abc
            import urllib.parse
            parsed = urllib.parse.urlparse(search_query)
            params = urllib.parse.parse_qs(parsed.query)
            list_id = params.get('list', [None])[0]

            if list_id:
                playlist_url = f"https://www.youtube.com/playlist?list={list_id}"
                print(f"DEBUG: Temiz playlist URL oluşturuldu: {playlist_url}")
            else:
                playlist_url = search_query

            try:
                data = await asyncio.wait_for(
                    self.bot.loop.run_in_executor(None, lambda: ytdl_playlist.extract_info(playlist_url, download=False)),
                    timeout=60.0
                )
            except asyncio.TimeoutError:
                return await interaction.followup.send("❌ Playlist yüklenirken zaman aşımı oluştu.")
            except Exception as e:
                return await interaction.followup.send(f"❌ Playlist yüklenemedi: {e}")

            if not data:
                return await interaction.followup.send("❌ Playlist bilgisi alınamadı.")

            entries = data.get('entries', [])
            if not entries:
                return await interaction.followup.send("❌ Playlist'te çalınabilir şarkı bulunamadı.")

            added = 0
            for entry in entries:
                if not entry:
                    continue
                title = entry.get('title') or entry.get('id', 'Unknown')
                # Fallback sırası: url → webpage_url → id'den inşa
                url = entry.get('url') or entry.get('webpage_url')
                if not url:
                    vid_id = entry.get('id')
                    if vid_id:
                        url = f"https://www.youtube.com/watch?v={vid_id}"
                    else:
                        continue
                elif not url.startswith('http'):
                    # Sadece video ID döndüyse tam URL'e çevir
                    url = f"https://www.youtube.com/watch?v={url}"
                self.queue.append({'title': title, 'url': url})
                added += 1

            if added == 0:
                return await interaction.followup.send("❌ Playlist'te çalınabilir şarkı bulunamadı.")

            playlist_title = data.get('title', 'Playlist')
            print(f"DEBUG: Playlist '{playlist_title}' -> {added} şarkı kuyruğa eklendi.")
            await interaction.followup.send(
                f"📋 **{playlist_title}** playlist'inden **{added} şarkı** kuyruğa eklendi!"
            )

            if self.voice_client is None or (not self.voice_client.is_playing() and not self.voice_client.is_paused()):
                self.text_channel = interaction.channel
                await self.play_next(interaction)
            return

        # --- TEKİL ŞARKI MODU ---
        if is_url:
            print(f"DEBUG: Tekil URL: '{search_query}'. AI refinement atlanıyor.")
            refined_query = search_query
            search_prefix = ""
        else:
            from ai_helper import refine_query
            print(f"DEBUG: AI refinement: '{search_query}'")
            try:
                refined_query = await asyncio.wait_for(refine_query(search_query), timeout=10.0)
                search_prefix = "ytsearch:"
            except asyncio.TimeoutError:
                print("DEBUG: AI refinement zaman aşımı, orijinal sorgu kullanılıyor.")
                refined_query = search_query
                search_prefix = "ytsearch:"

        # Improvement: If query is likely just a singer name, append a hint for better results
        if not is_url and len(refined_query.split()) <= 3 and "şarkı" not in refined_query.lower() and "music" not in refined_query.lower():
            search_query_with_hint = f"{refined_query} en popüler şarkısı"
            print(f"DEBUG: Singer-only query detected. Using hint: '{search_query_with_hint}'")
        else:
            search_query_with_hint = refined_query

        print(f"DEBUG: YouTube'dan çekiliyor: '{search_prefix}{search_query_with_hint}'")
        try:
            data = await asyncio.wait_for(
                self.bot.loop.run_in_executor(None, lambda: ytdl.extract_info(f"{search_prefix}{search_query_with_hint}", download=False)),
                timeout=20.0
            )
        except asyncio.TimeoutError:
            return await interaction.followup.send(f"❌ YouTube zaman aşımı: **{refined_query}**")
        except Exception as e:
            return await interaction.followup.send(f"❌ Bulunamadı: **{refined_query}** (Hata: {e})")

        if 'entries' in data and len(data['entries']) > 0:
            song_info = data['entries'][0]
        elif 'url' in data:
            song_info = data
        else:
            return await interaction.followup.send(f"❌ Şarkı bulunamadı: **{refined_query}**")

        print(f"DEBUG: Şarkı bulundu: '{song_info.get('title')}'")
        self.queue.append({'title': song_info.get('title'), 'url': song_info.get('webpage_url', song_info.get('url'))})

        if self.voice_client is None or (not self.voice_client.is_playing() and not self.voice_client.is_paused()):
            print("DEBUG: play_next başlatılıyor...")
            self.text_channel = interaction.channel
            await self.play_next(interaction)
        else:
            msg = f"✅ Kuyruğa eklendi: **{song_info.get('title')}**"
            if not is_url:
                msg += f" (Arama: *{search_query}*)"
            
            # Using edit_original_response clears the "thinking" status
            try:
                await interaction.edit_original_response(content=msg, embed=None, view=None)
            except:
                await interaction.followup.send(msg)

    async def pause(self, interaction):
        if self.voice_client and self.voice_client.is_playing():
            self.voice_client.pause()
            self.start_idle_timer() # Start idle timer when paused
            await interaction.response.send_message("⏸️ Paused", ephemeral=True)

    async def resume(self, interaction):
        if self.voice_client and self.voice_client.is_paused():
            self.voice_client.resume()
            self.stop_idle_timer() # Stop idle timer when resumed
            await interaction.response.send_message("▶️ Resumed", ephemeral=True)

    async def stop(self, interaction):
        self.queue = []
        self.stop_idle_timer()
        await self.cleanup_now_playing()
        if self.voice_client:
            await self.voice_client.disconnect()
            self.voice_client = None
        
        if interaction:
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
