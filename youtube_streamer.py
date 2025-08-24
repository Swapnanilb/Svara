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
        }
        
    def get_playlist_info(self, url):
        threading.Thread(target=self._fetch_playlist_data, args=(url,), daemon=True).start()

    def get_stream_info_for_id(self, video_id):
        url = f"https://www.youtube.com/watch?v={video_id}"
        threading.Thread(target=self._fetch_single_song_data, args=(url,), daemon=True).start()

    def _extract_video_id(self, url):
        """Extracts the video ID from a YouTube URL."""
        match = re.search(r'(?<=v=)[^&#]+', url)
        if match:
            return match.group(0)
        return None

    def _fetch_playlist_data(self, url):
        try:
            with yt.YoutubeDL(self.ydl_opts) as ydl:
                info_dict = ydl.extract_info(url, download=False)
                
                if '_type' in info_dict and info_dict['_type'] == 'playlist':
                    playlist_info = {
                        'title': info_dict.get('title', 'Unknown Playlist'),
                        'thumbnail_url': info_dict.get('thumbnail'),
                        'youtube_id': info_dict.get('id'), # Added unique playlist ID
                        'entries': []
                    }
                    for entry in info_dict['entries']:
                        if entry:
                            song_info = {
                                "title": entry.get('title', 'Unknown Title'),
                                "id": entry.get('id', 'Unknown ID'),
                                "duration": entry.get('duration', 0),
                                "thumbnail_url": entry.get('thumbnail'),
                                "url": entry.get('url')
                            }
                            playlist_info['entries'].append(song_info)
                    self.on_playlist_info_fetched(playlist_info)
                else:
                    self._fetch_single_song_data(url)

        except yt.DownloadError as e:
            print(f"Error fetching playlist info: {e}")
            self.on_playlist_info_fetched(None)

    def _fetch_single_song_data(self, url):
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

        self.on_single_song_info_fetched(full_song_info)