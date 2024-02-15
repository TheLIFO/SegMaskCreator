from PyQt5 import uic

from PyQt5 import QtWidgets
from PyQt5.QtCore import pyqtSlot
import vtk
from vtk.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor
# import pyvista as pv

# from pyvistaqt import QtInteractor



# this class contains the viewFrame depicting the loaded CT image in 3D

class View3D(QtWidgets.QWidget):
    
    def __init__(self, model, main_controller):
        super(View3D, self).__init__()
        
        self._model = model
        
        # self._container = QtWidgets.QGroupBox(self)
        # self._container.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding))
        
        layout = QtWidgets.QGridLayout()    
        self.setLayout(layout)    
        
        self.renderer3D = vtk.vtkRenderer()
        self.vtkWidget3D = QVTKRenderWindowInteractor(self)
        self.vtkWidget3D.GetRenderWindow().AddRenderer(self.renderer3D)
        self.iren3D = self.vtkWidget3D.GetRenderWindow().GetInteractor()
          
        layout.addWidget(self.vtkWidget3D, 0, 0)
        
        
        self.ui_view = uic.loadUi("views/ui_threshold.ui")        
        layout.addWidget(self.ui_view.gridLayoutWidget, 1, 0, 1, 1)
        
        self.ui_view.spinBox_threshold.textChanged.connect(self.spinBox_threshold_changed)
        self.ui_view.horizontal_slider_threshold.sliderReleased.connect(self.slider_threshold_changed)
        self.ui_view.checkBox_threshold_active.stateChanged.connect(self.checkbox_threshold_changed)
        
        # listen to model event signals 
        self._model.mesh_changed.connect(self.on_mesh_changed)
        # listen to threshold and threshold_active changed
        self._model.threshold_changed.connect(self.on_threshold_changed)
        self._model.threshold_bounds_changed.connect(self.on_threshold_bounds_changed)
        

    def slider_threshold_changed(self):
        self._model.threshold = self.ui_view.horizontal_slider_threshold.value()
    
    def spinBox_threshold_changed(self):
        self._model.threshold = self.ui_view.spinBox_threshold.value()
    
    def checkbox_threshold_changed(self):
        self._model.threshold_active = self.ui_view.checkBox_threshold_active.isChecked()
    
    def on_threshold_changed(self, threshold):
        self.ui_view.horizontal_slider_threshold.setValue(threshold)
        self.ui_view.spinBox_threshold.setValue(threshold)
        self.update_mesh()
        
    def on_threshold_bounds_changed(self, threshold_bounds):
        self.ui_view.horizontal_slider_threshold.setMinimum(round(threshold_bounds["min"]))
        self.ui_view.horizontal_slider_threshold.setMaximum(round(threshold_bounds["max"]))
        
        self.ui_view.spinBox_threshold.setMinimum(threshold_bounds["min"])
        self.ui_view.spinBox_threshold.setMaximum(threshold_bounds["max"])
    
    def closeEvent(self, QCloseEvent):
        super().closeEvent(QCloseEvent)
        self.vtkWidget3D.Finalize() # does not work?
        
    @pyqtSlot()
    def on_mesh_changed(self):
        self.update_mesh()
        
    
 
    def update_mesh(self):        
        # self.plotter3D.add_mesh(self._model.mesh, name = 'view3D')
        # self.plotter3D.show_axes_all()
        # self.plotter3D.set_scale(self._model.mesh_scale[0], self._model.mesh_scale[1], self._model.mesh_scale[2], True)
        # self.update()
        self.iren3D.Render()
