import sys
import re
from PySide6.QtWidgets import QApplication

from ui.main_window import DownloaderWindow
from utils.paths import create_download_directories


def clean_url(raw_arg):
    if not raw_arg:
        return None

    # Remove protocol prefix if present
    url = raw_arg.replace("ytdl://", "").replace("ytdl:", "")

    # Strip out quote characters, spaces, and percent artifacts
    url = url.replace("'", "").replace('"', "").replace("%1", "").strip()

    # Extract clean http/https URL matching standard YouTube links
    match = re.search(r'https?://[^\s\'"]+', url)
    if match:
        url = match.group(0)

    return url


def main():
    create_download_directories()

    app = QApplication(sys.argv)

    initial_url = None
    if len(sys.argv) > 1:
        initial_url = clean_url(sys.argv[1])

    window = DownloaderWindow(initial_url=initial_url)
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()