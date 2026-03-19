# 🎵 GMID Music Bot

**GMID Music Bot** is a professional, feature-rich Discord music bot designed to provide a high-quality listening experience with advanced AI integrations and seamless multilingual support. It features a modern interactive UI with custom emojis and intelligent search capabilities to find exactly what you're looking for.

---

## ✨ Key Features

-   **🤖 AI-Powered Lyrics**: Integrates OpenAI (GPT-4o) to fetch and understand lyrics for any song, even with vague queries or partial search terms.
-   **🌍 Multilingual Support**: Fully translated into 8 languages: English, Turkish, Spanish, Italian, German, French, Russian, and Chinese.
-   **🎨 Modern Interactive UI**: Features a sleek control panel using Discord buttons for Play/Pause, Skip, Stop, Loop, and Shuffle.
-   **💎 Auto-Emoji Management**: Automatically uploads high-quality custom button emojis to any server it joins, ensuring a consistent premium look.
-   **🎼 High-Fidelity Audio**: Powered by `yt-dlp` for high-quality music streaming directly from YouTube.
-   **📂 Queue & Playlist Support**: Easily play individual tracks or entire YouTube playlists with a single command.
-   **🚀 Smart Idle System**: Automatically disconnects from voice channels when empty or inactive to save system resources.

---

## 🛠️ Setup & Installation

Follow these steps to get your own instance of GMID Music Bot running:

### 1. Requirements
-   Python 3.8 or higher
-   FFmpeg installed on your system PATH

### 2. Clone the Repository
```bash
git clone https://github.com/yourusername/GMID-Music-Bot.git
cd GMID-Music-Bot
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables
Create a file named `.env` in the root directory and add your credentials:
```env
DISCORD_TOKEN=your_discord_bot_token
OPENAI_API_KEY=your_openai_api_key
GENIUS_ACCESS_TOKEN=your_genius_token (optional fallback)
```

### 5. Start the Bot
```bash
python main.py
```

---

## 🎮 Commands Overview

| Command | Description |
| :--- | :--- |
| `/play <query/url>` | Play a song or playlist from YouTube or search keywords. |
| `/lyrics` | Fetch AI-enhanced lyrics for the currently playing song. |
| `/again` | Replay the last played song instantly. |
| `/language <lang>` | Change the bot's interface language (e.g., `tr`, `en`, `es`). |
| `/help` | Display a detailed help guide with all available features. |

---

## 🏗️ Technologies Used

-   **Discord.py**: The core framework for Discord API interaction.
-   **yt-dlp**: For extracting and streaming high-quality audio from YouTube.
-   **OpenAI GPT-4o**: For intelligent lyric fetching and search refinement.
-   **Genius API**: Reliable secondary fallback for song lyrics.
-   **Custom Assets**: Professional UI button assets for a premium feel.

---

## ❤️ Support

If you find this project useful and would like to support its development, you can visit our [patreon](https://www.patreon.com/posts/discord-music-153384328?utm_medium=clipboard_copy&utm_source=copyLink&utm_campaign=postshare_creator&utm_content=join_link) page. Your support helps us add new features and keep the project alive!

---

*Developed by **BalamanMerkut**. Let the music play!* 🎧
