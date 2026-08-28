# YouTube Downloader

A modern desktop application built with Python and PySide6 that allows users to fetch, preview, and download YouTube videos or extract high-quality audio tracks. Features direct browser integration via custom protocol handlers, dynamic resolution selection, and background multi-threading for a responsive UI.

---

## Features

* **Modern Dark UI:** Responsive interface with custom Windows title bar styling and status feedback.
* **Video & Audio Downloads:** Download full MP4 videos in resolution up to 4K or extract MP3 audio files.
* **Format Selection:** Automatically queries YouTube to fetch available resolution options before downloading.
* **Browser Integration:** Supports custom protocol scheme (`ytdl://`) for direct links from one-click browser bookmarklets.
* **Multi-Threaded Processing:** Download and media information fetching run on background threads to keep the interface smooth.
* **Download Controls:** Real-time progress tracking with pause and cancel capabilities.

---

## Project Structure

```text
YouTubeDownloader/
│
├── main.py                     # Primary Application Entry Point
├── ui/
│   └── main_window.py          # PySide6 GUI Window & Theme Layout
├── core/
│   └── downloader.py          # yt-dlp & FFmpeg Download Engine
├── workers/
│   ├── info_worker.py          # Background Thread for Quality Fetching
│   └── download_worker.py      # Background Thread for Download Management
├── utils/
│   └── paths.py                # System Directory & Output Path Handlers
├── requirements.txt            # Project Python Dependencies
├── .gitignore                  # Git Version Control Exclusions
└── README.md                   # Project Documentation

```

---

## Requirements & Prerequisites

* **Python:** 3.10 or higher
* **FFmpeg:** `ffmpeg.exe` and `ffprobe.exe` placed in the project root folder (required for video/audio processing).

---

## Installation & Setup

1. **Clone the repository:**
```bash
git clone https://github.com/Inta-tech/YouTubeDownloader.git
cd YouTubeDownloader

```


2. **Set up a virtual environment:**
```bash
python -m venv .venv
.venv\Scripts\activate

```


3. **Install dependencies:**
```bash
pip install -r requirements.txt

```


4. **Add FFmpeg binaries:**
Place `ffmpeg.exe` and `ffprobe.exe` into the project root directory.

---

## Usage

1. **Run the Application:**
```bash
python main.py

```


2. **Download Media:**
* Paste a YouTube URL into the input field.
* Select **VIDEO** or **AUDIO** mode.
* For video mode, click **Check Available Qualities** to load stream options, select your preferred resolution, and click **Download**.



---

## Building Standalone Executable

To compile a single executable file using PyInstaller:

```bash
pyinstaller --noconsole --onefile --add-binary "ffmpeg.exe;." --add-binary "ffprobe.exe;." --name="YouTubeDownloader" main.py

```

The generated executable will be saved in the `dist/` directory.

---

Developed by Intasar Mostafiz
