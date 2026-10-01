# -*- coding: utf-8 -*-
"""Dynamic Jellyfin/Kodi discovery rows for Nimbus.

The Jellyfin for Kodi add-on mirrors the user's Jellyfin library into Kodi's
native video database.  That makes it possible to build lightweight,
privacy-preserving recommendations locally without storing Jellyfin
credentials in the skin/helper.

Two smart playlists are generated under the active Kodi profile:
- nimbus_jellyfin_because.xsp: titles similar to the most recently watched film
- nimbus_jellyfin_for_you.xsp: a broader preference profile from recent history

The generated playlists contain only unwatched titles already present in Kodi.
"""

import json
import time
import xml.etree.ElementTree as ET

import xbmc
import xbmcvfs


PLAYLIST_DIR = "special://profile/playlists/video/"
BECAUSE_PATH = PLAYLIST_DIR + "nimbus_jellyfin_because.xsp"
FOR_YOU_PATH = PLAYLIST_DIR + "nimbus_jellyfin_for_you.xsp"

MAX_LIBRARY_ITEMS = 2000
MAX_RECOMMENDATIONS = 20
HISTORY_SIZE = 10
MIN_REFRESH_SECONDS = 30


def _jsonrpc(method, params=None):
    request = {"jsonrpc": "2.0", "id": "nimbus-jellyfin", "method": method}
    if params is not None:
        request["params"] = params
    try:
        response = json.loads(xbmc.executeJSONRPC(json.dumps(request)))
        return response.get("result", {})
    except Exception:
        return {}


def _norm(values):
    return {
        str(value).strip().casefold()
        for value in (values or [])
        if str(value).strip()
    }


def _lastplayed_key(movie):
    return movie.get("lastplayed") or ""


def _rating(movie):
    try:
        return float(movie.get("rating") or 0)
    except (TypeError, ValueError):
        return 0.0


def _year(movie):
    try:
        return int(movie.get("year") or 0)
    except (TypeError, ValueError):
        return 0


def _write_title_playlist(path, name, movies):
    if not movies:
        if xbmcvfs.exists(path):
            xbmcvfs.delete(path)
        return

    if not xbmcvfs.exists(PLAYLIST_DIR):
        xbmcvfs.mkdirs(PLAYLIST_DIR)

    root = ET.Element("smartplaylist", {"type": "movies"})
    ET.SubElement(root, "name").text = name
    ET.SubElement(root, "match").text = "one"

    seen = set()
    for movie in movies:
        # Kodi's movie path is the identity we can safely address from an XSP
        # rule.  Title is not unique (remakes/editions can share it).
        path_value = (movie.get("file") or "").strip()
        if not path_value:
            continue
        key = path_value.casefold()
        if key in seen:
            continue
        seen.add(key)
        rule = ET.SubElement(root, "rule", {"field": "path", "operator": "is"})
        ET.SubElement(rule, "value").text = path_value

    ET.SubElement(root, "limit").text = str(MAX_RECOMMENDATIONS)
    ET.SubElement(root, "order", {"direction": "descending"}).text = "rating"

    payload = '<?xml version="1.0" encoding="UTF-8" standalone="yes" ?>\n'
    payload += ET.tostring(root, encoding="unicode")

    handle = xbmcvfs.File(path, "w")
    try:
        handle.write(payload)
    finally:
        handle.close()


class RecommendationEngine:
    def __init__(self, home_window):
        self.home_window = home_window
        self._last_refresh = 0.0

    def refresh(self, force=False):
        now = time.monotonic()
        if not force and now - self._last_refresh < MIN_REFRESH_SECONDS:
            return

        self._last_refresh = now
        movies = self._movies()
        if not movies:
            self._clear()
            return

        watched = [
            movie
            for movie in movies
            if int(movie.get("playcount") or 0) > 0 and movie.get("lastplayed")
        ]
        watched.sort(key=_lastplayed_key, reverse=True)

        unwatched = [movie for movie in movies if int(movie.get("playcount") or 0) < 1]

        if watched:
            source = watched[0]
            source_title = (source.get("title") or source.get("label") or "").strip()
            because = self._because_you_watched(source, unwatched)
            self.home_window.setProperty(
                "JellyfinBecauseYouWatchedLabel",
                "Because You Watched: {}".format(source_title)
                if source_title
                else "Because You Watched",
            )
            _write_title_playlist(
                BECAUSE_PATH,
                "Because You Watched",
                because,
            )
        else:
            self.home_window.setProperty(
                "JellyfinBecauseYouWatchedLabel", "Because You Watched"
            )
            _write_title_playlist(BECAUSE_PATH, "Because You Watched", [])

        for_you = self._for_you(watched, unwatched)
        _write_title_playlist(FOR_YOU_PATH, "You Might Like", for_you)

    def _movies(self):
        result = _jsonrpc(
            "VideoLibrary.GetMovies",
            {
                "properties": [
                    "title",
                    "genre",
                    "studio",
                    "playcount",
                    "lastplayed",
                    "rating",
                    "year",
                    "dateadded",
                    "file",
                ],
                "limits": {"start": 0, "end": MAX_LIBRARY_ITEMS},
            },
        )
        return result.get("movies", []) or []

    def _because_you_watched(self, source, candidates):
        source_genres = _norm(source.get("genre"))
        source_studios = _norm(source.get("studio"))
        source_year = _year(source)

        scored = []
        for movie in candidates:
            genres = _norm(movie.get("genre"))
            studios = _norm(movie.get("studio"))

            shared_genres = len(source_genres & genres)
            shared_studios = len(source_studios & studios)
            if shared_genres == 0 and shared_studios == 0:
                continue

            score = shared_genres * 5.0 + shared_studios * 2.0
            score += _rating(movie) * 0.2

            year = _year(movie)
            if source_year and year:
                score += max(0.0, 2.0 - abs(source_year - year) / 5.0)

            scored.append((score, movie))

        scored.sort(
            key=lambda item: (item[0], _rating(item[1]), item[1].get("dateadded") or ""),
            reverse=True,
        )
        return [movie for _, movie in scored[:MAX_RECOMMENDATIONS]]

    def _for_you(self, watched, candidates):
        if not watched:
            fallback = sorted(
                candidates,
                key=lambda movie: (_rating(movie), movie.get("dateadded") or ""),
                reverse=True,
            )
            return fallback[:MAX_RECOMMENDATIONS]

        genre_weights = {}
        studio_weights = {}

        for index, movie in enumerate(watched[:HISTORY_SIZE]):
            recency = 1.0 / (1.0 + index * 0.35)

            for genre in _norm(movie.get("genre")):
                genre_weights[genre] = genre_weights.get(genre, 0.0) + 3.0 * recency

            for studio in _norm(movie.get("studio")):
                studio_weights[studio] = studio_weights.get(studio, 0.0) + 1.5 * recency

        scored = []
        for movie in candidates:
            genres = _norm(movie.get("genre"))
            studios = _norm(movie.get("studio"))

            preference_score = sum(genre_weights.get(g, 0.0) for g in genres)
            preference_score += sum(studio_weights.get(s, 0.0) for s in studios)

            if preference_score <= 0:
                continue

            # Rating is deliberately only a tie-breaker; taste similarity dominates.
            score = preference_score + _rating(movie) * 0.15
            scored.append((score, movie))

        scored.sort(
            key=lambda item: (item[0], _rating(item[1]), item[1].get("dateadded") or ""),
            reverse=True,
        )
        return [movie for _, movie in scored[:MAX_RECOMMENDATIONS]]

    def _clear(self):
        self.home_window.setProperty(
            "JellyfinBecauseYouWatchedLabel", "Because You Watched"
        )
        for path in (BECAUSE_PATH, FOR_YOU_PATH):
            if xbmcvfs.exists(path):
                xbmcvfs.delete(path)
