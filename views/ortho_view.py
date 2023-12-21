import sys
import random

from PyQt5 import QtWidgets
from PyQt5.QtCore import Qt, QObject, pyqtSlot
import pyvista as pv

from pyvistaqt import QtInteractor
from model.model import Model


# this class contains the viewFrame depicting the loaded CT image in 3D

class OrthoView(QtWidgets.QWidget):
    def __init__(self, model, main_controller):
        super(OrthoView, self).__init__()
        layout = QtWidgets.QGridLayout()        
        self.setLayout(layout)
        self.plotter3D =  QtInteractor(self, shape=(2, 2))                
        layout.addWidget(self.plotter3D, 0, 0)
        
        # listen to model event signals     
        model.mesh_changed.connect(self.on_mesh_changed)

        self.cpos = [   (0.02430, 0.0336, 0.9446),
                        (0.02430, 0.0336, -0.02225),
                        (0.0, 1.0, 0.0)]
        self.plotter3D.disable()
        # self._viewer = self.plotter3D.subplot(1, 1).show()
        self.slice_x = 0
        self.slice_y = 0
        self.slice_z = 0
        
        mesh = pv.PolyData()
        
        self.plot_mesh(mesh, self.cpos)
    
    def closeEvent(self, QCloseEvent):
        super().closeEvent(QCloseEvent)
        self.plotter3D.Finalize()           
                
    @pyqtSlot(pv.DataSet)
    def on_mesh_changed(self, mesh):
        self.plot_mesh(mesh)
    
    def plot_model(self, model):
        try:
            mesh = model.getMesh()
            self.plot_mesh(mesh)                
        except Exception:
            pass
    
    def plot_mesh(self, mesh, cpos = None):                
        
        slices = mesh.slice_orthogonal(x = self.slice_x, y = self.slice_y, z = self.slice_z)
        dargs = dict(cmap='gist_ncar_r', name ='ortho')
        # XYZ - show 3D scene first
        self.plotter3D.subplot(1, 1)
        self.plotter3D.add_mesh(slices, **dargs)
        self.plotter3D.show_grid()
        if cpos is None:
            self.plotter3D.camera_position = cpos
        else:
            self.cpos = self.plotter3D.camera_position
        
        # XY
        self.plotter3D.subplot(0, 0)
        self.plotter3D.add_mesh(slices, **dargs)
        self.plotter3D.show_grid()
        self.plotter3D.camera_position = 'xy'
        self.plotter3D.enable_parallel_projection()
        # ZY
        self.plotter3D.subplot(0, 1)
        self.plotter3D.add_mesh(slices, **dargs)
        self.plotter3D.show_grid()
        self.plotter3D.camera_position = 'zy'
        self.plotter3D.enable_parallel_projection()
        # XZ
        self.plotter3D.subplot(1, 0)
        self.plotter3D.add_mesh(slices, **dargs)
        self.plotter3D.show_grid()
        self.plotter3D.camera_position = 'xz'
        self.plotter3D.enable_parallel_projection()
        self.update()
        

        
        

