# PyMu6 (an Youtube-based Music App)

<img width="1920" height="1020" alt="Screenshot 2025-07-22 231621" src="https://github.com/user-attachments/assets/b2a75c31-3e2a-434c-892b-f04d0ee4065c" />

PyMu6 is a modern, vibe-coded, and visually refreshed music player desktop app built with Python and Tkinter. It is a complete revamp of an older project that used the now-deprecated `youtube_dl`—now upgraded to use `yt-dlp` for better YouTube streaming support.

## Features

- 🎵 **Search and Play Music from YouTube**  
  Instantly search for any song or video on YouTube and stream its audio directly in the app.

- ❤️ **Liked Songs Sidebar**  
  Save your favorite tracks to a persistent "Liked Songs" list for quick access.

- ⏯️ **Playback Controls**  
  Play, pause, stop, and seek within tracks. See current and total time.

- 🔊 **Volume Control**  
  Adjust playback volume with a stylish slider.

- 🖼️ **Modern UI**  
  Spotify-inspired dark theme with custom icons and smooth title animations.

- 📂 **Persistent Storage**  
  Liked songs are saved in a CSV file and loaded automatically on startup.

- 🌐 **Internet Connectivity Check**  
  Warns you if you are offline.

## Requirements

- **Python 3.7+**
- **VLC Media Player**  
  You must have [VLC Media Player](https://www.videolan.org/vlc/) installed on your system.

### Python Libraries

Install these with pip:

```sh
pip install pandas python-vlc yt-dlp requests
```

- `tkinter` (comes with most Python installations)
- `pandas`
- `python-vlc`
- `yt-dlp`
- `requests`

## Assets

All required images are in the `assets/` folder:
- PyMu6.png
- heart (1).png
- Liked Songs.png
- smolmic.png

## Usage

1. **Install VLC Media Player** if you haven't already.
2. **Install Python dependencies** as shown above.
3. **Run the app:**

   ```sh
   python pymusic_app_final.py
   ```

4. **Search for music** using the search bar, play tracks, and add them to your liked songs!

## File Structure

```
pymusic_app_final.py
LikedSongs1.csv
assets/
    heart (1).png
    Liked Songs.png
    PyMu6.png
    smolmic.png
```

- `pymusic_app_final.py`: Main application code.
- `LikedSongs1.csv`: Stores your liked songs.
- `assets/`: Contains all UI images.

## Notes

- The app streams audio directly from YouTube using `yt-dlp` and VLC.
- Make sure your internet connection is active for searching and streaming.
- The UI is designed for a modern, minimal, and "vibe" experience.

---

Enjoy your music with PyMu6!  
Feel free to
