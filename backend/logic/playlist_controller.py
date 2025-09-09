import threading
from playlist_manager import PlaylistManager

class PlaylistController:
    def __init__(self, main_logic):
        self.main_logic = main_logic
        self.ui = main_logic.ui
        
        # Initialize playlist manager
        self.playlist_manager = PlaylistManager()

    def display_playlist_songs(self, playlist_id):
        """Display songs from a specific playlist."""
        self.main_logic.current_playlist_id = playlist_id
        self.ui.update_playlist_card_colors(playlist_id)
        self.ui.clear_track_list()
        threading.Thread(target=self._load_playlist_thread, args=(playlist_id,), daemon=True).start()
        
    def _load_playlist_thread(self, playlist_id):
        """Load playlist songs in a background thread."""
        songs = self.playlist_manager.get_songs(playlist_id)
        self.main_logic.songs_to_add = songs
        
        # Update shuffle indices if needed
        self.main_logic.playback_controller.update_shuffle_indices_for_new_playlist(len(songs))
        
        self.main_logic.selected_song_index = -1
        self.ui.after(10, self._update_ui_with_songs_in_chunks)

    def _update_ui_with_songs_in_chunks(self, chunk_size=50):
        """Update UI with songs in chunks to prevent blocking."""
        if self.main_logic.songs_to_add:
            chunk = self.main_logic.songs_to_add[:chunk_size]
            self.main_logic.songs_to_add = self.main_logic.songs_to_add[chunk_size:]
            
            for song in chunk:
                self.ui.create_song_widget(song)
            
            self.ui.after(10, self._update_ui_with_songs_in_chunks)

    def filter_songs(self, search_term):
        """Filter displayed songs by search term."""
        if search_term.lower() == "search playlist...":
            search_term = ""

        self.ui.clear_track_list()
        
        if not self.main_logic.current_playlist_id:
            return
        
        songs = self.playlist_manager.get_songs(self.main_logic.current_playlist_id)
        filtered_songs = [
            s for s in songs 
            if search_term.lower() in s['title'].lower()
        ]
        
        self.main_logic.songs_to_add = filtered_songs
        self.ui.after(10, self._update_ui_with_songs_in_chunks)

    def remove_song_by_index(self, index_to_remove):
        """Remove a song from the current playlist."""
        if not self.main_logic.current_playlist_id:
            return
        
        # Stop playback if removing the currently playing song
        if self.main_logic.current_song_index == index_to_remove:
            self.main_logic.music_player.stop()
            self.ui.reset_now_playing_view()
            self.main_logic.current_song_index = -1
        
        # Remove song from playlist
        self.playlist_manager.remove_song_from_playlist(
            self.main_logic.current_playlist_id, 
            index_to_remove
        )
        
        # Refresh the display
        self.display_playlist_songs(self.main_logic.current_playlist_id)

    def remove_playlist(self, playlist_id):
        """Remove a playlist entirely."""
        # Stop playback if removing the current playlist
        if self.main_logic.current_playlist_id == playlist_id:
            self.main_logic.music_player.stop()
            self.ui.reset_now_playing_view()
            self.main_logic.current_song_index = -1
            self.main_logic.current_playlist_id = None
        
        # Remove playlist
        self.playlist_manager.remove_playlist(playlist_id)
        
        # Update UI
        self.ui.load_playlist_cards()
        self.ui.clear_track_list()

    def upload_playlist_thumbnail(self, playlist_id, file_path):
        """Upload a custom thumbnail for a playlist."""
        if file_path:
            self.playlist_manager.update_playlist_thumbnail(playlist_id, file_path)
            self.ui.update_playlist_card_thumbnail(playlist_id)
            
    def remove_custom_playlist_thumbnail(self, playlist_id):
        """Remove custom thumbnail from a playlist."""
        self.playlist_manager.remove_playlist_thumbnail(playlist_id)
        self.ui.update_playlist_card_thumbnail(playlist_id)

    def add_song_to_playlist(self, playlist_id, song_info):
        """Add a song to a specific playlist."""
        if not self.playlist_manager.song_exists(playlist_id, song_info["id"]):
            self.playlist_manager.add_song_to_playlist(playlist_id, song_info)
            
            # Refresh display if this is the current playlist
            if self.main_logic.current_playlist_id == playlist_id:
                self.display_playlist_songs(playlist_id)
            
            return True
        return False

    def create_new_playlist_with_song(self, name, song_info):
        """Create a new playlist with a single song."""
        playlist_id = self.playlist_manager.add_new_playlist(name, [song_info])
        # Don't call UI methods directly from here - let the main logic handle UI updates
        self.display_playlist_songs(playlist_id)
        return playlist_id

    def get_current_playlist_songs(self):
        """Get songs from the currently selected playlist."""
        if not self.main_logic.current_playlist_id:
            return []
        return self.playlist_manager.get_songs(self.main_logic.current_playlist_id)

    def get_playlist_info(self, playlist_id):
        """Get information about a specific playlist."""
        all_playlists = self.playlist_manager.get_all_playlists()
        return all_playlists.get(playlist_id, {})

    def playlist_exists(self, playlist_id):
        """Check if a playlist exists."""
        all_playlists = self.playlist_manager.get_all_playlists()
        return playlist_id in all_playlists

    def get_playlist_by_url(self, url):
        """Get playlist ID by source URL."""
        return self.playlist_manager.get_playlist_by_url(url)