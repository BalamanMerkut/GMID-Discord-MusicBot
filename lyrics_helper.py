import re
import os
import asyncio
import lyricsgenius
from dotenv import load_dotenv

load_dotenv()
genius = None
if os.getenv("GENIUS_ACCESS_TOKEN"):
    genius = lyricsgenius.Genius(os.getenv("GENIUS_ACCESS_TOKEN"))
    genius.verbose = False # Disable verbose logging

def clean_song_title(title: str) -> str:
    """Removes common YouTube noise, markdown, years, and extra info from song titles."""
    # 1. Remove markdown characters
    title = title.replace('*', '').replace('_', '').replace('`', '').replace('~', '')

    # 2. Only remove specific YouTube noise inside parentheses/brackets
    noise_patterns = [
        r'\(official video\)', r'\[official video\]',
        r'\(music video\)', r'\[music video\]',
        r'\(video klip\)', r'\[video klip\]',
        r'\(resmi video\)', r'\[resmi video\]',
        r'\(ses\)', r'\[ses\]',
        r'\(sözleri\)', r'\[sözleri\]',
        r'\(lyrics\)', r'\[lyrics\]',
        r'\(audio\)', r'\[audio\]',
        r'\(video\)', r'\[video\]',
        r'\(official\)', r'\[official\]',
        r'\(hd\)', r'\[hd\]',
        r'\(hq\)', r'\[hq\]',
        r'\(live\)', r'\[live\]',
        r'\(explicit\)', r'\[explicit\]',
    ]
    for pattern in noise_patterns:
        title = re.sub(pattern, '', title, flags=re.IGNORECASE)

    # 3. Handle collaborations more carefully - just remove the keyword itself, keep the artist name
    title = re.sub(r'\b(feat|ft|prod|produced by)\.?\s*', ' ', title, flags=re.IGNORECASE)
    
    # 4. Remove standalone years
    title = re.sub(r'\b\d{4}\b', '', title)
    
    # 5. Clean up separators and extra spaces
    title = title.replace('-', ' ').replace('–', ' ').replace('—', ' ')
    
    # Final cleanup of double spaces and surrounding whitespace
    return ' '.join(title.split()).strip()

def get_similarity(s1: str, s2: str) -> float:
    """Simple similarity score based on overlapping words."""
    s1_words = set(re.findall(r'\w+', s1.lower()))
    s2_words = set(re.findall(r'\w+', s2.lower()))
    if not s1_words or not s2_words:
        return 0.0
    overlap = s1_words.intersection(s2_words)
    return len(overlap) / max(len(s1_words), len(s2_words))

async def get_lyrics(song_title: str) -> str:
    """Fetches lyrics for a given song title with a multi-stage search strategy."""
    if not genius:
        return "❌ Genius API token not found."

    # 1. Prepare multiple versions of the query
    original_title = song_title
    clean_title_full = clean_song_title(original_title)
    
    # Try to extract Artist and Song if it has a dash
    artist_song_query = None
    song_only_query = None
    if ' - ' in original_title or ' – ' in original_title or ' — ' in original_title:
        parts = re.split(r' - | – | — ', original_title, maxsplit=1)
        artist = clean_song_title(parts[0])
        song = clean_song_title(parts[1])
        artist_song_query = f"{artist} {song}"
        song_only_query = song

    # Queries to try in order of likelihood
    queries = [artist_song_query, clean_title_full, song_only_query]
    queries = [q for q in queries if q and len(q) > 2] # Filter out dummies
    
    print(f"DEBUG: Lyrics search queries: {queries}")

    try:
        loop = asyncio.get_event_loop()
        candidates = []
        bad_keywords = ['discography', 'tracklist', 'about', 'biography', 'credits', 'booklet', 'list of']
        
        # Search for each query version
        for query in queries:
            search_results = await loop.run_in_executor(None, lambda: genius.search_songs(query))
            if not search_results or 'hits' not in search_results:
                continue
            
            for hit in search_results['hits']:
                res_title = hit['result']['title']
                res_artist = hit['result']['primary_artist']['name']
                full_res_title = f"{res_artist} {res_title}"
                
                # Skip non-song pages
                if any(kw in res_title.lower() for kw in bad_keywords):
                    continue
                    
                score = get_similarity(query, full_res_title)
                # Keep track of which hit had the best score
                candidates.append({
                    'id': hit['result']['id'], 
                    'score': score, 
                    'title': full_res_title
                })

        # Sort all candidates from all queries by score
        candidates.sort(key=lambda x: x['score'], reverse=True)
        # Remove duplicates based on ID
        unique_candidates = []
        seen_ids = set()
        for c in candidates:
            if c['id'] not in seen_ids:
                unique_candidates.append(c)
                seen_ids.add(c['id'])
        
        print(f"DEBUG: Best Genius candidates: {unique_candidates[:3]}")

        # Try top 3 most similar
        for candidate in unique_candidates[:3]:
            if candidate['score'] < 0.15: # Very low threshold for multi-query
                continue
                
            song = await loop.run_in_executor(None, lambda: genius.search_song(song_id=candidate['id'], get_full_info=False))
            
            if song and song.lyrics:
                lyrics = song.lyrics
                if len(lyrics) > 150:
                    # Clean up
                    lyrics = re.sub(r'\d+ Embed', '', lyrics)
                    lyrics = re.sub(r'You might also like', '', lyrics, flags=re.IGNORECASE)
                    
                    if len(lyrics) > 1900:
                        lyrics = lyrics[:1900] + "..."
                    return lyrics
                    
        return "❌ Lyrics not found."
    except Exception as e:
        print(f"Lyrics error: {e}")
        return f"❌ Error fetching lyrics: {e}"

