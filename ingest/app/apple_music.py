import os
import requests
from typing import List, Dict, Optional
from datetime import datetime, timedelta
import pytz


class AppleMusicClient:
    def __init__(self):
        self.developer_token = os.getenv("APPLE_DEVELOPER_TOKEN")
        self.user_token = os.getenv("APPLE_MUSIC_USER_TOKEN")

        if not self.developer_token:
            raise ValueError("APPLE_DEVELOPER_TOKEN environment variable is required")
        if not self.user_token:
            raise ValueError("APPLE_MUSIC_USER_TOKEN environment variable is required")

        self.base_url = "https://api.music.apple.com/v1"
        self.headers = {
            "Authorization": f"Bearer {self.developer_token}",
            "Music-User-Token": self.user_token,
        }

    def get_recently_played(self, limit: int = 30) -> List[Dict]:
        url = f"{self.base_url}/me/recent/played/tracks"
        params = {"limit": limit}

        try:
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            data = response.json()

            songs = []
            for position, item in enumerate(data.get("data", [])):
                song = self._parse_song(item, position)
                if song:
                    songs.append(song)

            return songs

        except requests.exceptions.RequestException as e:
            print(f"Error fetching recently played songs: {e}")
            if hasattr(e, 'response') and e.response is not None:
                print(f"Response status: {e.response.status_code}")
                print(f"Response body: {e.response.text}")
            raise

    def _parse_song(self, item: Dict, position: int) -> Optional[Dict]:
        try:
            attributes = item.get("attributes", {})

            title = attributes.get("name")
            artist = attributes.get("artistName")
            album = attributes.get("albumName")

            if not title or not artist:
                return None

            apple_music_id = item.get("id")
            isrc = attributes.get("isrc")

            duration_ms = attributes.get("durationInMillis")
            release_date = attributes.get("releaseDate")

            apple_music_url = attributes.get("url")

            artwork = attributes.get("artwork", {})
            artwork_url = None
            if artwork:
                url_template = artwork.get("url")
                if url_template:
                    width = artwork.get("width", 600)
                    height = artwork.get("height", 600)
                    artwork_url = url_template.replace("{w}", str(width)).replace("{h}", str(height))

            played_at = None

            return {
                "title": title,
                "artist": artist,
                "album": album,
                "apple_music_id": apple_music_id,
                "isrc": isrc,
                "duration_ms": duration_ms,
                "release_date": release_date,
                "apple_music_url": apple_music_url,
                "artwork_url": artwork_url,
                "played_at": played_at,
                "position": position,
                "payload": item
            }

        except Exception as e:
            print(f"Error parsing song: {e}")
            return None
