import threading
import random
import time
import re
from youtube_streamer import YouTubeStreamer
from playlist_manager import PlaylistManager
from player import MusicPlayer

class MusicPlayerLogic:
    def __init__(self, ui_callback_handler):
        """
        Initialize the music player logic.
        ui_callback_handler should be an object that implements UI update methods.
        """
        self.ui = ui_callback_handler
        
        # Core components
        self.playlist_manager = PlaylistManager()
        self.yt_streamer = YouTubeStreamer(self.on_playlist_info_fetched, self.on_single_song_info_fetched)
        self.music_player = MusicPlayer(self.ui, self.play_next_song)
        self.youtube_streamer = YouTubeStreamer(self.on_playlist_info_fetched, self.on_single_song_info_fetched)
        
        # Player state
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
        self.selected_song_index = -1
        
        # Temporary storage
        self.songs_to_add = []

    def clean_title(self, title: str) -> str:
        """Return a simplified song title (remove artist/extra text)."""
        # Normalize separators
        title = title.replace("—", "-").replace("–", "-")

        # Split on separators commonly used in YouTube titles
        parts = re.split(r"[-|:]", title)

        # Take the first chunk as base
        base = parts[0].strip()

        # If base is very short (like "Official"), fallback to next
        if len(base) < 2 and len(parts) > 1:
            base = parts[1].strip()

        # Remove text inside () or [] like (Official Video), [Lyric]
        base = re.sub(r"[\(\[].*?[\)\]]", "", base)

        # Remove common keywords
        keywords = [
            "official", "video", "lyrics", "lyrical", "lyric", "cover",
            "audio", "remix", "live", "acoustic", "version", "full song"
        ]
        pattern = r"\b(" + "|".join(keywords) + r")\b"
        base = re.sub(pattern, "", base, flags=re.IGNORECASE)

        # Clean up
        base = re.sub(r"\s+", " ", base).strip(" -—–_|")

        return base if base else "Unknown Title"

    def on_playlist_info_fetched(self, playlist_info):
        """Handle playlist info fetched from YouTube."""
        self.ui.after(0, lambda: self._update_ui_with_new_playlist(playlist_info))

    def _update_ui_with_new_playlist(self, playlist_info):
        if not playlist_info:
            self.ui.show_error("Fetch Error", "Failed to fetch playlist information from YouTube.")
            return

        playlist_name = playlist_info.get('title', 'Unknown Playlist')
        songs = playlist_info.get('entries', [])
        thumbnail = playlist_info.get('thumbnail_url', None)
        source_url = playlist_info.get('original_url')
        
        threading.Thread(target=self._process_playlist_songs_thread, args=(playlist_name, songs, thumbnail, source_url), daemon=True).start()

    def _process_playlist_songs_thread(self, playlist_name, songs, thumbnail, source_url):
        existing_playlist_id = self.playlist_manager.get_playlist_by_url(source_url)
        
        if existing_playlist_id:
            # Update existing playlist
            old_songs = self.playlist_manager.get_songs(existing_playlist_id)
            old_ids = {s['id'] for s in old_songs}
            new_ids = {s['id'] for s in songs}
            
            added_ids = new_ids - old_ids
            removed_ids = old_ids - new_ids

            # Add new songs with full info
            for song in songs:
                if song['id'] in added_ids:
                    print(f"Fetching full info for new song: {song['id']}")
                    full_info = self.youtube_streamer.fetch_full_song_info(song['url'])
                    if full_info:
                        self.playlist_manager.add_song_to_playlist(existing_playlist_id, full_info)
            
            # Remove deleted songs
            if removed_ids:
                updated_songs = [s for s in old_songs if s['id'] not in removed_ids]
                self.playlist_manager.update_playlist_songs(existing_playlist_id, updated_songs)

            # Update metadata
            playlist_data = self.playlist_manager.get_all_playlists().get(existing_playlist_id, {})
            if playlist_data.get("name") != playlist_name:
                playlist_data["name"] = playlist_name
            if thumbnail and playlist_data.get("thumbnail") != thumbnail:
                playlist_data["thumbnail"] = thumbnail
            
            # Update UI
            self.ui.after(0, self.ui.hide_loading)
            self.ui.after(200, self.ui.load_playlist_cards)
            self.ui.after(200, lambda: self.display_playlist_songs(existing_playlist_id))

            if added_ids or removed_ids:
                self.ui.after(200, lambda: self.ui.show_info(
                    "Playlist Updated",
                    f"Playlist '{playlist_name}' updated.\n\n"
                    f"Added: {len(added_ids)} songs\nRemoved: {len(removed_ids)} songs"
                ))
            else:
                self.ui.after(200, lambda: self.ui.show_info(
                    "Already Exists",
                    f"Playlist '{playlist_name}' already exists with no changes."
                ))

        else:
            # New playlist
            full_songs = []
            for song in songs:
                print(f"Fetching full info for new song: {song['id']}")
                full_info = self.youtube_streamer.fetch_full_song_info(song['url'])
                if full_info:
                    full_songs.append(full_info)
            
            playlist_id = self.playlist_manager.add_new_playlist(
                playlist_name, full_songs, source_url, thumbnail
            )
            
            self.ui.after(0, self.ui.hide_loading)
            self.ui.after(200, lambda: self.ui.create_playlist_card(playlist_name, playlist_id))
            self.ui.after(200, lambda: self.display_playlist_songs(playlist_id))
            self.ui.after(200, lambda: self.ui.show_info(
                "Playlist Uploaded",
                f"Playlist '{playlist_name}' uploaded successfully."
            ))

    def on_single_song_info_fetched(self, full_song_info):
        self.ui.after(0, lambda: self._handle_single_song_info(full_song_info))
    
    def _handle_single_song_info(self, full_song_info):
        self.ui.hide_loading()
        
        if not full_song_info or not full_song_info.get('url'):
            self.ui.show_error("Playback Error", "Failed to get a valid stream URL for this song. YouTube may have changed its API. Try updating yt-dlp.")
            return

        self.ui.show_add_song_dialog(full_song_info)

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
                self.ui.update_now_playing_view(song, loading=True)
            else:
                self.music_player.play_song(self.current_song_info)
                self.ui.update_now_playing_view(self.current_song_info)
                self.stop_thread.clear()
                self.progress_thread = threading.Thread(target=self._update_progress_bar_thread, daemon=True)
                self.progress_thread.start()
            
            self.ui.update_play_pause_button()
            self.ui.highlight_current_song_widget()
            self.selected_song_index = index
        else:
            self.music_player.stop()
            self.ui.reset_now_playing_view()

    def _update_progress_bar_thread(self):
        while True:
            if self.stop_thread.is_set():
                break
            if self.music_player and self.music_player.is_playing:
                length_ms = self.music_player.get_length()
                pos_ms = self.music_player.get_pos()
                if length_ms > 0:
                    pos_sec = pos_ms / 1000
                    self.ui.after(0, lambda p=pos_sec: self.ui.update_progress(p))
            time.sleep(0.5)

    def display_playlist_songs(self, playlist_id):
        self.current_playlist_id = playlist_id
        self.ui.update_playlist_card_colors(playlist_id)
        self.ui.clear_track_list()
        threading.Thread(target=self._load_playlist_thread, args=(playlist_id,), daemon=True).start()
        
    def _load_playlist_thread(self, playlist_id):
        songs = self.playlist_manager.get_songs(playlist_id)
        self.songs_to_add = songs
        
        if self.is_shuffled:
            self.shuffled_indices = list(range(len(songs)))
            random.shuffle(self.shuffled_indices)
            self.current_shuffled_index = -1
        
        self.selected_song_index = -1
        self.ui.after(10, self._update_ui_with_songs_in_chunks)

    def _update_ui_with_songs_in_chunks(self, chunk_size=50):
        if self.songs_to_add:
            chunk = self.songs_to_add[:chunk_size]
            self.songs_to_add = self.songs_to_add[chunk_size:]
            
            for song in chunk:
                self.ui.create_song_widget(song)
            
            self.ui.after(10, self._update_ui_with_songs_in_chunks)

    def add_from_link(self, url):
        if not url.strip():
            return

        self.ui.show_loading("Fetching info from YouTube...")

        def process_link():
            try:
                if "list=" in url:
                    self.youtube_streamer.get_playlist_info(url)
                else:
                    full_info = self.youtube_streamer.fetch_full_song_info(url)
                    if full_info:
                        self.ui.after(0, lambda: self._handle_single_song_info(full_info))
                    else:
                        self.ui.after(0, self.ui.hide_loading)
                        self.ui.after(200, lambda: self.ui.show_error(
                            "Error",
                            "Could not fetch this song (no stream info). Try updating yt-dlp."
                        ))
            except Exception as e:
                print(f"Error fetching link: {e}")
                self.ui.after(0, self.ui.hide_loading)
                self.ui.after(200, lambda: self.ui.show_error(
                    "Error",
                    f"Could not fetch info from YouTube.\n\n{e}"
                ))

        threading.Thread(target=process_link, daemon=True).start()

    def sync_playlist(self):
        if not self.current_playlist_id:
            self.ui.show_info("Sync Error", "Please select a playlist to sync first.")
            return

        playlists = self.playlist_manager.get_all_playlists()
        playlist_data = playlists.get(self.current_playlist_id, {})
        url = playlist_data.get('source_url')

        if not url:
            self.ui.show_info("Sync Error", "This playlist does not have a source YouTube URL.")
            return

        self.sync_mode = True
        self.ui.show_loading("Syncing playlist from YouTube...")
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
        self.ui.update_play_pause_button()

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

        self.ui.update_shuffle_button(self.is_shuffled)
        print(f"Shuffle is now {'on' if self.is_shuffled else 'off'}")

    def toggle_repeat(self):
        self.is_repeated = not self.is_repeated
        self.ui.update_repeat_button(self.is_repeated)
        print(f"Repeat is now {'on' if self.is_repeated else 'off'}")

    def set_volume(self, volume):
        self.music_player.set_volume(volume)
        if volume > 0:
            self.last_volume = volume
        self.ui.update_mute_button(volume > 0)

    def toggle_mute(self):
        current_volume = self.ui.get_volume()
        if current_volume > 0:
            self.last_volume = current_volume
            self.ui.set_volume(0)
            self.music_player.set_volume(0)
        else:
            volume_to_set = self.last_volume if self.last_volume > 0 else 0.5
            self.ui.set_volume(volume_to_set)
            self.music_player.set_volume(volume_to_set)
        self.ui.update_mute_button(self.ui.get_volume() > 0)

    def seek_forward(self, seconds):
        if self.music_player.is_playing:
            current_pos = self.music_player.get_pos()
            new_pos_ms = current_pos + (seconds * 1000)
            self.music_player.set_pos(new_pos_ms)
            self.ui.set_progress(new_pos_ms / 1000)
            
    def seek_backward(self, seconds):
        if self.music_player.is_playing:
            current_pos = self.music_player.get_pos()
            new_pos_ms = max(0, current_pos - (seconds * 1000))
            self.music_player.set_pos(new_pos_ms)
            self.ui.set_progress(new_pos_ms / 1000)

    def handle_progress_change(self, value):
        pos_sec = float(value)
        self.ui.update_elapsed_time(pos_sec)
        
        if not self.is_seeking and self.music_player.is_playing:
            self.music_player.set_pos(pos_sec * 1000)

    def set_seeking(self, seeking):
        self.is_seeking = seeking

    def handle_slider_seek(self, progress):
        if self.music_player and self.music_player.is_playing:
            length_ms = self.music_player.get_length()
            new_pos = int(progress * length_ms)
            self.music_player.set_pos(new_pos)

    def remove_song_by_index(self, index_to_remove):
        if not self.current_playlist_id:
            return
        
        if self.current_song_index == index_to_remove:
            self.music_player.stop()
            self.ui.reset_now_playing_view()
            self.current_song_index = -1
        
        self.playlist_manager.remove_song_from_playlist(self.current_playlist_id, index_to_remove)
        self.display_playlist_songs(self.current_playlist_id)

    def filter_songs(self, search_term):
        if search_term.lower() == "search playlist...":
            search_term = ""

        self.ui.clear_track_list()
        
        songs = self.playlist_manager.get_songs(self.current_playlist_id)
        filtered_songs = [s for s in songs if search_term.lower() in s['title'].lower()]
        
        self.songs_to_add = filtered_songs
        self.ui.after(10, self._update_ui_with_songs_in_chunks)

    def select_next_song(self):
        song_count = len(self.ui.song_widgets)
        if not song_count:
            return
        
        new_index = (self.selected_song_index + 1) % song_count
        self.ui.select_song_by_index(new_index)
        self.selected_song_index = new_index

    def select_prev_song(self):
        song_count = len(self.ui.song_widgets)
        if not song_count:
            return
        
        new_index = (self.selected_song_index - 1 + song_count) % song_count
        self.ui.select_song_by_index(new_index)
        self.selected_song_index = new_index
        
    def play_selected_song(self):
        if self.selected_song_index != -1:
            self.play_song_by_index(self.selected_song_index)

    def volume_up(self):
        current_volume = self.ui.get_volume()
        new_volume = min(1.0, current_volume + 0.1)
        self.ui.set_volume(new_volume)
        self.music_player.set_volume(new_volume)

    def volume_down(self):
        current_volume = self.ui.get_volume()
        new_volume = max(0.0, current_volume - 0.1)
        self.ui.set_volume(new_volume)
        self.music_player.set_volume(new_volume)

    def remove_playlist(self, playlist_id):
        if self.current_playlist_id == playlist_id:
            self.music_player.stop()
            self.ui.reset_now_playing_view()
            self.current_song_index = -1
            self.current_playlist_id = None
        
        self.playlist_manager.remove_playlist(playlist_id)
        self.ui.load_playlist_cards()
        self.ui.clear_track_list()

    def upload_playlist_thumbnail(self, playlist_id, file_path):
        if file_path:
            self.playlist_manager.update_playlist_thumbnail(playlist_id, file_path)
            self.ui.update_playlist_card_thumbnail(playlist_id)
            
    def remove_custom_playlist_thumbnail(self, playlist_id):
        self.playlist_manager.remove_playlist_thumbnail(playlist_id)
        self.ui.update_playlist_card_thumbnail(playlist_id)

    def add_song_to_playlist(self, playlist_id, song_info):
        if not self.playlist_manager.song_exists(playlist_id, song_info["id"]):
            self.playlist_manager.add_song_to_playlist(playlist_id, song_info)
            self.display_playlist_songs(playlist_id)
            return True
        return False

    def create_new_playlist_with_song(self, name, song_info):
        playlist_id = self.playlist_manager.add_new_playlist(name, [song_info])
        self.ui.create_playlist_card(name, playlist_id)
        self.display_playlist_songs(playlist_id)
        return playlist_id

    def stop_and_cleanup(self):
        self.stop_thread.set()
        self.music_player.stop()