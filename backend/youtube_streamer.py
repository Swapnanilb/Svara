import threading
import yt_dlp as yt
import re
import time
import json
import os
from performance_logger import perf_logger

class YouTubeStreamer:
    """
    Handles fetching data from YouTube using yt-dlp.
    """

    def __init__(self, on_playlist_info_fetched, on_single_song_info_fetched):
        self.on_playlist_info_fetched = on_playlist_info_fetched
        self.on_single_song_info_fetched = on_single_song_info_fetched
        self.url_cache_file = "song_url_cache.json"
        self.url_cache = self._load_url_cache()
        self.cache_duration = 21600  # 6 hours cache
        self.metadata_cache_file = "song_metadata_cache.json"
        self.metadata_cache = self._load_metadata_cache()
        self.ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'extract_flat': 'in_playlist',
            'nocheckcertificate': True,
            'ignoreerrors': True
        }

    def get_playlist_info(self, url, existing_ids=None):
        threading.Thread(target=self._fetch_playlist_data, args=(url, existing_ids), daemon=True).start()
    
    def get_stream_info_for_id(self, video_id):
        url = f"https://www.youtube.com/watch?v={video_id}"
        threading.Thread(target=self._fetch_single_song_data, args=(url,), daemon=True).start()

    def _extract_video_id(self, url):
        """Extracts the video ID from a YouTube URL."""
        patterns = [
            r'(?<=v=)[^&#]+',
            r'(?<=/)([a-zA-Z0-9_-]{11})(?:\?|$)',
            r'(?<=embed/)[^/?]+'
        ]
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(0) if '=' in pattern else match.group(1) if match.groups() else match.group(0)
        return None

    def _fetch_playlist_data(self, url, existing_ids=None):
        """Fetches playlist data asynchronously."""
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
        Fetches song metadata with caching.
        """
        print(f"[YouTubeStreamer] Starting sync fetch for: {url}")
        
        # Extract video ID for caching
        video_id = self._extract_video_id(url)
        print(f"[YouTubeStreamer] Extracted video ID: {video_id}")
        
        if video_id:
            # Check cache first
            cached = self._get_cached_metadata(video_id)
            if cached:
                print(f"[YouTubeStreamer] Found cached metadata: {cached}")
                return cached
        
        print(f"[YouTubeStreamer] No cache found, fetching from YouTube...")
        full_song_info = {}
        try:
            # Try metadata-only extraction first
            opts = {
                'quiet': True,
                'no_warnings': True,
                'skip_download': True,
                'extract_flat': False
            }

            with yt.YoutubeDL(opts) as ydl:
                print(f"[YouTubeStreamer] Calling yt-dlp extract_info...")
                info_dict = ydl.extract_info(url, download=False)
                print(f"[YouTubeStreamer] yt-dlp returned: {bool(info_dict)}")

                if info_dict:
                    full_song_info = {
                        "title": info_dict.get('title', 'Unknown Title'),
                        "id": info_dict.get('id', video_id),
                        "duration": info_dict.get('duration', 0),
                        "thumbnail_url": info_dict.get('thumbnail')
                    }
                    print(f"[YouTubeStreamer] Extracted song info: {full_song_info}")
                    
                    # Cache the metadata
                    if video_id:
                        self._cache_metadata(video_id, full_song_info)
                        print(f"[YouTubeStreamer] Cached metadata for {video_id}")

        except yt.DownloadError as e:
            print(f"[YouTubeStreamer] yt-dlp DownloadError: {e}")
            # Fallback: create basic info from URL
            if video_id:
                full_song_info = {
                    "title": f"Video {video_id}",
                    "id": video_id,
                    "duration": 0,
                    "thumbnail_url": f"https://img.youtube.com/vi/{video_id}/maxresdefault.jpg"
                }
        except Exception as e:
            print(f"[YouTubeStreamer] Unexpected error: {e}")
            # Fallback: create basic info from URL
            if video_id:
                full_song_info = {
                    "title": f"Video {video_id}",
                    "id": video_id,
                    "duration": 0,
                    "thumbnail_url": f"https://img.youtube.com/vi/{video_id}/maxresdefault.jpg"
                }

        print(f"[YouTubeStreamer] Final result: {full_song_info}")
        return full_song_info

    def fetch_full_song_info(self, url: str):
        """
        Public wrapper to fetch a song's full metadata (sync).
        Useful for playlist syncing when added/removed songs are detected.
        """
        print(f"[YouTubeStreamer] Fetching song info for: {url}")
        result = self._fetch_single_song_data_sync(url)
        print(f"[YouTubeStreamer] Song info result: {result}")
        return result
    
    def get_fresh_stream_url(self, video_id, silent=False):
        """
        Get a stream URL for a video ID with caching.
        """
        start_time = time.time()
        current_time = time.time()
        from_cache = False
        
        # Check cache first
        if video_id in self.url_cache:
            cached_data = self.url_cache[video_id]
            if isinstance(cached_data, (list, tuple)) and len(cached_data) >= 2:
                cached_url, timestamp = cached_data[0], cached_data[1]
                if current_time - timestamp < self.cache_duration:
                    if not silent:
                        print(f"Using cached URL for {video_id}")
                    from_cache = True
                    load_time = time.time() - start_time
                    perf_logger.log_song_load(video_id, "Cached Song", load_time, from_cache)
                    return cached_url
        
        # Fetch fresh URL
        if not silent:
            print(f"Fetching fresh URL for {video_id}")
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
                        self._save_url_cache()
                        
                        load_time = time.time() - start_time
                        title = info_dict.get('title', 'Unknown')
                        perf_logger.log_song_load(video_id, title, load_time, from_cache)
                        return stream_url
                        
        except Exception as e:
            if not silent:
                print(f"Error getting stream URL: {e}")
            
        return None
    
    def _load_metadata_cache(self):
        """Load metadata cache from file."""
        if os.path.exists(self.metadata_cache_file):
            try:
                with open(self.metadata_cache_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return {}
        return {}
    
    def _save_metadata_cache(self):
        """Save metadata cache to file."""
        try:
            with open(self.metadata_cache_file, 'w', encoding='utf-8') as f:
                json.dump(self.metadata_cache, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving metadata cache: {e}")
    
    def _get_cached_metadata(self, video_id):
        """Get cached metadata for a video ID."""
        return self.metadata_cache.get(video_id)
    
    def _cache_metadata(self, video_id, metadata):
        """Cache metadata for a video ID."""
        self.metadata_cache[video_id] = metadata
        self._save_metadata_cache()
    
    def _load_url_cache(self):
        """Load URL cache from file."""
        if os.path.exists(self.url_cache_file):
            try:
                with open(self.url_cache_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return {}
        return {}
    
    def _save_url_cache(self):
        """Save URL cache to file."""
        try:
            with open(self.url_cache_file, 'w', encoding='utf-8') as f:
                json.dump(self.url_cache, f, indent=2)
        except Exception as e:
            print(f"Error saving URL cache: {e}")
    
    def preload_song_urls(self, video_ids):
        """Preload URLs for multiple songs in background."""
        def preload_worker():
            start_time = time.time()
            success_count = 0
            
            for video_id in video_ids[:5]:  # Limit to 5 songs
                if video_id not in self.url_cache:
                    result = self.get_fresh_stream_url(video_id, silent=True)
                    if result:
                        success_count += 1
                    time.sleep(0.5)  # Small delay between requests
            
            preload_time = time.time() - start_time
            perf_logger.log_preload_operation(video_ids[:5], preload_time, success_count)
        
        threading.Thread(target=preload_worker, daemon=True).start()
