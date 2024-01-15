import sys
import random

from PyQt5 import QtWidgets
from PyQt5.QtCore import Qt, QObject, pyqtSlot
import pyvista as pv

from pyvistaqt import QtInteractor, BackgroundPlotter, MultiPlotter
from model.model import Model

# importing pyqtgraph as pg
import pyqtgraph as pg


# this class contains the viewFrame depicting the loaded CT image in 3D

class View3D(QtWidgets.QWidget):
    
    def __init__(self, model, main_controller):
        super(View3D, self).__init__()
        
        self._model = model
        
        self._container = QtWidgets.QGroupBox(self)
        self._container.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding))
        
        layout = QtWidgets.QGridLayout()    
        self._container.setLayout(layout)    
        
        self.plotter3D =  QtInteractor(self)    
        # self.plotter3D.enable_stereo_render()    

        # threshold          
        self.bt_threshold = QtWidgets.QPushButton("Threshold")
        layout.addWidget(self.plotter3D, 0, 0)
        layout.addWidget(self.bt_threshold, 1, 0)
        self.bt_threshold.clicked.connect(main_controller.on_threshold_clicked)
               
        
        layout = QtWidgets.QVBoxLayout(self)
        layout.addWidget(self._container)
        # listen to model event signals 
        self._model.mesh_changed.connect(self.on_mesh_changed)

    def closeEvent(self, QCloseEvent):
        super().closeEvent(QCloseEvent)
        self.plotter3D.Finalize() # does not work -> creates weird openGL error
        
        
    @pyqtSlot(pv.DataSet)
    def on_mesh_changed(self):
        self.plot_mesh()
    
 
    def plot_mesh(self):        
        self.plotter3D.add_mesh(self._model.mesh, name = 'view3D')
        self.plotter3D.show_axes_all()
        # self.plotter3D.set_scale(self._model.mesh_scale[0], self._model.mesh_scale[1], self._model.mesh_scale[2], True)
        self.update()
