"""Step 4: local web app. Run with `python app.py`, then open http://127.0.0.1:5000

Reuses now_playing.py and similar_tracks.py from the same folder.
"""

import requests
import spotipy
from flask import Flask, jsonify, render_template, request

from now_playing import sp
from similar_tracks import get_similar

app = Flask(__name__)
_uri_cache = {}


# ---------- helpers ----------

def current_track():
    """Return the playing track dict from Spotify, or None."""
    cur = sp.current_user_playing_track()
    if not cur or not cur.get("item") or cur["item"].get("type") != "track":
        return None
    return cur


def find_uri(artist, title):
    """Look up (uri, 'Artist - Title') on Spotify for an artist/title pair (cached)."""
    key = (artist.lower(), title.lower())
    if key in _uri_cache:
        return _uri_cache[key]
    found = None
    for query in (f"track:{title} artist:{artist}", f"{artist} {title}"):
        items = sp.search(q=query, type="track", limit=1)["tracks"]["items"]
        if items:
            hit = items[0]
            found = (hit["uri"], f"{hit['artists'][0]['name']} - {hit['name']}")
            break
    _uri_cache[key] = found
    return found


def explain(e):
    reason = getattr(e, "reason", "") or ""
    if "NO_ACTIVE_DEVICE" in reason or e.http_status == 404:
        return "No active Spotify device. Open Spotify, play something, then retry."
    if e.http_status == 403:
        return ("Spotify refused the request (403). Playback control needs Premium, "
                "and your account must be listed under User Management.")
    return f"Spotify error {e.http_status}: {e.msg}"


@app.errorhandler(spotipy.SpotifyException)
def handle_spotify_error(e):
    return jsonify(error=explain(e)), 400


@app.errorhandler(requests.RequestException)
def handle_network_error(e):
    return jsonify(error=f"Network error talking to Last.fm: {e}"), 502


# ---------- routes ----------

@app.get("/")
def index():
    return render_template("index.html")


@app.get("/api/now")
def api_now():
    cur = current_track()
    if cur is None:
        return jsonify(playing=False)
    t = cur["item"]
    images = (t.get("album") or {}).get("images") or []
    art = images[1]["url"] if len(images) > 1 else (images[0]["url"] if images else None)
    return jsonify(
        playing=bool(cur.get("is_playing")),
        id=t["id"],
        artist=t["artists"][0]["name"],
        title=t["name"],
        art=art,
    )


@app.get("/api/similar")
def api_similar():
    cur = current_track()
    if cur is None:
        return jsonify(error="Nothing is playing right now."), 400
    t = cur["item"]
    artist, title = t["artists"][0]["name"], t["name"]
    try:
        tracks = get_similar(artist, title)
    except SystemExit as e:  # get_similar exits if the Last.fm key is missing
        return jsonify(error=str(e)), 400
    tracks.sort(key=lambda x: x["match"], reverse=True)
    return jsonify(seed={"artist": artist, "title": title}, tracks=tracks)


def _resolve_from_request():
    body = request.get_json(silent=True) or {}
    artist, title = body.get("artist"), body.get("title")
    if not artist or not title:
        return None, (jsonify(error="artist and title are required."), 400)
    found = find_uri(artist, title)
    if not found:
        return None, (jsonify(error=f"Couldn't find '{artist} - {title}' on Spotify."), 404)
    return found, None


@app.post("/api/queue")
def api_queue():
    found, err = _resolve_from_request()
    if err:
        return err
    uri, label = found
    sp.add_to_queue(uri)
    return jsonify(ok=True, label=label)


@app.post("/api/play")
def api_play():
    found, err = _resolve_from_request()
    if err:
        return err
    uri, label = found
    sp.start_playback(uris=[uri])
    return jsonify(ok=True, label=label)


if __name__ == "__main__":
    # Bound to 127.0.0.1 so it's only reachable from your own machine.
    app.run(host="127.0.0.1", port=5000, debug=False)
