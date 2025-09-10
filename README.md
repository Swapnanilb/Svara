<p align="center">
  <img src="./frontend/public/svara_logo.png" alt="Logo" width="200"/>
</p>


# SVARA Music Player - Modern YouTube Music Player

A modern, feature-rich music player built with React, Python, and Electron that streams music from YouTube with a beautiful, responsive interface. Transformed from a Python-only desktop application to a modern cross-platform solution with web-based UI and API-first architecture.

## ✨ Features

### 🎵 Core Music Features
- **YouTube Integration**: Stream music directly from YouTube playlists and individual songs
- **Playlist Management**: Create, organize, and manage multiple playlists
- **Advanced Playback Controls**: Play, pause, skip, shuffle, repeat, and seek
- **Volume Control**: Adjustable volume with mute/unmute functionality
- **Real-time Progress**: Live progress tracking with seek functionality

### 🎨 Modern UI/UX
- **Dual Theme Support**: Light and dark themes with persistent preference
- **Glassmorphism Design**: Modern glass-effect styling with smooth animations
- **Responsive Layout**: Three-view navigation (Home, Playlists, Songs)
- **Interactive Elements**: Hover effects, smooth transitions, and visual feedback
- **SVG Icons**: Clean, scalable icons throughout the interface

### 🔄 Smart Playlist Features
- **Auto-Sync**: Refresh playlists to sync with YouTube changes
- **Duplicate Detection**: Prevents duplicate songs and playlists
- **Single Song Support**: Add individual songs with playlist selection
- **Thumbnail Support**: Automatic thumbnail fetching and display

### ⚡ Performance & UX
- **Loading States**: Visual feedback for all operations with loading overlays
- **Error Handling**: Graceful error handling with user notifications
- **Optimized Refresh**: Smart sync that only checks for added/deleted songs
- **Persistent State**: Remembers theme preference and player state
- **Cross-Platform**: Runs as web app, desktop app, or Electron distribution
- **Performance Monitoring**: Real-time metrics tracking for optimization
- **Smart Caching**: Intelligent caching system with hit rate monitoring

## 🏗️ Project Structure
```
music-player-app/
├── backend/                        # Python API Server
│   ├── api_server.py               # FastAPI server with all endpoints
│   ├── music_player_logic.py       # Core music player logic
│   ├── logic/                      # Modular controller architecture
│   │   ├── playback_controller.py  # Playback control logic
│   │   ├── playlist_controller.py  # Playlist management
│   │   ├── progress_tracker.py     # Progress tracking system
│   │   ├── youtube_controller.py   # YouTube integration
│   │   └── ui_controller.py        # UI state management
│   ├── utils/                      # Utility modules
│   │   └── text_utils.py           # Text processing utilities
│   ├── player.py                   # VLC media player integration
│   ├── playlist_manager.py         # Playlist data management
│   ├── youtube_streamer.py         # YouTube API integration
│   ├── performance_logger.py       # Performance monitoring system
│   └── requirements.txt            # Python dependencies
├── frontend/                       # React Application
│   ├── src/
│   │   ├── components/             # React components
│   │   │   ├── PlayerControls.js
│   │   │   ├── PlaylistView.js
│   │   │   ├── HomeView.js
│   │   │   ├── SongsView.js
│   │   │   └── SettingsView.js
│   │   ├── services/               # API service layer
│   │   │   └── api.js
│   │   ├── App.js                  # Main application
│   │   └── spotify-player.css      # Modern styling
│   └── package.json
├── electron/                       # Electron Desktop Wrapper
│   ├── main.js                     # Electron main process
│   ├── preload.js                  # Preload script for security
│   └── package.json                # Electron configuration
├── build.py                        # Build automation script
├── run-dev.bat                     # Development environment startup
└── start-backend.bat               # Backend-only startup script
```

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- Node.js 16+
- VLC Media Player installed

### Quick Development Start
```bash
# Windows - Start full development environment
run-dev.bat

# Or start backend only
start-backend.bat
```

### 1. Backend Setup
```bash
cd backend
pip install -r requirements.txt
python api_server.py
```

### 2. Frontend Setup
```bash
cd frontend
npm install
npm start
```

### 3. Electron (Optional)
```bash
cd electron
npm install
npm run dev
```

## 📡 API Endpoints

### Player Control
- `GET /api/status` - Get current player status
- `POST /api/play` - Play song by playlist ID and index
- `POST /api/pause` - Toggle play/pause
- `POST /api/next` - Skip to next song
- `POST /api/previous` - Go to previous song
- `POST /api/volume` - Set volume (0.0-1.0)
- `POST /api/seek` - Seek to position in seconds
- `POST /api/mute` - Toggle mute/unmute

### Playlist Management
- `GET /api/playlists` - Get all playlists
- `GET /api/playlist/{id}/songs` - Get songs in playlist
- `POST /api/playlist/add` - Add YouTube playlist
- `POST /api/playlist/load` - Load playlist without playing

### Song Management
- `POST /api/song/check` - Check if song exists
- `POST /api/song/add` - Add individual song

## 🎯 Usage Guide

### Adding Content
1. **YouTube Playlists**: Paste playlist URL in Home view
2. **Individual Songs**: Paste song URL and select target playlist
3. **Auto-Detection**: App automatically detects playlist vs. song URLs

### Navigation
- **Home**: Add new content (playlists/songs)
- **Playlists**: Browse and manage your playlists
- **Songs**: View current playlist tracklist
- **Settings**: Toggle theme and app preferences

### Playback Controls
- Click playlist cards to load them
- Use play buttons to start playback
- Volume icon click for mute/unmute
- Progress bar for seeking
- Shuffle and repeat modes available

### Playlist Refresh
- Global refresh button in Playlists view
- Individual refresh buttons on each playlist card
- Syncs with YouTube to detect added/removed songs

## 🛠️ Development

### Building for Production
```bash
# Build all components
python build.py

# Or build specific components
python build.py --backend
python build.py --frontend
python build.py --electron
```

### Architecture Notes
- **Platform Migration**: Evolved from Python-only to modern Electron-based architecture
- **Frontend Modernization**: Replaced Python GUI (tkinter) with React-based interface
- **Modular Backend**: Controller-based architecture for maintainability
- **React Hooks**: Modern React patterns with functional components
- **API-First Design**: Clean separation between FastAPI backend and React frontend
- **Theme System**: CSS custom properties for dynamic theming
- **Cross-Platform Support**: Deployable as web app, desktop app, or Electron distribution
- **Performance Monitoring**: Built-in metrics tracking and performance analysis
- **Thread Management**: Safe progress tracking with proper cleanup
- **Utility Architecture**: Modular utilities for text processing and system monitoring

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📄 License

MIT License - see LICENSE file for details

## 🙏 Acknowledgments

- VLC Media Player for audio playback
- YouTube for music streaming
- React and Electron communities
- FastAPI for the robust backend framework