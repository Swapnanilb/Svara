import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox, filedialog, simpledialog
from tkinter import ttk
from PIL import Image, ImageTk
import urllib.request
import io
import time
import threading
import random
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
        
        self.loading_screen = None
        self.playlist_card_buttons = {}

        self.load_icons()
        self.create_widgets()
        self.load_playlist_cards()
        self.bind_keyboard_shortcuts()

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
            
            # Highlight the current song in the tracklist
            # Get the list of all items in the treeview
            items = self.playlist_tree.get_children()
            if items:
                # Clear any existing selection
                self.playlist_tree.selection_remove(self.playlist_tree.selection())
                
                # Get the item ID of the song at the current index
                song_item_id = items[self.current_song_index]
                
                # Set the selection to the new item
                self.playlist_tree.selection_set(song_item_id)
                
                # Make sure the selected item is visible
                self.playlist_tree.see(song_item_id)
        else:
            self.music_player.stop()
            self.reset_now_playing_view()
    
    def on_playlist_info_fetched(self, playlist_info):
        self.after(0, lambda: self._update_ui_with_new_playlist(playlist_info))

    def _update_ui_with_new_playlist(self, playlist_info):
        if playlist_info:
            if self.sync_mode:
                # Handle synchronization by replacing the entire playlist
                self.playlist_manager.update_playlist_songs(self.current_playlist_id, playlist_info['entries'])
                self.display_playlist_songs(self.current_playlist_id)
                messagebox.showinfo("Sync Complete", "Playlist has been successfully synced with YouTube.")
                self.sync_mode = False
            else:
                # Handle initial playlist creation
                playlist_name = playlist_info.get('title', 'Unknown Playlist')
                songs = playlist_info.get('entries', [])
                thumbnail = playlist_info.get('thumbnail_url', None)
                source_url = playlist_info.get('original_url')
                
                playlist_id = self.playlist_manager.add_new_playlist(playlist_name, songs, source_url)
                self.create_playlist_card(playlist_name, playlist_id, thumbnail)
                self.display_playlist_songs(playlist_id)
        
        self.hide_loading_screen()
        
    def on_single_song_info_fetched(self, full_song_info):
        self.after(0, lambda: self._handle_single_song_info(full_song_info))
    
    def _handle_single_song_info(self, full_song_info):
        self.hide_loading_screen()
        
        if not full_song_info or not full_song_info.get('url'):
            messagebox.showerror("Playback Error", "Failed to get a valid stream URL for this song. YouTube may have a changed its API. Try updating yt-dlp.")
            return

        self.show_add_song_dialog(full_song_info)

    def show_add_song_dialog(self, song_info):
        dialog = ctk.CTkToplevel(self)
        dialog.title("Add Song")
        dialog.geometry("400x200")
        dialog.resizable(False, False)
        dialog.grab_set()

        ctk.CTkLabel(dialog, text=f"How to add '{song_info['title']}'?", font=ctk.CTkFont(size=14, weight="bold"), wraplength=350).pack(pady=10)

        playlists = self.playlist_manager.get_all_playlists()
        
        # Option 1: Create a new playlist
        create_new_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        create_new_frame.pack(fill=tk.X, padx=20, pady=5)
        
        def create_new():
            name = simpledialog.askstring("New Playlist", "Enter a name for the new playlist:")
            if name:
                playlist_id = self.playlist_manager.add_new_playlist(name, [song_info], source_url=None)
                self.create_playlist_card(name, playlist_id, song_info.get('thumbnail_url'))
                self.display_playlist_songs(playlist_id)
                dialog.destroy()
        
        ctk.CTkButton(create_new_frame, text="Create New Playlist", command=create_new).pack(side=tk.LEFT, fill=tk.X, expand=True)

        # Option 2: Add to an existing playlist
        if playlists:
            add_to_existing_frame = ctk.CTkFrame(dialog, fg_color="transparent")
            add_to_existing_frame.pack(fill=tk.X, padx=20, pady=5)
            
            playlist_names = [p['name'] for p in playlists.values()]
            selected_playlist = ctk.StringVar(value=playlist_names[0])
            
            option_menu = ctk.CTkOptionMenu(add_to_existing_frame, variable=selected_playlist, values=playlist_names)
            option_menu.pack(side=tk.LEFT, padx=(0, 5), fill=tk.X, expand=True)

            def add_to_existing():
                selected_name = selected_playlist.get()
                selected_id = next(id for id, p in playlists.items() if p['name'] == selected_name)
                
                self.playlist_manager.add_song_to_playlist(selected_id, song_info)
                self.display_playlist_songs(selected_id)
                dialog.destroy()

            ctk.CTkButton(add_to_existing_frame, text="Add to Existing", command=add_to_existing).pack(side=tk.LEFT)

        ctk.CTkButton(dialog, text="Cancel", command=dialog.destroy).pack(pady=(10, 5))

    def _update_progress_bar_thread(self):
        while not self.stop_thread.is_set():
            if self.music_player.is_playing:
                pos_ms = self.music_player.get_pos()
                if pos_ms > 0:
                    pos_sec = pos_ms / 1000
                    self.after(0, lambda: self._update_gui_progress(pos_sec))
            
            time.sleep(1)

    def _update_gui_progress(self, pos_sec):
        if not self.is_seeking:
            self.progress_bar.set(pos_sec)
        self.elapsed_time_label.configure(text=time.strftime('%M:%S', time.gmtime(pos_sec)))
        
    def _handle_progress_change(self, value):
        # This function is called by the CTkSlider's command.
        # It handles both dragging and releasing.
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
        
        for playlist_id, playlist in self.playlist_manager.get_all_playlists().items():
            self.create_playlist_card(
                playlist['name'],
                playlist_id,
                playlist.get('thumbnail', None)
            )

    def create_playlist_card(self, name, playlist_id, thumbnail_url):
        card_frame = ctk.CTkFrame(self.playlist_cards_frame, corner_radius=10, fg_color="#2A2A2A")
        
        img = None
        if thumbnail_url:
            try:
                with urllib.request.urlopen(thumbnail_url) as url:
                    raw_data = url.read()
                pil_img = Image.open(io.BytesIO(raw_data)).resize((100, 100))
                img = ctk.CTkImage(light_image=pil_img, size=(100, 100))
            except Exception as e:
                print(f"Could not load thumbnail for {name}: {e}")
                img = ctk.CTkImage(light_image=Image.new("RGB", (100, 100), "black"), size=(100, 100))
        else:
            img = ctk.CTkImage(light_image=Image.new("RGB", (100, 100), "black"), size=(100, 100))

        # We'll use a button to make the entire card clickable
        card_button = ctk.CTkButton(card_frame, 
                                     text=name,
                                     image=img,
                                     compound="top",
                                     hover_color="#1DB954",
                                     fg_color="transparent",
                                     command=lambda p_id=playlist_id: self.display_playlist_songs(p_id))
        
        card_button.pack(padx=10, pady=10, expand=True, fill=tk.BOTH)
        card_frame.pack(fill=tk.X, padx=5, pady=5)
        self.playlist_card_buttons[playlist_id] = card_button

    def display_playlist_songs(self, playlist_id):
        self.current_playlist_id = playlist_id
        songs = self.playlist_manager.get_songs(playlist_id)

        for i in self.playlist_tree.get_children():
            self.playlist_tree.delete(i)
        
        for song in songs:
            duration_str = time.strftime('%M:%S', time.gmtime(song.get('duration', 0)))
            self.playlist_tree.insert("", "end", values=(song['title'], duration_str))
        
        for p_id, button in self.playlist_card_buttons.items():
            button.configure(fg_color="#1DB954" if p_id == playlist_id else "transparent")
            
        # Re-initialize shuffled list when a new playlist is displayed
        if self.is_shuffled:
            self.shuffled_indices = list(range(len(songs)))
            random.shuffle(self.shuffled_indices)
            self.current_shuffled_index = -1
            

    def filter_songs(self, event=None):
        search_term = self.search_bar.get().lower()
        if search_term == "Search Library...":
            search_term = ""

        songs = self.playlist_manager.get_songs(self.current_playlist_id)

        filtered_songs = [
            song for song in songs
            if search_term in song['title'].lower()
        ]

        for item in self.playlist_tree.get_children():
            self.playlist_tree.delete(item)

        for song in filtered_songs:
            duration_str = time.strftime('%M:%S', time.gmtime(song.get('duration', 0)))
            self.playlist_tree.insert("", "end", values=(song['title'], duration_str))

    def play_selected_song(self, event):
        selected_items = self.playlist_tree.selection()
        if not selected_items:
            return
        
        item = selected_items[0]
        index = self.playlist_tree.index(item)
        self.play_song_by_index(index)
        
    def add_from_link(self):
        url = self.link_entry.get()
        if not url:
            messagebox.showerror("Error", "Please enter a YouTube link.")
            return

        # Check if the playlist already exists before fetching the data
        existing_playlist_id = self.playlist_manager.get_playlist_by_url(url)
        if existing_playlist_id:
            messagebox.showinfo("Playlist Already Exists", "This playlist is already in your library.")
            self.display_playlist_songs(existing_playlist_id)
            self.link_entry.delete(0, tk.END)
            return

        self.show_loading_screen()
        self.yt_streamer.get_playlist_info(url)
        self.link_entry.delete(0, tk.END)

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
        self.show_loading_screen()
        self.yt_streamer.get_playlist_info(url)
    
    def show_loading_screen(self):
        if self.loading_screen:
            return
        
        self.loading_screen = ctk.CTkToplevel(self)
        self.loading_screen.title("Loading...")
        self.loading_screen.geometry("300x120")
        self.loading_screen.resizable(False, False)
        
        x = self.winfo_x() + self.winfo_width() // 2 - 150
        y = self.winfo_y() + self.winfo_height() // 2 - 60
        self.loading_screen.geometry(f"+{x}+{y}")
        
        ctk.CTkLabel(self.loading_screen, text="Loading playlist, please wait...", font=ctk.CTkFont(size=14, weight="bold")).pack(pady=(20, 10))
        
        self.loading_bar = ctk.CTkProgressBar(self.loading_screen, orientation="horizontal", mode="indeterminate", determinate_speed=1)
        self.loading_bar.pack(fill=tk.X, padx=20, pady=10)
        self.loading_bar.start()

        self.loading_screen.grab_set()

    def hide_loading_screen(self):
        if self.loading_screen:
            self.loading_bar.stop()
            self.loading_screen.destroy()
            self.loading_screen = None

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

    def remove_selected_song(self):
        selected_items = self.playlist_tree.selection()
        if not selected_items or not self.current_playlist_id:
            return
        
        item = selected_items[0]
        index_to_remove = self.playlist_tree.index(item)
        
        if self.current_song_index == index_to_remove:
            self.music_player.stop()
            self.reset_now_playing_view()
            self.current_song_index = -1
        
        self.playlist_manager.remove_song_from_playlist(self.current_playlist_id, index_to_remove)
        self.display_playlist_songs(self.current_playlist_id)

    def show_context_menu(self, event):
        item = self.playlist_tree.identify_row(event.y)
        if item:
            self.playlist_tree.selection_set(item)
            self.context_menu.post(event.x_root, event.y_root)

    def reset_now_playing_view(self):
        self.title_label.configure(text="No song playing")
        self.total_time_label.configure(text="0:00")
        self.progress_bar.set(0)
        
    def update_now_playing_view(self, song, loading=False):
        if loading:
            self.title_label.configure(text=f"Loading: {song.get('title', 'Unknown Title')}...")
            self.total_time_label.configure(text="0:00")
            self.progress_bar.set(0)
        else:
            self.title_label.configure(text=song.get('title', 'Unknown Title'))
            duration = song.get('duration', 0)
            self.total_time_label.configure(text=time.strftime('%M:%S', time.gmtime(duration)))
            self.progress_bar.configure(to=duration)

        try:
            thumbnail_url = song.get('thumbnail_url')
            if thumbnail_url:
                with urllib.request.urlopen(thumbnail_url) as url:
                    raw_data = url.read()
                pil_img = Image.open(io.BytesIO(raw_data)).resize((250, 140))
                self.current_thumbnail = ctk.CTkImage(light_image=pil_img, size=(250, 140))
                self.thumbnail_label.configure(image=self.current_thumbnail, text="")
            else:
                pil_img = Image.new("RGB", (250, 140), "black")
                self.current_thumbnail = ctk.CTkImage(light_image=pil_img, size=(250, 140))
                self.thumbnail_label.configure(image=self.current_thumbnail, text="")

        except Exception as e:
            print(f"Could not load thumbnail: {e}")
            pil_img = Image.new("RGB", (250, 140), "black")
            self.current_thumbnail = ctk.CTkImage(light_image=pil_img, size=(250, 140))
            self.thumbnail_label.configure(image=self.current_thumbnail, text="")
            
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
        except FileNotFoundError:
            self.play_img = self.pause_img = self.next_img = self.prev_img = None
            self.fast_fwd_img = self.fast_rew_img = None
            self.shuffle_off_img = self.shuffle_on_img = None
            self.repeat_off_img = self.repeat_on_img = None
            self.volume_img = self.volume_mute_img = None
            print("Warning: Icon files not found. Using text buttons.")

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
        
        # Add sync button
        sync_button = ctk.CTkButton(parent_frame, text="Sync Playlist", command=self.sync_playlist, fg_color="#1DB954")
        sync_button.pack(fill=ctk.X, padx=10, pady=5)


        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Treeview", background="#282828", foreground="white", fieldbackground="#282828", borderwidth=0, font=("Arial", 10))
        style.map("Treeview", background=[('selected', '#1DB954')])

        self.playlist_tree = ttk.Treeview(parent_frame, columns=("Title", "Duration"), show="headings")
        self.playlist_tree.heading("Title", text="Title")
        self.playlist_tree.heading("Duration", text="Duration")
        self.playlist_tree.column("Duration", stretch=ctk.NO, width=80)
        self.playlist_tree.pack(fill=ctk.BOTH, expand=True, padx=10, pady=5)
        self.playlist_tree.bind("<Double-1>", self.play_selected_song)
        self.playlist_tree.bind("<Return>", self.play_selected_song) # Add this line

        scrollbar = ttk.Scrollbar(parent_frame, orient="vertical", command=self.playlist_tree.yview)
        scrollbar.pack(side=ctk.RIGHT, fill=ctk.Y, padx=(0, 10))
        self.playlist_tree.configure(yscrollcommand=scrollbar.set)
        
        self.context_menu = tk.Menu(self, tearoff=0, bg="#1E1E1E", fg="white", activebackground="#1DB954", activeforeground="white")
        self.context_menu.add_command(label="Remove Song", command=self.remove_selected_song)
        self.playlist_tree.bind("<Button-3>", self.show_context_menu)

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