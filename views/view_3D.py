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
        
        
        self._container = QtWidgets.QGroupBox(self)
        self._container.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding))
        
        layout = QtWidgets.QGridLayout()    
        self._container.setLayout(layout)    
        
        self.plotter3d =  QtInteractor(self)        

        # threshold          
        self.bt_threshold = QtWidgets.QPushButton("Threshold")
        layout.addWidget(self.plotter3d, 0, 0)
        layout.addWidget(self.bt_threshold, 1, 0)
        self.bt_threshold.clicked.connect(main_controller.set_threshold_clicked)
               
        
        layout = QtWidgets.QVBoxLayout(self)
        layout.addWidget(self._container)
        # listen to model event signals 
        model.mesh_changed.connect(self.on_mesh_changed)

    def closeEvent(self, QCloseEvent):
        super().closeEvent(QCloseEvent)
        self.plotter3d.Finalize() # does not work -> creates weird openGL error
        
        
    @pyqtSlot(pv.DataSet)
    def on_mesh_changed(self, mesh):
        self.plot_mesh(mesh)
    
    def plot_model(self, model):
        try:
            mesh = model.getMesh()
            self.plot_mesh(mesh)                
        except Exception:
            pass
    
    def plot_mesh(self, mesh):        
        self.plotter3d.add_mesh(mesh, name = 'view3D')
        self.update()
