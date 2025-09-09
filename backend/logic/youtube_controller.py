import threading
from youtube_streamer import YouTubeStreamer

class YouTubeController:
    def __init__(self, main_logic):
        self.main_logic = main_logic
        self.ui = main_logic.ui
        
        # Initialize YouTube streamer
        self.yt_streamer = YouTubeStreamer(
            self.on_playlist_info_fetched, 
            self.on_single_song_info_fetched
        )

    def on_playlist_info_fetched(self, playlist_info):
        """Handle playlist info fetched from YouTube."""
        self.ui.after(0, lambda: self._update_ui_with_new_playlist(playlist_info))

    def _update_ui_with_new_playlist(self, playlist_info):
        """Process and update UI with new playlist information."""
        if not playlist_info:
            self.ui.show_error("Fetch Error", "Failed to fetch playlist information from YouTube.")
            return

        playlist_name = playlist_info.get('title', 'Unknown Playlist')
        songs = playlist_info.get('entries', [])
        thumbnail = playlist_info.get('thumbnail_url', None)
        source_url = playlist_info.get('original_url')
        
        # Process in background thread
        threading.Thread(
            target=self._process_playlist_songs_thread, 
            args=(playlist_name, songs, thumbnail, source_url), 
            daemon=True
        ).start()

    def _process_playlist_songs_thread(self, playlist_name, songs, thumbnail, source_url):
        """Process playlist songs in a background thread."""
        existing_playlist_id = self.main_logic.playlist_manager.get_playlist_by_url(source_url)
        
        if existing_playlist_id:
            self._update_existing_playlist(existing_playlist_id, playlist_name, songs, thumbnail)
        else:
            self._create_new_playlist(playlist_name, songs, source_url, thumbnail)

    def _update_existing_playlist(self, playlist_id, playlist_name, songs, thumbnail):
        """Update an existing playlist with new songs."""
        old_songs = self.main_logic.playlist_manager.get_songs(playlist_id)
        old_ids = {s['id'] for s in old_songs}
        new_ids = {s['id'] for s in songs}
        
        added_ids = new_ids - old_ids
        removed_ids = old_ids - new_ids

        # Add new songs with full info
        for song in songs:
            if song['id'] in added_ids:
                print(f"Fetching full info for new song: {song['id']}")
                full_info = self.yt_streamer.fetch_full_song_info(song['url'])
                if full_info:
                    self.main_logic.playlist_manager.add_song_to_playlist(playlist_id, full_info)
        
        # Remove deleted songs
        if removed_ids:
            updated_songs = [s for s in old_songs if s['id'] not in removed_ids]
            self.main_logic.playlist_manager.update_playlist_songs(playlist_id, updated_songs)

        # Update metadata
        self._update_playlist_metadata(playlist_id, playlist_name, thumbnail)

        # Update UI
        self._update_ui_after_playlist_sync(playlist_id, playlist_name, added_ids, removed_ids)

    def _create_new_playlist(self, playlist_name, songs, source_url, thumbnail):
        """Create a new playlist from YouTube data."""
        full_songs = []
        for song in songs:
            print(f"Fetching full info for new song: {song['id']}")
            full_info = self.yt_streamer.fetch_full_song_info(song['url'])
            if full_info:
                full_songs.append(full_info)
        
        playlist_id = self.main_logic.playlist_manager.add_new_playlist(
            playlist_name, full_songs, source_url, thumbnail
        )
        
        # Update UI
        self.ui.after(0, self.ui.hide_loading)
        self.ui.after(200, self.ui.load_playlist_cards)
        self.ui.after(200, lambda: self.main_logic.display_playlist_songs(playlist_id))
        self.ui.after(200, lambda: self.ui.show_info(
            "Playlist Uploaded",
            f"Playlist '{playlist_name}' uploaded successfully."
        ))

    def _update_playlist_metadata(self, playlist_id, playlist_name, thumbnail):
        """Update playlist metadata (name and thumbnail)."""
        playlist_data = self.main_logic.playlist_manager.get_all_playlists().get(playlist_id, {})
        
        if playlist_data.get("name") != playlist_name:
            playlist_data["name"] = playlist_name
            
        if thumbnail and playlist_data.get("thumbnail") != thumbnail:
            playlist_data["thumbnail"] = thumbnail

    def _update_ui_after_playlist_sync(self, playlist_id, playlist_name, added_ids, removed_ids):
        """Update UI after playlist synchronization."""
        self.ui.after(0, self.ui.hide_loading)
        self.ui.after(200, self.ui.load_playlist_cards)
        self.ui.after(200, lambda: self.main_logic.display_playlist_songs(playlist_id))

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

    def on_single_song_info_fetched(self, full_song_info):
        """Handle single song info fetched from YouTube."""
        self.ui.after(0, lambda: self._handle_single_song_info(full_song_info))
    
    def _handle_single_song_info(self, full_song_info):
        """Process single song information."""
        self.ui.hide_loading()
        
        if not full_song_info:
            self.ui.show_error(
                "Fetch Error", 
                "Failed to fetch song information from YouTube."
            )
            return

        self.ui.show_add_song_dialog(full_song_info)

    def add_from_link(self, url):
        """Add song or playlist from YouTube URL."""
        if not url.strip():
            return

        self.ui.show_loading("Fetching info from YouTube...")

        def process_link():
            try:
                if "list=" in url:
                    # Playlist URL
                    self.yt_streamer.get_playlist_info(url)
                else:
                    # Single song URL
                    full_info = self.yt_streamer.fetch_full_song_info(url)
                    if full_info:
                        self.ui.after(0, lambda: self._handle_single_song_info(full_info))
                    else:
                        self._show_fetch_error("Could not fetch this song (no stream info). Try updating yt-dlp.")
                        
            except Exception as e:
                print(f"Error fetching link: {e}")
                self._show_fetch_error(f"Could not fetch info from YouTube.\n\n{e}")

        threading.Thread(target=process_link, daemon=True).start()

    def _show_fetch_error(self, message):
        """Show error message for fetch failures."""
        self.ui.after(0, self.ui.hide_loading)
        self.ui.after(200, lambda: self.ui.show_error("Error", message))

    def sync_playlist(self):
        """Sync current playlist with YouTube source."""
        if not self.main_logic.current_playlist_id:
            self.ui.show_info("Sync Error", "Please select a playlist to sync first.")
            return

        playlist_data = self.main_logic.playlist_controller.get_playlist_info(
            self.main_logic.current_playlist_id
        )
        url = playlist_data.get('source_url')

        if not url:
            self.ui.show_info("Sync Error", "This playlist does not have a source YouTube URL.")
            return

        self.main_logic.sync_mode = True
        self.ui.show_loading("Syncing playlist from YouTube...")
        self.yt_streamer.get_playlist_info(url)
    
    def load_tracks_to_cache(self, songs):
        """Load tracks into cache in background thread."""
        def cache_tracks():
            cached_count = 0
            for song in songs:
                if song.get('id'):
                    try:
                        url = self.yt_streamer.get_fresh_stream_url(song['id'])
                        if url:
                            cached_count += 1
                    except Exception as e:
                        print(f"Error caching track {song.get('title', 'Unknown')}: {e}")
            
            self.ui.after(0, self.ui.hide_loading)
            self.ui.after(200, lambda: self.ui.show_info(
                "Load Tracks Complete",
                f"Successfully cached {cached_count} out of {len(songs)} tracks."
            ))
        
        threading.Thread(target=cache_tracks, daemon=True).start()
    
