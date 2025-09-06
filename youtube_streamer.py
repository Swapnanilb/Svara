import threading
import yt_dlp as yt
import re
import time

class YouTubeStreamer:
    """
    Handles fetching data from YouTube using yt-dlp.
    """

    def __init__(self, on_playlist_info_fetched, on_single_song_info_fetched):
        self.on_playlist_info_fetched = on_playlist_info_fetched
        self.on_single_song_info_fetched = on_single_song_info_fetched
        self.url_cache = {}  # Cache for stream URLs
        self.cache_duration = 3600  # 1 hour cache
        self.ydl_opts = {
            'format': 'bestaudio/best',
            'quiet': True,
            'no_warnings': True,
            'extract_flat': 'in_playlist',  # keep flat for fast playlist info
            'nocheckcertificate': True,
            'ignoreerrors': True,
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
        ydl_opts = {
            "quiet": True,
            "extract_flat": True,  # ✅ Only basic info (no full download of all songs)
            "skip_download": True
        }

        with yt.YoutubeDL(ydl_opts) as ydl:
            try:
                info = ydl.extract_info(url, download=False)

                playlist_info = {
                    "title": info.get("title", "Unknown Playlist"),
                    "original_url": url,
                    "thumbnail_url": info.get("thumbnails", [{}])[-1].get("url") if info.get("thumbnails") else None,
                    "entries": []
                }

                for entry in info.get("entries", []):
                    if entry and "id" in entry:
                        playlist_info["entries"].append({
                            "id": entry.get("id"),
                            "title": entry.get("title"),
                            "url": f"https://www.youtube.com/watch?v={entry['id']}",
                            "thumbnail_url": entry.get("thumbnails", [{}])[-1].get("url") if entry.get("thumbnails") else None,
                        })

                # ✅ Pass this lightweight info to main
                self.on_playlist_info_fetched(playlist_info)

            except Exception as e:
                print(f"Error fetching playlist info: {e}")
                self.on_playlist_info_fetched(None)

    def _fetch_single_song_data(self, url):
        """Fetch info async for adding single songs."""
        full_song_info = self._fetch_single_song_data_sync(url)
        if full_song_info:
            self.on_single_song_info_fetched(full_song_info)

    def _fetch_single_song_data_sync(self, url):
        """
        Fetches song metadata without storing temporary URLs.
        """
        full_song_info = {}
        try:
            # Force yt-dlp to resolve full info (not flat)
            opts = self.ydl_opts.copy()
            opts.pop('extract_flat', None)

            with yt.YoutubeDL(opts) as ydl:
                info_dict = ydl.extract_info(url, download=False)

                if info_dict:
                    full_song_info = {
                        "title": info_dict.get('title', 'Unknown Title'),
                        "id": info_dict.get('id', 'Unknown ID'),
                        "duration": info_dict.get('duration', 0),
                        "thumbnail_url": info_dict.get('thumbnail')
                        # No 'url' field - will be fetched fresh when needed
                    }

        except yt.DownloadError as e:
            print(f"Error fetching song info: {e}")

        return full_song_info

    def fetch_full_song_info(self, url: str):
        """
        Public wrapper to fetch a song's full metadata (sync).
        Useful for playlist syncing when added/removed songs are detected.
        """
        return self._fetch_single_song_data_sync(url)
    
    def get_fresh_stream_url(self, video_id):
        """
        Get a stream URL for a video ID with caching.
        """
        current_time = time.time()
        
        # Check cache first
        if video_id in self.url_cache:
            cached_url, timestamp = self.url_cache[video_id]
            if current_time - timestamp < self.cache_duration:
                return cached_url
        
        # Fetch fresh URL
        url = f"https://www.youtube.com/watch?v={video_id}"
        try:
            opts = self.ydl_opts.copy()
            opts.pop('extract_flat', None)

            with yt.YoutubeDL(opts) as ydl:
                info_dict = ydl.extract_info(url, download=False)

                if info_dict:
                    best_audio = next(
                        (f for f in info_dict.get('formats', [])
                         if f.get('acodec') != 'none' and f.get('vcodec') == 'none'),
                        None
                    )
                    
                    if best_audio:
                        stream_url = best_audio.get('url')
                        # Cache the URL
                        self.url_cache[video_id] = (stream_url, current_time)
                        return stream_url
                        
        except Exception as e:
            print(f"Error getting stream URL: {e}")
            
        return None
