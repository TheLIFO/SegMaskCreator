import sys
import random

from PyQt5 import QtWidgets
from PyQt5.QtCore import Qt, QObject, pyqtSlot
import pyvista as pv
import vtk


from pyvistaqt import QtInteractor
from model.model import Model
from datetime import datetime


# this class contains the viewFrame depicting the loaded CT image in 3D

class OrthoView(QtWidgets.QWidget):
    def __init__(self, model, main_controller):
        super(OrthoView, self).__init__()
        
        self._model = model
        layout = QtWidgets.QGridLayout()        
        self.setLayout(layout)
        self.plotter3D =  QtInteractor(self, shape=(2, 2))                
        layout.addWidget(self.plotter3D, 0, 0)
        
        # listen to model event signals     
        self._model.mesh_changed.connect(self.on_mesh_changed)
        self._model.slice_pos_changed.connect(self.on_slice_pos_changed)
        self._model.mesh_changed.connect(self.on_slice_bounds_changed)

        # self.cpos = [   (0.02430, 0.0336, 0.9446),
        #                 (0.02430, 0.0336, -0.02225),
        #                 (0.0, 1.0, 0.0)]
 
        
        self.cutter_X = vtk.vtkCutter()
        self.plane_X = vtk.vtkPlane()

        
        self.cutter_Y = vtk.vtkCutter()
        self.plane_Y = vtk.vtkPlane()

        
        self.cutter_Z = vtk.vtkCutter()
        self.plane_Z = vtk.vtkPlane()

        self.plotter3D.subplot(0, 0)
        self.clip_plane_widget_X = self.plotter3D.add_plane_widget(assign_to_axis = 'x', test_callback = False, callback = self.on_clip_plane_X_changed, interaction_event="always",)
        self.clip_plane_widget_Y = self.plotter3D.add_plane_widget(assign_to_axis = 'y', test_callback = False, callback = self.on_clip_plane_Y_changed, interaction_event="always",)
        self.clip_plane_widget_Z = self.plotter3D.add_plane_widget(assign_to_axis = 'z', test_callback = False, callback = self.on_clip_plane_Z_changed, interaction_event="always",)
        
    def on_clip_plane_X_changed(self, normal, origin):
        new_origin = [round(a) for a in list(origin)]
        slice_pos = self._model.slice_pos
        slice_pos['x'] = new_origin[0] 
        self._model.slice_pos = slice_pos

        print("pos: ", self._model.slice_pos, " - old_orig: ", origin, " - new_orig: ", new_origin)

    
    def on_clip_plane_Y_changed(self, normal, origin):
        new_origin = [round(a) for a in list(origin)]      
        slice_pos = self._model.slice_pos
        slice_pos['y'] = new_origin[1] 
        self._model.slice_pos = slice_pos

        print("pos: ", self._model.slice_pos, " - old_orig: ", origin, " - new_orig: ", new_origin)

    
    def on_clip_plane_Z_changed(self, normal, origin):
        new_origin = [round(a) for a in list(origin)]
        slice_pos = self._model.slice_pos
        slice_pos['z'] = new_origin[2] 
        self._model.slice_pos = slice_pos

        print("pos: ", self._model.slice_pos, " - old_orig: ", origin, " - new_orig: ", new_origin)

        
    def closeEvent(self, QCloseEvent):
        super().closeEvent(QCloseEvent)
        self.plotter3D.Finalize()           
                
    @pyqtSlot(pv.DataSet)
    def on_mesh_changed(self):
        self.update_mesh()
    
    def on_slice_pos_changed(self):
        if self._model.mesh is None:
            return
        self.update_plots()
    
    
    def on_slice_bounds_changed(self):
        bounds = self._model.slice_bounds
        self.clip_plane_widget_X.PlaceWidget(bounds["x"]["min"], bounds["x"]["max"], bounds["y"]["min"], bounds["y"]["max"], bounds["z"]["min"], bounds["z"]["max"])
        self.clip_plane_widget_Y.PlaceWidget(bounds["x"]["min"], bounds["x"]["max"], bounds["y"]["min"], bounds["y"]["max"], bounds["z"]["min"], bounds["z"]["max"])
        self.clip_plane_widget_Z.PlaceWidget(bounds["x"]["min"], bounds["x"]["max"], bounds["y"]["min"], bounds["y"]["max"], bounds["z"]["min"], bounds["z"]["max"])
    
    def update_plots(self):
        self.plane_X.SetOrigin([self._model.slice_pos["x"], 0, 0])
        self.plane_Y.SetOrigin([0, self._model.slice_pos["y"], 0])
        self.plane_Z.SetOrigin([0, 0, self._model.slice_pos["z"]])
        self.cutter_X.Update()
        self.cutter_Y.Update()
        self.cutter_Z.Update()
        self.clip_plane_widget_X.SetOrigin([self._model.slice_pos["x"], 0, 0])
        self.clip_plane_widget_Y.SetOrigin([0, self._model.slice_pos["y"], 0])
        self.clip_plane_widget_Z.SetOrigin([0, 0, self._model.slice_pos["z"]])
        
        self.plotter3D.camera.reset_clipping_range()
    
    def update_mesh(self):                
        if self._model.mesh is None:
            return
        self.plotter3D.subplot(0, 0)
        
        self.plotter3D.add_mesh(self._model.mesh, name = "mesh3D", opacity = 0.5)
        
        self.cutter_X.SetInputData(self._model.mesh)
        self.cutter_X.SetCutFunction(self.plane_X)
        # self.plane_X.SetOrigin([self._model.slice_pos["x"], self._model.slice_pos["y"], self._model.slice_pos["z"]])
        self.plane_X.SetOrigin(self._model.mesh.center)
        self.plane_X.SetNormal(1, 0, 0)
        
        self.cutter_Y.SetInputData(self._model.mesh)
        self.cutter_Y.SetCutFunction(self.plane_Y)
        # self.plane_Y.SetOrigin([self._model.slice_pos["x"], self._model.slice_pos["y"], self._model.slice_pos["z"]])#
        self.plane_Y.SetOrigin(self._model.mesh.center)
        self.plane_Y.SetNormal(0, 1, 0)
        
        self.cutter_Z.SetInputData(self._model.mesh)
        self.cutter_Z.SetCutFunction(self.plane_Z)
        self.plane_Z.SetOrigin([self._model.slice_pos["x"], self._model.slice_pos["y"], self._model.slice_pos["z"]])
        self.plane_Z.SetOrigin(self._model.mesh.center)
        self.plane_Z.SetNormal(0, 0, 1)
        
        self.plotter3D.subplot(0, 1)
        self.plotter3D.add_mesh(self.cutter_X, name = "cutter_X")
        self.plotter3D.view_yz()
        self.plotter3D.enable_parallel_projection()
        self.plotter3D.disable()
        
        self.plotter3D.subplot(1, 0)
        self.plotter3D.add_mesh(self.cutter_Y, name = "cutter_Y")
        self.plotter3D.view_xz()
        self.plotter3D.enable_parallel_projection()
        self.plotter3D.disable()
        
        self.plotter3D.subplot(1, 1)
        self.plotter3D.add_mesh(self.cutter_Z, name = "cutter_Z")
        self.plotter3D.view_xy()
        self.plotter3D.enable_parallel_projection()
        self.plotter3D.disable()

        self.update()
        

        
        

