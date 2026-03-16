import os
import asyncio
import lyricsgenius
from dotenv import load_dotenv

load_dotenv()
genius = None
if os.getenv("GENIUS_ACCESS_TOKEN"):
    genius = lyricsgenius.Genius(os.getenv("GENIUS_ACCESS_TOKEN"))

async def get_lyrics(song_title: str) -> str:
    """Fetches lyrics for a given song title using the Genius API."""
    if not genius:
        return "❌ Genius API token not found. Add GENIUS_ACCESS_TOKEN to your .env file."

    try:
        loop = asyncio.get_event_loop()
        song = await loop.run_in_executor(None, lambda: genius.search_song(song_title))

        if song:
            lyrics = song.lyrics
            if len(lyrics) > 1900:
                lyrics = lyrics[:1900] + "..."
            return lyrics
        return "❌ Lyrics not found."
    except Exception as e:
        print(f"Lyrics error: {e}")
        return f"❌ Error fetching lyrics: {e}"
