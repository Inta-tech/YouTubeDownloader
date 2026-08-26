from PySide6.QtCore import QThread, Signal
from core.downloader import (
    YouTubeDownloader,
    DownloadPaused,
    DownloadCancelled
)


class DownloadWorker(QThread):

    progress = Signal(float)
    status = Signal(str)
    finished = Signal(str, str)
    error = Signal(str)
    paused = Signal()
    cancelled = Signal()

    def __init__(self, url, mode, quality):
        super().__init__()
        self.url = url
        self.mode = mode
        self.quality = quality
        self.downloader = None

    def run(self):
        try:
            self.downloader = YouTubeDownloader(
                self.url,
                self.mode,
                self.quality,
                progress_callback=self.progress.emit,
                status_callback=self.status.emit
            )

            file_path, actual_quality = self.downloader.download()
            self.finished.emit(file_path, actual_quality)

        except DownloadPaused:
            self.paused.emit()

        except DownloadCancelled:
            if self.downloader:
                self.downloader.cleanup_partial_files()
            self.cancelled.emit()

        except Exception as e:
            self.error.emit(str(e))

        finally:
            self.downloader = None

    def pause_download(self):
        if self.downloader:
            self.downloader.request_pause()

    def cancel_download(self):
        if self.downloader:
            self.downloader.request_cancel()