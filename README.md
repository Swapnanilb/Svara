<p align=center>
   <img width="512" height="512" alt="Gemini_Generated_Image_794j8d794j8d794j" src="https://github.com/user-attachments/assets/5be11d9f-ddc6-4af2-876d-d2c415de1e77" />
</p>


# 🎵 Svara

A modern and easy-to-use **Python Music Player** with a user-friendly interface.  
Supports streaming music from **YouTube playlists and individual song links**, automatically adding loaded songs to your playlist. Perfect for personal use or as a base for further customization.

---

## 🚀 Features

- 🎧 **Play, Pause, Next, Previous** controls  
- 🔊 **Volume control** & **Mute**  
- 🔁 **Repeat** & 🔀 **Shuffle** options  
- 📂 **Load and manage playlists**  
- ▶️ **Play music directly from YouTube**  
- 🖼️ **Custom icons** for player controls  
- 🖥️ **Separate Load Music and Player UIs**  
- ⚡ **Smart URL Caching** for faster song loading  
- 🔄 **Load Tracks** button to pre-cache entire playlists  
- 🎵 **Enhanced Song Title Display** with artist and song names  
- 🔗 **Dynamic URL Fetching** - no more expired links  

---

## 📂 Project Structure
```
MUSIC-PLAYER/
├── components/                 # UI Components
│   ├── __init__.py
│   ├── control_panel.py        # Media controls with Load Tracks button
│   ├── now_playing_panel.py    # Current song display
│   ├── playlist_panel.py       # Playlist management panel
│   └── tracklist_panel.py      # Song list, search, and Load Tracks
│── icons/                      # Player icons (play, pause, next, etc.)
├── logic/                      # Logic Controllers
│   ├── __init__.py
│   ├── playback_controller.py  # Playback and audio control
│   ├── playlist_controller.py  # Playlist management
│   ├── progress_tracker.py     # Progress tracking  
│   ├── ui_controller.py        # UI state management
│   └── youtube_controller.py   # YouTube integration with caching
|── logo_animation.gif          # The splashscreen animation of the logo
├── utils/                      # Utilities
│   ├── __init__.py
│   ├── icon_loader.py          # Icon management
│   ├── image_utils.py          # Image processing
│   └── text_utils.py           # Enhanced text processing utilities
│── main.py                     # Entry point of the app
│── music_player_logic.py       # Logic for the app functions
│── music_player_ui.py          # User interface
│── player.py                   # Core player logic
│── playlist_manager.py         # Playlist handling with UTF-8 support
│── playlists.json              # Saved playlists (metadata only)
│── requirements.txt            # Python dependencies
│── youtube_streamer.py         # YouTube streaming with URL caching
│── README.md                   # Project documentation

```
---

## 🛠️ Installation & Setup

### 1. Clone the repository
```bash

git clone https://github.com/your-username/music-player.git
cd music-player

```

### 2. Create & activate a virtual environment
```bash

python -m venv venv

# On Windows
venv\Scripts\activate

# On Linux/Mac
source venv/bin/activate

```

### 3. Install dependencies
```bash

pip install -r requirements.txt

```

### 4. Run the application
```bash

python main.py

```

### 📦 Dependencies
* **customtkinter** — Modern UI framework
* **python-vlc** — Audio playback
* **yt-dlp** — YouTube streaming support
* **Pillow** — Image handling
* **pygame** — Additional audio support
* **pytube** — YouTube integration

You can install them via requirements.txt:
```bash

pip install -r requirements.txt

```

## ✨ New Features

### Smart Caching System
- **1-hour URL cache** prevents re-fetching stream URLs
- **Load Tracks button** pre-caches entire playlists for instant playback
- **Dynamic URL fetching** ensures songs never fail due to expired links

### Enhanced User Experience
- **Improved song titles** showing both artist and song names
- **Better scroll behavior** with proper bounds checking
- **Fixed UI states** for play/pause button accuracy
- **UTF-8 support** for international characters in song titles

## 🔧 Technical Improvements

- **Modular Architecture**: Clean separation between UI and logic
- **Error Handling**: Comprehensive error handling with user feedback
- **Performance**: Background processing and smart caching
- **Reliability**: No more expired URL issues
- **Compatibility**: UTF-8 encoding for international content

### 🤝 Contributing
Contributions are welcome!
1. Fork the repository
2. Create your feature branch:
   ```bash
   git checkout -b feature/YourFeature
   ```
3. Commit your changes:
   ```bash
   git commit -m 'Add some feature'
   ```
4. Push to the branch:
   ```bash
   git push origin feature/YourFeature
   ```
5. Open a Pull Request

---

## 📝 License

MIT License

Copyright (c) 2025 Swapnanil Basak & Piyush

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
