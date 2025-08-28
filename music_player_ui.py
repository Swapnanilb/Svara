import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox, filedialog, simpledialog
from PIL import Image
import urllib.request
import io
import time
import threading
import os

class MusicPlayerUI(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        self.title("Python Music Player")
        self.geometry("1280x800")
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("dark-blue")

        # UI state
        self.in_menu = False
        self.song_widgets = []
        self.placeholder_img = None
        self.loading_dialog = None
        self.playlist_card_buttons = {}
        
        # Icons
        self.play_img = None
        self.pause_img = None
        self.next_img = None
        self.prev_img = None
        self.fast_fwd_img = None
        self.fast_rew_img = None
        self.shuffle_off_img = None
        self.shuffle_on_img = None
        self.repeat_off_img = None
        self.repeat_on_img = None
        self.volume_img = None
        self.volume_mute_img = None
        
        self.load_icons()
        self.create_widgets()
        
        # Logic will be set after initialization
        self.logic = None

    def set_logic(self, logic):
        """Set the logic component and complete initialization."""
        self.logic = logic
        self.load_playlist_cards()
        self.bind_keyboard_shortcuts()

    def show_loading(self, message="Loading..."):
        """Show a small non-blocking loading dialog with a message."""
        if getattr(self, "loading_dialog", None) is not None and self.loading_dialog.winfo_exists():
            self.loading_label.configure(text=message)
            return

        self.loading_dialog = ctk.CTkToplevel(self)
        self.loading_dialog.title("Loading")
        self.loading_dialog.geometry("300x100")
        self.loading_dialog.resizable(False, False)
        self.loading_dialog.grab_set()

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
        """Close the loading dialog if it exists."""
        if getattr(self, "loading_dialog", None) is not None and self.loading_dialog.winfo_exists():
            self.loading_dialog.destroy()
        self.loading_dialog = None

    def show_error(self, title, message):
        """Show error message dialog."""
        messagebox.showerror(title, message)

    def show_info(self, title, message):
        """Show info message dialog."""
        messagebox.showinfo(title, message)

    def bind_keyboard_shortcuts(self):
        # Media controls using standard keys
        self.bind_all("<space>", lambda e: self.logic.toggle_play_pause())
        self.bind_all("<Right>", lambda e: self.logic.next_song())
        self.bind_all("<Left>", lambda e: self.logic.prev_song())
        # Use Function keys for volume to avoid all conflicts
        self.bind_all("<F10>", lambda e: self.logic.volume_up())
        self.bind_all("<F9>", lambda e: self.logic.volume_down())
        self.bind_all("<F12>", lambda e: self.logic.toggle_mute())
        # Seeking controls remain on Control + arrows
        self.bind_all("<Control-Right>", lambda e: self.logic.seek_forward(10))
        self.bind_all("<Control-Left>", lambda e: self.logic.seek_backward(10))
        
        # New keyboard bindings for track list navigation
        self.bind_all("<Up>", lambda e: self.logic.select_prev_song())
        self.bind_all("<Down>", lambda e: self.logic.select_next_song())
        self.bind_all("<Return>", lambda e: self.logic.play_selected_song())

    def select_song_by_index(self, index, scroll_into_view=True):
        if self.logic.selected_song_index != -1 and self.logic.selected_song_index < len(self.song_widgets):
            self.song_widgets[self.logic.selected_song_index].configure(fg_color="#282828")
            
        if 0 <= index < len(self.song_widgets):
            self.song_widgets[index].configure(fg_color="#3A3A3A")
            self.tracklist_scroll_frame.update_idletasks()

            # Only scroll when explicitly asked (not on hover)
            if scroll_into_view and hasattr(self.tracklist_scroll_frame, "_parent_canvas"):
                self.tracklist_scroll_frame._parent_canvas.yview_moveto(
                    index / len(self.song_widgets)
                )


    def load_playlist_cards(self):
        for widget in self.playlist_cards_frame.winfo_children():
            widget.destroy()
        
        self.playlist_card_buttons.clear()

        for playlist_id, playlist in self.logic.playlist_manager.get_all_playlists().items():
            self.create_playlist_card(playlist['name'], playlist_id)

    def get_image_from_path_or_url(self, source, size=(100, 100)):
        """Helper function to load an image from a local path or a URL."""
        img = None
        if source:
            try:
                if source.startswith(('http://', 'https://')):
                    with urllib.request.urlopen(source) as url:
                        raw_data = url.read()
                    pil_img = Image.open(io.BytesIO(raw_data)).resize(size)
                else:
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
        
        thumbnail_source = self.logic.playlist_manager.get_playlist_thumbnail(playlist_id)
        
        if not thumbnail_source:
            thumbnail_source = self.logic.playlist_manager.get_first_song_thumbnail(playlist_id)
            
        img = self.get_image_from_path_or_url(thumbnail_source)
        thumbnail_label.configure(image=img)

    def create_playlist_card(self, name, playlist_id):
        card_frame = ctk.CTkFrame(self.playlist_cards_frame, corner_radius=10, fg_color="#2A2A2A")
        card_frame.pack(fill=tk.X, padx=5, pady=5)
        
        thumbnail_source = self.logic.playlist_manager.get_playlist_thumbnail(playlist_id)
        if not thumbnail_source:
            thumbnail_source = self.logic.playlist_manager.get_first_song_thumbnail(playlist_id)

        img = self.get_image_from_path_or_url(thumbnail_source)
        thumbnail_label = ctk.CTkLabel(card_frame, image=img, text="", fg_color="transparent")
        thumbnail_label.pack(padx=10, pady=(10, 0), expand=True, fill=tk.BOTH)
        
        name_label = ctk.CTkLabel(card_frame, text=name, font=ctk.CTkFont(size=12, weight="bold"), wraplength=100)
        name_label.pack(padx=10, pady=(0, 10))

        self.playlist_card_buttons[playlist_id] = card_frame

        def bind_click(widget):
            widget.bind("<Button-1>", lambda e, p_id=playlist_id: self.logic.display_playlist_songs(p_id))

        bind_click(card_frame)
        bind_click(thumbnail_label)
        bind_click(name_label)

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

        x = parent_button.winfo_rootx()
        y = parent_button.winfo_rooty() + parent_button.winfo_height()
        menu.geometry(f"+{x}+{y}")

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

        def on_focus_out(event):
            menu.destroy()
            self._reset_menu_state()

        menu.bind("<FocusOut>", on_focus_out)
        menu.after(100, menu.focus_force)

    def _upload_playlist_thumbnail(self, playlist_id):
        file_path = filedialog.askopenfilename(
            title="Select an image file",
            filetypes=[("Image files", "*.png;*.jpg;*.jpeg;*.gif;*.bmp")]
        )
        self.logic.upload_playlist_thumbnail(playlist_id, file_path)

    def _remove_playlist(self, playlist_id):
        if messagebox.askyesno("Confirm Deletion", "Are you sure you want to remove this playlist?"):
            self.logic.remove_playlist(playlist_id)

    def _reset_menu_state(self):
        self.in_menu = False

    def update_playlist_card_colors(self, selected_playlist_id):
        for p_id, frame in self.playlist_card_buttons.items():
            if frame.winfo_exists():
                frame.configure(fg_color="#1DB954" if p_id == selected_playlist_id else "#2A2A2A")

    def clear_track_list(self):
        for widget in self.tracklist_scroll_frame.winfo_children():
            widget.destroy()
        self.song_widgets.clear()

    def create_song_widget(self, song):
        song_frame = ctk.CTkFrame(self.tracklist_scroll_frame, fg_color="#282828", corner_radius=10)
        song_frame.pack(fill=tk.X, padx=5, pady=5)
        
        thumbnail_label = ctk.CTkLabel(song_frame, image=self.placeholder_img, text="")
        thumbnail_label.pack(side=tk.LEFT, padx=(5, 10), pady=5)
        
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
        
        duration_str = time.strftime('%M:%S', time.gmtime(song.get('duration', 0)))
        duration_label = ctk.CTkLabel(song_frame, text=duration_str, font=ctk.CTkFont(size=12))
        duration_label.pack(side=tk.RIGHT, padx=5)
        
        self.song_widgets.append(song_frame)
        
        threading.Thread(target=self._load_thumbnail_async, args=(song.get('thumbnail_url'), thumbnail_label), daemon=True).start()
        
        def play_song_from_widget(event):
            index = self.song_widgets.index(song_frame)
            self.logic.play_song_by_index(index)
            self.select_song_by_index(index)

        def select_song_from_widget(event):
            index = self.song_widgets.index(song_frame)
            self.select_song_by_index(index)

        def show_context_menu_for_widget(event):
            index = self.song_widgets.index(song_frame)
            self.context_menu.entryconfigure("Remove Song", command=lambda: self.logic.remove_song_by_index(index))
            self.context_menu.post(event.x_root, event.y_root)

        song_frame.bind("<Button-1>", play_song_from_widget)
        thumbnail_label.bind("<Button-1>", play_song_from_widget)
        title_label.bind("<Button-1>", play_song_from_widget)
        duration_label.bind("<Button-1>", play_song_from_widget)

        # Remove auto-scroll on hover → just highlight
        # Temporary hover highlight (does not select)
        # Hover highlight
        def on_hover_enter(event, frame=song_frame):
            frame.configure(fg_color="#333333")

        def on_hover_leave(event, frame=song_frame):
            index = self.song_widgets.index(frame)
            if index != self.logic.selected_song_index:  # keep if selected
                frame.configure(fg_color="#282828")

        # Bind to the frame AND its children so the effect is continuous
        for widget in (song_frame, thumbnail_label, title_label, duration_label):
            widget.bind("<Enter>", on_hover_enter, add="+")
            widget.bind("<Leave>", on_hover_leave, add="+")




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

    def highlight_current_song_widget(self):
        for i, widget in enumerate(self.song_widgets):
            if i == self.logic.current_song_index:
                widget.configure(fg_color="#1DB954")
            else:
                widget.configure(fg_color="#282828")

    def filter_songs(self, event=None):
        search_term = self.search_bar.get().lower()
        self.logic.filter_songs(search_term)

    def add_from_link(self):
        url = self.link_entry.get().strip()
        if not url:
            return

        self.link_entry.delete(0, "end")
        self.after(100, self.focus_force)
        self.logic.add_from_link(url)

    def sync_playlist(self):
        self.logic.sync_playlist()

    def show_add_song_dialog(self, song_info):
        dialog = ctk.CTkToplevel(self)
        dialog.title("Add Song")
        dialog.geometry("400x250")
        dialog.resizable(False, False)

        dialog.grab_set()
        self.after(10, lambda: dialog.focus_force() if dialog.winfo_exists() else None)

        ctk.CTkLabel(
            dialog,
            text=f"How to add '{song_info['title']}'?",
            font=ctk.CTkFont(size=14, weight="bold"),
            wraplength=350
        ).pack(pady=10)

        playlists = self.logic.playlist_manager.get_all_playlists()

        create_new_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        create_new_frame.pack(fill=tk.X, padx=20, pady=5)

        ctk.CTkLabel(create_new_frame, text="➕ Create a New Playlist").pack(side=tk.LEFT, padx=5)

        def create_new():
            new_name = simpledialog.askstring("New Playlist", "Enter playlist name:", parent=dialog)
            if new_name:
                playlist_id = self.logic.create_new_playlist_with_song(new_name, song_info)
                messagebox.showinfo("Song Added", f"Song added to new playlist '{new_name}'")
                dialog.destroy()

        ctk.CTkButton(create_new_frame, text="Create", command=create_new).pack(side=tk.RIGHT, padx=5)

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
                    if self.logic.add_song_to_playlist(playlist_id, song_info):
                        messagebox.showinfo("Song Added", f"Song added to '{selected_name}'")
                    else:
                        messagebox.showinfo("Already Exists", f"Song already exists in '{selected_name}'")
                dialog.destroy()

            ctk.CTkButton(dialog, text="Add to Playlist", command=add_to_existing).pack(pady=10)

    def update_now_playing_view(self, song, loading=False):
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

    def reset_now_playing_view(self):
        self.title_label.configure(text="No song playing")
        self.total_time_label.configure(text="0:00")
        self.progress_bar.set(0)

    def update_play_pause_button(self):
        if self.logic.music_player.is_playing and not self.logic.music_player.is_paused:
            self.play_pause_button.configure(image=self.pause_img, text="")
        else:
            self.play_pause_button.configure(image=self.play_img, text="")

    def update_shuffle_button(self, is_shuffled):
        if self.shuffle_on_img and self.shuffle_off_img:
            image = self.shuffle_on_img if is_shuffled else self.shuffle_off_img
            self.shuffle_button.configure(image=image, text="")

    def update_repeat_button(self, is_repeated):
        if self.repeat_on_img and self.repeat_off_img:
            image = self.repeat_on_img if is_repeated else self.repeat_off_img
            self.repeat_button.configure(image=image, text="")

    def update_mute_button(self, has_volume):
        if has_volume:
            self.mute_button.configure(image=self.volume_img, text="")
        else:
            self.mute_button.configure(image=self.volume_mute_img, text="")

    def update_progress(self, pos_sec):
        self.progress_bar.set(pos_sec)
        self.update_elapsed_time(pos_sec)

    def update_elapsed_time(self, pos_sec):
        self.elapsed_time_label.configure(text=time.strftime('%M:%S', time.gmtime(int(pos_sec))))

    def set_progress(self, pos_sec):
        self.progress_bar.set(pos_sec)

    def get_volume(self):
        return self.volume_scale.get()

    def set_volume(self, volume):
        self.volume_scale.set(volume)

    def _on_slider_seek(self, event):
        if self.logic.music_player and self.logic.music_player.is_playing:
            progress = self.progress_bar.get()
            self.logic.handle_slider_seek(progress)

    def _handle_progress_change(self, value):
        self.logic.handle_progress_change(value)

    def on_progress_press(self, event=None):
        self.logic.set_seeking(True)

    def on_progress_release(self, event=None):
        self.logic.set_seeking(False)

    def set_volume_from_scale(self, value):
        volume = float(value)
        self.logic.set_volume(volume)

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
        self.context_menu.add_command(label="Remove Song", command=lambda: None)  # Will be set dynamically

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
        
        self.shuffle_button = ctk.CTkButton(player_controls_frame, image=self.shuffle_off_img, text="", command=lambda: self.logic.toggle_shuffle(), width=40, height=40)
        self.shuffle_button.pack(side=ctk.LEFT, padx=5)

        fast_rew_button = ctk.CTkButton(player_controls_frame, image=self.fast_rew_img, text="", command=lambda: self.logic.seek_backward(10), width=40, height=40)
        fast_rew_button.pack(side=ctk.LEFT, padx=5)

        prev_button = ctk.CTkButton(player_controls_frame, image=self.prev_img, text="", command=lambda: self.logic.prev_song(), width=40, height=40)
        prev_button.pack(side=ctk.LEFT, padx=5)
        
        self.play_pause_button = ctk.CTkButton(player_controls_frame, image=self.play_img, text="", command=lambda: self.logic.toggle_play_pause(), width=40, height=40)
        self.play_pause_button.pack(side=ctk.LEFT, padx=5)

        next_button = ctk.CTkButton(player_controls_frame, image=self.next_img, text="", command=lambda: self.logic.next_song(), width=40, height=40)
        next_button.pack(side=ctk.LEFT, padx=5)
        
        fast_fwd_button = ctk.CTkButton(player_controls_frame, image=self.fast_fwd_img, text="", command=lambda: self.logic.seek_forward(10), width=40, height=40)
        fast_fwd_button.pack(side=ctk.LEFT, padx=5)

        self.repeat_button = ctk.CTkButton(player_controls_frame, image=self.repeat_off_img, text="", command=lambda: self.logic.toggle_repeat(), width=40, height=40)
        self.repeat_button.pack(side=ctk.LEFT, padx=5)

        volume_frame = ctk.CTkFrame(control_frame, fg_color="#282828")
        volume_frame.pack(side=ctk.RIGHT)
        
        self.mute_button = ctk.CTkButton(volume_frame, image=self.volume_img, text="", command=lambda: self.logic.toggle_mute(), width=40, height=40)
        self.mute_button.pack(side=ctk.LEFT, padx=(0, 5))
        
        self.volume_scale = ctk.CTkSlider(volume_frame, from_=0, to=1, command=self.set_volume_from_scale)
        self.volume_scale.set(0.5)
        self.volume_scale.pack(side=ctk.LEFT, padx=5)

    def on_close(self):
        if self.logic:
            self.logic.stop_and_cleanup()
        self.destroy()