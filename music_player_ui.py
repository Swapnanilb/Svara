import customtkinter as ctk
from components.playlist_panel import PlaylistPanel
from components.tracklist_panel import TracklistPanel
from components.now_playing_panel import NowPlayingPanel
from components.control_panel import ControlPanel
from utils.icon_loader import IconLoader
from utils.image_utils import ImageUtils

class MusicPlayerUI(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        self.title("Python Music Player")
        self.geometry("1280x800")
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("dark-blue")

        # UI state
        self.in_menu = False
        self.logic = None
        
        # Load icons and initialize components
        self.icon_loader = IconLoader()
        self.image_utils = ImageUtils()
        
        self.create_widgets()

    def set_logic(self, logic):
        """Set the logic component and complete initialization."""
        self.logic = logic
        
        # Pass logic to all components
        self.playlist_panel.set_logic(logic)
        self.tracklist_panel.set_logic(logic)
        self.now_playing_panel.set_logic(logic)
        self.control_panel.set_logic(logic)
        
        # Load initial data and bind shortcuts
        self.playlist_panel.load_playlist_cards()
        self.bind_keyboard_shortcuts()

    def bind_keyboard_shortcuts(self):
        """Bind keyboard shortcuts for media controls."""
        if not self.logic:
            return
            
        # Media controls
        self.bind_all("<space>", lambda e: self.logic.toggle_play_pause())
        self.bind_all("<Right>", lambda e: self.logic.next_song())
        self.bind_all("<Left>", lambda e: self.logic.prev_song())
        
        # Volume controls
        self.bind_all("<F10>", lambda e: self.logic.volume_up())
        self.bind_all("<F9>", lambda e: self.logic.volume_down())
        self.bind_all("<F12>", lambda e: self.logic.toggle_mute())
        
        # Seeking controls
        self.bind_all("<Control-Right>", lambda e: self.logic.seek_forward(10))
        self.bind_all("<Control-Left>", lambda e: self.logic.seek_backward(10))
        
        # Track list navigation
        self.bind_all("<Up>", lambda e: self.logic.select_prev_song())
        self.bind_all("<Down>", lambda e: self.logic.select_next_song())
        self.bind_all("<Return>", lambda e: self.logic.play_selected_song())

    def show_loading(self, message="Loading..."):
        """Show a loading dialog."""
        if hasattr(self, "loading_dialog") and self.loading_dialog and self.loading_dialog.winfo_exists():
            self.loading_label.configure(text=message)
            return

        self.loading_dialog = ctk.CTkToplevel(self)
        self.loading_dialog.title("Loading")
        self.loading_dialog.geometry("300x100")
        self.loading_dialog.resizable(False, False)
        self.loading_dialog.grab_set()

        # Center the dialog
        self.loading_dialog.update_idletasks()
        x = (self.winfo_screenwidth() - self.loading_dialog.winfo_width()) // 2
        y = (self.winfo_screenheight() - self.loading_dialog.winfo_height()) // 2
        self.loading_dialog.geometry(f"+{x}+{y}")

        self.loading_label = ctk.CTkLabel(self.loading_dialog, text=message)
        self.loading_label.pack(pady=20)

        self.progress = ctk.CTkProgressBar(self.loading_dialog, mode="indeterminate")
        self.progress.pack(fill="x", padx=20, pady=10)
        self.progress.start()

    def hide_loading(self):
        """Hide the loading dialog."""
        if hasattr(self, "loading_dialog") and self.loading_dialog and self.loading_dialog.winfo_exists():
            self.loading_dialog.destroy()
        self.loading_dialog = None

    def show_error(self, title, message):
        """Show error message dialog."""
        from tkinter import messagebox
        messagebox.showerror(title, message)

    def show_info(self, title, message):
        """Show info message dialog."""
        from tkinter import messagebox
        messagebox.showinfo(title, message)

    def create_widgets(self):
        """Create the main UI layout."""
        main_frame = ctk.CTkFrame(self, fg_color="transparent")
        main_frame.pack(fill=ctk.BOTH, expand=True, padx=20, pady=20)
        
        # Create library frame (left side)
        library_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        library_frame.pack(side=ctk.LEFT, fill=ctk.BOTH, expand=True)

        # Create playlist panel
        self.playlist_panel = PlaylistPanel(
            library_frame, 
            self.icon_loader, 
            self.image_utils
        )
        self.playlist_panel.pack(side=ctk.LEFT, fill=ctk.Y, padx=(0, 10))

        # Create tracklist panel
        self.tracklist_panel = TracklistPanel(
            library_frame, 
            self.icon_loader, 
            self.image_utils
        )
        self.tracklist_panel.pack(side=ctk.LEFT, fill=ctk.BOTH, expand=True)

        # Create now playing panel (right side)
        now_playing_frame = ctk.CTkFrame(main_frame, fg_color="#1E1E1E", width=300)
        now_playing_frame.pack(side=ctk.RIGHT, fill=ctk.Y, padx=(10, 0))
        now_playing_frame.pack_propagate(False)

        self.now_playing_panel = NowPlayingPanel(
            now_playing_frame, 
            self.icon_loader, 
            self.image_utils
        )
        self.now_playing_panel.pack(fill=ctk.BOTH, expand=True)

        # Create control panel (bottom)
        self.control_panel = ControlPanel(
            self, 
            self.icon_loader, 
            self.image_utils
        )
        self.control_panel.pack(side=ctk.BOTTOM, fill=ctk.X)

    def on_close(self):
        """Handle application close."""
        if self.logic:
            self.logic.stop_and_cleanup()
        self.destroy()

    # Delegate methods to components
    def load_playlist_cards(self):
        return self.playlist_panel.load_playlist_cards()

    def update_playlist_card_thumbnail(self, playlist_id):
        return self.playlist_panel.update_playlist_card_thumbnail(playlist_id)

    def update_playlist_card_colors(self, selected_playlist_id):
        return self.playlist_panel.update_playlist_card_colors(selected_playlist_id)

    def clear_track_list(self):
        return self.tracklist_panel.clear_track_list()

    def create_song_widget(self, song):
        return self.tracklist_panel.create_song_widget(song)

    def highlight_current_song_widget(self):
        return self.tracklist_panel.highlight_current_song_widget()

    def select_song_by_index(self, index, scroll_into_view=True):
        return self.tracklist_panel.select_song_by_index(index, scroll_into_view)

    def filter_songs(self, event=None):
        return self.tracklist_panel.filter_songs(event)

    def update_now_playing_view(self, song, loading=False):
        return self.now_playing_panel.update_now_playing_view(song, loading)

    def reset_now_playing_view(self):
        return self.now_playing_panel.reset_now_playing_view()

    def update_progress(self, pos_sec):
        return self.now_playing_panel.update_progress(pos_sec)

    def update_elapsed_time(self, pos_sec):
        return self.now_playing_panel.update_elapsed_time(pos_sec)

    def set_progress(self, pos_sec):
        return self.now_playing_panel.set_progress(pos_sec)

    def update_play_pause_button(self):
        return self.control_panel.update_play_pause_button()

    def update_shuffle_button(self, is_shuffled):
        return self.control_panel.update_shuffle_button(is_shuffled)

    def update_repeat_button(self, is_repeated):
        return self.control_panel.update_repeat_button(is_repeated)

    def update_mute_button(self, has_volume):
        return self.control_panel.update_mute_button(has_volume)

    def get_volume(self):
        return self.control_panel.get_volume()

    def set_volume(self, volume):
        return self.control_panel.set_volume(volume)

    def add_from_link(self):
        return self.control_panel.add_from_link()

    def sync_playlist(self):
        return self.tracklist_panel.sync_playlist()
    
    def load_tracks(self):
        return self.tracklist_panel.load_tracks()

    def show_add_song_dialog(self, song_info):
        return self.tracklist_panel.show_add_song_dialog(song_info)