# 🎵 GMID Music Bot — Walkthrough

## Overview

GMID Music Bot is a Discord music bot built with Python and `discord.py`. It plays YouTube audio, fetches lyrics via Genius, and uses OpenAI to refine vague song search queries for more accurate playback.

---

## Project Structure

```
📦 GMID Discord music bot
 ┣ 📂 assets/              # PNG icons for each player state
 ┣ 📄 main.py              # Bot setup and slash commands (/play, /lyrics, /help)
 ┣ 📄 music_handler.py     # Voice connection, queue, and playback logic
 ┣ 📄 ui_components.py     # Discord UI buttons (Pause, Stop, Skip, Loop, Shuffle)
 ┣ 📄 lyrics_helper.py     # Genius API integration for lyrics
 ┣ 📄 ai_helper.py         # OpenAI integration for query refinement
 ┣ 📄 requirements.txt     # Python package dependencies
 ┣ 📄 .env.example         # Template for environment variables
 ┗ 📄 .gitignore           # Protects .env and excludes caches
```

---

## How It Works

### `/play` Command
1. User runs `/play <song name or URL>`
2. If a URL is detected → sent directly to yt-dlp for extraction
3. If a search term → sent to OpenAI to refine it to `"Artist - Song Title"` format
4. yt-dlp fetches the best audio stream from YouTube
5. FFmpeg streams audio to the Discord voice channel
6. A **Now Playing** embed appears with interactive control buttons

### `/lyrics` Command
1. User runs `/lyrics` while a song is playing
2. The current song title is sent to the Genius API via `lyricsgenius`
3. Lyrics are returned and displayed in a Discord embed (truncated to 1900 chars if too long)

### `/help` Command
Displays a clean embed listing all available slash commands.

---

## Control Panel Buttons

| Button | Action |
|--------|--------|
| ⏯️ | Pause / Resume playback |
| ⏹️ | Stop music and disconnect bot |
| ⏭️ | Skip to the next song in queue |
| 🔁 | Toggle loop on/off |
| 🔀 | Toggle shuffle on/off |

Each button updates the embed thumbnail to reflect the current playback state using the icons in the `assets/` folder.

---

## Environment Variables

All sensitive keys are stored in a `.env` file (never committed to GitHub):

| Variable | Purpose |
|----------|---------|
| `DISCORD_TOKEN` | Authenticates the bot with Discord |
| `GENIUS_ACCESS_TOKEN` | Fetches song lyrics from Genius |
| `OPENAI_API_KEY` | Refines search queries (optional) |

---

## Key Design Decisions

- **AI Refinement is optional** — if `OPENAI_API_KEY` is not set, the bot falls back to the original search query. No crash, no error.
- **Direct URL bypass** — when a YouTube URL is detected, the AI refinement step is skipped entirely to avoid modifying a valid URL.
- **Streaming, not downloading** — audio is streamed directly from YouTube via yt-dlp + FFmpeg, so no local files are created.
- **Per-guild players** — each Discord server gets its own `MusicPlayer` instance, so the bot can serve multiple servers simultaneously.
- **Reconnect support** — FFmpeg is configured with `-reconnect` flags to handle brief network interruptions gracefully.

---

*Built with `discord.py`, `yt-dlp`, `FFmpeg`, `lyricsgenius`, and `openai`.*
