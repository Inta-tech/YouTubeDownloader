import os
import re
import subprocess
import yt_dlp

from utils.paths import (
    VIDEO_DIR,
    AUDIO_DIR
)


class DownloadPaused(Exception):
    """Raised internally when the user pauses a download."""
    pass


class DownloadCancelled(Exception):
    """Raised internally when the user cancels a download."""
    pass


class YouTubeDownloader:

    def __init__(
        self,
        url,
        mode,
        quality,
        progress_callback=None,
        status_callback=None
    ):
        self.url = self.clean_youtube_url(url)
        self.mode = mode
        self.quality = quality

        self.progress_callback = progress_callback
        self.status_callback = status_callback

        self.pause_requested = False
        self.cancel_requested = False
        self.active_filename = None

    @staticmethod
    def clean_youtube_url(raw_url):
        if not raw_url:
            return ""

        # Strip prefixes, quotes, and whitespace
        clean = (
            raw_url.replace("ytdl://", "")
            .replace("ytdl:", "")
            .replace("'", "")
            .replace('"', "")
            .replace("%1", "")
            .strip()
        )

        # Extract standard 11-character YouTube video ID
        match = re.search(r'(?:v=|\/|be\/|embed\/)([a-zA-Z0-9_-]{11})', clean)
        if match:
            return f"https://www.youtube.com/watch?v={match.group(1)}"

        return clean

    def request_pause(self):
        self.pause_requested = True

    def request_cancel(self):
        self.cancel_requested = True

    def check_control(self):
        if self.cancel_requested:
            raise DownloadCancelled()
        if self.pause_requested:
            raise DownloadPaused()

    def progress_hook(self, data):
        self.check_control()

        filename = data.get("filename")
        if filename:
            self.active_filename = filename

        if data["status"] == "downloading":
            downloaded = data.get("downloaded_bytes", 0)
            total = (
                data.get("total_bytes")
                or data.get("total_bytes_estimate")
                or 0
            )

            if total:
                percent = (downloaded / total) * 100
                if self.progress_callback:
                    self.progress_callback(percent)

            speed = data.get("_speed_str", "")
            eta = data.get("_eta_str", "")

            if self.status_callback:
                self.status_callback(
                    f"Downloading  •  {speed}  •  ETA {eta}"
                )

        elif data["status"] == "finished":
            if self.progress_callback:
                self.progress_callback(100)

            if self.status_callback:
                self.status_callback("Processing with FFmpeg...")

            self.check_control()

    def get_available_qualities(self):
        options = {
            "quiet": True,
            "no_warnings": True
        }

        with yt_dlp.YoutubeDL(options) as ydl:
            info = ydl.extract_info(
                self.url,
                download=False
            )

        qualities = set()
        standard_qualities = {
            144, 240, 360, 480, 720, 1080, 1440, 2160
        }

        for fmt in info.get("formats", []):
            height = fmt.get("height")
            vcodec = fmt.get("vcodec")

            if (
                height
                and vcodec
                and vcodec != "none"
                and height in standard_qualities
            ):
                qualities.add(height)

        return (
            sorted(qualities, reverse=True),
            info
        )

    def download_video(self):
        options = {
            "format": (
                f"bestvideo[height<={self.quality}]"
                f"+bestaudio/"
                f"best[height<={self.quality}]"
            ),
            "merge_output_format": "mp4",
            "outtmpl": os.path.join(
                VIDEO_DIR,
                "%(title)s.%(ext)s"
            ),
            "noplaylist": True,
            "continuedl": True,
            "nopart": False,
            "progress_hooks": [self.progress_hook]
        }

        with yt_dlp.YoutubeDL(options) as ydl:
            self.check_control()
            info = ydl.extract_info(
                self.url,
                download=True
            )
            self.check_control()
            filename = ydl.prepare_filename(info)

        base_name = os.path.splitext(filename)[0]
        final_file = base_name + ".mp4"
        actual_quality = self.get_actual_video_quality(final_file)

        return final_file, actual_quality

    def download_audio(self):
        options = {
            "format": "bestaudio/best",
            "outtmpl": os.path.join(
                AUDIO_DIR,
                "%(title)s.%(ext)s"
            ),
            "noplaylist": True,
            "continuedl": True,
            "nopart": False,
            "progress_hooks": [self.progress_hook],
            "postprocessors": [
                {
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                    "preferredquality": self.quality
                }
            ]
        }

        with yt_dlp.YoutubeDL(options) as ydl:
            self.check_control()
            info = ydl.extract_info(
                self.url,
                download=True
            )
            self.check_control()
            filename = ydl.prepare_filename(info)

        base_name = os.path.splitext(filename)[0]
        final_file = base_name + ".mp3"

        return final_file, f"{self.quality} kbps"

    def get_actual_video_quality(self, file_path):
        try:
            command = [
                "ffprobe",
                "-v", "error",
                "-select_streams", "v:0",
                "-show_entries", "stream=width,height",
                "-of", "csv=s=x:p=0",
                file_path
            ]
            resolution = subprocess.check_output(
                command,
                text=True
            ).strip()

            width, height = resolution.split("x")
            return f"{height}p"
        except Exception:
            return "Unknown"

    def cleanup_partial_files(self):
        filename = self.active_filename
        if not filename:
            return

        possible_files = [
            filename,
            filename + ".part",
            filename + ".ytdl",
            filename + ".temp"
        ]

        for file_path in possible_files:
            try:
                if os.path.exists(file_path):
                    os.remove(file_path)
            except OSError:
                pass

        directory = os.path.dirname(filename)
        basename = os.path.basename(filename)

        if os.path.exists(directory):
            try:
                for name in os.listdir(directory):
                    if name.startswith(basename) and (
                        name.endswith(".part")
                        or name.endswith(".ytdl")
                        or name.endswith(".temp")
                    ):
                        try:
                            os.remove(os.path.join(directory, name))
                        except OSError:
                            pass
            except OSError:
                pass

        self.active_filename = None

    def download(self):
        if self.mode == "video":
            return self.download_video()
        return self.download_audio()