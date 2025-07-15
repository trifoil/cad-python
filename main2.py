import sys
from PyQt5.QtWidgets import QApplication, QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QGroupBox, QInputDialog, QMessageBox
from OCC.Core.BRepPrimAPI import BRepPrimAPI_MakeBox, BRepPrimAPI_MakePrism
from OCC.Core.gp import gp_Vec
from OCC.Extend.TopologyUtils import TopologyExplorer
from OCC.Core.TopoDS import topods
from OCC.Core.BRep import BRep_Tool
from OCC.Core.Geom import Geom_Plane
from OCC.Display.backend import load_backend

load_backend("pyqt5")
import OCC.Display.qtDisplay as qtDisplay

class CADApp(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("cad-python")
        self.setGeometry(100, 100, 800, 600)
        self.selected_face = None
        self.shape = None
        self.ais_shape = None
        self.initUI()
        self.display_cube()
        self.set_face_selection_mode()

    def initUI(self):
        main_layout = QVBoxLayout()
        self.setLayout(main_layout)

        # 3D Viewer
        self.canvas = qtDisplay.qtViewer3d(self)
        self.canvas.InitDriver()
        self.display = self.canvas._display
        main_layout.addWidget(self.canvas)

        # Controls
        controls = QGroupBox("Controls")
        controls_layout = QHBoxLayout()
        controls.setLayout(controls_layout)
        main_layout.addWidget(controls)

        self.extrude_btn = QPushButton("Extrude Selected Face", self)
        self.extrude_btn.clicked.connect(self.on_extrude)
        controls_layout.addWidget(self.extrude_btn)

    def display_cube(self):
        # Set light grey background
        if hasattr(self.display, 'View'):
            # OCC Quantity_NOC_LIGHTGRAY is (211, 211, 211)
            from OCC.Core.Quantity import Quantity_Color, Quantity_TOC_RGB
            light_grey = Quantity_Color(0.83, 0.83, 0.83, Quantity_TOC_RGB)
            white = Quantity_Color(1.0, 1.0, 1.0, Quantity_TOC_RGB)
            self.display.View.SetBgGradientColors(light_grey, white, 2)
        # Create and display a cube
        self.shape = BRepPrimAPI_MakeBox(60.0, 60.0, 60.0).Shape()
        self.display.EraseAll()
        self.ais_shape = self.display.DisplayShape(self.shape, update=True)[0]
        # Set edge color and width
        from OCC.Core.Quantity import Quantity_NOC_CYAN1, Quantity_Color
        from OCC.Core.Prs3d import Prs3d_Drawer
        ctx = self.display.Context
        drawer = self.ais_shape.Attributes()
        drawer.SetWireAspect(Prs3d_Drawer().WireAspect())
        drawer.WireAspect().SetColor(Quantity_Color(Quantity_NOC_CYAN1))
        drawer.WireAspect().SetWidth(2.0)
        ctx.Redisplay(self.ais_shape, True)
        self.display.FitAll()

    def set_face_selection_mode(self):
        # Set selection mode to face
        self.display.SetSelectionModeFace()
        self.display.register_select_callback(self.on_face_selected)

    def on_face_selected(self, shapes, x=None, y=None):
        # Called when a face is selected
        for shape in shapes:
            if shape.ShapeType() == 4:  # TopAbs_FACE
                self.selected_face = topods.Face(shape)
                self.display.Context.SetSelected(self.ais_shape, True)
                return
        self.selected_face = None

    def on_extrude(self):
        if self.selected_face is None:
            QMessageBox.warning(self, "No Face Selected", "Please select a face to extrude.")
            return
        # Ask user for extrusion distance
        dist, ok = QInputDialog.getDouble(self, "Extrude", "Enter extrusion distance:", 20.0, -1000.0, 1000.0, 2)
        if not ok:
            return
        # Get normal direction of the face
        surf = BRep_Tool.Surface(self.selected_face)
        plane = Geom_Plane.DownCast(surf)
        if plane is None:
            QMessageBox.warning(self, "Not a Planar Face", "Selected face is not planar and cannot be extruded.")
            return
        direction = plane.Axis().Direction()
        vec = gp_Vec(direction.X(), direction.Y(), direction.Z())
        # Extrude the face using BRepPrimAPI_MakePrism
        try:
            extruded = BRepPrimAPI_MakePrism(self.selected_face, vec.Scaled(dist)).Shape()
        except Exception as e:
            QMessageBox.critical(self, "Extrusion Failed", f"Extrusion operation failed: {e}")
            return
        self.shape = extruded
        self.display.EraseAll()
        self.ais_shape = self.display.DisplayShape(self.shape, update=True)[0]
        # Set edge color and width
        from OCC.Core.Quantity import Quantity_NOC_CYAN1, Quantity_Color
        from OCC.Core.Prs3d import Prs3d_Drawer
        ctx = self.display.Context
        drawer = self.ais_shape.Attributes()
        drawer.SetWireAspect(Prs3d_Drawer().WireAspect())
        drawer.WireAspect().SetColor(Quantity_Color(Quantity_NOC_CYAN1))
        drawer.WireAspect().SetWidth(2.0)
        ctx.Redisplay(self.ais_shape, True)
        self.display.FitAll()
        self.selected_face = None

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = CADApp()
    window.show()
    sys.exit(app.exec_())
