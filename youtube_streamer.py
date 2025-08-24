import threading
import yt_dlp as yt
import os
import re

class YouTubeStreamer:
    """
    Handles fetching data from YouTube using yt-dlp.
    """
    
    def __init__(self, on_playlist_info_fetched, on_single_song_info_fetched):
        self.on_playlist_info_fetched = on_playlist_info_fetched
        self.on_single_song_info_fetched = on_single_song_info_fetched
        self.ydl_opts = {
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'quiet': True,
            'no_warnings': True,
            'extract_flat': 'in_playlist',  # This option is key for fast playlist info retrieval
        }
        
    def get_playlist_info(self, url, existing_ids=None):
        threading.Thread(target=self._fetch_playlist_data, args=(url, existing_ids), daemon=True).start()

    def get_stream_info_for_id(self, video_id):
        url = f"https://www.youtube.com/watch?v={video_id}"
        threading.Thread(target=self._fetch_single_song_data, args=(url,), daemon=True).start()

    def _extract_video_id(self, url):
        """Extracts the video ID from a YouTube URL."""
        match = re.search(r'(?<=v=)[^&#]+', url)
        if match:
            return match.group(0)
        return None

    def _fetch_playlist_data(self, url, existing_ids=None):
        if existing_ids is None:
            existing_ids = set()

        try:
            with yt.YoutubeDL(self.ydl_opts) as ydl:
                info_dict = ydl.extract_info(url, download=False)
                
                if info_dict and 'entries' in info_dict:
                    new_entries = []
                    # This loop fetches detailed info only for new songs
                    for entry in info_dict['entries']:
                        if entry and 'id' in entry and entry['id'] not in existing_ids:
                            video_id = entry['id']
                            print(f"Fetching full info for new song: {video_id}")
                            full_song_info = self._fetch_single_song_data_sync(f"https://www.youtube.com/watch?v={video_id}")
                            if full_song_info:
                                new_entries.append(full_song_info)
                        else:
                            print(f"Skipping existing song: {entry.get('id')}")
                    
                    # Combine existing playlist data with new entries
                    playlist_info_with_new_songs = {
                        "entries": new_entries,
                        "title": info_dict.get('title'),
                        "thumbnail_url": info_dict.get('thumbnail'),
                        "original_url": info_dict.get('original_url')
                    }
                    self.on_playlist_info_fetched(playlist_info_with_new_songs)
                else:
                    # Handle single video URL which may have no 'entries'
                    full_song_info = self._fetch_single_song_data_sync(url)
                    if full_song_info:
                        self.on_single_song_info_fetched(full_song_info)

        except yt.DownloadError as e:
            print(f"Error fetching playlist info: {e}")
            self.on_playlist_info_fetched(None)

    def _fetch_single_song_data_sync(self, url):
        full_song_info = {}
        try:
            with yt.YoutubeDL(self.ydl_opts) as ydl:
                info_dict = ydl.extract_info(url, download=False)
                
                if info_dict:
                    best_audio = None
                    for format in info_dict.get('formats', []):
                        if format.get('ext') in ['m4a', 'webm'] and 'acodec' in format:
                            best_audio = format
                            break

                    if best_audio:
                        full_song_info = {
                            "title": info_dict.get('title', 'Unknown Title'),
                            "id": info_dict.get('id', 'Unknown ID'),
                            "duration": info_dict.get('duration', 0),
                            "thumbnail_url": info_dict.get('thumbnail'),
                            "url": best_audio.get('url')
                        }
                    else:
                        print("No suitable audio format found.")

        except yt.DownloadError as e:
            print(f"Error fetching song info: {e}")

        return full_song_info