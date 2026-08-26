from PySide6.QtCore import QThread, Signal
from core.downloader import YouTubeDownloader


class InfoWorker(QThread):

    finished = Signal(list, dict)
    error = Signal(str)
    status = Signal(str)

    def __init__(self, url):
        super().__init__()
        self.url = url

    def run(self):
        try:
            self.status.emit("Checking YouTube...")
            downloader = YouTubeDownloader(
                self.url,
                "video",
                None
            )
            qualities, info = downloader.get_available_qualities()
            self.finished.emit(qualities, info)
        except Exception as e:
            self.error.emit(str(e))