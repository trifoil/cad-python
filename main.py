import os
import sys
from OCC.Core.BRepPrimAPI import BRepPrimAPI_MakeBox
from PyQt5.QtWidgets import (
    QApplication, QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QWidget, QLabel
)
from PyQt5.QtCore import Qt, QPoint, QEvent
from OCC.Display.backend import load_backend

load_backend("pyqt5")
import OCC.Display.qtDisplay as qtDisplay
from PyQt5.QtGui import QCursor

class CustomTitleBar(QWidget):
    def __init__(self, parent=None, title="cad-python"):
        super().__init__(parent)
        self.parent = parent
        self.setObjectName("CustomTitleBar")
        self.setFixedHeight(38)
        self.setMouseTracking(True)  # Enable mouse tracking
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
        self.max_btn = QPushButton("❐", self)
        self.max_btn.setObjectName("TitleBarButton")
        self.max_btn.setFixedSize(28, 28)
        self.max_btn.clicked.connect(self.on_maximize_restore)
        layout.addWidget(self.max_btn)
        self.close_btn = QPushButton("×", self)
        self.close_btn.setObjectName("TitleBarButton")
        self.close_btn.setFixedSize(28, 28)
        self.close_btn.clicked.connect(self.on_close)
        layout.addWidget(self.close_btn)
        self._drag_pos = None
        self._is_maximized = False

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._drag_pos = event.globalPos() - self.parent.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if self._drag_pos and event.buttons() & Qt.LeftButton and not self._is_maximized:
            self.parent.move(event.globalPos() - self._drag_pos)
            event.accept()
        else:
            # Forward to parent for resize cursor
            self.parent._update_cursor(self.mapToParent(event.pos()))
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        self._drag_pos = None

    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.on_maximize_restore()
            event.accept()

    def on_close(self):
        self.parent.close()

    def on_minimize(self):
        self.parent.showMinimized()

    def on_maximize_restore(self):
        if not self._is_maximized:
            self.parent.showMaximized()
            self.max_btn.setText("❐")  # Optionally change to a restore icon
            self._is_maximized = True
        else:
            self.parent.showNormal()
            self.max_btn.setText("❐")  # Optionally change to a maximize icon
            self._is_maximized = False

class App(QDialog):
    BORDER_WIDTH = 2  # px, smaller border
    def __init__(self):
        super().__init__()
        self.setObjectName("MainWindow")
        self.title = "cad-python"
        self.left = 300
        self.top = 300
        self._width = 900
        self._height = 700
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Window)
        self._resizing = False
        self._resize_dir = None
        self._mouse_press_pos = None
        self._mouse_press_geom = None
        self._cursor_overridden = False  # Track override state
        self.setMouseTracking(True)  # Enable mouse tracking for main window
        self.installEventFilter(self)  # Install event filter on self
        self.initUI()

    def eventFilter(self, obj, event):
        # Always update cursor on mouse move, release, enter, leave
        if event.type() in (QEvent.MouseMove, QEvent.MouseButtonRelease, QEvent.Enter, QEvent.Leave):
            # Get mouse position relative to self
            if event.type() in (QEvent.MouseMove, QEvent.MouseButtonRelease):
                pos = obj.mapTo(self, event.pos())
            else:
                pos = self.mapFromGlobal(QCursor.pos())
            self._update_cursor(pos)
        return super().eventFilter(obj, event)

    def initUI(self):
        self.setWindowTitle(self.title)
        self.setGeometry(self.left, self.top, self._width, self._height)
        self.setStyleSheet(self.custom_stylesheet())

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(self.BORDER_WIDTH, self.BORDER_WIDTH, self.BORDER_WIDTH, self.BORDER_WIDTH)
        main_layout.setSpacing(0)

        # Custom title bar
        self.title_bar = CustomTitleBar(self, self.title)
        self.title_bar.setMouseTracking(True)
        self.title_bar.installEventFilter(self)
        main_layout.addWidget(self.title_bar, 0)

        # Top bar with buttons
        top_bar = QWidget(self)
        top_bar.setObjectName("TopBar")
        top_bar.setMouseTracking(True)
        top_bar.installEventFilter(self)
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
        self.canvas.setMouseTracking(True)
        self.canvas.installEventFilter(self)
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
        # Border only on the main window, not on all widgets
        return f"""
        #MainWindow {{
            border: {self.BORDER_WIDTH}px solid rgba(0,0,0,0); /* transparent border */
            background-color: #22262e;
        }}
        QDialog, QWidget {{
            background-color: #22262e;
            color: #f0f0f0;
            font-family: 'Segoe UI', 'Arial', sans-serif;
            font-size: 15px;
        }}
        QPushButton {{
            background-color: #2d313a;
            color: #f0f0f0;
            border: 1px solid #444a57;
            border-radius: 6px;
            padding: 6px 18px;
        }}
        QPushButton:hover {{
            background-color: #3a3f4b;
        }}
        QPushButton:pressed {{
            background-color: #1e2127;
        }}
        #TopBar {{
            background-color: #23262e;
            border-bottom: 1px solid #444a57;
        }}
        #CustomTitleBar {{
            background-color: #1a1c22;
            border-bottom: 1px solid #444a57;
        }}
        #TitleLabel {{
            font-size: 17px;
            font-weight: bold;
            color: #f0f0f0;
        }}
        #TitleBarButton {{
            background-color: #23262e;
            color: #f0f0f0;
            border: none;
            border-radius: 5px;
            font-size: 18px;
        }}
        #TitleBarButton:hover {{
            background-color: #e06c75;
            color: #fff;
        }}
        """

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._resize_dir = self._get_resize_direction(event.pos())
            if self._resize_dir:
                self._resizing = True
                self._mouse_press_pos = event.globalPos()
                self._mouse_press_geom = self.geometry()
            else:
                super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._resizing and self._resize_dir:
            self._resize_window(event.globalPos())
        else:
            self._update_cursor(event.pos())
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        self._resizing = False
        self._resize_dir = None
        # Update cursor after resizing in case mouse is not on border
        self._update_cursor(event.pos())
        super().mouseReleaseEvent(event)

    def _get_resize_direction(self, pos):
        x, y, w, h = pos.x(), pos.y(), self.width(), self.height()
        bw = self.BORDER_WIDTH
        left = x <= bw
        right = x >= w - bw
        top = y <= bw
        bottom = y >= h - bw
        # Corners first
        if top and left:
            return 'top_left'
        if top and right:
            return 'top_right'
        if bottom and left:
            return 'bottom_left'
        if bottom and right:
            return 'bottom_right'
        # Edges
        if left:
            return 'left'
        if right:
            return 'right'
        if top:
            return 'top'
        if bottom:
            return 'bottom'
        return None

    def _update_cursor(self, pos):
        direction = self._get_resize_direction(pos)
        cursors = {
            'left': Qt.SizeHorCursor,
            'right': Qt.SizeHorCursor,
            'top': Qt.SizeVerCursor,
            'bottom': Qt.SizeVerCursor,
            'top_left': Qt.SizeFDiagCursor,      # ↖️
            'bottom_right': Qt.SizeFDiagCursor,  # ↘️
            'top_right': Qt.SizeBDiagCursor,     # ↗️
            'bottom_left': Qt.SizeBDiagCursor,   # ↙️
        }
        if direction in cursors:
            if not self._cursor_overridden or QApplication.overrideCursor() is None or QApplication.overrideCursor().shape() != cursors[direction]:
                QApplication.setOverrideCursor(cursors[direction])
                self._cursor_overridden = True
        else:
            if self._cursor_overridden:
                QApplication.restoreOverrideCursor()
                self._cursor_overridden = False

    def _resize_window(self, global_pos):
        diff = global_pos - self._mouse_press_pos
        geom = self._mouse_press_geom
        min_width, min_height = self.minimumWidth(), self.minimumHeight()
        x, y, w, h = geom.x(), geom.y(), geom.width(), geom.height()
        dx, dy = diff.x(), diff.y()
        dir = self._resize_dir
        if 'left' in dir:
            new_x = x + dx
            new_w = w - dx
            if new_w >= min_width:
                x = new_x
                w = new_w
        if 'right' in dir:
            new_w = w + dx
            if new_w >= min_width:
                w = new_w
        if 'top' in dir:
            new_y = y + dy
            new_h = h - dy
            if new_h >= min_height:
                y = new_y
                h = new_h
        if 'bottom' in dir:
            new_h = h + dy
            if new_h >= min_height:
                h = new_h
        self.setGeometry(x, y, w, h)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    ex = App()
    if os.getenv("APPVEYOR") is None:
        sys.exit(app.exec_())

