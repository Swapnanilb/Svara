import threading
import random
from player import MusicPlayer

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
            
            # Stop any existing progress tracking
            self.main_logic.progress_tracker.stop_progress_tracking()
            
            if not song.get('url'):
                # Need to fetch stream URL
                self.main_logic.youtube_controller.yt_streamer.get_stream_info_for_id(song['id'])
                self.ui.update_now_playing_view(song, loading=True)
            else:
                # Ready to play
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
        songs = self.main_logic.playlist_manager.get_songs(self.main_logic.current_playlist_id)
        if not songs:
            return

        next_index = self._calculate_next_song_index(songs)
        self.play_song_by_index(next_index)

    def _calculate_next_song_index(self, songs):
        """Calculate the next song index based on playback mode."""
        if self.is_repeated:
            return self.main_logic.current_song_index
        elif self.is_shuffled:
            return self._get_next_shuffled_index(songs)
        else:
            return (self.main_logic.current_song_index + 1) % len(songs)

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
            songs = self.main_logic.playlist_manager.get_songs(self.main_logic.current_playlist_id)
            if songs:
                self.shuffled_indices = list(range(len(songs)))
                random.shuffle(self.shuffled_indices)
                self.current_shuffled_index = -1
        else:
            self.shuffled_indices = []
            self.current_shuffled_index = -1

        self.ui.update_shuffle_button(self.is_shuffled)
        print(f"Shuffle is now {'on' if self.is_shuffled else 'off'}")

    def toggle_repeat(self):
        """Toggle repeat mode on/off."""
        self.is_repeated = not self.is_repeated
        self.ui.update_repeat_button(self.is_repeated)
        print(f"Repeat is now {'on' if self.is_repeated else 'off'}")

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

    def stop_and_cleanup(self):
        """Stop playback and clean up resources."""
        self.music_player.stop()