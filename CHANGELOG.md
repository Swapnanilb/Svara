# Changelog

All notable changes to SVARA Music Player will be documented in this file.

## [1.5.0](https://github.com/Swapnanilb/Svara/releases/tag/v1.5.0) - 2025-09-25

### 🚀 Real-Time Progress Tracking
- **WebSocket Integration**: Added real-time progress updates during playlist processing
- **Live Progress Bar**: Shows "Processing X/Y songs" with current song title
- **Background Processing**: Continue using app while songs load in background
- **Tab-Friendly Loading**: Loading overlay only in Home view, free navigation between tabs
- **Progress Persistence**: Switch tabs and return to see current progress

### 🔧 Technical Improvements
- **WebSocket Server**: Added `/ws` endpoint for bi-directional communication
- **ProgressWebSocket Class**: Frontend WebSocket client for real-time updates
- **Enhanced YouTube Controller**: Progress callbacks with thread-safe event loops
- **Global State Management**: Loading state persists across navigation
- **Improved yt-dlp**: Updated to latest version with better format handling

### 🎨 UI/UX Enhancements
- **Smart Loading Dialog**: Centered positioning for both light and dark themes
- **Non-Blocking Interface**: Access all tabs while content loads
- **Visual Progress Feedback**: Real-time song processing updates
- **Consistent Theming**: Fixed loading dialog styling across themes
- **Input Visibility**: Improved text contrast in input fields

### 🐛 Bug Fixes
- Fixed loading state disappearing when switching tabs
- Resolved asyncio event loop errors in background threads
- Fixed dialog centering issues in different themes
- Improved input text visibility in light mode
- Enhanced WebSocket connection stability

## [1.0.0](https://github.com/Swapnanilb/Svara/releases/tag/v1.0.0) - 2025-09-20

### 🛠️ Technical Architecture Transformation
- **Complete Platform Migration**: Transition from Python-only desktop app to modern Electron-based architecture
- **Frontend Modernization**: Replace Python GUI (tkinter) with React-based web interface
- **API-First Design**: Convert monolithic Python app to FastAPI backend + React frontend architecture
- **Cross-Platform Support**: Enable deployment as web app, desktop app, or Electron distribution
- **Modular Backend**: Refactored with controller-based design for maintainability
- **New API Endpoints**: Added /api/mute, /api/playlist/load, /api/song/check, /api/song/add
- **React State Management**: Implemented hooks-based state management
- **CSS Architecture**: Comprehensive styling with theme variables and responsive design
- **Component Organization**: Structured components with proper separation of concerns

### 🔧 Technical Infrastructure
- **Modular Architecture**: New `utils/` directory with text processing utilities
- **Progress Controller**: Dedicated `progress_tracker.py` for smooth playback progress
- **Performance Logger**: Comprehensive logging system with JSON output and readable format
- **Thread Safety**: Proper threading with cleanup and resource management
- **Error Resilience**: Graceful handling of performance logging failures

### 🛠️ Development Experience
- **Automated Startup**: `run-dev.bat` for complete development environment setup
- **Backend Testing**: `start-backend.bat` for isolated backend development
- **Process Management**: Automatic cleanup of existing processes before startup
- **Build Automation**: Enhanced `build.py` with component-specific build options
- **Performance Analysis**: Built-in log viewer and metrics analysis tools

### 🎨 Major UI/UX Overhaul
- **Modern Design System**: Complete redesign with glassmorphism effects and smooth animations
- **Dual Theme Support**: Light and dark themes with persistent localStorage preference
- **Responsive Navigation**: Three-view layout (Home, Playlists, Songs, Settings) with sidebar navigation
- **SVG Icon System**: Replaced emoji icons with scalable SVG icons for better visibility
- **Interactive Elements**: Enhanced hover effects, transitions, and visual feedback
- **Card-Based Layout**: Responsive playlist cards with thumbnails and modern styling

### 🎵 Enhanced Music Features
- **Volume Icon Mute**: Click volume icon to toggle mute/unmute with visual state indicators
- **Advanced Player Controls**: Improved playback controls with orange progress fills
- **Smart Playlist Loading**: Click playlists to load without auto-playing, separate play buttons
- **Real-time Status**: Enhanced status tracking with better synchronization
- **Improved Sliders**: Orange progress fills for volume and seek sliders
- **Advanced Progress Tracking**: Threaded progress updates with smooth seeking and drag controls
- **Smart Text Processing**: Automatic song title cleaning and formatting utilities
- **Thread-Safe Operations**: Proper progress tracking cleanup and resource management
- **Improved Seeking**: Preview progress during drag with commit-on-release functionality

### 🔄 Playlist Management System
- **Playlist Refresh System**: Global and individual playlist refresh with loading screens
- **Smart Sync**: Optimized refresh that only checks for added/deleted songs
- **Duplicate Prevention**: Comprehensive duplicate detection for songs and playlists
- **Single Song Support**: Add individual YouTube songs with playlist selection dialog
- **URL Validation**: Proper YouTube URL validation and loading states

### ⚡ Performance & UX Enhancements
- **Loading States**: Comprehensive loading overlays and spinners for all async operations
- **Error Handling**: Improved error messages and graceful failure handling
- **Persistent State**: Theme preferences and player state survive app restarts
- **Optimized Animations**: Reduced heavy animations for better performance
- **Volume Slider Fixes**: Corrected jumping and visibility issues
- **Performance Monitoring**: Real-time tracking of playlist loads, song loads, and cache operations
- **Session Analytics**: Complete session tracking with startup/shutdown logging
- **Cache Performance**: Hit rate monitoring and efficiency metrics for optimization
- **API Monitoring**: Response time tracking with status indicators and performance analysis
- **Colored Logging**: Human-readable log format with performance indicators and emoji status

### 📈 Performance Optimizations
- **Cache Analytics**: Detailed cache hit/miss tracking for optimization insights
- **Load Time Monitoring**: Track and optimize playlist and song loading performance
- **Memory Management**: Efficient progress tracking with minimal resource usage
- **Preload Operations**: Smart preloading with success rate tracking
- **API Efficiency**: Request timing and optimization metrics

### 🐛 Bug Fixes & Improvements
- Fixed playlist refresh loading screen positioning and centering
- Resolved theme persistence issues across app restarts
- Fixed horizontal scrollbar during loading screens
- Corrected volume slider local state management
- Improved URL validation for YouTube links
- Fixed loading overlay viewport centering
- Fixed progress tracking thread cleanup on application shutdown
- Improved seeking accuracy with proper position validation
- Enhanced error handling in performance logging system
- Optimized progress update frequency for better performance
- Fixed potential memory leaks in threaded operations

### 📱 User Experience
- **Intuitive Navigation**: Clear visual hierarchy and navigation patterns
- **Visual Feedback**: Loading spinners, success states, and progress indicators
- **Accessibility**: Better contrast ratios and interactive element sizing
- **Responsive Design**: Optimized for different screen sizes and resolutions
- **Smooth Transitions**: Enhanced animations throughout interface

### 📝 Documentation & Development
- **Comprehensive Documentation**: Updated README.md with full feature documentation
- **Version History**: Detailed CHANGELOG.md with complete version tracking
- **Project Configuration**: Proper .gitignore for Python, Node.js, and Electron projects
- **API Documentation**: Complete endpoint documentation and usage patterns
- **Component Organization**: Logical frontend module structure
- **Theme System**: CSS custom properties for dynamic theming
- **Automated Startup**: `run-dev.bat` for complete development environment setup
- **Backend Testing**: `start-backend.bat` for isolated backend development
- **Process Management**: Automatic cleanup of existing processes before startup
- **Build Automation**: Enhanced `build.py` with component-specific build options
- **Performance Analysis**: Built-in log viewer and metrics analysis tools

## [0.0.1] - 2025-08-24

### Initial Release
- Basic YouTube music streaming functionality
- Simple playlist management
- VLC media player integration
- React frontend with Electron wrapper
- FastAPI backend server
- Basic playback controls (play, pause, skip)
- Volume control and seeking
- YouTube playlist import