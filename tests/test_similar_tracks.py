import pytest

import similar_tracks
from similar_tracks import clean_title


@pytest.mark.parametrize(
    "raw, expected",
    [
        ("Track Name - Original Mix", "Track Name"),
        ("Track Name (Extended Mix)", "Track Name"),
        ("Track Name - Radio Edit", "Track Name"),
        ("Track Name (Club Mix)", "Track Name"),
        ("Track Name (feat. Someone)", "Track Name"),
        ("Track Name - feat. Someone", "Track Name"),
        ("Plain Title", "Plain Title"),
    ],
)
def test_clean_title_strips_dance_suffixes(raw, expected):
    assert clean_title(raw) == expected


def test_clean_title_keeps_named_remixes():
    # A specific remix is a different recording, so it must not be stripped.
    assert clean_title("Track Name (Artist Remix)") == "Track Name (Artist Remix)"


def test_get_similar_falls_back_to_cleaned_title(monkeypatch):
    calls = []

    def fake_by_track(artist, title, limit=50):
        calls.append(title)
        if title == "Track Name":
            return [{"artist": "X", "title": "Y", "match": 0.8, "source": "similar track"}]
        return []

    monkeypatch.setattr(similar_tracks, "similar_by_track", fake_by_track)
    result = similar_tracks.get_similar("Artist", "Track Name - Original Mix")

    assert calls == ["Track Name - Original Mix", "Track Name"]
    assert result[0]["match"] == 0.8


def test_get_similar_falls_back_to_artists(monkeypatch):
    monkeypatch.setattr(similar_tracks, "similar_by_track", lambda *a, **k: [])
    monkeypatch.setattr(
        similar_tracks,
        "similar_by_artist",
        lambda artist: [{"artist": "Z", "title": "T", "match": 0.5, "source": "similar artist"}],
    )
    result = similar_tracks.get_similar("Artist", "Obscure Track")
    assert result[0]["source"] == "similar artist"
