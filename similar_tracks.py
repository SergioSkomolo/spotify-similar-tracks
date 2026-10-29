"""Step 2: find tracks similar to the one currently playing, using Last.fm.

Tries the exact track first, then a cleaned-up title (house/dance tracks often
carry suffixes like "- Original Mix"), then falls back to similar artists'
top tracks.
"""

import os
import re

import requests
from dotenv import load_dotenv

load_dotenv()

LASTFM_URL = "https://ws.audioscrobbler.com/2.0/"


def lastfm(method, **params):
    api_key = os.getenv("LASTFM_API_KEY")
    if not api_key:
        raise SystemExit("LASTFM_API_KEY is missing from your .env file.")
    params.update(method=method, api_key=api_key, format="json", autocorrect=1)
    resp = requests.get(LASTFM_URL, params=params, timeout=15)
    resp.raise_for_status()
    data = resp.json()
    if "error" in data:
        print(f"  (Last.fm said: error {data['error']} - {data.get('message')})")
        return {}
    return data


def clean_title(title):
    """Strip common dance-music suffixes that Last.fm usually doesn't use."""
    t = re.sub(
        r"\s*[-(\[]\s*(original|extended|radio|club|album|single)"
        r"( mix| edit| version)?\s*[)\]]?\s*$",
        "",
        title,
        flags=re.I,
    )
    t = re.sub(r"\s*[(\[]\s*(feat\.?|ft\.?|featuring)[^)\]]*[)\]]", "", t, flags=re.I)
    t = re.sub(r"\s*-\s*(feat\.?|ft\.?)\s.*$", "", t, flags=re.I)
    return t.strip()


def similar_by_track(artist, title, limit=50):
    data = lastfm("track.getSimilar", artist=artist, track=title, limit=limit)
    tracks = data.get("similartracks", {}).get("track", [])
    return [
        {
            "artist": t["artist"]["name"],
            "title": t["name"],
            "match": float(t.get("match", 0)),
            "source": "similar track",
        }
        for t in tracks
    ]


def similar_by_artist(artist, artists=10, per_artist=3):
    """Fallback: top tracks from artists similar to the seed artist."""
    data = lastfm("artist.getSimilar", artist=artist, limit=artists)
    results = []
    for a in data.get("similarartists", {}).get("artist", []):
        a_match = float(a.get("match", 0))
        top = lastfm("artist.getTopTracks", artist=a["name"], limit=per_artist)
        for t in top.get("toptracks", {}).get("track", []):
            results.append(
                {
                    "artist": a["name"],
                    "title": t["name"],
                    "match": a_match,
                    "source": "similar artist",
                }
            )
    return results


def get_similar(artist, title):
    attempts = [title]
    cleaned = clean_title(title)
    if cleaned and cleaned != title:
        attempts.append(cleaned)

    for t in attempts:
        print(f"Trying track lookup: {artist} - {t}")
        found = similar_by_track(artist, t)
        if found:
            return found

    print(f"No track-level results. Falling back to artists similar to {artist}...")
    return similar_by_artist(artist)


if __name__ == "__main__":
    from now_playing import get_now_playing

    now = get_now_playing()
    if now is None:
        raise SystemExit("Nothing playing right now. Start a track and run again.")

    artist, title, _track_id = now
    print(f"Seed: {artist} - {title}\n")

    similar = get_similar(artist, title)
    print()
    if not similar:
        print("Still nothing. Check the 'Last.fm said' lines above for the reason.")
    for i, t in enumerate(similar, start=1):
        print(f"{i:>2}. {t['artist']} - {t['title']}  (match {t['match']:.2f}, {t['source']})")
