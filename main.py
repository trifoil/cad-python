import os
import sys
from OCC.Core.BRepPrimAPI import BRepPrimAPI_MakeBox
from PyQt5.QtWidgets import (
    QApplication, QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QWidget, QLabel
)
from PyQt5.QtCore import Qt, QPoint
from OCC.Display.backend import load_backend

load_backend("pyqt5")
import OCC.Display.qtDisplay as qtDisplay

class CustomTitleBar(QWidget):
    def __init__(self, parent=None, title="cad-python"):
        super().__init__(parent)
        self.parent = parent
        self.setObjectName("CustomTitleBar")
        self.setFixedHeight(38)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 0, 8, 0)
        layout.setSpacing(8)
        self.title_label = QLabel(title, self)
        self.title_label.setObjectName("TitleLabel")
        layout.addWidget(self.title_label)
        layout.addStretch(1)
        self.min_btn = QPushButton("–", self)
        self.min_btn.setObjectName("TitleBarButton")
        self.min_btn.setFixedSize(28, 28)
        self.min_btn.clicked.connect(self.on_minimize)
        layout.addWidget(self.min_btn)
        self.close_btn = QPushButton("×", self)
        self.close_btn.setObjectName("TitleBarButton")
        self.close_btn.setFixedSize(28, 28)
        self.close_btn.clicked.connect(self.on_close)
        layout.addWidget(self.close_btn)
        self._drag_pos = None

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._drag_pos = event.globalPos() - self.parent.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if self._drag_pos and event.buttons() & Qt.LeftButton:
            self.parent.move(event.globalPos() - self._drag_pos)
            event.accept()

    def mouseReleaseEvent(self, event):
        self._drag_pos = None

    def on_close(self):
        self.parent.close()

    def on_minimize(self):
        self.parent.showMinimized()

class App(QDialog):
    def __init__(self):
        super().__init__()
        self.title = "cad-python"
        self.left = 300
        self.top = 300
        self.width = 900
        self.height = 700
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Window)
        self.initUI()

    def initUI(self):
        self.setWindowTitle(self.title)
        self.setGeometry(self.left, self.top, self.width, self.height)
        self.setStyleSheet(self.custom_stylesheet())

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Custom title bar
        self.title_bar = CustomTitleBar(self, self.title)
        main_layout.addWidget(self.title_bar, 0)

        # Top bar with buttons
        top_bar = QWidget(self)
        top_bar.setObjectName("TopBar")
        top_bar_layout = QHBoxLayout(top_bar)
        top_bar_layout.setContentsMargins(10, 10, 10, 10)
        top_bar_layout.setSpacing(10)
        btn1 = QPushButton("Button 1", top_bar)
        btn2 = QPushButton("Button 2", top_bar)
        top_bar_layout.addWidget(btn1)
        top_bar_layout.addWidget(btn2)
        top_bar_layout.addStretch(1)
        main_layout.addWidget(top_bar, 0)

        # 3D Viewer area
        self.canvas = qtDisplay.qtViewer3d(self)
        self.canvas.setSizePolicy(self.canvas.sizePolicy().Expanding, self.canvas.sizePolicy().Expanding)
        main_layout.addWidget(self.canvas, 1)
        self.setLayout(main_layout)
        self.show()
        self.canvas.InitDriver()
        self.display = self.canvas._display
        self.set_occt_background()
        self.displayCube()

    def set_occt_background(self):
        # Set a dark gradient background for the OCCT viewer
        if hasattr(self.display, 'View'):
            from OCC.Core.Quantity import Quantity_Color, Quantity_TOC_RGB
            dark1 = Quantity_Color(0.13, 0.15, 0.18, Quantity_TOC_RGB)  # #22262e
            dark2 = Quantity_Color(0.08, 0.09, 0.11, Quantity_TOC_RGB)  # #15171c
            self.display.View.SetBgGradientColors(dark1, dark2, 2)

    def displayCube(self):
        cube = BRepPrimAPI_MakeBox(50.0, 50.0, 50.0).Shape()
        self.display.EraseAll()
        self.ais_cube = self.display.DisplayShape(cube)[0]
        self.display.FitAll()

    def custom_stylesheet(self):
        # Modern dark theme with custom title bar
        return """
        QDialog, QWidget {
            background-color: #22262e;
            color: #f0f0f0;
            font-family: 'Segoe UI', 'Arial', sans-serif;
            font-size: 15px;
        }
        QPushButton {
            background-color: #2d313a;
            color: #f0f0f0;
            border: 1px solid #444a57;
            border-radius: 6px;
            padding: 6px 18px;
        }
        QPushButton:hover {
            background-color: #3a3f4b;
        }
        QPushButton:pressed {
            background-color: #1e2127;
        }
        #TopBar {
            background-color: #23262e;
            border-bottom: 1px solid #444a57;
        }
        #CustomTitleBar {
            background-color: #1a1c22;
            border-bottom: 1px solid #444a57;
        }
        #TitleLabel {
            font-size: 17px;
            font-weight: bold;
            color: #f0f0f0;
        }
        #TitleBarButton {
            background-color: #23262e;
            color: #f0f0f0;
            border: none;
            border-radius: 5px;
            font-size: 18px;
        }
        #TitleBarButton:hover {
            background-color: #e06c75;
            color: #fff;
        }
        """

if __name__ == "__main__":
    app = QApplication(sys.argv)
    ex = App()
    if os.getenv("APPVEYOR") is None:
        sys.exit(app.exec_())

