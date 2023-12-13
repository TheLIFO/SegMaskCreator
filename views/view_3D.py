import sys
import random

from PyQt5 import QtWidgets
from PyQt5.QtCore import Qt, QObject, pyqtSlot
import pyvista as pv

from pyvistaqt import QtInteractor, BackgroundPlotter, MultiPlotter
from model.model import Model

# importing pyqtgraph as pg
import pyqtgraph as pg

class View3D(QtWidgets.QWidget):
    
    def __init__(self, parent, model, main_controller, is_visible = False):
        super().__init__(parent)
        self.is_visible = is_visible
        
        
        self.layout = QtWidgets.QGridLayout()
        self.setLayout(self.layout)
            
        self.plotter =  QtInteractor(self)        
        self.layout.addWidget(self.plotter.interactor, 0, 0)
 
        # threshold          
        self.bt_threshold = QtWidgets.QPushButton("Threshold")
        self.layout.addWidget(self.bt_threshold, 1, 0)
        self.bt_threshold.clicked.connect(main_controller.set_threshold_clicked)

                       
        # listen to model event signals 
        model.mesh_changed.connect(self.on_mesh_changed)
        
        if is_visible:
            self.show()             
    
    # def _setVisible(self, is_visible):
    #     self.is_visible = is_visible
    #     self._update()
        
    # def _update(self):
    #     if self.is_visible:   
    #         self.plotter.update()         
    #         self.plotter.show()            
            
  
    
    @pyqtSlot(pv.DataSet)
    def on_mesh_changed(self, mesh):
        self.plot_mesh(mesh)
    
    def plot_model(self, model):
        if self.is_visible:  
            try:
                mesh = model.getMesh()
                self.plot_mesh(mesh)                
            except Exception:
                pass
    
    def plot_mesh(self, mesh):
        self.plotter.clear()
        self.plotter.add_mesh(mesh)
        self.update()
