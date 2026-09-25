import sys
import re
import os
import ctypes
import tempfile
from datetime import datetime
from PyQt6.QtCore import Qt, QUrl, QTimer, QTime, QPoint, QSettings, QSize
from PyQt6.QtGui import QPixmap, QPainter, QColor, QPolygon, QIcon, QPen
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                             QHBoxLayout, QGridLayout, QPushButton, QComboBox, 
                             QLabel, QFileDialog, QDialog, QFormLayout)
from PyQt6.QtMultimedia import (QCamera, QMediaCaptureSession, QMediaDevices,
                                QImageCapture, QMediaRecorder)
from PyQt6.QtMultimediaWidgets import QVideoWidget

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Settings")
        self.setStyleSheet("background-color: #2b2b2b; color: white;")
        
        self.settings = QSettings("settings.ini", QSettings.Format.IniFormat)
        
        self.layout = QFormLayout(self)
        
        default_dir = os.path.join(os.path.expanduser("~"), "Pictures", "Camera")
        saved_dir = self.settings.value("save_directory", default_dir)
        os.makedirs(saved_dir, exist_ok=True)
        
        self.dir_layout = QHBoxLayout()
        self.dir_label = QLabel(saved_dir)
        self.dir_btn = QPushButton("Browse")
        self.dir_btn.clicked.connect(self.browse_dir)
        self.dir_layout.addWidget(self.dir_label)
        self.dir_layout.addWidget(self.dir_btn)
        
        self.img_format = QComboBox()
        self.img_format.addItems(["JPEG", "PNG", "WEBP"])
        self.img_format.setCurrentText(self.settings.value("img_format", "JPEG"))
        self.img_format.currentTextChanged.connect(lambda text: self.settings.setValue("img_format", text))
        
        self.vid_format = QComboBox()
        self.vid_format.addItems(["MP4", "WEBM"])
        self.vid_format.setCurrentText(self.settings.value("vid_format", "MP4"))
        self.vid_format.currentTextChanged.connect(lambda text: self.settings.setValue("vid_format", text))
        
        self.layout.addRow("Save Directory:", self.dir_layout)
        self.layout.addRow("Picture Format:", self.img_format)
        self.layout.addRow("Video Format:", self.vid_format)

    def browse_dir(self):
        directory = QFileDialog.getExistingDirectory(self, "Select Save Directory")
        if directory:
            self.dir_label.setText(directory)
            self.settings.setValue("save_directory", directory)

class CameraApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Camera")
        self.setMinimumSize(1024, 640)
        
        self.setStyleSheet("background-color: #1e1e1e; color: white;")

        self.settings_dialog = SettingsDialog(self)
        self.is_recording = False
        self.was_maximized = False
        
        self.record_seconds = 0
        self.record_timer = QTimer(self)
        self.record_timer.timeout.connect(self.update_timer)

        self.generate_arrow_icon()
        self.setup_ui()
        self.setup_camera()
        
        self.set_dark_title_bar()

    def set_dark_title_bar(self):
        try:
            hwnd = int(self.winId())
            DWMWA_USE_IMMERSIVE_DARK_MODE = 20
            rendering_policy = ctypes.c_int(1)
            ctypes.windll.dwmapi.DwmSetWindowAttribute(
                hwnd, 
                DWMWA_USE_IMMERSIVE_DARK_MODE, 
                ctypes.byref(rendering_policy), 
                ctypes.sizeof(rendering_policy)
            )
        except Exception:
            pass

    def generate_arrow_icon(self):
        self.arrow_path = os.path.join(tempfile.gettempdir(), "cam_arrow.png").replace("\\", "/")
        pixmap = QPixmap(12, 12)
        pixmap.fill(Qt.GlobalColor.transparent)
        
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setBrush(QColor("#cccccc"))
        painter.setPen(Qt.PenStyle.NoPen)
        
        points = [QPoint(2, 4), QPoint(10, 4), QPoint(6, 9)]
        painter.drawPolygon(QPolygon(points))
        painter.end()
        
        pixmap.save(self.arrow_path, "PNG")

    # --- Icon Generation Methods ---
    def create_camera_icon(self):
        pixmap = QPixmap(24, 24)
        pixmap.fill(Qt.GlobalColor.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setBrush(QColor("white"))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(7, 4, 10, 4, 1, 1) 
        painter.drawRoundedRect(2, 7, 20, 13, 2, 2) 
        painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_Clear)
        painter.drawEllipse(7, 8, 10, 10) 
        painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceOver)
        painter.drawEllipse(9, 10, 6, 6) 
        painter.drawEllipse(18, 9, 2, 2) 
        painter.end()
        return QIcon(pixmap)

    def create_video_icon(self):
        pixmap = QPixmap(24, 24)
        pixmap.fill(Qt.GlobalColor.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setBrush(QColor("white"))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(3, 6, 12, 12, 2, 2) 
        poly = QPolygon([QPoint(15, 10), QPoint(22, 6), QPoint(22, 18), QPoint(15, 14)]) 
        painter.drawPolygon(poly)
        painter.end()
        return QIcon(pixmap)

    def create_stop_icon(self):
        pixmap = QPixmap(24, 24)
        pixmap.fill(Qt.GlobalColor.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setBrush(QColor("#ff4444"))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(6, 6, 12, 12, 2, 2)
        painter.end()
        return QIcon(pixmap)

    def create_fullscreen_icon(self):
        pixmap = QPixmap(24, 24)
        pixmap.fill(Qt.GlobalColor.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        pen = QPen(QColor("white"))
        pen.setWidth(2)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(pen)
        
        # Top-left corner
        painter.drawLine(4, 4, 9, 4)
        painter.drawLine(4, 4, 4, 9)
        # Top-right corner
        painter.drawLine(20, 4, 15, 4)
        painter.drawLine(20, 4, 20, 9)
        # Bottom-left corner
        painter.drawLine(4, 20, 9, 20)
        painter.drawLine(4, 20, 4, 15)
        # Bottom-right corner
        painter.drawLine(20, 20, 15, 20)
        painter.drawLine(20, 20, 20, 15)
        
        painter.end()
        return QIcon(pixmap)

    def create_settings_icon(self):
        pixmap = QPixmap(24, 24)
        pixmap.fill(Qt.GlobalColor.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setBrush(QColor("white"))
        painter.setPen(Qt.PenStyle.NoPen)
        
        # Translate to center to draw the gear
        painter.translate(12, 12)
        for _ in range(8):
            painter.drawRoundedRect(-2, -10, 4, 5, 1, 1)
            painter.rotate(45)
            
        painter.drawEllipse(-6, -6, 12, 12)
        
        # Punch out the center
        painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_Clear)
        painter.drawEllipse(-3, -3, 6, 6)
        painter.end()
        return QIcon(pixmap)

    def setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # --- Camera Viewport ---
        self.video_container = QWidget()
        self.video_container.setStyleSheet("background-color: #000000;")
        self.video_layout = QVBoxLayout(self.video_container)
        self.video_layout.setContentsMargins(0, 0, 0, 0) 
        
        self.video_widget = QVideoWidget()
        self.video_layout.addWidget(self.video_widget)
        
        self.toast_label = QLabel("📸 Picture Saved", self.video_widget)
        self.toast_label.setStyleSheet("""
            background-color: rgba(40, 40, 40, 200); 
            color: white; 
            padding: 10px 20px; 
            border-radius: 8px; 
            font-size: 16px;
            font-weight: bold;
        """)
        self.toast_label.hide()

        # --- Bottom Control Bar ---
        self.control_bar = QWidget()
        
        css = """
            QWidget { background-color: #1a1a1a; }
            QPushButton {
                background-color: #2b2b2b;
                border: 1px solid #3d3d3d;
                border-radius: 4px;
                padding: 6px 12px;
                color: white;
            }
            QComboBox {
                background-color: #2b2b2b;
                border: 1px solid #3d3d3d;
                border-radius: 4px;
                padding: 4px 18px 4px 6px; 
                color: white;
            }
            QComboBox::drop-down {
                subcontrol-origin: padding;
                subcontrol-position: top right;
                width: 18px;
                border: none;
            }
            QComboBox::down-arrow {
                image: url("ARROW_PATH");
            }
            QPushButton:hover, QComboBox:hover { background-color: #383838; }
        """.replace("ARROW_PATH", self.arrow_path)
        
        self.control_bar.setStyleSheet(css)
        
        control_layout = QGridLayout(self.control_bar)
        control_layout.setContentsMargins(15, 10, 15, 10)
        
        left_widget = QWidget()
        left_layout = QHBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)
        
        self.camera_combo = QComboBox()
        self.camera_combo.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToContents)
        self.camera_combo.setMinimumWidth(210)
        self.camera_combo.currentIndexChanged.connect(self.change_camera)
        
        self.res_combo = QComboBox()
        self.res_combo.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToContents)
        self.res_combo.setMinimumWidth(150)
        
        self.fps_combo = QComboBox()
        self.fps_combo.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToContents)
        self.fps_combo.setMinimumWidth(85)
        
        left_layout.addWidget(self.camera_combo)
        left_layout.addWidget(self.res_combo)
        left_layout.addWidget(self.fps_combo)
        left_layout.addStretch()

        center_widget = QWidget()
        center_layout = QHBoxLayout(center_widget)
        center_layout.setContentsMargins(0, 0, 0, 0)
        center_layout.setSpacing(10)
        
        self.photo_btn = QPushButton()
        self.photo_btn.setIcon(self.create_camera_icon())
        self.photo_btn.setIconSize(QSize(20, 20))
        self.photo_btn.setFixedSize(40, 40)
        self.photo_btn.setToolTip("Take Photo")
        self.photo_btn.clicked.connect(self.take_photo)

        self.video_btn = QPushButton()
        self.video_btn.setIcon(self.create_video_icon())
        self.video_btn.setIconSize(QSize(20, 20))
        self.video_btn.setFixedSize(40, 40)
        self.video_btn.setToolTip("Record Video")
        self.video_btn.clicked.connect(self.toggle_video)
        
        self.timer_label = QLabel("00:00")
        self.timer_label.setFixedWidth(40) 
        self.timer_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.timer_label.setStyleSheet("color: #ff4444; font-weight: bold; font-size: 14px; background: transparent; border: none;")
        self.timer_label.hide()
        
        center_layout.addWidget(self.photo_btn)
        center_layout.addWidget(self.video_btn)
        center_layout.addWidget(self.timer_label)

        right_widget = QWidget()
        right_layout = QHBoxLayout(right_widget)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(10)
        
        self.fullscreen_btn = QPushButton()
        self.fullscreen_btn.setIcon(self.create_fullscreen_icon())
        self.fullscreen_btn.setIconSize(QSize(20, 20))
        self.fullscreen_btn.setFixedSize(40, 40)
        self.fullscreen_btn.setToolTip("Fullscreen (Press Esc to exit)")
        self.fullscreen_btn.clicked.connect(self.toggle_fullscreen)
        
        self.settings_btn = QPushButton()
        self.settings_btn.setIcon(self.create_settings_icon())
        self.settings_btn.setIconSize(QSize(20, 20))
        self.settings_btn.setFixedSize(40, 40)
        self.settings_btn.setToolTip("Settings")
        self.settings_btn.clicked.connect(self.settings_dialog.exec)
        
        right_layout.addStretch()
        right_layout.addWidget(self.fullscreen_btn)
        right_layout.addWidget(self.settings_btn)

        control_layout.addWidget(left_widget, 0, 0, Qt.AlignmentFlag.AlignLeft)
        control_layout.addWidget(center_widget, 0, 1, Qt.AlignmentFlag.AlignCenter)
        control_layout.addWidget(right_widget, 0, 2, Qt.AlignmentFlag.AlignRight)
        
        control_layout.setColumnStretch(0, 1)
        control_layout.setColumnStretch(1, 0)
        control_layout.setColumnStretch(2, 1)

        main_layout.addWidget(self.video_container, 1) 
        main_layout.addWidget(self.control_bar)

    def setup_camera(self):
        self.capture_session = QMediaCaptureSession()
        self.capture_session.setVideoOutput(self.video_widget)
        
        self.image_capture = QImageCapture()
        self.capture_session.setImageCapture(self.image_capture)
        
        self.media_recorder = QMediaRecorder()
        self.capture_session.setRecorder(self.media_recorder)
        
        self.available_cameras = QMediaDevices.videoInputs()
        
        for cam in self.available_cameras:
            clean_name = re.sub(r'\s*\([^)]*(VID|PID)[^)]*\)', '', cam.description(), flags=re.IGNORECASE)
            self.camera_combo.addItem(clean_name)
            
        if self.available_cameras:
            self.change_camera(0)

    def change_camera(self, index):
        if index < 0 or not self.available_cameras: return
        
        self.camera = QCamera(self.available_cameras[index])
        self.capture_session.setCamera(self.camera)
        
        self.res_combo.clear()
        self.fps_combo.clear()
        
        formats = self.camera.cameraDevice().videoFormats()
        res_list = []
        fps_set = set()
        
        for fmt in formats:
            res = fmt.resolution()
            fps_set.add(int(fmt.maxFrameRate()))
            res_str = f"{res.width()}x{res.height()}"
            
            if res.height() == 1080: label = f"1080p ({res_str})"
            elif res.height() == 2160: label = f"4K ({res_str})"
            elif res.height() == 720: label = f"720p ({res_str})"
            else: label = f"{res.height()}p ({res_str})"
            
            if label not in res_list:
                res_list.append(label)
                self.res_combo.addItem(label, fmt)
        
        for fps in sorted(fps_set):
            self.fps_combo.addItem(f"{fps} FPS")
            
        self.camera.start()

    def take_photo(self):
        self.video_layout.setContentsMargins(30, 30, 30, 30) 
        QTimer.singleShot(150, lambda: self.video_layout.setContentsMargins(0, 0, 0, 0)) 
        
        save_dir = self.settings_dialog.dir_label.text()
        ext = self.settings_dialog.img_format.currentText().lower()
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        path = os.path.join(save_dir, f"capture_{timestamp}.{ext}")
        
        self.image_capture.captureToFile(path)
        
        self.toast_label.adjustSize()
        x = int((self.video_widget.width() - self.toast_label.width()) / 2)
        y = int((self.video_widget.height() - self.toast_label.height()) / 2)
        self.toast_label.move(x, y)
        self.toast_label.show()
        
        QTimer.singleShot(1500, self.toast_label.hide)

    def toggle_video(self):
        if self.is_recording:
            self.media_recorder.stop()
            self.video_btn.setIcon(self.create_video_icon())
            self.video_btn.setToolTip("Record Video")
            self.is_recording = False
            self.record_timer.stop()
            self.timer_label.hide()
        else:
            save_dir = self.settings_dialog.dir_label.text()
            ext = self.settings_dialog.vid_format.currentText().lower()
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            path = QUrl.fromLocalFile(os.path.join(save_dir, f"video_{timestamp}.{ext}"))
            
            self.media_recorder.setOutputLocation(path)
            self.media_recorder.record()
            self.video_btn.setIcon(self.create_stop_icon())
            self.video_btn.setToolTip("Stop Recording")
            self.is_recording = True
            
            self.record_seconds = 0
            self.timer_label.setText("00:00")
            self.timer_label.show()
            self.record_timer.start(1000)

    def update_timer(self):
        self.record_seconds += 1
        time_str = QTime(0, 0, 0).addSecs(self.record_seconds).toString("mm:ss")
        self.timer_label.setText(time_str)
        
    def toggle_fullscreen(self):
        if self.isFullScreen():
            if self.was_maximized:
                self.showMaximized()
            else:
                self.showNormal()
            self.control_bar.show()
        else:
            self.was_maximized = self.isMaximized()
            self.showFullScreen()
            self.control_bar.hide()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape and self.isFullScreen():
            self.toggle_fullscreen()
        super().keyPressEvent(event)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if not self.toast_label.isHidden():
            x = int((self.video_widget.width() - self.toast_label.width()) / 2)
            y = int((self.video_widget.height() - self.toast_label.height()) / 2)
            self.toast_label.move(x, y)

if __name__ == "__main__":
    # Tell Windows this is a distinct app so it uses your icon in the taskbar
    try:
        myappid = 'custom.webcamviewer.app.1'
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
    except Exception:
        pass

    app = QApplication(sys.argv)
    
    # Load and apply the icon to the application and window
    app_icon = QIcon(resource_path("icon.ico"))
    app.setWindowIcon(app_icon)
    
    app.setStyle("Fusion")
    window = CameraApp()
    window.setWindowIcon(app_icon)
    window.showMaximized()
    sys.exit(app.exec())