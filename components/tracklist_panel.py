import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox, simpledialog
import threading
import time

class TracklistPanel(ctk.CTkFrame):
    def __init__(self, parent, icon_loader, image_utils):
        super().__init__(parent, fg_color="#1E1E1E")
        
        self.icon_loader = icon_loader
        self.image_utils = image_utils
        self.logic = None
        
        # State
        self.song_widgets = []
        
        self.create_widgets()

    def set_logic(self, logic):
        """Set the logic component."""
        self.logic = logic

    def create_widgets(self):
        """Create the tracklist panel widgets."""
        # Search bar
        self.search_bar = ctk.CTkEntry(self, placeholder_text="Search Playlist...")
        self.search_bar.pack(fill=tk.X, padx=10, pady=10)
        self.search_bar.bind("<KeyRelease>", self.filter_songs)
        
        # Sync button
        sync_button = ctk.CTkButton(
            self, 
            text="Sync Playlist", 
            command=self.sync_playlist, 
            fg_color="#1DB954"
        )
        sync_button.pack(fill=tk.X, padx=10, pady=5)
        
        # Scrollable tracklist
        self.tracklist_scroll_frame = ctk.CTkScrollableFrame(self, fg_color="#1E1E1E")
        self.tracklist_scroll_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(5, 10))
        
        # Context menu
        self.context_menu = tk.Menu(
            self, 
            tearoff=0, 
            bg="#1E1E1E", 
            fg="white", 
            activebackground="#1DB954", 
            activeforeground="white"
        )
        self.context_menu.add_command(label="Remove Song", command=lambda: None)

        # Bind mousewheel events
        self._bind_mousewheel()

    def _bind_mousewheel(self):
        """Bind mousewheel events for scrolling."""
        def _on_mousewheel(event):
            # Normalize mousewheel across OS
            if event.num == 5 or event.delta < 0:   # scroll down
                self.tracklist_scroll_frame._parent_canvas.yview_scroll(30, "units")
            elif event.num == 4 or event.delta > 0: # scroll up
                self.tracklist_scroll_frame._parent_canvas.yview_scroll(-30, "units")

        # Bind for Windows / Mac / Linux
        self.tracklist_scroll_frame.bind_all("<MouseWheel>", _on_mousewheel)   # Windows / Mac
        self.tracklist_scroll_frame.bind_all("<Button-4>", _on_mousewheel)     # Linux scroll up
        self.tracklist_scroll_frame.bind_all("<Button-5>", _on_mousewheel)     # Linux scroll down

    def clear_track_list(self):
        """Clear all song widgets from the tracklist."""
        for widget in self.tracklist_scroll_frame.winfo_children():
            widget.destroy()
        self.song_widgets.clear()

    def create_song_widget(self, song):
        """Create a song widget for the tracklist."""
        song_frame = ctk.CTkFrame(self.tracklist_scroll_frame, fg_color="#282828", corner_radius=10)
        song_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Thumbnail
        placeholder_img = self.icon_loader.get_placeholder_img()
        thumbnail_label = ctk.CTkLabel(song_frame, image=placeholder_img, text="")
        thumbnail_label.pack(side=tk.LEFT, padx=(5, 10), pady=5)
        
        # Title
        display_title = self.logic.clean_title(song.get('title', 'Unknown Title'))
        title_label = ctk.CTkLabel(
            song_frame,
            text=display_title,
            anchor="w",
            justify="left",
            font=ctk.CTkFont(size=12, weight="bold"),
            wraplength=400
        )
        title_label.pack(side=tk.LEFT, padx=5, expand=True, fill=tk.X)
        
        # Duration
        duration_str = time.strftime('%M:%S', time.gmtime(song.get('duration', 0)))
        duration_label = ctk.CTkLabel(song_frame, text=duration_str, font=ctk.CTkFont(size=12))
        duration_label.pack(side=tk.RIGHT, padx=5)
        
        self.song_widgets.append(song_frame)
        
        # Load thumbnail asynchronously
        threading.Thread(
            target=self._load_thumbnail_async, 
            args=(song.get('thumbnail_url'), thumbnail_label), 
            daemon=True
        ).start()
        
        # Bind events
        self._bind_song_widget_events(song_frame, thumbnail_label, title_label, duration_label)
        
        return song_frame

    def _bind_song_widget_events(self, song_frame, thumbnail_label, title_label, duration_label):
        """Bind events for song widget interactions."""
        def play_song_from_widget(event):
            index = self.song_widgets.index(song_frame)
            self.logic.play_song_by_index(index)
            self.select_song_by_index(index)

        def show_context_menu_for_widget(event):
            index = self.song_widgets.index(song_frame)
            self.context_menu.entryconfigure(
                "Remove Song", 
                command=lambda: self.logic.remove_song_by_index(index)
            )
            self.context_menu.post(event.x_root, event.y_root)

        # Hover effects
        def on_hover_enter(event, frame=song_frame):
            frame.configure(fg_color="#333333")

        def on_hover_leave(event, frame=song_frame):
            index = self.song_widgets.index(frame)
            if index != self.logic.selected_song_index:
                frame.configure(fg_color="#282828")

        # Bind to all widgets
        widgets = [song_frame, thumbnail_label, title_label, duration_label]
        
        for widget in widgets:
            widget.bind("<Button-1>", play_song_from_widget)
            widget.bind("<Button-3>", show_context_menu_for_widget)
            widget.bind("<Enter>", on_hover_enter, add="+")
            widget.bind("<Leave>", on_hover_leave, add="+")

    def _load_thumbnail_async(self, url, widget):
        """Load thumbnail image asynchronously."""
        try:
            img = self.image_utils.get_image_from_path_or_url(url, size=(50, 50))
            self.after(0, lambda w=widget, i=img: w.winfo_exists() and w.configure(image=i))
        except Exception as e:
            print(f"Error loading thumbnail: {e}")

    def select_song_by_index(self, index, scroll_into_view=True):
        """Select a song by index and optionally scroll it into view."""
        if not self.logic:
            return
            
        # Deselect previous
        if (self.logic.selected_song_index != -1 and 
            self.logic.selected_song_index < len(self.song_widgets)):
            self.song_widgets[self.logic.selected_song_index].configure(fg_color="#282828")
            
        # Select new
        if 0 <= index < len(self.song_widgets):
            self.song_widgets[index].configure(fg_color="#3A3A3A")
            self.tracklist_scroll_frame.update_idletasks()

            # Scroll into view if requested
            if (scroll_into_view and 
                hasattr(self.tracklist_scroll_frame, "_parent_canvas")):
                self.tracklist_scroll_frame._parent_canvas.yview_moveto(
                    index / len(self.song_widgets)
                )

    def highlight_current_song_widget(self):
        """Highlight the currently playing song widget."""
        if not self.logic:
            return
            
        for i, widget in enumerate(self.song_widgets):
            if i == self.logic.current_song_index:
                widget.configure(fg_color="#1DB954")
            else:
                widget.configure(fg_color="#282828")

    def filter_songs(self, event=None):
        """Filter songs based on search term."""
        if not self.logic:
            return
            
        search_term = self.search_bar.get().lower()
        self.logic.filter_songs(search_term)

    def sync_playlist(self):
        """Sync the current playlist."""
        if self.logic:
            self.logic.sync_playlist()

    def show_add_song_dialog(self, song_info):
        """Show dialog for adding a song to playlists."""
        if not self.logic:
            return
            
        dialog = ctk.CTkToplevel(self)
        dialog.title("Add Song")
        dialog.geometry("400x250")
        dialog.resizable(False, False)

        dialog.grab_set()
        self.after(10, lambda: dialog.focus_force() if dialog.winfo_exists() else None)

        # Title
        ctk.CTkLabel(
            dialog,
            text=f"How to add '{song_info['title']}'?",
            font=ctk.CTkFont(size=14, weight="bold"),
            wraplength=350
        ).pack(pady=10)

        playlists = self.logic.playlist_manager.get_all_playlists()

        # Create new playlist option
        create_new_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        create_new_frame.pack(fill=tk.X, padx=20, pady=5)

        ctk.CTkLabel(create_new_frame, text="➕ Create a New Playlist").pack(side=tk.LEFT, padx=5)

        def create_new():
            new_name = simpledialog.askstring(
                "New Playlist", 
                "Enter playlist name:", 
                parent=dialog
            )
            if new_name:
                playlist_id = self.logic.create_new_playlist_with_song(new_name, song_info)
                messagebox.showinfo("Song Added", f"Song added to new playlist '{new_name}'")
                dialog.destroy()

        ctk.CTkButton(create_new_frame, text="Create", command=create_new).pack(side=tk.RIGHT, padx=5)

        # Existing playlists option
        if playlists:
            ctk.CTkLabel(dialog, text="📂 Or select existing playlist:").pack(pady=(15, 5))

            listbox = ctk.CTkComboBox(
                dialog,
                values=[pl["name"] for pl in playlists.values()],
                width=300
            )
            listbox.pack(pady=5)

            def add_to_existing():
                selected_name = listbox.get()
                if not selected_name:
                    return

                playlist_id = next(
                    (pid for pid, pl in playlists.items() if pl["name"] == selected_name), 
                    None
                )
                if playlist_id:
                    if self.logic.add_song_to_playlist(playlist_id, song_info):
                        messagebox.showinfo("Song Added", f"Song added to '{selected_name}'")
                    else:
                        messagebox.showinfo("Already Exists", f"Song already exists in '{selected_name}'")
                dialog.destroy()

            ctk.CTkButton(dialog, text="Add to Playlist", command=add_to_existing).pack(pady=10)