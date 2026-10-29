# Spotify Similar Tracks

Find songs that match the vibe of whatever is playing on Spotify, then queue or play them in one click.

Spotify's own audio-analysis and recommendation endpoints are closed to newly created apps, so this project combines **Spotify** (playback, search, queue) with **Last.fm** (listener-based track similarity). It ships as both a terminal tool and a small local web app.

![status](https://img.shields.io/badge/status-working%20prototype-yellow) ![python](https://img.shields.io/badge/python-3.9%2B-blue) ![license](https://img.shields.io/badge/license-MIT-green)

## What it does

1. Reads the track currently playing on your Spotify account.
2. Asks Last.fm for similar tracks, each with a match score from 0 to 1.
3. Cleans up dance-music title suffixes (`- Original Mix`, `(feat. ...)`) so lookups succeed, and falls back to similar artists' top tracks when a track has no data.
4. Lets you filter by match score, then **queue** or **play** any result on your active Spotify device.

## Why Last.fm and not Spotify's recommendations?

Apps created after November 27, 2024 get a 403 from Spotify's recommendations, audio-features, audio-analysis and related-artists endpoints. That removed the obvious way to do this, so similarity comes from Last.fm instead, and Spotify is used for what it still does well.

## Architecture

```
 Browser UI (templates/index.html)
        |  fetch()
        v
 Flask app (app.py) ---- /api/now, /api/similar, /api/queue, /api/play
        |                         |
        v                         v
 now_playing.py            similar_tracks.py
 (Spotify OAuth,           (Last.fm lookups,
  playback, search)         title cleaning, fallback)
```

- `now_playing.py` - Spotify OAuth (authorization-code flow) and the shared client.
- `similar_tracks.py` - Last.fm lookups, title normalisation, artist-level fallback.
- `interactive.py` - terminal interface (`q 3`, `p 3`, `qa`, `r`).
- `app.py` + `templates/index.html` - local web interface.
- `tests/` - unit tests for the title cleaning and fallback logic, run in CI.

## Setup

**Requirements:** Python 3.9+, a Spotify **Premium** account (needed for playback control), and free API credentials from Spotify and Last.fm.

1. **Spotify app:** create one at <https://developer.spotify.com/dashboard> (Web API). Add the redirect URI `http://127.0.0.1:8888/callback` and add your account under *User Management*.
2. **Last.fm key:** create one at <https://www.last.fm/api/account/create>.
3. **Install:**
   ```bash
   git clone https://github.com/<your-username>/spotify-similar-tracks.git
   cd spotify-similar-tracks
   python3 -m venv venv && source venv/bin/activate
   pip install -r requirements.txt
   ```
4. **Configure:** copy `.env.example` to `.env` and fill in your values.

## Usage

Start a song in Spotify (any device), then:

```bash
python app.py          # web app at http://127.0.0.1:5000
# or
python interactive.py  # terminal version
```

The first run opens a browser window to authorise Spotify access. The token is cached locally in `.cache` (git-ignored).

## Development

```bash
pip install -r requirements-dev.txt
pytest
```

## Security notes

- Credentials live in `.env` and the token cache in `.cache`; both are git-ignored. If either is ever committed, rotate the Spotify client secret and Last.fm key immediately.
- The web app binds to `127.0.0.1` only, so nothing on your network can reach it or control your playback.
- Scopes are limited to what is needed: `user-read-currently-playing`, `user-read-playback-state`, `user-modify-playback-state`.

## Limitations

- Match scores come from listener behaviour, not audio, so they say nothing about key or tempo.
- Niche tracks may have no Last.fm data; the artist-level fallback is less precise.
- Matching Last.fm results back to Spotify uses search, so remixes and edits can occasionally match the wrong version. The UI shows what was matched.
- Spotify Development Mode limits the app to a handful of authorised users, so this is a personal tool, not a public service.

## Roadmap

- Key and tempo filtering using an audio-features source, with Camelot-wheel harmonic matching.
- Combined ranking (similarity + key + tempo + energy).
- Save the shortlist to a new Spotify playlist.
- Containerise and deploy with HTTPS and per-session token storage.

## License

MIT
