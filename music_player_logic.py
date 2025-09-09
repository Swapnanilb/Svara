from logic.playback_controller import PlaybackController
from logic.playlist_controller import PlaylistController
from logic.ui_controller import UIController
from logic.youtube_controller import YouTubeController
from logic.progress_tracker import ProgressTracker
from utils.text_utils import TextUtils

class MusicPlayerLogic:
    def __init__(self, ui_callback_handler):
        """
        Initialize the music player logic with modular controllers.
        ui_callback_handler should be an object that implements UI update methods.
        """
        self.ui = ui_callback_handler
        self.text_utils = TextUtils()
        
        # Initialize controllers
        self.playback_controller = PlaybackController(self)
        self.playlist_controller = PlaylistController(self)
        self.ui_controller = UIController(self)
        self.youtube_controller = YouTubeController(self)
        self.progress_tracker = ProgressTracker(self)
        
        # Global state that controllers need access to
        self.current_playlist_id = None
        self.current_song_index = -1
        self.selected_song_index = -1
        self.sync_mode = False
        
        # Temporary storage
        self.songs_to_add = []

    # Text processing utility
    def clean_title(self, title: str) -> str:
        """Return a simplified song title (remove artist/extra text)."""
        return self.text_utils.clean_song_title(title)

    # Delegate methods to appropriate controllers
    def play_song_by_index(self, index):
        """Play a song by its index in the current playlist."""
        self.playback_controller.play_song_by_index(index)

    def play_next_song(self):
        """Play the next song based on current mode (shuffle/repeat)."""
        self.playback_controller.play_next_song()

    def toggle_play_pause(self):
        """Toggle between play and pause states."""
        self.playback_controller.toggle_play_pause()

    def next_song(self):
        """Skip to the next song."""
        self.playback_controller.next_song()

    def prev_song(self):
        """Skip to the previous song."""
        self.playback_controller.prev_song()

    def toggle_shuffle(self):
        """Toggle shuffle mode on/off."""
        self.playback_controller.toggle_shuffle()

    def toggle_repeat(self):
        """Toggle repeat mode on/off."""
        self.playback_controller.toggle_repeat()

    def set_volume(self, volume):
        """Set the playback volume."""
        self.playback_controller.set_volume(volume)

    def toggle_mute(self):
        """Toggle mute on/off."""
        self.playback_controller.toggle_mute()

    def volume_up(self):
        """Increase volume by 10%."""
        self.playback_controller.volume_up()

    def volume_down(self):
        """Decrease volume by 10%."""
        self.playback_controller.volume_down()

    def seek_forward(self, seconds):
        """Seek forward by specified seconds."""
        self.playback_controller.seek_forward(seconds)

    def seek_backward(self, seconds):
        """Seek backward by specified seconds."""
        self.playback_controller.seek_backward(seconds)

    def preview_progress(self, value):
        """Preview progress position without seeking."""
        self.progress_tracker.preview_progress(value)

    def set_seeking(self, seeking):
        """Set seeking state."""
        self.progress_tracker.set_seeking(seeking)

    def handle_slider_seek(self, seconds):
        """Handle slider seek operation."""
        self.progress_tracker.handle_slider_seek(seconds)

    def display_playlist_songs(self, playlist_id):
        """Display songs from a specific playlist."""
        self.playlist_controller.display_playlist_songs(playlist_id)

    def add_from_link(self, url):
        """Add song or playlist from YouTube URL."""
        self.youtube_controller.add_from_link(url)

    def sync_playlist(self):
        """Sync current playlist with YouTube source."""
        self.youtube_controller.sync_playlist()
    
    def load_tracks(self):
        """Load tracks of current playlist into cache."""
        if not self.current_playlist_id:
            self.ui.show_info("Load Tracks", "Please select a playlist first.")
            return
        
        songs = self.playlist_manager.get_songs(self.current_playlist_id)
        if not songs:
            self.ui.show_info("Load Tracks", "No tracks found in the current playlist.")
            return
        
        self.ui.show_loading(f"Loading {len(songs)} tracks into cache...")
        self.youtube_controller.load_tracks_to_cache(songs)

    def filter_songs(self, search_term):
        """Filter displayed songs by search term."""
        self.playlist_controller.filter_songs(search_term)

    def remove_song_by_index(self, index_to_remove):
        """Remove a song from the current playlist."""
        self.playlist_controller.remove_song_by_index(index_to_remove)

    def select_next_song(self):
        """Select the next song in the list."""
        self.ui_controller.select_next_song()

    def select_prev_song(self):
        """Select the previous song in the list."""
        self.ui_controller.select_prev_song()

    def play_selected_song(self):
        """Play the currently selected song."""
        self.ui_controller.play_selected_song()

    def remove_playlist(self, playlist_id):
        """Remove a playlist entirely."""
        self.playlist_controller.remove_playlist(playlist_id)

    def upload_playlist_thumbnail(self, playlist_id, file_path):
        """Upload a custom thumbnail for a playlist."""
        self.playlist_controller.upload_playlist_thumbnail(playlist_id, file_path)

    def remove_custom_playlist_thumbnail(self, playlist_id):
        """Remove custom thumbnail from a playlist."""
        self.playlist_controller.remove_custom_playlist_thumbnail(playlist_id)

    def add_song_to_playlist(self, playlist_id, song_info):
        """Add a song to a specific playlist."""
        return self.playlist_controller.add_song_to_playlist(playlist_id, song_info)

    def create_new_playlist_with_song(self, name, song_info):
        """Create a new playlist with a single song."""
        playlist_id = self.playlist_controller.create_new_playlist_with_song(name, song_info)
        # Refresh playlist cards after creation
        self.ui.load_playlist_cards()
        return playlist_id

    def stop_and_cleanup(self):
        """Stop playback and clean up resources."""
        self.playback_controller.stop_and_cleanup()
        self.progress_tracker.stop_and_cleanup()

    # Properties for controllers to access
    @property
    def playlist_manager(self):
        """Access to playlist manager through playlist controller."""
        return self.playlist_controller.playlist_manager

    @property
    def music_player(self):
        """Access to music player through playback controller."""
        return self.playback_controller.music_player

    @property
    def is_seeking(self):
        """Check if currently seeking."""
        return self.progress_tracker.is_seeking