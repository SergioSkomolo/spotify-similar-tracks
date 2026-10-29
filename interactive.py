"""Step 3: interactive picker. Shows similar tracks above a match threshold and
lets you queue or play them on your active Spotify device.

Commands:
  q 3    add track 3 to the queue
  p 3    play track 3 right now
  qa     add every listed track to the queue
  r      refresh using whatever is playing now
  x      quit
"""

import spotipy

from now_playing import sp, get_now_playing
from similar_tracks import get_similar

MIN_MATCH = 0.50          # only show tracks at or above this Last.fm match score
_uri_cache = {}


def find_uri(artist, title):
    """Look up a Spotify track URI for an artist/title pair (cached)."""
    key = (artist.lower(), title.lower())
    if key in _uri_cache:
        return _uri_cache[key]

    uri = None
    for query in (f"track:{title} artist:{artist}", f"{artist} {title}"):
        items = sp.search(q=query, type="track", limit=1)["tracks"]["items"]
        if items:
            hit = items[0]
            uri = (hit["uri"], f"{hit['artists'][0]['name']} - {hit['name']}")
            break

    _uri_cache[key] = uri
    return uri


def do_queue(track):
    found = find_uri(track["artist"], track["title"])
    if not found:
        print(f"  Couldn't find '{track['artist']} - {track['title']}' on Spotify.")
        return False
    uri, label = found
    try:
        sp.add_to_queue(uri)
        print(f"  Queued: {label}")
        return True
    except spotipy.SpotifyException as e:
        explain(e)
        return False


def do_play(track):
    found = find_uri(track["artist"], track["title"])
    if not found:
        print(f"  Couldn't find '{track['artist']} - {track['title']}' on Spotify.")
        return
    uri, label = found
    try:
        sp.start_playback(uris=[uri])
        print(f"  Playing: {label}")
    except spotipy.SpotifyException as e:
        explain(e)


def explain(e):
    reason = getattr(e, "reason", "") or ""
    if "NO_ACTIVE_DEVICE" in reason or e.http_status == 404:
        print("  No active Spotify device. Open Spotify, play something, then retry.")
    elif e.http_status == 403:
        print("  Spotify refused (403). Playback control needs Premium, and the "
              "account must be listed under User Management.")
    else:
        print(f"  Spotify error {e.http_status}: {e.msg}")


def load_candidates():
    now = get_now_playing()
    if now is None:
        print("Nothing playing right now. Start a track in Spotify, then press r.")
        return None, []
    artist, title, _ = now
    print(f"\nSeed: {artist} - {title}\n")
    similar = get_similar(artist, title)
    strong = [t for t in similar if t["match"] >= MIN_MATCH]
    strong.sort(key=lambda t: t["match"], reverse=True)
    return (artist, title), strong


def show(candidates):
    print()
    if not candidates:
        print(f"No tracks at or above {MIN_MATCH:.2f}. "
              f"Lower MIN_MATCH at the top of the file to see more.")
        return
    for i, t in enumerate(candidates, start=1):
        print(f"{i:>2}. {t['artist']} - {t['title']}  (match {t['match']:.2f})")


def main():
    seed, candidates = load_candidates()
    show(candidates)

    while True:
        raw = input("\n[q N] queue  [p N] play  [qa] queue all  [r] refresh  [x] quit > ").strip().lower()
        if raw in ("x", "quit", "exit"):
            break
        if raw == "r":
            seed, candidates = load_candidates()
            show(candidates)
            continue
        if raw == "qa":
            done = sum(do_queue(t) for t in candidates)
            print(f"  {done} of {len(candidates)} queued.")
            continue

        parts = raw.split()
        if len(parts) == 2 and parts[0] in ("q", "p") and parts[1].isdigit():
            n = int(parts[1])
            if 1 <= n <= len(candidates):
                (do_queue if parts[0] == "q" else do_play)(candidates[n - 1])
            else:
                print("  That number isn't in the list.")
        else:
            print("  Didn't understand that. Examples: 'q 3', 'p 1', 'qa', 'r', 'x'.")


if __name__ == "__main__":
    main()
