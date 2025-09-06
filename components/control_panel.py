import customtkinter as ctk
import tkinter as tk

class ControlPanel(ctk.CTkFrame):
    def __init__(self, parent, icon_loader, image_utils):
        super().__init__(parent, fg_color="#282828")
        
        self.icon_loader = icon_loader
        self.image_utils = image_utils
        self.logic = None
        
        self.create_widgets()

    def set_logic(self, logic):
        """Set the logic component."""
        self.logic = logic

    def create_widgets(self):
        """Create the control panel widgets."""
        # Add song frame (left side)
        self.create_add_frame()
        
        # Player controls (center)
        self.create_player_controls()
        
        # Volume controls (right side)
        self.create_volume_controls()

    def create_add_frame(self):
        """Create the add song/playlist frame."""
        add_frame = ctk.CTkFrame(self, fg_color="#282828")
        add_frame.pack(side=tk.LEFT, padx=10)
        
        self.link_entry = ctk.CTkEntry(
            add_frame, 
            width=300, 
            placeholder_text="Enter YouTube Song or Playlist URL"
        )
        self.link_entry.pack(side=tk.LEFT, padx=5)
        
        add_button = ctk.CTkButton(
            add_frame, 
            text="Add Song/Playlist", 
            command=self.add_from_link, 
            fg_color="#1DB954"
        )
        add_button.pack(side=tk.LEFT, padx=5)

    def create_player_controls(self):
        """Create the main player control buttons."""
        player_controls_frame = ctk.CTkFrame(self, fg_color="#282828")
        player_controls_frame.pack(side=tk.LEFT, padx=20)
        
        # Get icons
        icons = self.icon_loader.get_all_icons()
        
        # Shuffle button
        self.shuffle_button = ctk.CTkButton(
            player_controls_frame, 
            image=icons.get('shuffle_off'), 
            text="", 
            command=self._toggle_shuffle, 
            width=40, 
            height=40
        )
        self.shuffle_button.pack(side=tk.LEFT, padx=5)

        # Fast rewind button
        fast_rew_button = ctk.CTkButton(
            player_controls_frame, 
            image=icons.get('fast_rew'), 
            text="", 
            command=self._seek_backward, 
            width=40, 
            height=40
        )
        fast_rew_button.pack(side=tk.LEFT, padx=5)

        # Previous button
        prev_button = ctk.CTkButton(
            player_controls_frame, 
            image=icons.get('prev'), 
            text="", 
            command=self._prev_song, 
            width=40, 
            height=40
        )
        prev_button.pack(side=tk.LEFT, padx=5)
        
        # Play/Pause button
        self.play_pause_button = ctk.CTkButton(
            player_controls_frame, 
            image=icons.get('play'), 
            text="", 
            command=self._toggle_play_pause, 
            width=40, 
            height=40
        )
        self.play_pause_button.pack(side=tk.LEFT, padx=5)

        # Next button
        next_button = ctk.CTkButton(
            player_controls_frame, 
            image=icons.get('next'), 
            text="", 
            command=self._next_song, 
            width=40, 
            height=40
        )
        next_button.pack(side=tk.LEFT, padx=5)
        
        # Fast forward button
        fast_fwd_button = ctk.CTkButton(
            player_controls_frame, 
            image=icons.get('fast_fwd'), 
            text="", 
            command=self._seek_forward, 
            width=40, 
            height=40
        )
        fast_fwd_button.pack(side=tk.LEFT, padx=5)

        # Repeat button
        self.repeat_button = ctk.CTkButton(
            player_controls_frame, 
            image=icons.get('repeat_off'), 
            text="", 
            command=self._toggle_repeat, 
            width=40, 
            height=40
        )
        self.repeat_button.pack(side=tk.LEFT, padx=5)

    def create_volume_controls(self):
        """Create the volume control widgets."""
        volume_frame = ctk.CTkFrame(self, fg_color="#282828")
        volume_frame.pack(side=tk.RIGHT)
        
        # Mute button
        icons = self.icon_loader.get_all_icons()
        self.mute_button = ctk.CTkButton(
            volume_frame, 
            image=icons.get('volume'), 
            text="", 
            command=self._toggle_mute, 
            width=40, 
            height=40
        )
        self.mute_button.pack(side=tk.LEFT, padx=(0, 5))
        
        # Volume slider
        self.volume_scale = ctk.CTkSlider(
            volume_frame, 
            from_=0, 
            to=1, 
            command=self.set_volume_from_scale
        )
        self.volume_scale.set(0.5)
        self.volume_scale.pack(side=tk.LEFT, padx=5)

    # Command methods that delegate to logic
    def add_from_link(self):
        """Add song/playlist from URL."""
        if not self.logic:
            return
            
        url = self.link_entry.get().strip()
        if not url:
            return

        self.link_entry.delete(0, "end")
        self.after(100, self.focus_force)
        self.logic.add_from_link(url)

    def _toggle_play_pause(self):
        """Toggle play/pause."""
        if self.logic:
            self.logic.toggle_play_pause()

    def _next_song(self):
        """Play next song."""
        if self.logic:
            self.logic.next_song()

    def _prev_song(self):
        """Play previous song."""
        if self.logic:
            self.logic.prev_song()

    def _seek_forward(self):
        """Seek forward 10 seconds."""
        if self.logic:
            self.logic.seek_forward(10)

    def _seek_backward(self):
        """Seek backward 10 seconds."""
        if self.logic:
            self.logic.seek_backward(10)

    def _toggle_shuffle(self):
        """Toggle shuffle mode."""
        if self.logic:
            self.logic.toggle_shuffle()

    def _toggle_repeat(self):
        """Toggle repeat mode."""
        if self.logic:
            self.logic.toggle_repeat()

    def _toggle_mute(self):
        """Toggle mute."""
        if self.logic:
            self.logic.toggle_mute()

    def set_volume_from_scale(self, value):
        """Set volume from slider."""
        if self.logic:
            volume = float(value)
            self.logic.set_volume(volume)

    # Update methods called by main UI
    def update_play_pause_button(self):
        """Update play/pause button icon."""
        if not self.logic:
            return
            
        icons = self.icon_loader.get_all_icons()
        if self.logic.music_player.is_playing and not self.logic.music_player.is_paused:
            self.play_pause_button.configure(image=icons.get('pause'), text="")
        else:
            self.play_pause_button.configure(image=icons.get('play'), text="")

    def update_shuffle_button(self, is_shuffled):
        """Update shuffle button icon."""
        icons = self.icon_loader.get_all_icons()
        if icons.get('shuffle_on') and icons.get('shuffle_off'):
            image = icons.get('shuffle_on') if is_shuffled else icons.get('shuffle_off')
            self.shuffle_button.configure(image=image, text="")

    def update_repeat_button(self, is_repeated):
        """Update repeat button icon."""
        icons = self.icon_loader.get_all_icons()
        if icons.get('repeat_on') and icons.get('repeat_off'):
            image = icons.get('repeat_on') if is_repeated else icons.get('repeat_off')
            self.repeat_button.configure(image=image, text="")

    def update_mute_button(self, has_volume):
        """Update mute button icon."""
        icons = self.icon_loader.get_all_icons()
        if has_volume:
            self.mute_button.configure(image=icons.get('volume'), text="")
        else:
            self.mute_button.configure(image=icons.get('volume_mute'), text="")

    def get_volume(self):
        """Get current volume from slider."""
        return self.volume_scale.get()

    def set_volume(self, volume):
        """Set volume slider position."""
        self.volume_scale.set(volume)