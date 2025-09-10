import json
import os
import uuid

class PlaylistManager:
    """
    Manages multiple playlists, including adding, removing, and saving.
    """
    def __init__(self, filename="playlists.json"):
        self.filename = filename
        self.playlists = self.load_playlists()

    def load_playlists(self):
        if os.path.exists(self.filename):
            try:
                with open(self.filename, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except (json.JSONDecodeError, FileNotFoundError):
                return {}
        return {}

    def save_playlists(self):
        with open(self.filename, 'w', encoding='utf-8') as f:
            json.dump(self.playlists, f, indent=4, ensure_ascii=False)

    def add_new_playlist(self, name, songs, source_url=None, thumbnail=None):
        playlist_id = str(uuid.uuid4())
        self.playlists[playlist_id] = {
            "name": name,
            "songs": songs,
            "source_url": source_url,
            "thumbnail": thumbnail  # Store the thumbnail URL or local path here
        }
        self.save_playlists()
        return playlist_id

    def remove_playlist(self, playlist_id):
        if playlist_id in self.playlists:
            del self.playlists[playlist_id]
            self.save_playlists()

    def add_song_to_playlist(self, playlist_id, song_info):
        if playlist_id in self.playlists:
            # Check if the song already exists (compare by video ID or URL)
            existing = self.playlists[playlist_id]["songs"]
            if any(s.get("id") == song_info.get("id") for s in existing):
                return False  # ❌ Song already exists

            # Otherwise, add it
            self.playlists[playlist_id]["songs"].append(song_info)
            self.save_playlists()
            return True
        return False  # Playlist doesn't exist

    def remove_song_from_playlist(self, playlist_id, song_index):
        if playlist_id in self.playlists and 0 <= song_index < len(self.playlists[playlist_id]['songs']):
            del self.playlists[playlist_id]['songs'][song_index]
            self.save_playlists()

    def update_playlist_songs(self, playlist_id, new_songs):
        if playlist_id in self.playlists:
            self.playlists[playlist_id]['songs'] = new_songs
            self.save_playlists()
    
    def update_playlist_thumbnail(self, playlist_id, thumbnail_path):
        """Updates the thumbnail for a specific playlist."""
        if playlist_id in self.playlists:
            self.playlists[playlist_id]['thumbnail'] = thumbnail_path
            self.save_playlists()
            
    def remove_playlist_thumbnail(self, playlist_id):
        """Removes the custom thumbnail from a playlist."""
        if playlist_id in self.playlists and 'thumbnail' in self.playlists[playlist_id]:
            self.playlists[playlist_id]['thumbnail'] = self.playlists[playlist_id].get('source_thumbnail', None)
            self.save_playlists()
            
    def get_playlist_thumbnail(self, playlist_id):
        """Returns the custom or YouTube thumbnail for the playlist."""
        return self.playlists.get(playlist_id, {}).get('thumbnail')

    def get_first_song_thumbnail(self, playlist_id):
        if playlist_id in self.playlists and self.playlists[playlist_id]['songs']:
            return self.playlists[playlist_id]['songs'][0].get('thumbnail_url')
        return None

    def get_songs(self, playlist_id):
        return self.playlists.get(playlist_id, {}).get('songs', [])

    def get_all_playlists(self):
        return self.playlists
    
    def get_playlist_by_url(self, source_url):
        """
        Returns the playlist ID if a playlist with the given source URL exists, otherwise returns None.
        """
        for playlist_id, playlist_data in self.playlists.items():
            if playlist_data.get("source_url") == source_url:
                return playlist_id
        return None
        
    def get_playlist_url(self, playlist_id):
        return self.playlists.get(playlist_id, {}).get('source_url', None)
    
    def update_playlist_if_changed(self, playlist_id, new_songs):
        """Update the playlist only if there are new or changed songs."""
        if playlist_id not in self.playlists:
            return False

        existing_ids = {s["id"] for s in self.playlists[playlist_id]["songs"]}
        new_ids = {s["id"] for s in new_songs}

        if existing_ids == new_ids:
            return False  # No changes

        # Update playlist with fresh songs
        self.playlists[playlist_id]["songs"] = new_songs
        self.save_playlists()
        return True
    
    def diff_playlist(self, playlist_id, new_songs):
        """Return lists of added and removed songs by ID."""
        existing = {s['id'] for s in self.playlists.get(playlist_id, {}).get('songs', [])}
        incoming = {s['id'] for s in new_songs}

        added_ids = incoming - existing
        removed_ids = existing - incoming

        return added_ids, removed_ids
    
    def song_exists(self, playlist_id, song_id):
        """Check if a song with the given ID already exists in a specific playlist."""
        if playlist_id in self.playlists:
            for song in self.playlists[playlist_id].get("songs", []):
                if song.get("id") == song_id:
                    return True
        return False

    def ensure_default_playlist(self):
        """
        Ensure that a default 'My Songs' playlist exists.
        If not, create it and return its ID.
        """
        # Look for an existing 'My Songs' playlist
        for playlist_id, playlist in self.playlists.items():
            if playlist.get("name") == "My Songs":
                return playlist_id

        # If not found, create a new one
        new_id = str(len(self.playlists) + 1)  # or use uuid if you prefer unique IDs
        self.playlists[new_id] = {
            "name": "My Songs",
            "songs": [],
            "source_url": None,
            "thumbnail": None
        }
        self.save_playlists()
        return new_id
