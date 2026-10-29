"""Authenticate with Spotify and read the currently playing track."""

from dotenv import load_dotenv
import spotipy
from spotipy.oauth2 import SpotifyOAuth

load_dotenv()  # reads SPOTIPY_CLIENT_ID, SPOTIPY_CLIENT_SECRET, SPOTIPY_REDIRECT_URI from .env

SCOPE = (
    "user-read-currently-playing "
    "user-read-playback-state "
    "user-modify-playback-state"
)

sp = spotipy.Spotify(auth_manager=SpotifyOAuth(scope=SCOPE))


def get_now_playing():
    """Return (artist, title, spotify_track_id) or None if nothing is playing."""
    current = sp.current_user_playing_track()
    if not current or not current.get("item"):
        return None
    track = current["item"]
    return track["artists"][0]["name"], track["name"], track["id"]


if __name__ == "__main__":
    result = get_now_playing()
    if result is None:
        print("Nothing playing right now. Start a track in Spotify and run again.")
    else:
        artist, title, track_id = result
        print(f"Now playing: {artist} - {title}  (id: {track_id})")
