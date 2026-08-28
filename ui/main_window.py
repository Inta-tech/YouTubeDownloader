import os
import re
import ctypes

from PySide6.QtWidgets import (
    QWidget,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QHBoxLayout,
    QLineEdit,
    QMessageBox,
    QComboBox,
    QProgressBar,
    QFrame,
    QSizePolicy
)
from PySide6.QtCore import Qt

from workers.download_worker import DownloadWorker
from workers.info_worker import InfoWorker
from utils.paths import DOWNLOAD_DIR


def get_clean_youtube_url(raw_url: str) -> str:
    if not raw_url:
        return ""

    clean = (
        raw_url.replace("ytdl://", "")
        .replace("ytdl:", "")
        .replace("'", "")
        .replace('"', "")
        .replace("%1", "")
        .strip()
    )

    match = re.search(r'(?:v=|\/|be\/|embed\/)([a-zA-Z0-9_-]{11})', clean)
    if match:
        return f"https://www.youtube.com/watch?v={match.group(1)}"

    return clean


class DownloaderWindow(QWidget):

    def __init__(self, initial_url=None):
        super().__init__()

        self.worker = None
        self.info_worker = None
        self.current_mode = None
        self.video_qualities = []
        self.last_folder = DOWNLOAD_DIR
        self.is_paused = False

        self.setup_ui()
        self.set_windows_titlebar()

        if initial_url:
            clean_text = get_clean_youtube_url(initial_url)
            if clean_text:
                self.url_input.setText(clean_text)

    def set_windows_titlebar(self):
        try:
            hwnd = int(self.winId())
            dark_mode = ctypes.c_int(1)
            ctypes.windll.dwmapi.DwmSetWindowAttribute(
                hwnd, 20, ctypes.byref(dark_mode), ctypes.sizeof(dark_mode)
            )
            caption_color = ctypes.c_int(0x120D0B)
            ctypes.windll.dwmapi.DwmSetWindowAttribute(
                hwnd, 35, ctypes.byref(caption_color), ctypes.sizeof(caption_color)
            )
            text_color = ctypes.c_int(0xFAF7F5)
            ctypes.windll.dwmapi.DwmSetWindowAttribute(
                hwnd, 36, ctypes.byref(text_color), ctypes.sizeof(text_color)
            )
        except Exception:
            pass

    def setup_ui(self):
        self.setWindowTitle("YouTube Downloader")

        self.resize(580, 620)
        self.setMinimumSize(520, 580)

        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(24, 20, 24, 20)
        main_layout.setSpacing(12)

        # Header
        header_layout = QVBoxLayout()
        header_layout.setSpacing(2)

        brand = QLabel("MEDIA DOWNLOADER")
        brand.setStyleSheet("color: #ff375f; font-size: 10px; font-weight: 700; letter-spacing: 1.5px;")

        title = QLabel("YouTube Downloader")
        title.setStyleSheet("color: #f7f8fa; font-size: 22px; font-weight: 700;")

        subtitle = QLabel("Download videos and audio in your preferred quality.")
        subtitle.setStyleSheet("color: #8f96a3; font-size: 12px;")

        header_layout.addWidget(brand)
        header_layout.addWidget(title)
        header_layout.addWidget(subtitle)
        main_layout.addLayout(header_layout)

        # URL Card
        url_card = QFrame()
        url_card.setObjectName("card")
        url_layout = QVBoxLayout(url_card)
        url_layout.setContentsMargins(16, 12, 16, 16)
        url_layout.setSpacing(8)

        url_label = QLabel("VIDEO URL")
        url_label.setStyleSheet("color: #aeb4bf; font-size: 10px; font-weight: 700; letter-spacing: 1px;")

        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("Paste a YouTube link here...")
        self.url_input.setFixedHeight(40)
        self.url_input.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        url_layout.addWidget(url_label)
        url_layout.addWidget(self.url_input)
        main_layout.addWidget(url_card)

        # Download Type
        type_label = QLabel("DOWNLOAD TYPE")
        type_label.setStyleSheet("color: #aeb4bf; font-size: 10px; font-weight: 700; letter-spacing: 1px;")
        main_layout.addWidget(type_label)

        type_layout = QHBoxLayout()
        type_layout.setSpacing(10)

        self.video_button = QPushButton()
        self.video_button.setCheckable(True)
        self.video_button.setMinimumHeight(52)
        video_layout = QVBoxLayout(self.video_button)
        video_layout.setContentsMargins(5, 5, 5, 5)
        video_layout.setSpacing(1)

        video_name = QLabel("VIDEO")
        video_name.setAlignment(Qt.AlignCenter)
        video_name.setAttribute(Qt.WA_TransparentForMouseEvents)
        video_name.setStyleSheet("font-size: 13px; font-weight: 700;")

        video_description = QLabel("MP4 • HD / 4K")
        video_description.setAlignment(Qt.AlignCenter)
        video_description.setAttribute(Qt.WA_TransparentForMouseEvents)
        video_description.setStyleSheet("color: #858c99; font-size: 10px; font-weight: 500;")

        video_layout.addWidget(video_name)
        video_layout.addWidget(video_description)

        self.audio_button = QPushButton()
        self.audio_button.setCheckable(True)
        self.audio_button.setMinimumHeight(52)
        audio_layout = QVBoxLayout(self.audio_button)
        audio_layout.setContentsMargins(5, 5, 5, 5)
        audio_layout.setSpacing(1)

        audio_name = QLabel("AUDIO")
        audio_name.setAlignment(Qt.AlignCenter)
        audio_name.setAttribute(Qt.WA_TransparentForMouseEvents)
        audio_name.setStyleSheet("font-size: 13px; font-weight: 700;")

        audio_description = QLabel("MP3 • High Quality")
        audio_description.setAlignment(Qt.AlignCenter)
        audio_description.setAttribute(Qt.WA_TransparentForMouseEvents)
        audio_description.setStyleSheet("color: #858c99; font-size: 10px; font-weight: 500;")

        audio_layout.addWidget(audio_name)
        audio_layout.addWidget(audio_description)

        self.video_button.clicked.connect(self.select_video)
        self.audio_button.clicked.connect(self.select_audio)

        type_layout.addWidget(self.video_button)
        type_layout.addWidget(self.audio_button)
        main_layout.addLayout(type_layout)

        # Quality Card
        quality_card = QFrame()
        quality_card.setObjectName("card")
        quality_layout = QVBoxLayout(quality_card)
        quality_layout.setContentsMargins(16, 12, 16, 16)
        quality_layout.setSpacing(8)

        quality_label = QLabel("QUALITY")
        quality_label.setStyleSheet("color: #aeb4bf; font-size: 10px; font-weight: 700; letter-spacing: 1px;")

        self.quality_combo = QComboBox()
        self.quality_combo.setFixedHeight(40)
        self.quality_combo.addItem("Select Video or Audio")

        quality_layout.addWidget(quality_label)
        quality_layout.addWidget(self.quality_combo)
        main_layout.addWidget(quality_card)

        # Check Button
        self.check_button = QPushButton("Check Available Qualities")
        self.check_button.setMinimumHeight(38)
        self.check_button.clicked.connect(self.check_video)
        main_layout.addWidget(self.check_button)

        # Status Area
        status_layout = QHBoxLayout()
        self.status_indicator = QLabel("●")
        self.status_indicator.setStyleSheet("color: #6b7280; font-size: 8px;")

        self.status_label = QLabel("Ready to download")
        self.status_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.status_label.setStyleSheet("color: #9299a6; font-size: 12px;")

        status_layout.addWidget(self.status_indicator)
        status_layout.addSpacing(4)
        status_layout.addWidget(self.status_label)
        main_layout.addLayout(status_layout)

        # Progress
        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        self.progress_bar.setMinimumHeight(8)
        self.progress_bar.setMaximumHeight(8)
        self.progress_bar.setTextVisible(False)
        main_layout.addWidget(self.progress_bar)

        # Download Button
        self.download_button = QPushButton("Download")
        self.download_button.setMinimumHeight(44)
        self.download_button.setEnabled(False)
        self.download_button.clicked.connect(self.start_download)
        main_layout.addWidget(self.download_button)

        # Download Controls
        self.control_layout = QHBoxLayout()
        self.control_layout.setSpacing(8)

        self.pause_button = QPushButton("Pause")
        self.cancel_button = QPushButton("Cancel")
        self.pause_button.setMinimumHeight(36)
        self.cancel_button.setMinimumHeight(36)

        self.pause_button.clicked.connect(self.toggle_pause)
        self.cancel_button.clicked.connect(self.cancel_download)

        self.pause_button.setVisible(False)
        self.cancel_button.setVisible(False)

        self.control_layout.addWidget(self.pause_button)
        self.control_layout.addWidget(self.cancel_button)
        main_layout.addLayout(self.control_layout)

        # Open Folder
        self.open_folder_button = QPushButton("Open Download Folder")
        self.open_folder_button.setMinimumHeight(34)
        self.open_folder_button.setVisible(False)
        self.open_folder_button.clicked.connect(self.open_download_folder)
        main_layout.addWidget(self.open_folder_button)

        # Footer
        footer = QLabel("Files are automatically saved to your Downloads folder")
        footer.setAlignment(Qt.AlignCenter)
        footer.setStyleSheet("color: #626a77; font-size: 10px;")

        # Developer Credit
        credit = QLabel("Developed by Intasar Mostafiz")
        credit.setAlignment(Qt.AlignCenter)
        credit.setStyleSheet("color: #aeb4bf; font-size: 11px; font-weight: bold;")

        main_layout.addStretch()
        main_layout.addWidget(footer)
        main_layout.addWidget(credit)
        self.setLayout(main_layout)

        # Stylesheet
        self.setStyleSheet("""
            QWidget { background-color: #0b0d12; color: #f5f7fa; font-family: "Segoe UI"; font-size: 13px; }
            QFrame#card { background-color: #14171e; border: 1px solid #252a34; border-radius: 12px; }
            QLineEdit { background-color: #0f1218; border: 1px solid #2a303b; border-radius: 8px; padding: 0 12px; color: #f5f7fa; }
            QLineEdit:focus { border: 1px solid #ff375f; }
            QPushButton { background-color: #151921; border: 1px solid #2a303b; border-radius: 10px; color: #e9ebef; font-weight: 600; }
            QPushButton:hover { background-color: #1b1f28; border: 1px solid #414957; }
            QPushButton:checked { background-color: #21131a; border: 1px solid #ff375f; color: #ffffff; }
            QPushButton:disabled { background-color: #15181f; border: 1px solid #222731; color: #555c68; }
            QComboBox { background-color: #0f1218; border: 1px solid #2a303b; border-radius: 8px; padding: 0 12px; color: #f5f7fa; }
            QComboBox::drop-down { border: none; padding-right: 12px; }
            QComboBox QAbstractItemView { background-color: #14171e; border: 1px solid #252a34; selection-background-color: #21131a; selection-color: #ff375f; }
            QProgressBar { background-color: #171a22; border: none; border-radius: 4px; }
            QProgressBar::chunk { background-color: #ff375f; border-radius: 4px; }
        """)

        self.download_button.setStyleSheet("""
            QPushButton { background-color: #ff375f; border: none; border-radius: 10px; color: white; font-size: 14px; font-weight: 700; }
            QPushButton:hover { background-color: #ff4b6f; }
            QPushButton:disabled { background-color: #242832; color: #5c6370; }
        """)

        self.check_button.setStyleSheet("""
            QPushButton { background-color: #151921; border: 1px solid #2a303b; border-radius: 8px; color: #dfe2e7; font-weight: 600; }
            QPushButton:hover { background-color: #1c2029; border: 1px solid #ff375f; color: white; }
        """)

    def select_video(self):
        self.current_mode = "video"
        self.video_button.setChecked(True)
        self.audio_button.setChecked(False)
        self.quality_combo.clear()
        self.quality_combo.addItem("Click 'Check Available Qualities'")
        self.download_button.setEnabled(False)
        self.status_indicator.setStyleSheet("color: #ff375f; font-size: 8px;")
        self.status_label.setText("Video mode selected")

    def select_audio(self):
        self.current_mode = "audio"
        self.audio_button.setChecked(True)
        self.video_button.setChecked(False)
        self.quality_combo.clear()
        self.quality_combo.addItem("Best quality", "0")
        self.quality_combo.addItem("192 kbps", "192")
        self.quality_combo.addItem("128 kbps", "128")
        self.download_button.setEnabled(True)
        self.status_indicator.setStyleSheet("color: #ff375f; font-size: 8px;")
        self.status_label.setText("Audio mode selected")

    def check_video(self):
        raw_url = self.url_input.text()
        url = get_clean_youtube_url(raw_url)
        self.url_input.setText(url)

        if not url:
            QMessageBox.warning(self, "Missing URL", "Please paste a YouTube URL first.")
            return

        if self.current_mode != "video":
            QMessageBox.warning(self, "Select Video", "Please select Video mode first.")
            return

        self.check_button.setEnabled(False)
        self.download_button.setEnabled(False)
        self.quality_combo.clear()
        self.quality_combo.addItem("Checking available qualities...")
        self.status_indicator.setStyleSheet("color: #ff375f; font-size: 8px;")
        self.status_label.setText("Checking YouTube...")
        self.progress_bar.setValue(0)

        self.info_worker = InfoWorker(url)
        self.info_worker.status.connect(self.update_status)
        self.info_worker.finished.connect(self.qualities_found)
        self.info_worker.error.connect(self.quality_check_error)
        self.info_worker.start()

    def qualities_found(self, qualities, info):
        self.video_qualities = qualities
        self.quality_combo.clear()

        if not qualities:
            self.quality_combo.addItem("No video qualities found")
            self.status_indicator.setStyleSheet("color: #ef4444; font-size: 8px;")
            self.status_label.setText("No downloadable video qualities found")
            self.check_button.setEnabled(True)
            return

        for quality in qualities:
            self.quality_combo.addItem(f"{quality}p", quality)

        title = info.get("title", "Video found")
        duration = info.get("duration")

        if duration:
            minutes = duration // 60
            seconds = duration % 60
            duration_text = f"{minutes}:{seconds:02d}"
        else:
            duration_text = "Unknown duration"

        if len(title) > 55:
            title = title[:52] + "..."

        self.status_indicator.setStyleSheet("color: #22c55e; font-size: 8px;")
        self.status_label.setText(f"{title}  •  {duration_text}  •  {len(qualities)} qualities available")
        self.download_button.setEnabled(True)
        self.check_button.setEnabled(True)

    def quality_check_error(self, message):
        self.quality_combo.clear()
        self.quality_combo.addItem("Unable to load qualities")
        self.status_indicator.setStyleSheet("color: #ef4444; font-size: 8px;")
        self.status_label.setText("Failed to check YouTube")
        self.check_button.setEnabled(True)
        self.download_button.setEnabled(False)
        QMessageBox.critical(self, "YouTube Error", message)

    def start_download(self):
        raw_url = self.url_input.text()
        url = get_clean_youtube_url(raw_url)
        self.url_input.setText(url)

        if not url:
            QMessageBox.warning(self, "Missing URL", "Please enter a YouTube URL.")
            return

        if not self.current_mode:
            QMessageBox.warning(self, "Download Type", "Please select Video or Audio.")
            return

        quality = self.quality_combo.currentData()
        if quality is None:
            QMessageBox.warning(self, "Quality", "Please select a quality.")
            return

        self.is_paused = False

        widgets = [
            self.download_button, self.check_button,
            self.video_button, self.audio_button,
            self.url_input, self.quality_combo
        ]
        for widget in widgets:
            widget.setEnabled(False)

        self.pause_button.setVisible(True)
        self.cancel_button.setVisible(True)
        self.pause_button.setText("Pause")

        self.progress_bar.setValue(0)
        self.open_folder_button.setVisible(False)
        self.status_indicator.setStyleSheet("color: #ff375f; font-size: 8px;")
        self.status_label.setText("Starting download...")

        self.worker = DownloadWorker(url, self.current_mode, quality)
        self.worker.progress.connect(self.update_progress)
        self.worker.status.connect(self.update_status)
        self.worker.finished.connect(self.download_finished)
        self.worker.error.connect(self.download_error)
        self.worker.paused.connect(self.on_paused)
        self.worker.cancelled.connect(self.on_cancelled)
        self.worker.start()

    def toggle_pause(self):
        if not self.worker:
            return

        if not self.is_paused:
            self.worker.pause_download()
            self.pause_button.setText("Resume")
            self.is_paused = True
            self.status_label.setText("Pausing download...")
        else:
            self.start_download()

    def cancel_download(self):
        if not self.worker:
            return

        reply = QMessageBox.question(
            self, "Cancel Download",
            "Are you sure you want to cancel this download?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            self.status_label.setText("Cancelling download...")
            self.worker.cancel_download()

    def on_paused(self):
        self.status_indicator.setStyleSheet("color: #f59e0b; font-size: 8px;")
        self.status_label.setText("Download paused")

    def on_cancelled(self):
        self.status_indicator.setStyleSheet("color: #ef4444; font-size: 8px;")
        self.status_label.setText("Download cancelled")
        self.hide_download_controls()
        self.enable_controls()

    def update_progress(self, value):
        self.progress_bar.setValue(int(value))

    def update_status(self, text):
        if not self.is_paused:
            self.status_label.setText(text)

    def download_finished(self, file_path, actual_quality):
        self.progress_bar.setValue(100)
        self.status_indicator.setStyleSheet("color: #22c55e; font-size: 8px;")
        self.status_label.setText("Download completed successfully")
        self.last_folder = os.path.dirname(file_path)

        self.hide_download_controls()
        self.open_folder_button.setVisible(True)

        QMessageBox.information(
            self, "Download Complete",
            f"Download completed successfully!\n\n"
            f"Actual quality: {actual_quality}\n\n"
            f"File:\n{os.path.basename(file_path)}\n\n"
            f"Saved to:\n{file_path}"
        )
        self.enable_controls()

    def download_error(self, message):
        self.status_indicator.setStyleSheet("color: #ef4444; font-size: 8px;")
        self.status_label.setText("Download failed")
        self.hide_download_controls()
        QMessageBox.critical(self, "Download Error", message)
        self.enable_controls()

    def hide_download_controls(self):
        self.pause_button.setVisible(False)
        self.cancel_button.setVisible(False)

    def enable_controls(self):
        self.download_button.setEnabled(True)
        self.check_button.setEnabled(True)
        self.video_button.setEnabled(True)
        self.audio_button.setEnabled(True)
        self.url_input.setEnabled(True)
        self.quality_combo.setEnabled(True)

    def open_download_folder(self):
        folder = getattr(self, "last_folder", DOWNLOAD_DIR)
        if os.path.exists(folder):
            os.startfile(folder)