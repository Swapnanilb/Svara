# Setup VLC path before importing
from vlc_setup import setup_vlc_path
setup_vlc_path()

import vlc
import threading

class MusicPlayer:
    """
    Handles music playback using the VLC library.
    """
    def __init__(self, app, on_song_end_callback):
        self.app = app
        self.on_song_end_callback = on_song_end_callback
        
        # We need to set up the instance with arguments to control caching.
        self.vlc_instance = vlc.Instance("--network-caching=8000", "--aout=directsound")
        
        self.vlc_player = self.vlc_instance.media_player_new()
        self.is_playing = False
        self.is_paused = False
        self.current_song_info = None
        self.set_volume(0.5)
        
        self.event_manager = self.vlc_player.event_manager()
        self.event_manager.event_attach(vlc.EventType.MediaPlayerEndReached, self._on_media_end)
        
    def _on_media_end(self, event):
        # Use threading to avoid UI callback issues
        threading.Thread(target=self.on_song_end_callback, daemon=True).start()

    def play_song(self, song_info):
        """Plays a song given its dictionary (which contains the 'url')."""
        self.current_song_info = song_info
        
        media = self.vlc_instance.media_new(song_info['url'])
        self.vlc_player.set_media(media)
        self.vlc_player.play()
        
        self.is_playing = True
        self.is_paused = False

    def stop(self):
        self.vlc_player.stop()
        self.is_playing = False
        self.is_paused = False
        
    def pause(self):
        if self.is_playing and not self.is_paused:
            self.vlc_player.pause()
            self.is_paused = True
        
    def unpause(self):
        if self.is_playing and self.is_paused:
            self.vlc_player.pause()
            self.is_paused = False

    def get_pos(self):
        """Return current position (ms)."""
        try:
            return self.vlc_player.get_time() or 0
        except Exception as e:
            print(f"Error getting track pos: {e}")
            return 0

    def set_pos(self, pos_ms):
        """Seek to given position (ms)."""
        try:
            self.vlc_player.set_time(int(pos_ms))
        except Exception as e:
            print(f"Error setting track pos: {e}")

    def set_volume(self, volume):
        """Set volume (0.0 - 1.0)."""
        try:
            self.vlc_player.audio_set_volume(int(volume * 100))
        except Exception as e:
            print(f"Error setting volume: {e}")
    
    def get_length(self):
        """Return track length in milliseconds (or 0 if unavailable)."""
        try:
            return self.vlc_player.get_length() or 0
        except Exception as e:
            print(f"Error getting track length: {e}")
            return 0
        
    @property
    def duration(self):
        """Return duration in ms (shortcut for get_length)."""
        return self.get_length()
