# 🎵 GMID Music Bot

A feature-rich Discord music bot that plays audio from YouTube, fetches song lyrics via Genius, and uses OpenAI to refine song searches for better accuracy.

---

## ✨ Features

- 🎵 **Play music** from YouTube — search by name or paste a direct URL
- 🤖 **AI-powered search refinement** using OpenAI (finds the correct song even from vague queries)
- 📜 **Lyrics fetching** via Genius API
- 🎛️ **Interactive control panel** with buttons: Pause/Resume, Stop, Skip, Loop, Shuffle
- 🖼️ Custom state icons (play, pause, loop, shuffle, stop, skip)

---

## 📋 Requirements

- Python 3.9+
- FFmpeg installed and available in your system PATH
- A Discord Bot Token
- A Genius API Access Token
- An OpenAI API Key (optional — bot works without it, AI refinement will be disabled)

---

## 🚀 Setup

### 1. Clone the repository
```bash
git clone https://github.com/your-username/gmid-music-bot.git
cd gmid-music-bot
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
| `GENIUS_ACCESS_TOKEN` | [Genius API Clients](https://genius.com/api-clients) → Generate Access Token |
| `OPENAI_API_KEY` | [OpenAI Platform](https://platform.openai.com/api-keys) *(optional)* |

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
 ┣ 📄 .env.example     # Template for environment variables
 ┗ 📄 .gitignore       # Excludes .env and cache files
```

---

## ⚠️ Notes

- The bot requires **Message Content Intent** and **Voice State Intent** enabled in the Discord Developer Portal.
- Global slash command sync can take up to **1 hour** to appear on Discord. For immediate testing, type `!sync` in your server (bot owner only).
- FFmpeg must be installed for audio playback to work.

---

## 📄 License

MIT License — feel free to use, modify and distribute.
