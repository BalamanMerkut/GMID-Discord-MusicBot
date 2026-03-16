import os
import asyncio
import lyricsgenius
from dotenv import load_dotenv

load_dotenv()
genius = None
if os.getenv("GENIUS_ACCESS_TOKEN"):
    genius = lyricsgenius.Genius(os.getenv("GENIUS_ACCESS_TOKEN"))

async def get_lyrics(song_title: str) -> str:
    """Fetches lyrics for a given song title."""
    if not genius:
        return "❌ Genius API token not found."

    try:
        # Search for the song - using executor to avoid blocking
        loop = asyncio.get_event_loop()
        song = await loop.run_in_executor(None, lambda: genius.search_song(song_title))
        
        if song:
            # Clean up lyrics
            lyrics = song.lyrics
            # Limit length for Discord (2000 chars)
            if len(lyrics) > 1900:
                lyrics = lyrics[:1900] + "..."
            return lyrics
        return "❌ Lyrics not found."
    except Exception as e:
        print(f"Lyrics error: {e}")
        return f"❌ Error fetching lyrics: {e}"

