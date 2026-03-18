# 🎵 GMID Music Bot

A feature-rich Discord music bot that plays audio from YouTube, fetches song lyrics via Genius, and uses OpenAI to refine song searches for better accuracy.

---

## ✨ Features

- 🎵 **Play music** from YouTube — search by name or paste a direct URL
- 🤖 **AI-powered search refinement** using OpenAI (finds the correct song even from vague descriptions)
- 🎤 **Singer-Only Search** — Automatically finds popular tracks if you only provide an artist's name
- 📜 **Lyrics fetching** via Genius AI
- ⏱️ **5-Minute Idle Auto-Disconnect** — Leaves the voice channel if inactive for 5 minutes
- 🎛️ **Interactive persistent control panel** — A single "Now Playing" message that stays at the bottom and updates for each song
- 🗑️ **Automated UI Cleanup** — Deletes the music panel when the music stops or bot leaves
- 🖼️ Custom state icons (play, pause, loop, shuffle, stop, skip)

---

## 📋 Requirements

- Python 3.9+
- FFmpeg installed and available in your system PATH
- A Discord Bot Token
- A Genius API Access Token (optional)
- An OpenAI API Key (optional — bot works without it, AI refinement will be disabled)

---

## 🚀 Setup

### 1. Clone the repository
```bash
git clone https://github.com/BalamanMerkut/GMID-Discord-MusicBot.git
cd GMID-Discord-MusicBot
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Configure your API keys
Copy `.env.example` to `.env` and fill in your tokens:
```bash
cp .env.example .env
```

Open `.env` and replace the placeholder values:
```
DISCORD_TOKEN=your_discord_bot_token_here
GENIUS_ACCESS_TOKEN=your_genius_access_token_here
OPENAI_API_KEY=your_openai_api_key_here
```

#### Where to get your keys:
| Key | Link |
|-----|------|
| `DISCORD_TOKEN` | [Discord Developer Portal](https://discord.com/developers/applications) → Your App → Bot → Token |
| `GENIUS_ACCESS_TOKEN` | [Genius API Clients](https://genius.com/api-clients) |
| `OPENAI_API_KEY` | [OpenAI Platform](https://platform.openai.com/api-keys) |

### 4. Install FFmpeg
Download from [ffmpeg.org](https://ffmpeg.org/download.html) and add it to your system PATH.

### 5. Run the bot
```bash
python main.py
```

---

## 🎮 Commands

| Command | Description |
|---------|-------------|
| `/play <song or URL>` | Play a song by name or YouTube URL |
| `/again` | Replay the last played song |
| `/lyrics` | Get lyrics for the currently playing song |
| `/help` | Show all available commands |

### Control Panel Buttons
| Button | Action |
|--------|--------|
| ⏯️ | Pause / Resume |
| ⏹️ | Stop and disconnect |
| ⏭️ | Skip to next song |
| 🔁 | Toggle loop |
| 🔀 | Toggle shuffle |

---

## 📁 Project Structure

```
📦 GMID Discord music bot
 ┣ 📂 assets/          # State icons (play, pause, stop, skip, loop, shuffle)
 ┣ 📄 main.py          # Bot entry point and slash commands
 ┣ 📄 music_handler.py # Music queue, playback, and voice management
 ┣ 📄 ui_components.py # Discord UI buttons and embeds
 ┣ 📄 lyrics_helper.py # Genius API lyrics fetching
 ┣ 📄 ai_helper.py     # OpenAI query refinement
 ┣ 📄 requirements.txt # Python dependencies
 ┣ 📄 example.env      # Template for environment variables
 ┗ 📄 README.md        # This file
```

---

## 📄 License

MIT License — feel free to use, modify and distribute.
