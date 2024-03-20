import sys
import vtk
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget
from vtk.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor

class MyMainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        # Create a VTK renderer and render window
        self.renderer = vtk.vtkRenderer()
        # self.renderWindow = vtk.vtkRenderWindow()
        # self.renderWindow.AddRenderer(self.renderer)

        # Create a Qt widget for VTK rendering
        self.vtkWidget = QVTKRenderWindowInteractor(self)
        self.vtkWidget.GetRenderWindow().AddRenderer(self.renderer)
        self.iren = self.vtkWidget.GetRenderWindow().GetInteractor()
        

        # Set up layout
        self.layout = QVBoxLayout()
        self.layout.addWidget(self.vtkWidget)

        # Create a central widget and set the layout
        self.centralWidget = QWidget()
        self.centralWidget.setLayout(self.layout)
        self.setCentralWidget(self.centralWidget)
        
        
        colors = vtk.vtkNamedColors()
        
        sphereSource = vtk.vtkSphereSource()
        sphereSource.SetCenter(0.0, 0.0, 0.0)
        sphereSource.SetRadius(1.0)
        sphereSource.Update()

        polydata = sphereSource.GetOutput()

        # Create a mapper
        mapper = vtk.vtkPolyDataMapper()
        mapper.SetInputData(polydata)

        # Create an actor
        actor = vtk.vtkActor()
        actor.SetMapper(mapper)
        actor.GetProperty().SetColor(colors.GetColor3d('MistyRose'))
        self.renderer.AddActor(actor)
        self.renderer.SetBackground(colors.GetColor3d('SlateGray'))
        
        self.axes_actor = vtk.vtkAxesActor()

        self.axes_widget = vtk.vtkOrientationMarkerWidget()
        self.axes_widget.SetInteractor(self.iren)
        # rgba = [0] * 4
        # colors.GetColor('Carrot', rgba)
        self.axes_widget.SetOutlineColor(0.9300, 0.5700, 0.1300)
        self.axes_widget.SetOrientationMarker(self.axes_actor)
        self.axes_widget.SetViewport(0.0, 0.0, 0.4, 0.4)
        self.axes_widget.SetEnabled(1)
        # widget.InteractiveOn()

        self.renderer.GetActiveCamera().Azimuth(50)
        self.renderer.GetActiveCamera().Elevation(-30)

        self.renderer.ResetCamera()
        self.iren.Render()

        # Begin mouse interaction
        self.iren.Start()
            

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MyMainWindow()
    window.show()
    sys.exit(app.exec_())