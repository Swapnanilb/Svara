import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox, filedialog

class PlaylistPanel(ctk.CTkScrollableFrame):
    def __init__(self, parent, icon_loader, image_utils):
        super().__init__(parent, width=200, fg_color="#1E1E1E")
        
        self.icon_loader = icon_loader
        self.image_utils = image_utils
        self.logic = None
        
        # State
        self.playlist_card_buttons = {}
        self.in_menu = False

    def set_logic(self, logic):
        """Set the logic component."""
        self.logic = logic

    def load_playlist_cards(self):
        """Load all playlist cards from the playlist manager."""
        if not self.logic:
            return
            
        # Clear existing cards
        for widget in self.winfo_children():
            widget.destroy()
        
        self.playlist_card_buttons.clear()

        # Create cards for all playlists
        for playlist_id, playlist in self.logic.playlist_manager.get_all_playlists().items():
            self.create_playlist_card(playlist['name'], playlist_id)

    def create_playlist_card(self, name, playlist_id):
        """Create a playlist card widget."""
        card_frame = ctk.CTkFrame(self, corner_radius=10, fg_color="#2A2A2A")
        card_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Get thumbnail
        thumbnail_source = self.logic.playlist_manager.get_playlist_thumbnail(playlist_id)
        if not thumbnail_source:
            thumbnail_source = self.logic.playlist_manager.get_first_song_thumbnail(playlist_id)

        img = self.image_utils.get_image_from_path_or_url(thumbnail_source)
        thumbnail_label = ctk.CTkLabel(card_frame, image=img, text="", fg_color="transparent")
        thumbnail_label.pack(padx=10, pady=(10, 0), expand=True, fill=tk.BOTH)
        
        # Playlist name
        name_label = ctk.CTkLabel(
            card_frame, 
            text=name, 
            font=ctk.CTkFont(size=12, weight="bold"), 
            wraplength=100
        )
        name_label.pack(padx=10, pady=(0, 10))

        # Store reference
        self.playlist_card_buttons[playlist_id] = card_frame

        # Bind click events
        def bind_click(widget):
            widget.bind("<Button-1>", lambda e, p_id=playlist_id: self.logic.display_playlist_songs(p_id))

        bind_click(card_frame)
        bind_click(thumbnail_label)
        bind_click(name_label)

        # Options button
        options_button = ctk.CTkButton(
            card_frame, 
            text="...", 
            font=ctk.CTkFont(size=20),
            width=25, 
            height=25, 
            fg_color="transparent",
            hover_color="#3A3A3A", 
            command=lambda: self.show_playlist_options(options_button, playlist_id)
        )
        options_button.place(relx=1.0, rely=0, anchor="ne", x=-5, y=5)

    def update_playlist_card_thumbnail(self, playlist_id):
        """Update the thumbnail for a specific playlist card."""
        card_frame = self.playlist_card_buttons.get(playlist_id)
        if not card_frame or not card_frame.winfo_exists():
            return
        
        thumbnail_label = card_frame.winfo_children()[0]
        
        thumbnail_source = self.logic.playlist_manager.get_playlist_thumbnail(playlist_id)
        if not thumbnail_source:
            thumbnail_source = self.logic.playlist_manager.get_first_song_thumbnail(playlist_id)
            
        img = self.image_utils.get_image_from_path_or_url(thumbnail_source)
        thumbnail_label.configure(image=img)

    def update_playlist_card_colors(self, selected_playlist_id):
        """Update playlist card colors to highlight the selected one."""
        for p_id, frame in self.playlist_card_buttons.items():
            if frame.winfo_exists():
                color = "#1DB954" if p_id == selected_playlist_id else "#2A2A2A"
                frame.configure(fg_color=color)

    def show_playlist_options(self, parent_button, playlist_id):
        """Show options menu for a playlist."""
        self.in_menu = True
        options = ["Upload Image", "Remove Custom Image", "Remove Playlist"]

        menu = ctk.CTkToplevel(self)
        menu.overrideredirect(True)
        menu.attributes("-alpha", 0.95)

        # Position menu
        x = parent_button.winfo_rootx()
        y = parent_button.winfo_rooty() + parent_button.winfo_height()
        menu.geometry(f"+{x}+{y}")

        # Create option buttons
        for option in options:
            cmd = None
            if option == "Upload Image":
                cmd = lambda p_id=playlist_id: self._upload_playlist_thumbnail(p_id)
            elif option == "Remove Custom Image":
                cmd = lambda p_id=playlist_id: self.logic.remove_custom_playlist_thumbnail(p_id)
            elif option == "Remove Playlist":
                cmd = lambda p_id=playlist_id: self._remove_playlist(p_id)

            button = ctk.CTkButton(
                menu,
                text=option,
                command=lambda c=cmd: [c(), menu.destroy(), self._reset_menu_state()],
                fg_color="#3A3A3A",
                hover_color="#1DB954",
                compound="left",
                anchor="w"
            )
            button.pack(fill=tk.X, padx=5, pady=2)

        # Handle focus loss
        def on_focus_out(event):
            menu.destroy()
            self._reset_menu_state()

        menu.bind("<FocusOut>", on_focus_out)
        menu.after(100, menu.focus_force)

    def _upload_playlist_thumbnail(self, playlist_id):
        """Handle playlist thumbnail upload."""
        file_path = filedialog.askopenfilename(
            title="Select an image file",
            filetypes=[("Image files", "*.png;*.jpg;*.jpeg;*.gif;*.bmp")]
        )
        if file_path and self.logic:
            self.logic.upload_playlist_thumbnail(playlist_id, file_path)

    def _remove_playlist(self, playlist_id):
        """Handle playlist removal with confirmation."""
        if messagebox.askyesno("Confirm Deletion", "Are you sure you want to remove this playlist?"):
            if self.logic:
                self.logic.remove_playlist(playlist_id)

    def _reset_menu_state(self):
        """Reset menu state."""
        self.in_menu = False