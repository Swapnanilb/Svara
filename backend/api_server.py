from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
import time
import atexit

from music_player_logic import MusicPlayerLogic
from performance_logger import perf_logger

app = FastAPI(title="Music Player API")

# Enable CORS for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request models
class PlayRequest(BaseModel):
    playlist_id: str
    song_index: int

class VolumeRequest(BaseModel):
    volume: float  # 0.0 to 1.0

class SeekRequest(BaseModel):
    position: float  # seconds

class PlaylistRequest(BaseModel):
    url: str

class AddSongRequest(BaseModel):
    url: str
    playlist_id: str | None = None
    playlist_name: str | None = None

class RefreshPlaylistRequest(BaseModel):
    playlist_id: str

class HeadlessUI:
    def __init__(self):
        self.current_song = None
        self.is_playing = False
        self.is_paused = False
        self.volume = 0.5
        self.position = 0
        self.duration = 0
        self.is_muted = False
        self.pre_mute_volume = 0.5
        
    def update_now_playing(self, song_info): self.current_song = song_info
    def update_play_button(self, is_playing): self.is_playing = is_playing
    def update_pause_button(self, is_paused): self.is_paused = is_paused
    def update_progress(self, position, duration=None): 
        self.position = position * 1000 if isinstance(position, (int, float)) else 0
        if duration: self.duration = duration
    def show_info(self, title, message): print(f"{title}: {message}")
    def show_loading(self, message): print(f"Loading: {message}")
    def hide_loading(self): pass
    def show_error(self, title, message): print(f"Error {title}: {message}")
    def show_add_song_dialog(self, song_info): print(f"Song ready: {song_info.get('title')}")
    def load_playlist_cards(self): pass
    def after(self, delay, callback): callback() if callable(callback) else None
    def update_playlist_card_colors(self, playlist_id): pass
    def update_tracklist(self, songs, filtered_songs=None): pass
    def update_selected_song(self, index): pass
    def clear_track_list(self): pass
    def create_song_widget(self, song): pass
    def reset_now_playing_view(self): pass
    def update_playlist_card_thumbnail(self, playlist_id): pass
    def update_now_playing_view(self, song, loading=False): self.current_song = song
    def update_play_pause_button(self): pass
    def highlight_current_song_widget(self): pass
    def update_shuffle_button(self, is_shuffled): pass
    def update_repeat_button(self, is_repeated): pass
    def update_mute_button(self, is_unmuted): pass
    def get_volume(self): return self.volume
    def set_volume(self, volume): self.volume = volume
    def set_progress(self, seconds): self.position = seconds * 1000

# Global instances
ui_handler = HeadlessUI()
logic = MusicPlayerLogic(ui_handler)

@app.get("/")
async def root():
    return {"message": "Music Player API Server"}

@app.get("/api/status")
async def get_status():
    """Get current player status"""
    # Get real-time position and duration from music player
    position = logic.music_player.get_pos() if logic.music_player else 0
    duration = logic.music_player.get_length() if logic.music_player else 0
    is_playing = logic.music_player.is_playing if logic.music_player else False
    is_paused = logic.music_player.is_paused if logic.music_player else False
    
    return {
        "current_song": ui_handler.current_song,
        "is_playing": is_playing,
        "is_paused": is_paused,
        "volume": ui_handler.volume,
        "position": position,
        "duration": duration,
        "current_playlist_id": logic.current_playlist_id,
        "current_song_index": logic.current_song_index,
        "is_muted": ui_handler.is_muted
    }

@app.get("/api/playlists")
async def get_playlists():
    start_time = time.time()
    result = {"playlists": logic.playlist_manager.get_all_playlists()}
    perf_logger.log_api_request("/api/playlists", "GET", time.time() - start_time)
    return result

@app.post("/api/play")
async def play_song(request: PlayRequest):
    logic.current_playlist_id = request.playlist_id
    logic.play_song_by_index(request.song_index)
    return {"message": "Playing"}

@app.post("/api/pause")
async def toggle_pause():
    logic.toggle_play_pause()
    return {"message": "Toggled"}

@app.post("/api/next")
async def next_song():
    logic.next_song()
    return {"message": "Next"}

@app.post("/api/previous")
async def previous_song():
    logic.prev_song()
    return {"message": "Previous"}

@app.post("/api/volume")
async def set_volume(request: VolumeRequest):
    logic.set_volume(request.volume)
    ui_handler.volume = request.volume
    return {"message": "Volume set"}

@app.post("/api/seek")
async def seek_position(request: SeekRequest):
    print(f"Seek request: {request.position} seconds")
    if logic.music_player and logic.music_player.is_playing:
        logic.music_player.set_pos(int(request.position * 1000))
        print(f"Seeked to: {request.position} seconds")
    return {"message": "Seeked"}

@app.post("/api/playlist/add")
async def add_playlist(request: PlaylistRequest):
    import threading
    import time
    
    # Check if playlist already exists by URL
    existing_playlist_id = logic.playlist_manager.get_playlist_by_url(request.url)
    if existing_playlist_id:
        return {"message": "Playlist already exists", "exists": True}
    
    # Create event to wait for completion
    add_complete = threading.Event()
    result_data = {"exists": False, "message": "Playlist added successfully"}
    
    # Override the update method to capture results
    original_update_method = logic.youtube_controller._update_existing_playlist
    original_create_method = logic.youtube_controller._create_new_playlist
    
    def capture_existing_update(playlist_id, playlist_name, songs, thumbnail):
        result_data["exists"] = True
        result_data["message"] = "Playlist already exists"
        add_complete.set()
        original_update_method(playlist_id, playlist_name, songs, thumbnail)
    
    def capture_new_create(playlist_name, songs, source_url, thumbnail):
        add_complete.set()
        original_create_method(playlist_name, songs, source_url, thumbnail)
    
    logic.youtube_controller._update_existing_playlist = capture_existing_update
    logic.youtube_controller._create_new_playlist = capture_new_create
    
    try:
        # Start the add process
        logic.add_from_link(request.url)
        
        # Wait for completion (max 15 seconds for faster response)
        if add_complete.wait(timeout=15):
            return result_data
        else:
            return {"message": "Playlist added successfully", "exists": False}
    finally:
        # Restore original methods
        logic.youtube_controller._update_existing_playlist = original_update_method
        logic.youtube_controller._create_new_playlist = original_create_method

@app.post("/api/playlist/{playlist_id}/refresh")
async def refresh_playlist(playlist_id: str):
    """Refresh an existing playlist from its YouTube source"""
    import threading
    import time
    
    start_time = time.time()
    
    if playlist_id not in logic.playlist_manager.playlists:
        raise HTTPException(status_code=404, detail="Playlist not found")
    
    playlist = logic.playlist_manager.playlists[playlist_id]
    source_url = playlist.get("source_url")
    
    if not source_url:
        raise HTTPException(status_code=400, detail="Playlist has no source URL to refresh from")
    
    # Store original song count
    original_songs = len(playlist.get("songs", []))
    
    # Create event to wait for completion
    refresh_complete = threading.Event()
    result_data = {"added": 0, "removed": 0}
    
    # Override the update method to capture results
    original_update_method = logic.youtube_controller._update_ui_after_playlist_sync
    
    def capture_results(pid, pname, added_ids, removed_ids):
        if pid == playlist_id:
            result_data["added"] = len(added_ids)
            result_data["removed"] = len(removed_ids)
            refresh_complete.set()
        original_update_method(pid, pname, added_ids, removed_ids)
    
    logic.youtube_controller._update_ui_after_playlist_sync = capture_results
    
    try:
        # Start the refresh
        logic.add_from_link(source_url)
        
        # Wait for completion (max 30 seconds)
        if refresh_complete.wait(timeout=30):
            refresh_time = time.time() - start_time
            total_songs = len(logic.playlist_manager.playlists[playlist_id].get("songs", []))
            
            perf_logger.log_playlist_refresh(
                playlist_id, result_data["added"], result_data["removed"], 
                total_songs, refresh_time
            )
            perf_logger.log_api_request(f"/api/playlist/{playlist_id}/refresh", "POST", refresh_time)
            
            return {
                "message": "Refresh completed",
                "added": result_data["added"],
                "removed": result_data["removed"],
                "total_songs": total_songs
            }
        else:
            raise HTTPException(status_code=408, detail="Refresh operation timed out")
    finally:
        # Restore original method
        logic.youtube_controller._update_ui_after_playlist_sync = original_update_method

@app.post("/api/song/check")
async def check_song_exists(request: AddSongRequest):
    import re
    
    print(f"Checking song: {request.url}")
    
    if "list=" in request.url:
        raise HTTPException(status_code=400, detail="Use /api/playlist/add for playlist URLs")
    
    # Extract video ID from URL without fetching full data
    video_id_match = re.search(r'(?:v=|/)([a-zA-Z0-9_-]{11})', request.url)
    if not video_id_match:
        raise HTTPException(status_code=400, detail="Invalid YouTube URL")
    
    video_id = video_id_match.group(1)
    print(f"Video ID: {video_id}")
    
    if request.playlist_id:
        existing_songs = logic.playlist_manager.get_songs(request.playlist_id)
        if any(song.get('id') == video_id for song in existing_songs):
            print("Song already exists")
            return {"exists": True, "message": "Song already exists in playlist"}
    
    print("Song does not exist")
    return {"exists": False}

@app.post("/api/song/add")
async def add_song(request: AddSongRequest):
    from youtube_streamer import YouTubeStreamer
    
    print(f"Adding song: {request.url}")
    
    if "list=" in request.url:
        raise HTTPException(status_code=400, detail="Use /api/playlist/add for playlist URLs")
    
    try:
        yt_streamer = YouTubeStreamer(None, None)
        print("Fetching song info...")
        song_info = yt_streamer.fetch_full_song_info(request.url)
        print(f"Song info fetched: {song_info}")
        
        if not song_info:
            raise HTTPException(status_code=400, detail="Could not fetch song information")
        
        if request.playlist_id:
            print(f"Adding to playlist: {request.playlist_id}")
            success = logic.add_song_to_playlist(request.playlist_id, song_info)
            if not success:
                raise HTTPException(status_code=404, detail="Playlist not found")
            return {"message": "Song added to playlist"}
        else:
            if not request.playlist_name:
                raise HTTPException(status_code=400, detail="Playlist name required for new playlist")
            
            print(f"Creating new playlist: {request.playlist_name}")
            playlist_id = logic.create_new_playlist_with_song(request.playlist_name, song_info)
            return {"message": "New playlist created with song", "playlist_id": playlist_id}
    except Exception as e:
        print(f"Error in add_song: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/playlist/{playlist_id}/songs")
async def get_playlist_songs(playlist_id: str):
    return {"songs": logic.playlist_manager.get_songs(playlist_id)}

@app.post("/api/shuffle")
async def toggle_shuffle():
    logic.toggle_shuffle()
    return {"message": "Shuffle toggled"}

@app.post("/api/repeat")
async def toggle_repeat():
    logic.toggle_repeat()
    return {"message": "Repeat toggled"}

@app.post("/api/mute")
async def toggle_mute():
    if ui_handler.is_muted:
        # Unmute: restore previous volume
        logic.set_volume(ui_handler.pre_mute_volume)
        ui_handler.volume = ui_handler.pre_mute_volume
        ui_handler.is_muted = False
    else:
        # Mute: save current volume and set to 0
        ui_handler.pre_mute_volume = ui_handler.volume
        logic.set_volume(0)
        ui_handler.volume = 0
        ui_handler.is_muted = True
    return {"message": "Mute toggled", "is_muted": ui_handler.is_muted}

@app.post("/api/playlist/load")
async def load_playlist(request: PlayRequest):
    """Load playlist without starting playback or updating now playing"""
    start_time = time.time()
    
    logic.current_playlist_id = request.playlist_id
    logic.current_song_index = request.song_index
    
    # Preload first few songs in background
    songs = logic.playlist_manager.get_songs(request.playlist_id)
    cached_songs = 0
    
    if songs:
        video_ids = [song.get('id') for song in songs[:5] if song.get('id')]
        if video_ids:
            # Count cached songs
            for video_id in video_ids:
                if video_id in logic.youtube_controller.yt_streamer.url_cache:
                    cached_songs += 1
            
            logic.youtube_controller.yt_streamer.preload_song_urls(video_ids)
    
    load_time = time.time() - start_time
    perf_logger.log_playlist_load(request.playlist_id, len(songs), load_time, cached_songs)
    perf_logger.log_api_request("/api/playlist/load", "POST", load_time)
    
    return {"message": "Playlist loaded"}

@app.post("/api/playlist/preload")
async def preload_playlist(request: PlayRequest):
    """Preload URLs for playlist songs"""
    songs = logic.playlist_manager.get_songs(request.playlist_id)
    if songs:
        video_ids = [song.get('id') for song in songs if song.get('id')]
        if video_ids:
            logic.youtube_controller.yt_streamer.preload_song_urls(video_ids)
    return {"message": "Preloading started"}

@app.post("/api/stop")
async def stop_playback():
    logic.stop_and_cleanup()
    return {"message": "Stopped"}

@app.delete("/api/playlist/{playlist_id}")
async def delete_playlist(playlist_id: str):
    """Delete a playlist"""
    if playlist_id not in logic.playlist_manager.playlists:
        raise HTTPException(status_code=404, detail="Playlist not found")
    
    logic.playlist_manager.remove_playlist(playlist_id)
    return {"message": "Playlist deleted"}

@app.get("/api/cache/stats")
async def get_cache_stats():
    """Get cache statistics"""
    import os
    import json
    
    url_cache_count = 0
    metadata_cache_count = 0
    
    # Count URL cache entries
    url_cache_file = "song_url_cache.json"
    if os.path.exists(url_cache_file):
        try:
            with open(url_cache_file, 'r') as f:
                url_cache = json.load(f)
                url_cache_count = len(url_cache)
        except:
            pass
    
    # Count metadata cache entries
    metadata_cache_file = "song_metadata_cache.json"
    if os.path.exists(metadata_cache_file):
        try:
            with open(metadata_cache_file, 'r') as f:
                metadata_cache = json.load(f)
                metadata_cache_count = len(metadata_cache)
        except:
            pass
    
    return {
        "url_cache_count": url_cache_count,
        "metadata_cache_count": metadata_cache_count
    }

@app.post("/api/cache/clear")
async def clear_cache():
    """Clear all cache files"""
    import os
    
    files_cleared = []
    
    # Clear URL cache
    url_cache_file = "song_url_cache.json"
    if os.path.exists(url_cache_file):
        os.remove(url_cache_file)
        files_cleared.append("URL cache")
    
    # Clear metadata cache
    metadata_cache_file = "song_metadata_cache.json"
    if os.path.exists(metadata_cache_file):
        os.remove(metadata_cache_file)
        files_cleared.append("Metadata cache")
    
    # Clear in-memory caches
    if hasattr(logic.youtube_controller.yt_streamer, 'url_cache'):
        logic.youtube_controller.yt_streamer.url_cache.clear()
    if hasattr(logic.youtube_controller.yt_streamer, 'metadata_cache'):
        logic.youtube_controller.yt_streamer.metadata_cache.clear()
    
    return {
        "message": "Cache cleared",
        "cleared": files_cleared
    }

# Register shutdown handler
def shutdown_handler():
    perf_logger.log_cache_stats()
    perf_logger.log_app_shutdown()

atexit.register(shutdown_handler)

if __name__ == "__main__":
    print("Starting Music Player API Server...")
    perf_logger.log_cache_stats()  # Log initial cache state
    uvicorn.run(app, host="127.0.0.1", port=5001, log_level="info")