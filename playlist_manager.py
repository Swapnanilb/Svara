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
                with open(self.filename, 'r') as f:
                    return json.load(f)
            except (json.JSONDecodeError, FileNotFoundError):
                return {}
        return {}

    def save_playlists(self):
        with open(self.filename, 'w') as f:
            json.dump(self.playlists, f, indent=4)

    def add_new_playlist(self, name, songs, source_url=None):
        # The duplicate check has been moved to main.py for efficiency.
        # This function now assumes the check has already been performed.
        playlist_id = str(uuid.uuid4())
        self.playlists[playlist_id] = {
            "name": name,
            "songs": songs,
            "source_url": source_url
        }
        self.save_playlists()
        return playlist_id

    def remove_playlist(self, playlist_id):
        if playlist_id in self.playlists:
            del self.playlists[playlist_id]
            self.save_playlists()

    def add_song_to_playlist(self, playlist_id, song_info):
        if playlist_id in self.playlists:
            if not any(s['id'] == song_info['id'] for s in self.playlists[playlist_id]['songs']):
                self.playlists[playlist_id]['songs'].append(song_info)
                self.save_playlists()

    def remove_song_from_playlist(self, playlist_id, song_index):
        if playlist_id in self.playlists and 0 <= song_index < len(self.playlists[playlist_id]['songs']):
            del self.playlists[playlist_id]['songs'][song_index]
            self.save_playlists()

    def update_playlist_songs(self, playlist_id, new_songs):
        if playlist_id in self.playlists:
            self.playlists[playlist_id]['songs'] = new_songs
            self.save_playlists()

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