import os
import re

def get_clean_youtube_url(raw_url: str) -> str:
    if not raw_url:
        return ""

    # Clean protocol prefixes, quotes, and whitespace
    clean = (
        raw_url.replace("ytdl://", "")
        .replace("ytdl:", "")
        .replace("'", "")
        .replace('"', "")
        .replace("%1", "")
        .strip()
    )

    # Regex to extract the 11-character YouTube video ID
    match = re.search(r'(?:v=|\/|be\/|embed\/)([a-zA-Z0-9_-]{11})', clean)
    if match:
        video_id = match.group(1)
        return f"https://www.youtube.com/watch?v={video_id}"

    return clean

DOWNLOAD_DIR = os.path.join(
    os.path.expanduser("~"),
    "Downloads"
)

VIDEO_DIR = os.path.join(
    DOWNLOAD_DIR,
    "Videos"
)

AUDIO_DIR = os.path.join(
    DOWNLOAD_DIR,
    "Audio"
)


def create_download_directories():
    os.makedirs(
        VIDEO_DIR,
        exist_ok=True
    )
    os.makedirs(
        AUDIO_DIR,
        exist_ok=True
    )