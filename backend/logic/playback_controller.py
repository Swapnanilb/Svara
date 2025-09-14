import threading
import random
import time
from player import MusicPlayer
from performance_logger import perf_logger

class PlaybackController:
    def __init__(self, main_logic):
        self.main_logic = main_logic
        self.ui = main_logic.ui
        
        # Initialize music player
        self.music_player = MusicPlayer(self.ui, self.play_next_song)
        
        # Playback state
        self.current_song_info = None
        self.is_shuffled = False
        self.is_repeated = False
        self.shuffled_indices = []
        self.current_shuffled_index = -1
        self.last_volume = 0.5

    def play_song_by_index(self, index):
        """Play a song by its index in the current playlist."""
        if not self.main_logic.current_playlist_id:
            return

        songs = self.main_logic.playlist_manager.get_songs(self.main_logic.current_playlist_id)
        if 0 <= index < len(songs):
            song = songs[index]
            self.main_logic.current_song_index = index
            self.current_song_info = song
            
            # Stop any existing progress tracking and playback
            self.main_logic.progress_tracker.stop_progress_tracking()
            self.music_player.stop()
            
            # Preload next few songs in background
            self._preload_upcoming_songs(songs, index)
            
            # Always fetch fresh URL for YouTube songs
            if song.get('id'):  # YouTube song
                self.ui.update_now_playing_view(song, loading=True)
                threading.Thread(target=self._play_with_fresh_url, args=(song,), daemon=True).start()
            else:
                # Local file or other source
                self.music_player.play_song(self.current_song_info)
                self.ui.update_now_playing_view(self.current_song_info)
                self.main_logic.progress_tracker.start_progress_tracking()
            
            self.ui.update_play_pause_button()
            self.ui.highlight_current_song_widget()
            self.main_logic.selected_song_index = index
        else:
            self.music_player.stop()
            self.ui.reset_now_playing_view()

    def play_next_song(self):
        """Play the next song based on current mode (shuffle/repeat)."""
        try:
            if not self.main_logic.current_playlist_id:
                print("No current playlist, stopping playback")
                self.music_player.stop()
                return
                
            songs = self.main_logic.playlist_manager.get_songs(self.main_logic.current_playlist_id)
            if not songs:
                print("No songs in playlist, stopping playback")
                self.music_player.stop()
                return

            next_index = self._calculate_next_song_index(songs)
            if next_index == -1:
                print("Reached end of playlist, stopping playback")
                self.music_player.stop()
                self.ui.reset_now_playing_view()
                return
            
            self.play_song_by_index(next_index)
        except Exception as e:
            print(f"Error in play_next_song: {e}")
            self.music_player.stop()

    def _calculate_next_song_index(self, songs):
        """Calculate the next song index based on playback mode."""
        if self.is_repeated:
            return self.main_logic.current_song_index
        elif self.is_shuffled:
            return self._get_next_shuffled_index(songs)
        else:
            next_index = self.main_logic.current_song_index + 1
            if next_index >= len(songs):
                return -1  # Signal end of playlist
            return next_index

    def _get_next_shuffled_index(self, songs):
        """Get the next index for shuffle mode."""
        if not self.shuffled_indices:
            self.shuffled_indices = list(range(len(songs)))
            random.shuffle(self.shuffled_indices)
        
        self.current_shuffled_index = (self.current_shuffled_index + 1) % len(self.shuffled_indices)
        return self.shuffled_indices[self.current_shuffled_index]

    def _get_prev_shuffled_index(self, songs):
        """Get the previous index for shuffle mode."""
        if not self.shuffled_indices:
            self.shuffled_indices = list(range(len(songs)))
            random.shuffle(self.shuffled_indices)
        
        self.current_shuffled_index = (self.current_shuffled_index - 1 + len(self.shuffled_indices)) % len(self.shuffled_indices)
        return self.shuffled_indices[self.current_shuffled_index]

    def toggle_play_pause(self):
        """Toggle between play and pause states."""
        if self.music_player.is_playing and not self.music_player.is_paused:
            self.music_player.pause()
            self.main_logic.progress_tracker.stop_progress_tracking()
        elif self.music_player.is_paused:
            self.music_player.unpause()
            self.main_logic.progress_tracker.start_progress_tracking()
        elif self.main_logic.current_song_index != -1 and self.main_logic.current_playlist_id:
            self.play_song_by_index(self.main_logic.current_song_index)
        else:
            # Start playing first available playlist
            self._play_first_available()
        
        self.ui.update_play_pause_button()

    def _play_first_available(self):
        """Start playing the first available playlist."""
        playlists = self.main_logic.playlist_manager.get_all_playlists()
        first_playlist_id = list(playlists.keys())[0] if playlists else None
        if first_playlist_id:
            self.main_logic.display_playlist_songs(first_playlist_id)
            self.play_song_by_index(0)

    def next_song(self):
        """Skip to the next song."""
        songs = self.main_logic.playlist_manager.get_songs(self.main_logic.current_playlist_id)
        if not songs:
            return

        next_index = self._calculate_next_song_index(songs)
        self.play_song_by_index(next_index)

    def prev_song(self):
        """Skip to the previous song."""
        songs = self.main_logic.playlist_manager.get_songs(self.main_logic.current_playlist_id)
        if not songs:
            return

        if self.is_repeated:
            prev_index = self.main_logic.current_song_index
        elif self.is_shuffled:
            prev_index = self._get_prev_shuffled_index(songs)
        else:
            prev_index = (self.main_logic.current_song_index - 1 + len(songs)) % len(songs)
            
        self.play_song_by_index(prev_index)

    def toggle_shuffle(self):
        """Toggle shuffle mode on/off."""
        self.is_shuffled = not self.is_shuffled
        
        if self.is_shuffled:
            # Disable repeat when shuffle is enabled
            self.is_repeated = False
            self.ui.update_repeat_button(self.is_repeated)
            print("🔀 Shuffle ON | 🔁 Repeat OFF")
            
            songs = self.main_logic.playlist_manager.get_songs(self.main_logic.current_playlist_id)
            if songs:
                self.shuffled_indices = list(range(len(songs)))
                random.shuffle(self.shuffled_indices)
                self.current_shuffled_index = -1
        else:
            self.shuffled_indices = []
            self.current_shuffled_index = -1
            print("🔀 Shuffle OFF")

        self.ui.update_shuffle_button(self.is_shuffled)

    def toggle_repeat(self):
        """Toggle repeat mode on/off."""
        self.is_repeated = not self.is_repeated
        
        if self.is_repeated:
            # Disable shuffle when repeat is enabled
            self.is_shuffled = False
            self.shuffled_indices = []
            self.current_shuffled_index = -1
            self.ui.update_shuffle_button(self.is_shuffled)
            print("🔁 Repeat ON | 🔀 Shuffle OFF")
        else:
            print("🔁 Repeat OFF")
        
        self.ui.update_repeat_button(self.is_repeated)

    def set_volume(self, volume):
        """Set the playback volume."""
        self.music_player.set_volume(volume)
        if volume > 0:
            self.last_volume = volume
        self.ui.update_mute_button(volume > 0)

    def toggle_mute(self):
        """Toggle mute on/off."""
        current_volume = self.ui.get_volume()
        if current_volume > 0:
            self.last_volume = current_volume
            self.ui.set_volume(0)
            self.music_player.set_volume(0)
        else:
            volume_to_set = self.last_volume if self.last_volume > 0 else 0.5
            self.ui.set_volume(volume_to_set)
            self.music_player.set_volume(volume_to_set)
        self.ui.update_mute_button(self.ui.get_volume() > 0)

    def volume_up(self):
        """Increase volume by 10%."""
        current_volume = self.ui.get_volume()
        new_volume = min(1.0, current_volume + 0.1)
        self.ui.set_volume(new_volume)
        self.music_player.set_volume(new_volume)

    def volume_down(self):
        """Decrease volume by 10%."""
        current_volume = self.ui.get_volume()
        new_volume = max(0.0, current_volume - 0.1)
        self.ui.set_volume(new_volume)
        self.music_player.set_volume(new_volume)

    def seek_forward(self, seconds):
        """Seek forward by specified seconds."""
        if self.music_player.is_playing:
            current_pos = self.music_player.get_pos()
            new_pos_ms = current_pos + (seconds * 1000)
            self.music_player.set_pos(new_pos_ms)
            self.ui.set_progress(new_pos_ms / 1000)
            
    def seek_backward(self, seconds):
        """Seek backward by specified seconds."""
        if self.music_player.is_playing:
            current_pos = self.music_player.get_pos()
            new_pos_ms = max(0, current_pos - (seconds * 1000))
            self.music_player.set_pos(new_pos_ms)
            self.ui.set_progress(new_pos_ms / 1000)

    def update_shuffle_indices_for_new_playlist(self, song_count):
        """Update shuffle indices when a new playlist is loaded."""
        if self.is_shuffled and song_count > 0:
            self.shuffled_indices = list(range(song_count))
            random.shuffle(self.shuffled_indices)
            self.current_shuffled_index = -1

    def _play_with_fresh_url(self, song):
        """Fetch fresh URL and play song in background thread."""
        try:
            fresh_url = self.main_logic.youtube_controller.yt_streamer.get_fresh_stream_url(song['id'])
            if fresh_url:
                # Update song info with fresh URL
                song_with_url = song.copy()
                song_with_url['url'] = fresh_url
                self.current_song_info = song_with_url
                
                # Play on main thread
                self.ui.after(0, lambda: self._start_playback(song_with_url))
            else:
                self.ui.after(0, lambda: self._show_playback_error(song))
        except Exception as e:
            print(f"Error fetching fresh URL: {e}")
            self.ui.after(0, lambda: self._show_playback_error(song))
    
    def _start_playback(self, song_with_url):
        """Start playback with fresh URL on main thread."""
        self.music_player.play_song(song_with_url)
        self.ui.update_now_playing_view(song_with_url)
        self.main_logic.progress_tracker.start_progress_tracking()
        # Force UI update after playback starts
        self.ui.after(100, self.ui.update_play_pause_button)
    
    def _show_playback_error(self, song):
        """Show error when unable to get fresh URL."""
        self.ui.update_now_playing_view(song, loading=False)
        self.ui.show_error(
            "Playback Error",
            f"Unable to play '{song.get('title', 'Unknown')}'. The video may be unavailable."
        )

    def _preload_upcoming_songs(self, songs, current_index):
        """Preload URLs for upcoming songs."""
        upcoming_ids = []
        for i in range(1, 4):  # Next 3 songs
            next_idx = (current_index + i) % len(songs)
            song = songs[next_idx]
            if song.get('id'):
                upcoming_ids.append(song['id'])
        
        if upcoming_ids:
            # Count cache hits before preloading
            cache_hits = sum(1 for vid_id in upcoming_ids 
                           if vid_id in self.main_logic.youtube_controller.yt_streamer.url_cache)
            cache_misses = len(upcoming_ids) - cache_hits
            
            perf_logger.log_cache_operation("preload_upcoming", upcoming_ids, cache_hits, cache_misses)
            self.main_logic.youtube_controller.yt_streamer.preload_song_urls(upcoming_ids)

    def stop_and_cleanup(self):
        """Stop playback and clean up resources."""
        self.music_player.stop()