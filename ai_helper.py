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
