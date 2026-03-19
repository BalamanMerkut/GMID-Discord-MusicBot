import os
import asyncio
from openai import AsyncOpenAI
from dotenv import load_dotenv

load_dotenv()
load_dotenv()
client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

async def refine_query(query: str) -> str:
    """Refines a vague search query into a specific song name and artist."""
    if not os.getenv("OPENAI_API_KEY"):
        return query # Fallback to original query if no API key

    try:
        response = await client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a music expert. The user will give you a vague description or lyrics of a song. Your job is to return ONLY the most likely song name and artist. No other text."},
                {"role": "user", "content": f"What song is this: {query}"}
            ],
            max_tokens=50
        )
        refined = response.choices[0].message.content.strip()
        print(f"DEBUG: AI Refined query: '{query}' -> '{refined}'")
        return refined
    except Exception as e:
        print(f"AI Refinement error: {e}")
        return query

async def get_lyrics_ai(song_title: str) -> str:
    """Uses OpenAI to find or generate the lyrics for a song."""
    if not os.getenv("OPENAI_API_KEY"):
        return "❌ OpenAI API key not found in .env"

    try:
        response = await client.chat.completions.create(
            model="gpt-4o", # Using 4o for better accuracy and recall
            messages=[
                {"role": "system", "content": "You are a music historian and enthusiast. Your task is to provide the full, accurate lyrics for the requested song. If you know the lyrics, return them exactly. If the song is instrumental, state that. If you are unsure, provide the most likely lyrics part or explain you cannot find them. Keep the formatting clean."},
                {"role": "user", "content": f"Please provide the full lyrics for the song: {song_title}"}
            ],
            max_tokens=1500 # Lyrics can be long
        )
        lyrics = response.choices[0].message.content.strip()
        
        # Limit length for Discord (2000 chars)
        if len(lyrics) > 1900:
            lyrics = lyrics[:1900] + "..."
            
        return lyrics
    except Exception as e:
        print(f"AI Lyrics error: {e}")
        return f"❌ Error fetching lyrics via AI: {e}"
