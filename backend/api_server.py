from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

from music_player_logic import MusicPlayerLogic

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
    return {"playlists": logic.playlist_manager.get_all_playlists()}

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
    # Check if playlist already exists
    existing_playlist_id = logic.playlist_manager.get_playlist_by_url(request.url)
    if existing_playlist_id:
        return {"message": "Playlist already exists", "exists": True}
    
    logic.add_from_link(request.url)
    return {"message": "Added"}

@app.post("/api/song/check")
async def check_song_exists(request: AddSongRequest):
    import re
    
    if "list=" in request.url:
        raise HTTPException(status_code=400, detail="Use /api/playlist/add for playlist URLs")
    
    # Extract video ID from URL without fetching full data
    video_id_match = re.search(r'(?:v=|/)([a-zA-Z0-9_-]{11})', request.url)
    if not video_id_match:
        raise HTTPException(status_code=400, detail="Invalid YouTube URL")
    
    video_id = video_id_match.group(1)
    
    if request.playlist_id:
        existing_songs = logic.playlist_manager.get_songs(request.playlist_id)
        if any(song.get('id') == video_id for song in existing_songs):
            return {"exists": True, "message": "Song already exists in playlist"}
    
    return {"exists": False}

@app.post("/api/song/add")
async def add_song(request: AddSongRequest):
    from youtube_streamer import YouTubeStreamer
    
    if "list=" in request.url:
        raise HTTPException(status_code=400, detail="Use /api/playlist/add for playlist URLs")
    
    yt_streamer = YouTubeStreamer(None, None)
    song_info = yt_streamer.fetch_full_song_info(request.url)
    
    if not song_info:
        raise HTTPException(status_code=400, detail="Could not fetch song information")
    
    if request.playlist_id:
        success = logic.add_song_to_playlist(request.playlist_id, song_info)
        if not success:
            raise HTTPException(status_code=404, detail="Playlist not found")
        return {"message": "Song added to playlist"}
    else:
        if not request.playlist_name:
            raise HTTPException(status_code=400, detail="Playlist name required for new playlist")
        
        playlist_id = logic.create_new_playlist_with_song(request.playlist_name, song_info)
        return {"message": "New playlist created with song", "playlist_id": playlist_id}

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
    logic.current_playlist_id = request.playlist_id
    logic.current_song_index = request.song_index
    
    return {"message": "Playlist loaded"}

@app.post("/api/stop")
async def stop_playback():
    logic.stop_and_cleanup()
    return {"message": "Stopped"}

if __name__ == "__main__":
    print("Starting Music Player API Server...")
    uvicorn.run(app, host="127.0.0.1", port=5001, log_level="info")