import threading
import time

class ProgressTracker:
    def __init__(self, main_logic):
        self.main_logic = main_logic
        self.ui = main_logic.ui
        
        # Progress tracking state
        self.progress_thread = None
        self.stop_thread = threading.Event()
        self.is_seeking = False
        self.skip_next_update = False

    def start_progress_tracking(self):
        """Start the progress tracking thread."""
        self.stop_thread.clear()
        self.progress_thread = threading.Thread(target=self._update_progress_bar_thread, daemon=True)
        self.progress_thread.start()

    def stop_progress_tracking(self):
        """Stop the progress tracking thread."""
        self.stop_thread.set()

    def _update_progress_bar_thread(self):
        """Background thread that updates the progress bar."""
        while True:
            if self.stop_thread.is_set():
                break
                
            if self.main_logic.music_player and self.main_logic.music_player.is_playing:
                if self.skip_next_update:
                    self.skip_next_update = False
                    time.sleep(0.5)
                    continue
                    
                length_ms = self.main_logic.music_player.get_length()
                pos_ms = self.main_logic.music_player.get_pos()
                
                if length_ms > 0 and not self.is_seeking:
                    pos_sec = pos_ms / 1000
                    self.ui.after(0, lambda p=pos_sec: self.ui.update_progress(p))
                    
            time.sleep(0.5)

    def preview_progress(self, value):
        """Update elapsed time label without seeking (for smooth drag/click)."""
        pos_sec = float(value)
        self.ui.update_elapsed_time(pos_sec)

    def set_seeking(self, seeking):
        """Set the seeking state."""
        self.is_seeking = seeking

    def handle_slider_seek(self, seconds):
        """Commit the actual seek after release/click."""
        if (self.main_logic.music_player and 
            self.main_logic.music_player.is_playing):
            
            new_pos_ms = int(float(seconds) * 1000)
            length_ms = self.main_logic.music_player.get_length()
            new_pos_ms = max(0, min(new_pos_ms, length_ms))
            
            self.main_logic.music_player.set_pos(new_pos_ms)
            self.ui.set_progress(new_pos_ms / 1000)

    def skip_next_progress_update(self):
        """Skip the next progress update (useful after manual seeking)."""
        self.skip_next_update = True

    def stop_and_cleanup(self):
        """Stop progress tracking and clean up resources."""
        self.stop_progress_tracking()