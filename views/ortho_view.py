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
        
        # plotter for overview
        self.setLayout(layout)
        self.plotter3D =  QtInteractor(self)                
        layout.addWidget(self.plotter3D, 0, 0)
        
        
        # plotter for several cut 2D views
        self.plotter_ortho_view_yz =  QtInteractor(self)   
        self.plotter_ortho_view_yz.enable_image_style()
        layout.addWidget(self.plotter_ortho_view_yz, 0, 1)
        
        self.plotter_ortho_view_xz =  QtInteractor(self)
        self.plotter_ortho_view_xz.enable_image_style()
        layout.addWidget(self.plotter_ortho_view_xz, 1, 0)
        
        self.plotter_ortho_view_xy =  QtInteractor(self)
        self.plotter_ortho_view_xy.enable_image_style()
        layout.addWidget(self.plotter_ortho_view_xy, 1, 1)
        
        
        
        self.plotter_ortho_view_r =  QtInteractor(self)
        self.plotter_ortho_view_r.enable_image_style()
        layout.addWidget(self.plotter_ortho_view_r, 0, 2)
        
        # listen to model event signals     
        self._model.mesh_changed.connect(self.on_mesh_changed)
        self._model.slice_pos_changed.connect(self.on_slice_pos_changed)
        self._model.mesh_changed.connect(self.on_slice_bounds_changed)

        self.cutter_YZ = vtk.vtkCutter()
        self.plane_YZ = vtk.vtkPlane()
        
        self.cutter_XZ = vtk.vtkCutter()
        self.plane_XZ = vtk.vtkPlane()

        self.cutter_XY = vtk.vtkCutter()
        self.plane_XY = vtk.vtkPlane()
        
        self.cutter_R = vtk.vtkCutter()
        self.plane_R = vtk.vtkPlane()
        

        # self.plotter_ortho_views.subplot(0, 0)
        self.clip_plane_widget_X = self.plotter3D.add_plane_widget(assign_to_axis = 'x', test_callback = False, callback = self.on_clip_plane_X_changed, interaction_event="always",)
        self.clip_plane_widget_Y = self.plotter3D.add_plane_widget(assign_to_axis = 'y', test_callback = False, callback = self.on_clip_plane_Y_changed, interaction_event="always",)
        self.clip_plane_widget_Z = self.plotter3D.add_plane_widget(assign_to_axis = 'z', test_callback = False, callback = self.on_clip_plane_Z_changed, interaction_event="always",)
        self.clip_plane_widget_R = self.plotter3D.add_plane_widget(assign_to_axis = 'z', test_callback = False, callback = self.on_clip_plane_R_changed, interaction_event="always",)
        
    def on_clip_plane_X_changed(self, normal, origin):
        new_origin = [round(a*2)/2 for a in list(origin)]                
        self._model.slice_pos =  {  "x": new_origin[0],
                                    "y": self._model.slice_pos["y"],
                                    "z": self._model.slice_pos["z"],
                                    "r": self._model.slice_pos["r"],
                                    "r_a": self._model.slice_pos["r_a"],
                                    "r_x": self._model.slice_pos["r_x"],
                                    "r_y": self._model.slice_pos["r_y"]}
        
    def on_clip_plane_Y_changed(self, normal, origin):
        new_origin = [round(a*2)/2 for a in list(origin)]                
        self._model.slice_pos =  {  "x": self._model.slice_pos["x"],
                                    "y": new_origin[1],
                                    "z": self._model.slice_pos["z"],
                                    "r": self._model.slice_pos["r"],
                                    "r_a": self._model.slice_pos["r_a"],
                                    "r_x": self._model.slice_pos["r_x"],
                                    "r_y": self._model.slice_pos["r_y"] }          

    def on_clip_plane_Z_changed(self, normal, origin):
        new_origin = [round(a*2)/2 for a in list(origin)]        
        self._model.slice_pos = {   "x": self._model.slice_pos["x"],
                                    "y": self._model.slice_pos["y"],
                                    "z": new_origin[2],
                                    "r": self._model.slice_pos["r"],
                                    "r_a": self._model.slice_pos["r_a"],
                                    "r_x": self._model.slice_pos["r_x"],
                                    "r_y": self._model.slice_pos["r_y"] }

    def on_clip_plane_R_changed(self, normal, origin):
        print ("TODO")
        pass
        new_origin = [round(a*10)/10 for a in list(origin)]        
        self._model.slice_pos = {   "x": self._model.slice_pos["x"],
                                    "y": self._model.slice_pos["y"],
                                    "z": self._model.slice_pos["z"],
                                    "r": self._model.slice_pos["r"],
                                    "r_a": self._model.slice_pos["r_a"],
                                    "r_x": self._model.slice_pos["r_x"],
                                    "r_y": self._model.slice_pos["r_y"] }
        
                 
    @pyqtSlot(pv.DataSet)
    def on_mesh_changed(self):
        if self._model.mesh is None:
            return
        self.update_mesh()
    
    def on_slice_pos_changed(self):
        if self._model.mesh is None:
            return
        print ('on slice pos changed (ortho view)')
        self.update_plots()
    
    
    def on_slice_bounds_changed(self):
        bounds = self._model.slice_bounds
        self.clip_plane_widget_X.PlaceWidget(bounds["x"]["min"], bounds["x"]["max"], bounds["y"]["min"], bounds["y"]["max"], bounds["z"]["min"], bounds["z"]["max"])
        self.clip_plane_widget_Y.PlaceWidget(bounds["x"]["min"], bounds["x"]["max"], bounds["y"]["min"], bounds["y"]["max"], bounds["z"]["min"], bounds["z"]["max"])
        self.clip_plane_widget_Z.PlaceWidget(bounds["x"]["min"], bounds["x"]["max"], bounds["y"]["min"], bounds["y"]["max"], bounds["z"]["min"], bounds["z"]["max"])
    
        # TODO
        self.clip_plane_widget_R.PlaceWidget(bounds["x"]["min"], bounds["x"]["max"], bounds["y"]["min"], bounds["y"]["max"], bounds["z"]["min"], bounds["z"]["max"])
    
    
    def update_plots(self):
        
        print("update plot 3D ortho...(1)")
        
        self.plane_YZ.SetOrigin([self._model.slice_pos["x"], 0, 0])
        self.plane_XZ.SetOrigin([0, self._model.slice_pos["y"], 0])
        self.plane_XY.SetOrigin([0, 0, self._model.slice_pos["z"]])

        #TODO
        self.plane_R.SetOrigin([self._model.slice_pos["r_x"], self._model.slice_pos["r_y"], 0])
        
        print("update plot 3D ortho...(cutter)")
        
        if self._model.show_cut_views["x"]:
            self.cutter_YZ.Update()
        if self._model.show_cut_views["y"]:
            self.cutter_XZ.Update()
        if self._model.show_cut_views["z"]:
            self.cutter_XY.Update()
        if self._model.show_cut_views["r"]:
            self.cutter_R.Update()


        self.clip_plane_widget_X.SetOrigin([self._model.slice_pos["x"], self._model.mesh.center[1], self._model.mesh.center[2]])
        self.clip_plane_widget_Y.SetOrigin([self._model.mesh.center[0], self._model.slice_pos["y"], self._model.mesh.center[2]])
        self.clip_plane_widget_Z.SetOrigin([self._model.mesh.center[0], self._model.mesh.center[2], self._model.slice_pos["z"]])
        self.clip_plane_widget_R.SetOrigin([self._model.slice_pos["r_x"], self._model.slice_pos["r_y"], 0])
        
        self.plotter_ortho_view_yz.camera.reset_clipping_range()
        self.plotter_ortho_view_xz.camera.reset_clipping_range()
        self.plotter_ortho_view_xy.camera.reset_clipping_range()
        self.plotter_ortho_view_r.camera.reset_clipping_range()
        
        print("update plot 3D ortho...ok")
        
        
    
    def update_mesh(self):   
                     
        if self._model.mesh is None:
            return
        print("update mesh...")
        self.plotter3D.add_mesh(self._model.mesh, name = "mesh3Doverview", opacity = 0.5, show_scalar_bar = False)
        self.plotter3D.show_axes_all()
        # self.plotter3D.set_scale(self._model.mesh_scale[0], self._model.mesh_scale[1], self._model.mesh_scale[2], True)
               
        self.cutter_YZ.SetInputData(self._model.mesh)
        self.cutter_YZ.SetCutFunction(self.plane_YZ)        
        self.plane_YZ.SetOrigin(self._model.mesh.center)
        self.plane_YZ.SetNormal(1, 0, 0)
        
        self.cutter_XZ.SetInputData(self._model.mesh)
        self.cutter_XZ.SetCutFunction(self.plane_XZ)        
        self.plane_XZ.SetOrigin(self._model.mesh.center)
        self.plane_XZ.SetNormal(0, 1, 0)
        
        self.cutter_XY.SetInputData(self._model.mesh)
        self.cutter_XY.SetCutFunction(self.plane_XY)        
        self.plane_XY.SetOrigin(self._model.mesh.center)
        self.plane_XY.SetNormal(0, 0, 1)
        
        self.cutter_R.SetInputData(self._model.mesh)
        self.cutter_R.SetCutFunction(self.plane_R)        
        self.plane_R.SetOrigin(self._model.mesh.center)
        self.plane_R.SetNormal(0, 0, 1)
        
        
        font_scale = 1.5
        self.plotter_ortho_view_yz.add_mesh(self.cutter_YZ, name = "cutter_YZ", show_scalar_bar = False)
        self.plotter_ortho_view_yz.view_yz()
        self.plotter_ortho_view_yz.enable_parallel_projection()
        self.plotter_ortho_view_yz.add_ruler(
                pointa=[0, self._model.mesh.bounds[2], self._model.mesh.bounds[4]], # line y
                pointb=[0, self._model.mesh.bounds[3], self._model.mesh.bounds[4]], # line y
                flip_range=True,
                title="Y Distance",
                font_size_factor = font_scale)
        self.plotter_ortho_view_yz.add_ruler(
                pointa=[0, self._model.mesh.bounds[3], self._model.mesh.bounds[5]], # line z
                pointb=[0, self._model.mesh.bounds[3], self._model.mesh.bounds[4]], # line z
                flip_range=True,
                title="Z Distance",
                font_size_factor = font_scale)
        
        self.plotter_ortho_view_xz.add_mesh(self.cutter_XZ, name = "cutter_XZ", show_scalar_bar = False)
        self.plotter_ortho_view_xz.view_xz()
        self.plotter_ortho_view_xz.enable_parallel_projection()
        self.plotter_ortho_view_xz.add_ruler(
                pointa=[self._model.mesh.bounds[0], self._model.mesh.bounds[2], 0.0], # line x
                pointb=[self._model.mesh.bounds[1], self._model.mesh.bounds[2], 0.0], # line x
                flip_range=True,
                title="X Distance",
                font_size_factor = font_scale)
        self.plotter_ortho_view_xz.add_ruler(
                pointa=[0.0, self._model.mesh.bounds[3], self._model.mesh.bounds[5]], # line z
                pointb=[0.0, self._model.mesh.bounds[3], self._model.mesh.bounds[4]], # line z
                flip_range=True,
                title="Z Distance",
                font_size_factor = font_scale)
        
        
        self.plotter_ortho_view_xy.add_mesh(self.cutter_XY, name = "cutter_XY", show_scalar_bar = False)
        self.plotter_ortho_view_xy.view_xy()
        self.plotter_ortho_view_xy.enable_parallel_projection()
        self.plotter_ortho_view_xy.add_ruler(
                pointa=[self._model.mesh.bounds[0], self._model.mesh.bounds[2], 0.0], # line x
                pointb=[self._model.mesh.bounds[1], self._model.mesh.bounds[2], 0.0], # line x
                flip_range=True,
                title="X Distance",
                font_size_factor = font_scale)
        self.plotter_ortho_view_xy.add_ruler(
                pointa=[self._model.mesh.bounds[0], self._model.mesh.bounds[3], 0.0], # line y
                pointb=[self._model.mesh.bounds[0], self._model.mesh.bounds[2], 0.0], # line y
                flip_range=True,
                title="Y Distance",
                font_size_factor = font_scale)

        self.plotter_ortho_view_xy.add_mesh(self.cutter_R, name = "cutter_R", show_scalar_bar = False)
        self.plotter_ortho_view_xy.view_xy()
        self.plotter_ortho_view_xy.enable_parallel_projection()
        # self.plotter_ortho_view_xy.add_ruler(
        #         pointa=[self._model.mesh.bounds[0], self._model.mesh.bounds[2], 0.0], # line x
        #         pointb=[self._model.mesh.bounds[1], self._model.mesh.bounds[2], 0.0], # line x
        #         flip_range=True,
        #         title="X Distance",
        #         font_size_factor = font_scale)
        # self.plotter_ortho_view_xy.add_ruler(
        #         pointa=[self._model.mesh.bounds[0], self._model.mesh.bounds[3], 0.0], # line y
        #         pointb=[self._model.mesh.bounds[0], self._model.mesh.bounds[2], 0.0], # line y
        #         flip_range=True,
        #         title="Y Distance",
        #         font_size_factor = font_scale)


        self.update()
        self.update_plots()

        print("update mesh...ok")
        
        
    def closeEvent(self, QCloseEvent):
        super().closeEvent(QCloseEvent)
        self.plotter_ortho_view_yz.Finalize()
        self.plotter_ortho_view_xz.Finalize()
        self.plotter_ortho_view_xy.Finalize()
        self.plotter3D.Finalize() 

