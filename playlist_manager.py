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

    def add_new_playlist(self, name, songs, thumbnail=None, youtube_id=None):
        playlist_id = str(uuid.uuid4())
        self.playlists[playlist_id] = {
            "name": name,
            "thumbnail": thumbnail,
            "youtube_id": youtube_id,  # Store the YouTube playlist ID
            "songs": songs
        }
        self.save_playlists()
        return playlist_id

    def find_playlist_by_youtube_id(self, youtube_id):
        if not youtube_id:
            return None
        for playlist_id, playlist_data in self.playlists.items():
            if playlist_data.get("youtube_id") == youtube_id:
                return playlist_id
        return None

    def add_new_songs_to_existing_playlist(self, playlist_id, new_songs):
        if playlist_id not in self.playlists:
            return 0
        
        existing_songs = self.playlists[playlist_id]['songs']
        existing_song_ids = {song['id'] for song in existing_songs}
        
        new_songs_added_count = 0
        for song in new_songs:
            if song['id'] not in existing_song_ids:
                existing_songs.append(song)
                new_songs_added_count += 1
        
        if new_songs_added_count > 0:
            self.save_playlists()
            
        return new_songs_added_count

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

    def get_songs(self, playlist_id):
        return self.playlists.get(playlist_id, {}).get('songs', [])
    
    def get_all_playlists(self):
        return self.playlists