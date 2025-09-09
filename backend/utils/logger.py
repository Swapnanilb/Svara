import os
import time
from datetime import datetime

class MusicPlayerLogger:
    def __init__(self, log_file="music_player.log"):
        self.log_file = log_file
        self._write_log("INFO", "Music Player Started")
    
    def _write_log(self, level, message):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] {level}: {message}\n"
        
        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write(log_entry)
    
    def log_playlist_import(self, playlist_name, song_count, load_time):
        self._write_log("INFO", f"Playlist imported - Name: '{playlist_name}', Songs: {song_count}, Load time: {load_time:.2f}s")
    
    def log_song_load(self, song_title, load_time):
        self._write_log("INFO", f"Song loaded - '{song_title}', Load time: {load_time:.2f}s")
    
    def log_song_play(self, song_title):
        self._write_log("INFO", f"Playing - '{song_title}'")
    
    def log_cache_activity(self, action, song_count=None):
        if song_count:
            self._write_log("INFO", f"Cache {action} - {song_count} songs")
        else:
            self._write_log("INFO", f"Cache {action}")
    
    def log_error(self, error_type, message):
        self._write_log("ERROR", f"{error_type}: {message}")
    
    def log_warning(self, message):
        self._write_log("WARNING", message)

# Global logger instance
logger = MusicPlayerLogger()