import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox, filedialog, simpledialog
from PIL import Image
import urllib.request
import io
import time
import threading
import random
import re
import os

# Import the core modules
from youtube_streamer import YouTubeStreamer
from playlist_manager import PlaylistManager
from player import MusicPlayer

class MusicPlayerApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        self.title("Python Music Player")
        self.geometry("1280x800")
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("dark-blue")

        self.playlist_manager = PlaylistManager()
        self.yt_streamer = YouTubeStreamer(self.on_playlist_info_fetched, self.on_single_song_info_fetched)
        self.music_player = MusicPlayer(self, self.play_next_song)
        self.youtube_streamer = YouTubeStreamer(self.on_playlist_info_fetched, self.on_single_song_info_fetched)
        self.current_song_index = -1
        self.current_playlist_id = None
        self.is_shuffled = False
        self.is_repeated = False
        self.shuffled_indices = []
        self.current_shuffled_index = -1
        self.current_song_info = None
        self.progress_thread = None
        self.stop_thread = threading.Event()
        self.last_volume = 0.5
        self.is_seeking = False
        self.sync_mode = False
        self.in_menu = False
        self.songs_to_add = [] # List to hold songs to be added in chunks
        self.song_widgets = []
        self.placeholder_img = None
        self.selected_song_index = -1
        self.loading_dialog = None 

        
        self.playlist_card_buttons = {}

        self.load_icons()
        self.create_widgets()
        self.load_playlist_cards()
        self.bind_keyboard_shortcuts()


    def show_loading(self, message="Loading..."):
        """Show a small non-blocking loading dialog with a message."""
        import customtkinter as ctk

        # FIX: check both attribute existence and not None
        if getattr(self, "loading_dialog", None) is not None and self.loading_dialog.winfo_exists():
            self.loading_label.configure(text=message)
            return

        self.loading_dialog = ctk.CTkToplevel(self)
        self.loading_dialog.title("Loading")
        self.loading_dialog.geometry("300x100")
        self.loading_dialog.resizable(False, False)
        self.loading_dialog.grab_set()  # Keep focus

        # Center window
        self.loading_dialog.update_idletasks()
        x = (self.winfo_screenwidth() - self.loading_dialog.winfo_width()) // 2
        y = (self.winfo_screenheight() - self.loading_dialog.winfo_height()) // 2
        self.loading_dialog.geometry(f"+{x}+{y}")

        self.loading_label = ctk.CTkLabel(self.loading_dialog, text=message)
        self.loading_label.pack(pady=20)

        # Optional: Add a progress bar
        self.progress = ctk.CTkProgressBar(self.loading_dialog, mode="indeterminate")
        self.progress.pack(fill="x", padx=20, pady=10)
        self.progress.start()



    def hide_loading(self):
        """Close the loading dialog if it exists."""
        if getattr(self, "loading_dialog", None) is not None and self.loading_dialog.winfo_exists():
            self.loading_dialog.destroy()
        self.loading_dialog = None

    def _on_slider_seek(self, event):
        if self.music_player and self.music_player.is_playing:
            progress = self.progress_bar.get()  # value between 0 and 1
            length_ms = self.music_player.get_length()
            new_pos = int(progress * length_ms)
            self.music_player.set_pos(new_pos)



    # --- Core Application Logic and Callbacks ---
    
    def bind_keyboard_shortcuts(self):
        # Media controls using standard keys
        self.bind_all("<space>", lambda e: self.toggle_play_pause())
        self.bind_all("<Right>", lambda e: self.next_song())
        self.bind_all("<Left>", lambda e: self.prev_song())
        # Use Function keys for volume to avoid all conflicts
        self.bind_all("<F10>", lambda e: self.volume_up())
        self.bind_all("<F9>", lambda e: self.volume_down())
        self.bind_all("<F12>", lambda e: self.toggle_mute())
        # Seeking controls remain on Control + arrows
        self.bind_all("<Control-Right>", lambda e: self.seek_forward(10))
        self.bind_all("<Control-Left>", lambda e: self.seek_backward(10))
        
        # New keyboard bindings for track list navigation
        self.bind_all("<Up>", self.select_prev_song)
        self.bind_all("<Down>", self.select_next_song)
        self.bind_all("<Return>", self.play_selected_song)

    def select_next_song(self, event=None):
        if not self.song_widgets:
            return
        
        new_index = (self.selected_song_index + 1) % len(self.song_widgets)
        self.select_song_by_index(new_index)

    def select_prev_song(self, event=None):
        if not self.song_widgets:
            return
        
        new_index = (self.selected_song_index - 1 + len(self.song_widgets)) % len(self.song_widgets)
        self.select_song_by_index(new_index)
        
    def select_song_by_index(self, index):
        if self.selected_song_index != -1 and self.selected_song_index < len(self.song_widgets):
            self.song_widgets[self.selected_song_index].configure(fg_color="#282828")
            
        self.selected_song_index = index
        self.song_widgets[self.selected_song_index].configure(fg_color="#3A3A3A")
        self.tracklist_scroll_frame.update_idletasks()

        # ✅ Fix: use parent canvas for scrolling
        if hasattr(self.tracklist_scroll_frame, "_parent_canvas"):
            self.tracklist_scroll_frame._parent_canvas.yview_moveto(
                self.selected_song_index / len(self.song_widgets)
            )

    def play_selected_song(self, event=None):
        if self.selected_song_index != -1:
            self.play_song_by_index(self.selected_song_index)

    def volume_up(self):
        current_volume = self.volume_scale.get()
        new_volume = min(1.0, current_volume + 0.1)
        self.volume_scale.set(new_volume)
        self.music_player.set_volume(new_volume)

    def volume_down(self):
        current_volume = self.volume_scale.get()
        new_volume = max(0.0, current_volume - 0.1)
        self.volume_scale.set(new_volume)
        self.music_player.set_volume(new_volume)

    def seek_forward(self, seconds):
        if self.music_player.is_playing:
            current_pos = self.music_player.get_pos()
            new_pos_ms = current_pos + (seconds * 1000)
            self.music_player.set_pos(new_pos_ms)
            self.progress_bar.set(new_pos_ms / 1000)
            
    def seek_backward(self, seconds):
        if self.music_player.is_playing:
            current_pos = self.music_player.get_pos()
            new_pos_ms = max(0, current_pos - (seconds * 1000))
            self.music_player.set_pos(new_pos_ms)
            self.progress_bar.set(new_pos_ms / 1000)

    def play_next_song(self):
        songs = self.playlist_manager.get_songs(self.current_playlist_id)
        if not songs:
            return

        next_index_to_play = -1
        if self.is_repeated:
            next_index_to_play = self.current_song_index
        elif self.is_shuffled:
            if not self.shuffled_indices:
                self.shuffled_indices = list(range(len(songs)))
                random.shuffle(self.shuffled_indices)
            
            self.current_shuffled_index = (self.current_shuffled_index + 1) % len(self.shuffled_indices)
            next_index_to_play = self.shuffled_indices[self.current_shuffled_index]
        else:
            next_index_to_play = (self.current_song_index + 1) % len(songs)
        
        self.play_song_by_index(next_index_to_play)
        
    def play_song_by_index(self, index):
        if not self.current_playlist_id:
            return

        songs = self.playlist_manager.get_songs(self.current_playlist_id)
        if 0 <= index < len(songs):
            song = songs[index]
            self.current_song_index = index
            self.current_song_info = song
            
            self.stop_thread.set()
            
            if not song.get('url'):
                self.yt_streamer.get_stream_info_for_id(song['id'])
                self.update_now_playing_view(song, loading=True)
            else:
                self.music_player.play_song(self.current_song_info)
                self.update_now_playing_view(self.current_song_info)
                self.stop_thread.clear()
                self.progress_thread = threading.Thread(target=self._update_progress_bar_thread, daemon=True)
                self.progress_thread.start()
            
            self.update_play_pause_button()
            self.highlight_current_song_widget()
            self.selected_song_index = index
        else:
            self.music_player.stop()
            self.reset_now_playing_view()

    def clean_title(self, title: str) -> str:
        """Return a simplified song title (remove artist/extra text)."""

        # Normalize separators
        title = title.replace("—", "-").replace("–", "-")

        # Split on separators commonly used in YouTube titles
        # Example: "Parbona - Lyrical | Borbaad | ..." -> ["Parbona", "Lyrbaad", "Borbaad", ...]
        parts = re.split(r"[-|:]", title)

        # Take the first chunk as base
        base = parts[0].strip()

        # If base is very short (like "Official"), fallback to next
        if len(base) < 2 and len(parts) > 1:
            base = parts[1].strip()

        # Remove text inside () or [] like (Official Video), [Lyric]
        base = re.sub(r"[\(\[].*?[\)\]]", "", base)

        # Remove common keywords (lyrical, lyrics, official, cover, etc.)
        keywords = [
            "official", "video", "lyrics", "lyrical", "lyric", "cover",
            "audio", "remix", "live", "acoustic", "version", "full song"
        ]
        pattern = r"\b(" + "|".join(keywords) + r")\b"
        base = re.sub(pattern, "", base, flags=re.IGNORECASE)

        # Clean up
        base = re.sub(r"\s+", " ", base).strip(" -–—_|")

        return base if base else "Unknown Title"
    

    
    def on_playlist_info_fetched(self, playlist_info):
        # ✅ FIX: Do NOT hide the loading screen here. It should remain visible
        # during the subsequent detailed song info fetching.
        # self.after(0, self.hide_loading) # <-- Removed

        if playlist_info:
            # ✅ Update UI with new playlist data
            self.after(0, lambda: self._update_ui_with_new_playlist(playlist_info))
        else:
            # Handle failed fetch gracefully
            self.after(0, lambda: messagebox.showerror(
                "Fetch Error",
                "Failed to fetch playlist information from YouTube."
            ))

    def _update_ui_with_new_playlist(self, playlist_info):
        if not playlist_info:
            return

        playlist_name = playlist_info.get('title', 'Unknown Playlist')
        songs = playlist_info.get('entries', [])
        thumbnail = playlist_info.get('thumbnail_url', None)
        source_url = playlist_info.get('original_url')
        
        # Kick off the detailed song fetching in a new thread to keep the UI responsive.
        threading.Thread(target=self._process_playlist_songs_thread, args=(playlist_name, songs, thumbnail, source_url), daemon=True).start()

    def _process_playlist_songs_thread(self, playlist_name, songs, thumbnail, source_url):
        # Check if playlist already exists
        existing_playlist_id = self.playlist_manager.get_playlist_by_url(source_url)
        
        if existing_playlist_id:
            # ✅ Compare with existing songs
            old_songs = self.playlist_manager.get_songs(existing_playlist_id)
            old_ids = {s['id'] for s in old_songs}
            new_ids = {s['id'] for s in songs}
            
            added_ids = new_ids - old_ids
            removed_ids = old_ids - new_ids

            # ✅ Add new songs with full info
            for song in songs:
                if song['id'] in added_ids:
                    print(f"Fetching full info for new song: {song['id']}")
                    full_info = self.youtube_streamer.fetch_full_song_info(song['url'])
                    if full_info:
                        self.playlist_manager.add_song_to_playlist(existing_playlist_id, full_info)
            
            # ✅ Remove deleted songs
            if removed_ids:
                updated_songs = [s for s in old_songs if s['id'] not in removed_ids]
                self.playlist_manager.update_playlist_songs(existing_playlist_id, updated_songs)

            # ✅ Update metadata (title / thumbnail) if changed
            playlist_data = self.playlist_manager.get_all_playlists().get(existing_playlist_id, {})
            if playlist_data.get("name") != playlist_name:
                playlist_data["name"] = playlist_name
            if thumbnail and playlist_data.get("thumbnail") != thumbnail:
                playlist_data["thumbnail"] = thumbnail
            
            # ✅ Hide loading screen and show messages on the main thread
            self.after(0, self.hide_loading)
            self.after(200, self.load_playlist_cards)
            self.after(200, lambda: self.display_playlist_songs(existing_playlist_id))

            # ✅ Feedback after UI redraw
            if added_ids or removed_ids:
                self.after(200, lambda: messagebox.showinfo(
                    "Playlist Updated",
                    f"Playlist '{playlist_name}' updated.\n\n"
                    f"Added: {len(added_ids)} songs\nRemoved: {len(removed_ids)} songs"
                ))
            else:
                self.after(200, lambda: messagebox.showinfo(
                    "Already Exists",
                    f"Playlist '{playlist_name}' already exists with no changes."
                ))

        else:
            # ✅ New playlist → fetch full info for ALL songs once
            full_songs = []
            for song in songs:
                print(f"Fetching full info for new song: {song['id']}")
                full_info = self.youtube_streamer.fetch_full_song_info(song['url'])
                if full_info:
                    full_songs.append(full_info)
            
            playlist_id = self.playlist_manager.add_new_playlist(
                playlist_name, full_songs, source_url, thumbnail
            )
            
            # ✅ Hide loading screen and show messages on the main thread
            self.after(0, self.hide_loading)
            self.after(200, lambda: self.create_playlist_card(playlist_name, playlist_id))
            self.after(200, lambda: self.display_playlist_songs(playlist_id))

            # ✅ Feedback after UI redraw
            self.after(200, lambda: messagebox.showinfo(
                "Playlist Uploaded",
                f"Playlist '{playlist_name}' uploaded successfully."
            ))


    def fetch_full_song_info(self, video_url):
        """Fetch detailed info for a single YouTube video."""
        import yt_dlp
        ydl_opts = {
            "quiet": True,
            "format": "bestaudio/best",
            "noplaylist": True,
        }
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(video_url, download=False)
                return {
                    "id": info.get("id"),
                    "title": info.get("title"),
                    "url": info.get("url"),  # ✅ direct audio stream URL
                    "thumbnail_url": info.get("thumbnail"),
                    "duration": info.get("duration")
                }
        except Exception as e:
            print(f"Error fetching full song info: {e}")
            return None


    
    def on_single_song_info_fetched(self, full_song_info):
        self.after(0, lambda: self._handle_single_song_info(full_song_info))
    
    def _handle_single_song_info(self, full_song_info):
        # FIX: Hide the loading screen here, after the async task is done.
        self.hide_loading()
        
        if not full_song_info or not full_song_info.get('url'):
            messagebox.showerror("Playback Error", "Failed to get a valid stream URL for this song. YouTube may have a changed its API. Try updating yt-dlp.")
            return

        self.show_add_song_dialog(full_song_info)

    def show_add_song_dialog(self, song_info):
        dialog = ctk.CTkToplevel(self)
        dialog.title("Add Song")
        dialog.geometry("400x250")
        dialog.resizable(False, False)

        # ✅ Safe grab + focus with after()
        dialog.grab_set()
        self.after(10, lambda: dialog.focus_force() if dialog.winfo_exists() else None)

        # Song title
        ctk.CTkLabel(
            dialog,
            text=f"How to add '{song_info['title']}'?",
            font=ctk.CTkFont(size=14, weight="bold"),
            wraplength=350
        ).pack(pady=10)

        playlists = self.playlist_manager.get_all_playlists()

        # --- Option 1: Create New Playlist ---
        create_new_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        create_new_frame.pack(fill=tk.X, padx=20, pady=5)

        ctk.CTkLabel(create_new_frame, text="➕ Create a New Playlist").pack(side=tk.LEFT, padx=5)

        def create_new():
            new_name = simpledialog.askstring("New Playlist", "Enter playlist name:", parent=dialog)
            if new_name:
                playlist_id = self.playlist_manager.add_new_playlist(new_name, [song_info])
                self.create_playlist_card(new_name, playlist_id)
                self.display_playlist_songs(playlist_id)
                messagebox.showinfo("Song Added", f"Song added to new playlist '{new_name}'")
                dialog.destroy()

        ctk.CTkButton(create_new_frame, text="Create", command=create_new).pack(side=tk.RIGHT, padx=5)

        # --- Option 2: Add to Existing Playlist ---
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

                playlist_id = next((pid for pid, pl in playlists.items() if pl["name"] == selected_name), None)
                if playlist_id:
                    if not self.playlist_manager.song_exists(playlist_id, song_info["id"]):
                        self.playlist_manager.add_song_to_playlist(playlist_id, song_info)
                        self.display_playlist_songs(playlist_id)
                        messagebox.showinfo("Song Added", f"Song added to '{selected_name}'")
                    else:
                        messagebox.showinfo("Already Exists", f"Song already exists in '{selected_name}'")
                dialog.destroy()

            ctk.CTkButton(dialog, text="Add to Playlist", command=add_to_existing).pack(pady=10)
        
    def _update_progress_bar_thread(self):
        while True:
            if self.music_player and self.music_player.is_playing:
                length_ms = self.music_player.get_length()
                pos_ms = self.music_player.get_pos()
                if length_ms > 0:
                    pos_sec = pos_ms / 1000
                    # update progress bar in seconds
                    self.after(0, lambda p=pos_sec: self.progress_bar.set(p))
                    # update elapsed time label
                    self.after(0, lambda: self.elapsed_time_label.configure(
                        text=time.strftime('%M:%S', time.gmtime(int(pos_sec)))
                    ))
            time.sleep(0.5)

    def _update_gui_progress(self, pos_sec):
        if not self.is_seeking:
            self.progress_bar.set(pos_sec)
        self.elapsed_time_label.configure(text=time.strftime('%M:%S', time.gmtime(pos_sec)))
        
    def _handle_progress_change(self, value):
        pos_sec = float(value)
        self.elapsed_time_label.configure(text=time.strftime('%M:%S', time.gmtime(pos_sec)))
        
        if not self.is_seeking and self.music_player.is_playing:
            self.music_player.set_pos(pos_sec * 1000)

    def on_progress_press(self, event=None):
        self.is_seeking = True

    def on_progress_release(self, event=None):
        self.is_seeking = False

    def load_initial_playlist(self):
        # This is now handled by display_playlist_songs
        pass
    
    def load_playlist_cards(self):
        for widget in self.playlist_cards_frame.winfo_children():
            widget.destroy()
        
        # Clear the dictionary before reloading to prevent stale references
        self.playlist_card_buttons.clear() 

        for playlist_id, playlist in self.playlist_manager.get_all_playlists().items():
            self.create_playlist_card(
                playlist['name'],
                playlist_id
            )

    def get_image_from_path_or_url(self, source, size=(100, 100)):
        """Helper function to load an image from a local path or a URL."""
        img = None
        if source:
            try:
                if source.startswith(('http://', 'https://')):
                    # It's a URL
                    with urllib.request.urlopen(source) as url:
                        raw_data = url.read()
                    pil_img = Image.open(io.BytesIO(raw_data)).resize(size)
                else:
                    # It's a local file path
                    pil_img = Image.open(source).resize(size)
                
                img = ctk.CTkImage(light_image=pil_img, size=size)
            except Exception as e:
                print(f"Could not load thumbnail from {source}: {e}")
                img = ctk.CTkImage(light_image=Image.new("RGB", size), size=size)
        else:
            img = ctk.CTkImage(light_image=Image.new("RGB", size), size=size)
        return img

    def update_playlist_card_thumbnail(self, playlist_id):
        card_frame = self.playlist_card_buttons.get(playlist_id)
        if not card_frame or not card_frame.winfo_exists():
            return
        
        thumbnail_label = card_frame.winfo_children()[0]
        
        thumbnail_source = self.playlist_manager.get_playlist_thumbnail(playlist_id)
        
        if not thumbnail_source:
            thumbnail_source = self.playlist_manager.get_first_song_thumbnail(playlist_id)
            
        img = self.get_image_from_path_or_url(thumbnail_source)
        thumbnail_label.configure(image=img)

    def create_playlist_card(self, name, playlist_id):
        # Use a CTkFrame to act as the clickable card container
        card_frame = ctk.CTkFrame(self.playlist_cards_frame, corner_radius=10, fg_color="#2A2A2A")
        card_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Get thumbnail source
        thumbnail_source = self.playlist_manager.get_playlist_thumbnail(playlist_id)
        if not thumbnail_source:
            thumbnail_source = self.playlist_manager.get_first_song_thumbnail(playlist_id)

        # Create thumbnail label
        img = self.get_image_from_path_or_url(thumbnail_source)
        thumbnail_label = ctk.CTkLabel(card_frame, image=img, text="", fg_color="transparent")
        thumbnail_label.pack(padx=10, pady=(10, 0), expand=True, fill=tk.BOTH)
        
        # Create name label
        name_label = ctk.CTkLabel(card_frame, text=name, font=ctk.CTkFont(size=12, weight="bold"), wraplength=100)
        name_label.pack(padx=10, pady=(0, 10))

        self.playlist_card_buttons[playlist_id] = card_frame

        # Bind click events to the frame and its children
        def bind_click(widget):
            widget.bind("<Button-1>", lambda e, p_id=playlist_id: self.display_playlist_songs(p_id))

        bind_click(card_frame)
        bind_click(thumbnail_label)
        bind_click(name_label)

        # Create the triple dot options button
        options_button = ctk.CTkButton(card_frame, text="...", font=ctk.CTkFont(size=20),
                                       width=25, height=25, fg_color="transparent",
                                       hover_color="#3A3A3A", command=lambda: self.show_playlist_options(options_button, playlist_id))
        options_button.place(relx=1.0, rely=0, anchor="ne", x=-5, y=5)

    def show_playlist_options(self, parent_button, playlist_id):
        self.in_menu = True
        options = ["Upload Image", "Remove Custom Image", "Remove Playlist"]

        menu = ctk.CTkToplevel(self)
        menu.overrideredirect(True)
        menu.attributes("-alpha", 0.95)

        # ✅ Correct: absolute screen coordinates of the button
        x = parent_button.winfo_rootx()
        y = parent_button.winfo_rooty() + parent_button.winfo_height()
        menu.geometry(f"+{x}+{y}")

        for option in options:
            cmd = None
            if option == "Upload Image":
                cmd = lambda p_id=playlist_id: self.upload_playlist_thumbnail(p_id)
            elif option == "Remove Custom Image":
                cmd = lambda p_id=playlist_id: self.remove_custom_playlist_thumbnail(p_id)
            elif option == "Remove Playlist":
                cmd = lambda p_id=playlist_id: self.remove_playlist(p_id)

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

        def on_focus_out(event):
            menu.destroy()
            self._reset_menu_state()

        menu.bind("<FocusOut>", on_focus_out)
        menu.after(100, menu.focus_force)

    def _reset_menu_state(self):
        self.in_menu = False
        
    def remove_playlist(self, playlist_id):
        if messagebox.askyesno("Confirm Deletion", "Are you sure you want to remove this playlist?"):
            if self.current_playlist_id == playlist_id:
                self.music_player.stop()
                self.reset_now_playing_view()
                self.current_song_index = -1
                self.current_playlist_id = None
            
            self.playlist_manager.remove_playlist(playlist_id)
            self.load_playlist_cards()
            self.clear_track_list()

    def upload_playlist_thumbnail(self, playlist_id):
        file_path = filedialog.askopenfilename(
            title="Select an image file",
            filetypes=[("Image files", "*.png;*.jpg;*.jpeg;*.gif;*.bmp")]
        )
        if file_path:
            self.playlist_manager.update_playlist_thumbnail(playlist_id, file_path)
            self.update_playlist_card_thumbnail(playlist_id)
            
    def remove_custom_playlist_thumbnail(self, playlist_id):
        self.playlist_manager.remove_playlist_thumbnail(playlist_id)
        self.update_playlist_card_thumbnail(playlist_id)

    def display_playlist_songs(self, playlist_id):
        self.current_playlist_id = playlist_id

        # Update card colors immediately for feedback
        for p_id, frame in self.playlist_card_buttons.items():
            if frame.winfo_exists():
                frame.configure(fg_color="#1DB954" if p_id == playlist_id else "#2A2A2A")

        self.update_playlist_card_thumbnail(playlist_id)
        
        # Clear existing items
        self.clear_track_list()
        
        # Start a new thread to load the songs
        threading.Thread(target=self._load_playlist_thread, args=(playlist_id,), daemon=True).start()
        
    def _load_playlist_thread(self, playlist_id):
        songs = self.playlist_manager.get_songs(playlist_id)
        self.songs_to_add = songs
        
        # Re-initialize shuffled list when a new playlist is displayed
        if self.is_shuffled:
            self.shuffled_indices = list(range(len(songs)))
            random.shuffle(self.shuffled_indices)
            self.current_shuffled_index = -1
        
        # Reset selected song index
        self.selected_song_index = -1

        # Schedule the UI update on the main thread
        self.after(10, self._update_ui_with_songs_in_chunks)

    def _update_ui_with_songs_in_chunks(self, chunk_size=50):
        if self.songs_to_add:
            chunk = self.songs_to_add[:chunk_size]
            self.songs_to_add = self.songs_to_add[chunk_size:]
            
            for song in chunk:
                self.create_song_widget(song)
            
            # Schedule the next chunk update
            self.after(10, self._update_ui_with_songs_in_chunks)

    def create_song_widget(self, song):
        song_frame = ctk.CTkFrame(self.tracklist_scroll_frame, fg_color="#282828", corner_radius=10)
        song_frame.pack(fill=tk.X, padx=5, pady=5)
        
        thumbnail_label = ctk.CTkLabel(song_frame, image=self.placeholder_img, text="")
        thumbnail_label.pack(side=tk.LEFT, padx=(5, 10), pady=5)
        
        # ✅ Use cleaned title here
        display_title = self.clean_title(song.get('title', 'Unknown Title'))
        title_label = ctk.CTkLabel(
            song_frame,
            text=display_title,
            anchor="w",
            justify="left",
            font=ctk.CTkFont(size=12, weight="bold"),
            wraplength=400
        )
        title_label.pack(side=tk.LEFT, padx=5, expand=True, fill=tk.X)
        
        duration_str = time.strftime('%M:%S', time.gmtime(song.get('duration', 0)))
        duration_label = ctk.CTkLabel(song_frame, text=duration_str, font=ctk.CTkFont(size=12))
        duration_label.pack(side=tk.RIGHT, padx=5)
        
        self.song_widgets.append(song_frame)
        
        # Load thumbnail async
        threading.Thread(target=self._load_thumbnail_async, args=(song.get('thumbnail_url'), thumbnail_label), daemon=True).start()
        
        def play_song_from_widget(event):
            index = self.song_widgets.index(song_frame)
            self.play_song_by_index(index)
            self.select_song_by_index(index)

        def select_song_from_widget(event):
            index = self.song_widgets.index(song_frame)
            self.select_song_by_index(index)

        def show_context_menu_for_widget(event):
            index = self.song_widgets.index(song_frame)
            self.context_menu.entryconfigure("Remove Song", command=lambda: self.remove_song_by_index(index))
            self.context_menu.post(event.x_root, event.y_root)

        # Bind events
        song_frame.bind("<Button-1>", play_song_from_widget)
        thumbnail_label.bind("<Button-1>", play_song_from_widget)
        title_label.bind("<Button-1>", play_song_from_widget)
        duration_label.bind("<Button-1>", play_song_from_widget)

        song_frame.bind("<Enter>", select_song_from_widget)

        song_frame.bind("<Button-3>", show_context_menu_for_widget)
        thumbnail_label.bind("<Button-3>", show_context_menu_for_widget)
        title_label.bind("<Button-3>", show_context_menu_for_widget)
        duration_label.bind("<Button-3>", show_context_menu_for_widget)

        return song_frame
        
    def _load_thumbnail_async(self, url, widget):
        try:
            img = self.get_image_from_path_or_url(url, size=(50, 50))
            self.after(0, lambda w=widget, i=img: w.winfo_exists() and w.configure(image=i))
        except Exception as e:
            print(f"Error loading thumbnail: {e}")

    def clear_track_list(self):
        for widget in self.tracklist_scroll_frame.winfo_children():
            widget.destroy()
        self.song_widgets.clear()
        
    def highlight_current_song_widget(self):
        # Reset color for all widgets
        for i, widget in enumerate(self.song_widgets):
            if i == self.current_song_index:
                widget.configure(fg_color="#1DB954")
            else:
                widget.configure(fg_color="#282828")

    def filter_songs(self, event=None):
        search_term = self.search_bar.get().lower()
        if search_term == "Search Playlist...":
            search_term = ""

        self.clear_track_list()
        
        songs = self.playlist_manager.get_songs(self.current_playlist_id)
        filtered_songs = [s for s in songs if search_term in s['title'].lower()]
        
        self.songs_to_add = filtered_songs
        self.after(10, self._update_ui_with_songs_in_chunks)


    def add_from_link(self):
        url = self.link_entry.get().strip()
        if not url:
            return

        # Clear the input field
        self.link_entry.delete(0, "end")

        # ✅ Delay refocusing main window to avoid TclError
        self.after(100, self.focus_force)

        self.show_loading("Fetching info from YouTube...")

        def process_link():
            try:
                if "list=" in url:
                    # ✅ Playlist flow
                    self.youtube_streamer.get_playlist_info(url)
                else:
                    # ✅ Single song flow
                    full_info = self.youtube_streamer.fetch_full_song_info(url)
                    if full_info:
                        # Call the handler for single songs
                        self.after(0, lambda: self._handle_single_song_info(full_info))
                    else:
                        self.after(0, self.hide_loading)
                        self.after(200, lambda: messagebox.showerror(
                            "Error",
                            "Could not fetch this song (no stream info). Try updating yt-dlp."
                        ))
            except Exception as e:
                print(f"Error fetching link: {e}")
                self.after(0, self.hide_loading)
                self.after(200, lambda: messagebox.showerror(
                    "Error",
                    f"Could not fetch info from YouTube.\n\n{e}"
                ))

        threading.Thread(target=process_link, daemon=True).start()


    def sync_playlist(self):
        if not self.current_playlist_id:
            messagebox.showinfo("Sync Error", "Please select a playlist to sync first.")
            return

        playlists = self.playlist_manager.get_all_playlists()
        playlist_data = playlists.get(self.current_playlist_id, {})
        url = playlist_data.get('source_url')

        if not url:
            messagebox.showinfo("Sync Error", "This playlist does not have a source YouTube URL.")
            return

        self.sync_mode = True
        # ✅ Show loading screen before starting the fetch
        self.show_loading("Syncing playlist from YouTube…")

        # Start fetching playlist data
        self.yt_streamer.get_playlist_info(url)

    def toggle_play_pause(self):
        if self.music_player.is_playing and not self.music_player.is_paused:
            self.music_player.pause()
            self.stop_thread.set()
        elif self.music_player.is_paused:
            self.music_player.unpause()
            self.stop_thread.clear()
            self.progress_thread = threading.Thread(target=self._update_progress_bar_thread, daemon=True)
            self.progress_thread.start()
        elif self.current_song_index != -1 and self.current_playlist_id:
            self.play_song_by_index(self.current_song_index)
        else:
            first_playlist_id = list(self.playlist_manager.get_all_playlists().keys())[0] if self.playlist_manager.get_all_playlists() else None
            if first_playlist_id:
                self.display_playlist_songs(first_playlist_id)
                self.play_song_by_index(0)
        self.update_play_pause_button()
    
    def next_song(self):
        songs = self.playlist_manager.get_songs(self.current_playlist_id)
        if not songs:
            return

        next_index_to_play = -1
        if self.is_repeated:
            next_index_to_play = self.current_song_index
        elif self.is_shuffled:
            if not self.shuffled_indices:
                self.shuffled_indices = list(range(len(songs)))
                random.shuffle(self.shuffled_indices)
            
            self.current_shuffled_index = (self.current_shuffled_index + 1) % len(self.shuffled_indices)
            next_index_to_play = self.shuffled_indices[self.current_shuffled_index]
        else:
            next_index_to_play = (self.current_song_index + 1) % len(songs)
        
        self.play_song_by_index(next_index_to_play)

    def prev_song(self):
        songs = self.playlist_manager.get_songs(self.current_playlist_id)
        if not songs:
            return

        if self.is_repeated:
            next_index_to_play = self.current_song_index
        elif self.is_shuffled:
            if not self.shuffled_indices:
                self.shuffled_indices = list(range(len(songs)))
                random.shuffle(self.shuffled_indices)
            
            self.current_shuffled_index = (self.current_shuffled_index - 1 + len(self.shuffled_indices)) % len(self.shuffled_indices)
            next_index_to_play = self.shuffled_indices[self.current_shuffled_index]
        else:
            next_index_to_play = (self.current_song_index - 1 + len(songs)) % len(songs)
            
        self.play_song_by_index(next_index_to_play)
    
    def update_play_pause_button(self):
        if self.music_player.is_playing and not self.music_player.is_paused:
            self.play_pause_button.configure(image=self.pause_img, text="")
        else:
            self.play_pause_button.configure(image=self.play_img, text="")

    def toggle_shuffle(self):
        self.is_shuffled = not self.is_shuffled
        if self.is_shuffled:
            songs = self.playlist_manager.get_songs(self.current_playlist_id)
            if songs:
                self.shuffled_indices = list(range(len(songs)))
                random.shuffle(self.shuffled_indices)
                self.current_shuffled_index = -1
        else:
            self.shuffled_indices = []
            self.current_shuffled_index = -1

        if self.shuffle_on_img and self.shuffle_off_img:
            image = self.shuffle_on_img if self.is_shuffled else self.shuffle_off_img
            self.shuffle_button.configure(image=image, text="")
        print(f"Shuffle is now {'on' if self.is_shuffled else 'off'}")

    def toggle_repeat(self):
        self.is_repeated = not self.is_repeated
        if self.repeat_on_img and self.repeat_off_img:
            image = self.repeat_on_img if self.is_repeated else self.repeat_off_img
            self.repeat_button.configure(image=image, text="")
        print(f"Repeat is now {'on' if self.is_repeated else 'off'}")

    def set_volume_from_scale(self, value):
        volume = float(value)
        self.music_player.set_volume(volume)
        if volume > 0:
            self.last_volume = volume
            self.mute_button.configure(image=self.volume_img, text="")
        else:
            self.mute_button.configure(image=self.volume_mute_img, text="")

    def toggle_mute(self):
        if self.volume_scale.get() > 0:
            self.last_volume = self.volume_scale.get()
            self.volume_scale.set(0)
            self.music_player.set_volume(0)
            self.mute_button.configure(image=self.volume_mute_img, text="")
        else:
            volume_to_set = self.last_volume if self.last_volume > 0 else 0.5
            self.volume_scale.set(volume_to_set)
            self.music_player.set_volume(volume_to_set)
            self.mute_button.configure(image=self.volume_img, text="")

    def remove_song_by_index(self, index_to_remove):
        if not self.current_playlist_id:
            return
        
        if self.current_song_index == index_to_remove:
            self.music_player.stop()
            self.reset_now_playing_view()
            self.current_song_index = -1
        
        self.playlist_manager.remove_song_from_playlist(self.current_playlist_id, index_to_remove)
        self.display_playlist_songs(self.current_playlist_id)

    def show_context_menu(self, event):
        # This function is deprecated with the new UI.
        pass

    def reset_now_playing_view(self):
        self.title_label.configure(text="No song playing")
        self.total_time_label.configure(text="0:00")
        self.progress_bar.set(0)
        
    def update_now_playing_view(self, song, loading=False):
        if loading:
            # ✅ Clean the title before showing
            display_title = self.clean_title(song.get('title', 'Unknown Title'))
            self.title_label.configure(text=f"Loading: {display_title}...")
            self.total_time_label.configure(text="0:00")
            self.progress_bar.set(0)
        else:
            # ✅ Clean the title before showing
            display_title = self.clean_title(song.get('title', 'Unknown Title'))
            self.title_label.configure(text=display_title)
            duration = song.get('duration', 0)
            self.total_time_label.configure(text=time.strftime('%M:%S', time.gmtime(duration)))
            self.progress_bar.configure(to=duration)

        try:
            thumbnail_url = song.get('thumbnail_url')
            if thumbnail_url:
                img = self.get_image_from_path_or_url(thumbnail_url, size=(250, 140))
                self.thumbnail_label.configure(image=img, text="")
            else:
                img = self.get_image_from_path_or_url(None, size=(250, 140))
                self.thumbnail_label.configure(image=img, text="")
        except Exception as e:
            print(f"Could not load thumbnail: {e}")
            img = self.get_image_from_path_or_url(None, size=(250, 140))
            self.thumbnail_label.configure(image=img, text="")
            
    def load_icons(self):
        try:
            self.play_img = ctk.CTkImage(light_image=Image.open("icons/play.png"), size=(30, 30))
            self.pause_img = ctk.CTkImage(light_image=Image.open("icons/pause.png"), size=(30, 30))
            self.next_img = ctk.CTkImage(light_image=Image.open("icons/next.png"), size=(30, 30))
            self.prev_img = ctk.CTkImage(light_image=Image.open("icons/prev.png"), size=(30, 30))
            self.fast_fwd_img = ctk.CTkImage(light_image=Image.open("icons/fast_fwd.png"), size=(25, 25))
            self.fast_rew_img = ctk.CTkImage(light_image=Image.open("icons/fast_rew.png"), size=(25, 25))
            self.shuffle_off_img = ctk.CTkImage(light_image=Image.open("icons/shuffle_off.png"), size=(25, 25))
            self.shuffle_on_img = ctk.CTkImage(light_image=Image.open("icons/shuffle_on.png"), size=(25, 25))
            self.repeat_off_img = ctk.CTkImage(light_image=Image.open("icons/repeat_off.png"), size=(25, 25))
            self.repeat_on_img = ctk.CTkImage(light_image=Image.open("icons/repeat_on.png"), size=(25, 25))
            self.volume_img = ctk.CTkImage(light_image=Image.open("icons/volume.png"), size=(25, 25))
            self.volume_mute_img = ctk.CTkImage(light_image=Image.open("icons/volume_mute.png"), size=(25, 25))
            self.placeholder_img = ctk.CTkImage(light_image=Image.new("RGB", (50, 50), "gray"), size=(50, 50))
        except FileNotFoundError:
            self.play_img = self.pause_img = self.next_img = self.prev_img = None
            self.fast_fwd_img = self.fast_rew_img = None
            self.shuffle_off_img = self.shuffle_on_img = None
            self.repeat_off_img = self.repeat_on_img = None
            self.volume_img = self.volume_mute_img = None
            print("Warning: Icon files not found. Using text buttons.")
            self.placeholder_img = ctk.CTkImage(light_image=Image.new("RGB", (50, 50), "gray"), size=(50, 50))

    def create_widgets(self):
        main_frame = ctk.CTkFrame(self, fg_color="transparent")
        main_frame.pack(fill=ctk.BOTH, expand=True, padx=20, pady=20)
        
        # New Layout
        library_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        library_frame.pack(side=ctk.LEFT, fill=ctk.BOTH, expand=True)

        self.playlist_cards_frame = ctk.CTkScrollableFrame(library_frame, width=200, fg_color="#1E1E1E")
        self.playlist_cards_frame.pack(side=ctk.LEFT, fill=ctk.Y, padx=(0, 10))

        self.tracklist_frame = ctk.CTkFrame(library_frame, fg_color="#1E1E1E")
        self.tracklist_frame.pack(side=ctk.LEFT, fill=ctk.BOTH, expand=True)

        now_playing_frame = ctk.CTkFrame(main_frame, fg_color="#1E1E1E", width=300)
        now_playing_frame.pack(side=ctk.RIGHT, fill=ctk.Y, padx=(10, 0))
        now_playing_frame.pack_propagate(False)

        self.setup_tracklist_view(self.tracklist_frame)
        self.setup_now_playing_view(now_playing_frame)
        self.setup_control_panel(self)

    def setup_tracklist_view(self, parent_frame):
        self.search_bar = ctk.CTkEntry(parent_frame, placeholder_text="Search Playlist...")
        self.search_bar.pack(fill=ctk.X, padx=10, pady=10)
        self.search_bar.bind("<KeyRelease>", self.filter_songs)
        
        sync_button = ctk.CTkButton(parent_frame, text="Sync Playlist", command=self.sync_playlist, fg_color="#1DB954")
        sync_button.pack(fill=ctk.X, padx=10, pady=5)
        
        self.tracklist_scroll_frame = ctk.CTkScrollableFrame(parent_frame, fg_color="#1E1E1E")
        self.tracklist_scroll_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(5, 10))
        
        self.context_menu = tk.Menu(self, tearoff=0, bg="#1E1E1E", fg="white", activebackground="#1DB954", activeforeground="white")
        self.context_menu.add_command(label="Remove Song", command=lambda: self.remove_song_by_index(self.current_song_index))

    def setup_now_playing_view(self, parent_frame):
        self.current_thumbnail = ctk.CTkImage(light_image=Image.new("RGB", (250, 140), "black"), size=(250, 140))
        self.thumbnail_label = ctk.CTkLabel(parent_frame, image=self.current_thumbnail, text="", fg_color="transparent")
        self.thumbnail_label.pack(pady=20)
        
        self.title_label = ctk.CTkLabel(parent_frame, text="No song playing", font=ctk.CTkFont(size=14, weight="bold"), wraplength=250)
        self.title_label.pack(pady=10)
        
        self.progress_bar_frame = ctk.CTkFrame(parent_frame, fg_color="transparent")
        self.progress_bar_frame.pack(fill=ctk.X, padx=20, pady=10)
        
        self.elapsed_time_label = ctk.CTkLabel(self.progress_bar_frame, text="0:00", font=ctk.CTkFont(size=10))
        self.elapsed_time_label.pack(side=ctk.LEFT)
        
        self.progress_bar = ctk.CTkSlider(self.progress_bar_frame, from_=0, to=100, command=self._handle_progress_change)
        self.progress_bar.pack(side=ctk.LEFT, fill=ctk.X, expand=True, padx=5)
        self.progress_bar.bind("<ButtonPress-1>", self.on_progress_press)
        self.progress_bar.bind("<ButtonRelease-1>", self.on_progress_release)

        self.total_time_label = ctk.CTkLabel(self.progress_bar_frame, text="0:00", font=ctk.CTkFont(size=10))
        self.total_time_label.pack(side=ctk.LEFT)

    def setup_control_panel(self, parent_frame):
        control_frame = ctk.CTkFrame(parent_frame, fg_color="#282828")
        control_frame.pack(side=ctk.BOTTOM, fill=ctk.X)
        
        add_frame = ctk.CTkFrame(control_frame, fg_color="#282828")
        add_frame.pack(side=ctk.LEFT, padx=10)
        self.link_entry = ctk.CTkEntry(add_frame, width=300, placeholder_text="Enter YouTube Song or Playlist URL")
        self.link_entry.pack(side=ctk.LEFT, padx=5)
        add_button = ctk.CTkButton(add_frame, text="Add Song/Playlist", command=self.add_from_link, fg_color="#1DB954")
        add_button.pack(side=ctk.LEFT, padx=5)
        
        player_controls_frame = ctk.CTkFrame(control_frame, fg_color="#282828")
        player_controls_frame.pack(side=ctk.LEFT, padx=20)
        
        self.shuffle_button = ctk.CTkButton(player_controls_frame, image=self.shuffle_off_img, text="", command=self.toggle_shuffle, width=40, height=40)
        self.shuffle_button.pack(side=ctk.LEFT, padx=5)

        fast_rew_button = ctk.CTkButton(player_controls_frame, image=self.fast_rew_img, text="", command=lambda: self.seek_backward(10), width=40, height=40)
        fast_rew_button.pack(side=ctk.LEFT, padx=5)

        prev_button = ctk.CTkButton(player_controls_frame, image=self.prev_img, text="", command=self.prev_song, width=40, height=40)
        prev_button.pack(side=ctk.LEFT, padx=5)
        
        self.play_pause_button = ctk.CTkButton(player_controls_frame, image=self.play_img, text="", command=self.toggle_play_pause, width=40, height=40)
        self.play_pause_button.pack(side=ctk.LEFT, padx=5)

        next_button = ctk.CTkButton(player_controls_frame, image=self.next_img, text="", command=self.next_song, width=40, height=40)
        next_button.pack(side=ctk.LEFT, padx=5)
        
        fast_fwd_button = ctk.CTkButton(player_controls_frame, image=self.fast_fwd_img, text="", command=lambda: self.seek_forward(10), width=40, height=40)
        fast_fwd_button.pack(side=ctk.LEFT, padx=5)

        self.repeat_button = ctk.CTkButton(player_controls_frame, image=self.repeat_off_img, text="", command=self.toggle_repeat, width=40, height=40)
        self.repeat_button.pack(side=ctk.LEFT, padx=5)

        volume_frame = ctk.CTkFrame(control_frame, fg_color="#282828")
        volume_frame.pack(side=ctk.RIGHT)
        
        self.mute_button = ctk.CTkButton(volume_frame, image=self.volume_img, text="", command=self.toggle_mute, width=40, height=40)
        self.mute_button.pack(side=ctk.LEFT, padx=(0, 5))
        
        self.volume_scale = ctk.CTkSlider(volume_frame, from_=0, to=1, command=self.set_volume_from_scale)
        self.volume_scale.set(self.last_volume)
        self.volume_scale.pack(side=ctk.LEFT, padx=5)
        self.music_player.set_volume(self.last_volume)

    def on_close(self):
        self.stop_thread.set()
        self.music_player.stop()
        self.destroy()

if __name__ == "__main__":
    app = MusicPlayerApp()
    app.protocol("WM_DELETE_WINDOW", app.on_close)
    app.mainloop()