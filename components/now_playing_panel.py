import customtkinter as ctk
from PIL import Image
import time

class NowPlayingPanel(ctk.CTkFrame):
    def __init__(self, parent, icon_loader, image_utils):
        super().__init__(parent, fg_color="transparent")
        
        self.icon_loader = icon_loader
        self.image_utils = image_utils
        self.logic = None
        
        self.create_widgets()

    def set_logic(self, logic):
        """Set the logic component."""
        self.logic = logic

    def create_widgets(self):
        """Create the now playing panel widgets."""
        # Thumbnail
        self.current_thumbnail = ctk.CTkImage(
            light_image=Image.new("RGB", (250, 140), "black"), 
            size=(250, 140)
        )
        self.thumbnail_label = ctk.CTkLabel(
            self, 
            image=self.current_thumbnail, 
            text="", 
            fg_color="transparent"
        )
        self.thumbnail_label.pack(pady=20)
        
        # Title
        self.title_label = ctk.CTkLabel(
            self, 
            text="No song playing", 
            font=ctk.CTkFont(size=14, weight="bold"), 
            wraplength=250
        )
        self.title_label.pack(pady=10)
        
        # Progress bar frame
        self.create_progress_bar()

    def create_progress_bar(self):
        """Create the progress bar and time labels."""
        self.progress_bar_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.progress_bar_frame.pack(fill="x", padx=20, pady=10)
        
        # Elapsed time
        self.elapsed_time_label = ctk.CTkLabel(
            self.progress_bar_frame, 
            text="0:00", 
            font=ctk.CTkFont(size=10)
        )
        self.elapsed_time_label.pack(side="left")
        
        # Progress slider
        self.progress_bar = ctk.CTkSlider(
            self.progress_bar_frame, 
            from_=0, 
            to=100, 
            command=self._handle_progress_change
        )
        self.progress_bar.pack(side="left", fill="x", expand=True, padx=5)
        self.progress_bar.bind("<ButtonPress-1>", self.on_progress_press)
        self.progress_bar.bind("<ButtonRelease-1>", self.on_progress_release)

        # Total time
        self.total_time_label = ctk.CTkLabel(
            self.progress_bar_frame, 
            text="0:00", 
            font=ctk.CTkFont(size=10)
        )
        self.total_time_label.pack(side="left")

    def update_now_playing_view(self, song, loading=False):
        """Update the now playing view with song information."""
        if not self.logic:
            return
            
        if loading:
            display_title = self.logic.clean_title(song.get('title', 'Unknown Title'))
            self.title_label.configure(text=f"Loading: {display_title}...")
            self.total_time_label.configure(text="0:00")
            self.progress_bar.set(0)
        else:
            display_title = self.logic.clean_title(song.get('title', 'Unknown Title'))
            self.title_label.configure(text=display_title)
            duration = song.get('duration', 0)
            self.total_time_label.configure(text=time.strftime('%M:%S', time.gmtime(duration)))
            self.progress_bar.configure(to=duration)

        # Update thumbnail
        self._update_thumbnail(song)

    def _update_thumbnail(self, song):
        """Update the thumbnail image."""
        try:
            thumbnail_url = song.get('thumbnail_url')
            img = self.image_utils.get_image_from_path_or_url(
                thumbnail_url, 
                size=(250, 140)
            )
            self.thumbnail_label.configure(image=img, text="")
        except Exception as e:
            print(f"Could not load thumbnail: {e}")
            img = self.image_utils.get_image_from_path_or_url(None, size=(250, 140))
            self.thumbnail_label.configure(image=img, text="")

    def reset_now_playing_view(self):
        """Reset the now playing view to default state."""
        self.title_label.configure(text="No song playing")
        self.total_time_label.configure(text="0:00")
        self.progress_bar.set(0)

    def update_progress(self, pos_sec):
        """Update progress bar position if not seeking."""
        if self.logic and not self.logic.is_seeking:
            self.progress_bar.set(pos_sec)
            self.update_elapsed_time(pos_sec)

    def update_elapsed_time(self, pos_sec):
        """Update the elapsed time label."""
        self.elapsed_time_label.configure(
            text=time.strftime('%M:%S', time.gmtime(int(pos_sec)))
        )

    def set_progress(self, pos_sec):
        """Set progress bar position."""
        self.progress_bar.set(pos_sec)

    def _handle_progress_change(self, value):
        """Handle progress bar changes during user interaction."""
        if self.logic:
            if self.logic.is_seeking:
                self._dragging = True
            # Preview elapsed time without seeking
            self.logic.preview_progress(value)

    def on_progress_press(self, event=None):
        """Handle progress bar press events."""
        if self.logic:
            self.logic.set_seeking(True)
            self._dragging = False

    def on_progress_release(self, event=None):
        """Handle progress bar release events."""
        if self.logic:
            self.logic.set_seeking(False)
            # Commit seek operation
            self.logic.handle_slider_seek(self.progress_bar.get())