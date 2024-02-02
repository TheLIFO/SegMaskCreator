import sys
import vtk
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget
from vtk.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor

class MyMainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        # Create a VTK renderer and render window
        self.renderer = vtk.vtkRenderer()
        self.renderWindow = vtk.vtkRenderWindow()
        self.renderWindow.AddRenderer(self.renderer)

        # Create a Qt widget for VTK rendering
        self.vtkWidget = QVTKRenderWindowInteractor(self)
        self.vtkWidget.SetRenderWindow(self.renderWindow)

        # Set up layout
        self.layout = QVBoxLayout()
        self.layout.addWidget(self.vtkWidget)

        # Create a central widget and set the layout
        self.centralWidget = QWidget()
        self.centralWidget.setLayout(self.layout)
        self.setCentralWidget(self.centralWidget)
        
        
        

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MyMainWindow()
    window.show()
    sys.exit(app.exec_())