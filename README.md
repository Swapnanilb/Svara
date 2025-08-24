# 🎵 Python Music Player

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

---

## 📂 Project Structure
```
MUSIC-PLAYER/
│── icons/ # Player icons (play, pause, next, etc.)
│── myVenv/ # Virtual environment (ignored in Git)
│── config.py # Configuration file
│── main.py # Entry point of the app
│── player.py # Core player logic
│── playlist_manager.py # Playlist handling
│── playlists.json # Saved playlists (ignored in Git)
│── requirements.txt # Python dependencies
│── ui.py # User interface
│── youtube_streamer.py # YouTube streaming support
│── README.md # Project documentation

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
* **vlc** — Audio playback
* **yt-dlp** — YouTube streaming support
* **tkinter** — User interface
* **Pillow** — Image handling

You can install them via requirements.txt:
```bash

pip install -r requirements.txt

```

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
