import pretty_errors
from PyQt5 import QtWidgets
from PyQt5.QtCore import Qt, QObject, pyqtSlot

import vtk
from vtk.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor

# from pyvistaqt import QtInteractor
from model.model import Model
from datetime import datetime
from views.lut import Luts

# this class contains the viewFrame depicting the loaded CT image in 3D
class OrthoViewSlice():
    def __init__(self, model, name, parent, origin, normal, overview_iren, overview_ren):
        
            
        self.name = name
        self.normal = normal
        self._model = model        
        
        
        self.planeWidget = vtk.vtkImagePlaneWidget()        
        self.planeWidget.SetResliceInterpolateToCubic()   
        self.planeWidget.SetMarginSizeX(0)
        self.planeWidget.SetMarginSizeY(0)
        self.planeWidget.AddObserver('InteractionEvent', self.on_clip_plane_changed)
        self.planeWidget.TextureVisibilityOn()    
        self.planeWidget.SetInteractor(overview_iren)
        self.planeWidget.SetCurrentRenderer(overview_ren)
        
        self.ren = vtk.vtkRenderer()
        camera = vtk.vtkCamera()
        camera.ParallelProjectionOn()
        self.ren.SetActiveCamera(camera)
        self.vtkWidget = QVTKRenderWindowInteractor(parent)
        self.vtkWidget.GetRenderWindow().AddRenderer(self.ren)
        self.iren = self.vtkWidget.GetRenderWindow().GetInteractor()    
        
        
        # this is a cursor of sort
        self.sphere = vtk.vtkSphereSource()
        self.sphere.SetRadius(0.5)  
        mapper = vtk.vtkPolyDataMapper()
        mapper.SetInputConnection(self.sphere.GetOutputPort())
        sphereactor = vtk.vtkActor()
        sphereactor.SetMapper(mapper)
        sphereactor.GetProperty().SetColor(vtk.vtkNamedColors().GetColor3d("Gold"))
        self.ren.AddActor(sphereactor)
        
        # self.ren.AddActor2D(scalarBar)
    
    def on_clip_plane_changed(self, caller, event):
        self.reslicer.Update()
        self.iren.Render()
        
        
    
    def get_widget(self):
        return self.vtkWidget 

    def set_input(self, inputs, luts):
        self.inputs = inputs
        
        self.inputs[1].Update()
        
        # resize 'mapper', 'self.actor' and 'self.reslicer' to fit len(inputs)
        self.mapper = [None] * len(inputs)
        self.reslicer = [None] * len(inputs)
        self.actor = [None] * len(inputs)
        
                
        for idx in range(len(inputs)):
            if idx == 0:                
                self.reslicer[idx] = self.planeWidget.GetReslice()        
                self.reslicer[idx].SetOutputSpacing (self._model.mesh_scale)
            else:
                # several additional reslicers (starting with e.g. threshed image)
                self.reslicer[idx] = vtk.vtkImageReslice()            
                self.reslicer[idx].SetOutputSpacing  (self.reslicer[0].GetOutputSpacing()) # setting the same reslicer properties as the first on
                self.reslicer[idx].SetOutputOrigin   (self.reslicer[0].GetOutputOrigin())
                self.reslicer[idx].SetResliceAxes    (self.reslicer[0].GetResliceAxes())
                self.reslicer[idx].SetInputConnection(inputs[idx].GetOutputPort())
                
            
            # Create an instance of vtkImageMapToColors
            self.mapper[idx] = vtk.vtkImageMapToColors()
            self.mapper[idx].SetInputConnection(self.reslicer[idx].GetOutputPort())  # Set the input as the extracted slice from vtkImageReslice
            self.mapper[idx].SetLookupTable(luts[idx])
            
            self.actor[idx] = vtk.vtkImageActor()
            self.actor[idx].GetMapper().SetInputConnection(self.mapper[idx].GetOutputPort())
            self.ren.AddActor(self.actor[idx])
            
        
        self.planeWidget.On()
        self.planeWidget.SetInputData(self.inputs[0].GetOutput())
        self.planeWidget.PlaceWidget(self._model.slice_bounds['x']['min'] * self._model.mesh_scale[0], self._model.slice_bounds['x']['max'] * self._model.mesh_scale[0], 
                                     self._model.slice_bounds['y']['min'] * self._model.mesh_scale[1], self._model.slice_bounds['y']['max'] * self._model.mesh_scale[1],
                                     self._model.slice_bounds['z']['min'] * self._model.mesh_scale[2], self._model.slice_bounds['z']['max'] * self._model.mesh_scale[2])
        self.reslicer[0].Update()
        self.ren.ResetCamera() 
        
        self.ren.ResetCameraClippingRange()        
        self.iren.Start()
        self.update()
    
    def set_normal(self, normal):
        self.normal = normal
        self.update()
    
    def update(self):
        self.iren.Render()        
        # self.iren3D.Render() # TODO link to orthooverview emit signal when orthoview is updated??
    
    def mouseMoveCallback(self, obj, event):
        
        (lastX, lastY) = self.iren.GetLastEventPosition()
        (mouseX, mouseY) = self.iren.GetEventPosition()        
        
        
        coordinate = vtk.vtkCoordinate()
        coordinate.SetCoordinateSystemToDisplay()
        coordinate.SetValue(mouseX, mouseY)
        coord = coordinate.GetComputedWorldValue(self.ren)
        print("coord:", coord)
        
        self.sphere.SetCenter(coord[0], coord[1], 0)
        self.iren.Render()
        #transform coordinates from local orientation to global one according to resliceorientation
        origin = self.reslicer.GetOutput().GetOrigin()
        pixel = [coord[0], coord[1]]
        resliceAxes = self.reslicer.GetResliceAxes()
        coord = resliceAxes.MultiplyDoublePoint([pixel[0]+origin[0], pixel[1]+origin[1], origin[2], 1])
        
        
        
        # translate coordinates into array indices
        x = round(coord[0]/self._model.mesh_scale[0])
        y = round(coord[1]/self._model.mesh_scale[1])
        z = round(coord[2]/self._model.mesh_scale[2])
        
        if  (x < self._model.slice_bounds['x'].min) or (x > self._model.slice_bounds['x'].max) or \
            (y < self._model.slice_bounds['y'].min) or (y > self._model.slice_bounds['y'].max) or \
            (z < self._model.slice_bounds['z'].min) or (z > self._model.slice_bounds['z'].max):            
            value = 0
            value_threshed = 0
        else:
            value          = self.mesh.GetOutput().GetScalarComponentAsDouble(x, y, z, 0)
            value_threshed = self.threshed.GetOutput().GetScalarComponentAsDouble(x, y, z, 0)
                
        print("x mouse: ", mouseX, " y mouse: ", mouseY, "world-x: ",coord[0], " world-y: ", coord[1],"world-z: ", coord[2],"   Scalar: ", value, "threshed: ", value_threshed)
        
        self.interactorStyle.OnMouseMove()

    def set_slice(self, position):
        
        # sliceSpacing = self.reslicer.GetOutput().GetSpacing()[2]
        
        
        # position = self.planeWidget.GetSlicePosition()
        self.planeWidget.SetSlicePosition(position)
        
        
        self.reslicer.Update()
        self.reslicer_threshed.Update()
        self.reslicer_threshed.SetOutputOrigin(self.reslicer.GetOutputOrigin())        
        self.reslicer_threshed.SetResliceAxes(self.reslicer.GetResliceAxes())
        self.update()
     
    
class OrthoViewOverview():   
      
    def __init__(self, model, name, parent):
        
            
        self.name = name        
        self._model = model   
        
        self.ren = vtk.vtkRenderer()
        self.vtkWidget = QVTKRenderWindowInteractor(parent)
        self.vtkWidget.GetRenderWindow().AddRenderer(self.ren)
        self.iren = self.vtkWidget.GetRenderWindow().GetInteractor()
        
        colors = vtk.vtkNamedColors()
        
        
        #create outline of 3D view
        outline = vtk.vtkOutlineFilter()
        outline.SetInputData(self._model.mesh.GetOutput())

        outlineMapper = vtk.vtkPolyDataMapper()
        outlineMapper.SetInputConnection(outline.GetOutputPort())

        self.outlineActor = vtk.vtkActor()
        self.outlineActor.SetMapper(outlineMapper)
        
        # Create transfer mapping scalar value to opacity.
        opacityTransferFunction = vtk.vtkPiecewiseFunction()
        opacityTransferFunction.AddPoint(0, 0.0)
        opacityTransferFunction.AddPoint(450, 0.0)
        opacityTransferFunction.AddPoint(451, 0.2)
        
        opacityThreshedTransferFunction = vtk.vtkPiecewiseFunction()
        opacityThreshedTransferFunction.AddPoint(0, 0)
        opacityThreshedTransferFunction.AddPoint(1, 1)
        opacityThreshedTransferFunction.AddPoint(2500, 1)
        
        # Create transfer mapping scalar value to color.
        colorTransferFunction = vtk.vtkColorTransferFunction()
        colorTransferFunction.AddRGBPoint(0.0, 0.0, 0.0, 0.0)
        colorTransferFunction.AddRGBPoint(255.0, 1.0, 1.0, 1.0)

        colorThreshedTransferFunction = vtk.vtkColorTransferFunction()
        colorThreshedTransferFunction.AddRGBPoint(0.0, 1.0, 0.0, 0.0)
        colorThreshedTransferFunction.AddRGBPoint(255.0, 1.0, 0.0, 0.0)
        
        # The property describes how the data will look.
        volumeProperty = vtk.vtkVolumeProperty()
        volumeProperty.SetColor(colorTransferFunction)
        volumeProperty.SetScalarOpacity(opacityTransferFunction)
        volumeProperty.ShadeOn()
        volumeProperty.SetInterpolationTypeToLinear()

        # The property describes how the data will look.
        volumeThreshedProperty = vtk.vtkVolumeProperty()
        volumeThreshedProperty.SetColor(colorThreshedTransferFunction)
        volumeThreshedProperty.SetScalarOpacity(opacityThreshedTransferFunction)
        volumeThreshedProperty.ShadeOn()
        volumeThreshedProperty.SetInterpolationTypeToLinear()


        # The mapper / ray cast function know how to render the data.
        volumeMapper = vtk.vtkFixedPointVolumeRayCastMapper()
        volumeMapper.SetInputConnection(self._model.mesh.GetOutputPort())
        
        # The volume holds the mapper and the property and
        # can be used to position/orient the volume.
        volume = vtk.vtkVolume()
        volume.SetMapper(volumeMapper)
        volume.SetProperty(volumeProperty)

            # The mapper / ray cast function know how to render the data.
        volumeThreshedMapper = vtk.vtkFixedPointVolumeRayCastMapper()
        volumeThreshedMapper.SetInputConnection(self._model.mesh_threshed.GetOutputPort())

      
        # The volume holds the mapper and the property and
        # can be used to position/orient the volume.
        volumeThreshed = vtk.vtkVolume()
        volumeThreshed.SetMapper(volumeThreshedMapper)
        volumeThreshed.SetProperty(volumeThreshedProperty)

        self.ren.AddVolume(volume)
        self.ren.AddVolume(volumeThreshed)
        self.ren.AddActor(self.outlineActor)
        self.ren.SetBackground(colors.GetColor3d('Wheat'))
        self.ren.GetActiveCamera().Azimuth(45)
        self.ren.GetActiveCamera().Elevation(30)
        
                    
        self.interactorStyle3D = vtk.vtkInteractorStyleTrackballCamera()
        self.iren.SetInteractorStyle(self.interactorStyle3D)
    
    def get_widget(self):
        return self.vtkWidget 

    def set_input(self, inputs):
        self.inputs = inputs
        
        self.inputs[1].Update()
        
        # resize 'mapper', 'self.actor' and 'self.reslicer' to fit len(inputs)
        mapper = [None] * len(inputs)
      
        self.actor = [None] * len(inputs)
        
        self.ren.ResetCamera() 
        self._model.mesh_threshed.Update()
        
        self.ren.ResetCameraClippingRange()        
        self.iren.Start()
        self.update()
        
    def update(self):
        self.iren.Render()
    
    
class OrthoView(QtWidgets.QWidget):
    def __init__(self, model, main_controller):
        super(OrthoView, self).__init__()
        
        self._model = model
        
        self.ortho_views = {}
        self.ortho_overview = OrthoViewOverview(self._model, "OrthoOverview", self)
        
        self.ortho_views['xy'] = OrthoViewSlice(self._model, 'xy', self, [0,0,0], [0,0,1], self.ortho_overview.iren, self.ortho_overview.ren)
        self.ortho_views['xz'] = OrthoViewSlice(self._model, 'xz', self, [0,0,0], [0,1,0], self.ortho_overview.iren, self.ortho_overview.ren)
        self.ortho_views['yz'] = OrthoViewSlice(self._model, 'yz', self, [0,0,0], [1,0,0], self.ortho_overview.iren, self.ortho_overview.ren)
        
        layout = QtWidgets.QGridLayout()        
        self.setLayout(layout)           
        
        
        # sp_retain = widget.sizePolicy()
        # sp_retain.setRetainSizeWhenHidden(True)
        # widget.setSizePolicy(sp_retain)
        
        self.ortho_overview.get_widget().sizePolicy().setRetainSizeWhenHidden(True)
        self.ortho_views['yz'].get_widget().sizePolicy().setRetainSizeWhenHidden(True)
        self.ortho_views['xz'].get_widget().sizePolicy().setRetainSizeWhenHidden(True)
        self.ortho_views['xy'].get_widget().sizePolicy().setRetainSizeWhenHidden(True)
        
        # plotter for overview        
        layout.addWidget(self.ortho_overview.get_widget(), 0, 0)
                
        # plotter for several cut 2D views
        layout.addWidget(self.ortho_views['yz'].get_widget(), 0, 1)
        layout.addWidget(self.ortho_views['xz'].get_widget(), 1, 0)
        layout.addWidget(self.ortho_views['xy'].get_widget(), 1, 1)
        
        # listen to model event signals     
        self._model.mesh_changed.connect(self.on_mesh_changed)
        self._model.slice_pos_changed.connect(self.on_slice_pos_changed)
        self._model.slice_bounds_changed.connect(self.on_slice_bounds_changed)
        self._model.show_cut_views_changed.connect(self.on_show_cut_views_changed)

        
        #update visibility of widgets
        self.on_show_cut_views_changed(self._model.show_cut_views)
        
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
        return
        new_origin = [round(a*10)/10 for a in list(origin)]        
        self._model.slice_pos = {   "x": self._model.slice_pos["x"],
                                    "y": self._model.slice_pos["y"],
                                    "z": self._model.slice_pos["z"],
                                    "r": self._model.slice_pos["r"],
                                    "r_a": self._model.slice_pos["r_a"],
                                    "r_x": self._model.slice_pos["r_x"],
                                    "r_y": self._model.slice_pos["r_y"] }
        
    def on_clip_plane_RC_changed(self, normal, origin):
        print ("TODO")
        return
        new_origin = [round(a*10)/10 for a in list(origin)]        
        self._model.slice_pos = {   "x": self._model.slice_pos["x"],
                                    "y": self._model.slice_pos["y"],
                                    "z": self._model.slice_pos["z"],
                                    "r": self._model.slice_pos["r"],
                                    "r_a": self._model.slice_pos["r_a"],
                                    "r_x": self._model.slice_pos["r_x"],
                                    "r_y": self._model.slice_pos["r_y"] }
        
                 
    @pyqtSlot()
    def on_mesh_changed(self):
        if self._model.mesh is None:
            return
        self.update_mesh()
    
    def on_slice_pos_changed(self):
        if self._model.mesh is None:
            return
        print ('on slice pos changed (ortho view)')
        self.update_plots()
    
    
    def on_slice_bounds_changed(self, slice_bounds):
        pass
        """
        # TODO !!!!
        self.clip_plane_widget_X.PlaceWidget(slice_bounds["x"]["min"], slice_bounds["x"]["max"], slice_bounds["y"]["min"], slice_bounds["y"]["max"], slice_bounds["z"]["min"], slice_bounds["z"]["max"])
        self.clip_plane_widget_Y.PlaceWidget(slice_bounds["x"]["min"], slice_bounds["x"]["max"], slice_bounds["y"]["min"], slice_bounds["y"]["max"], slice_bounds["z"]["min"], slice_bounds["z"]["max"])
        self.clip_plane_widget_Z.PlaceWidget(slice_bounds["x"]["min"], slice_bounds["x"]["max"], slice_bounds["y"]["min"], slice_bounds["y"]["max"], slice_bounds["z"]["min"], slice_bounds["z"]["max"])
    
        # TODO
        self.clip_plane_widget_R.PlaceWidget(slice_bounds["x"]["min"], slice_bounds["x"]["max"], slice_bounds["y"]["min"], slice_bounds["y"]["max"], slice_bounds["z"]["min"], slice_bounds["z"]["max"])
        """
    
    def on_show_cut_views_changed(self, show_cut_views):
        for show_cut_view in show_cut_views:
            self.ortho_views[show_cut_view].get_widget().setVisible(show_cut_views[show_cut_view])
        
        
        
        if not self._model.mesh == None:
            self.update_plots()
        
        
    def update_plots(self):
        pass
        # TODO!!!!
        # TODO update_plots only updates cutters that have changed -> own dict with setter method emitting resp. signal with new pos_slice value
        # "to be implemented"-planes in other views need still be updated, or are done automatically
        
        # print("update plot 3D ortho...(1)")
        
        # self.plane_YZ.SetOrigin([self._model.slice_pos["x"], 0, 0])
        # self.plane_XZ.SetOrigin([0, self._model.slice_pos["y"], 0])
        # self.plane_XY.SetOrigin([0, 0, self._model.slice_pos["z"]])

        # #TODO
        # self.plane_R.SetOrigin([self._model.slice_pos["r_x"], self._model.slice_pos["r_y"], 0])
        
        # print("update plot 3D ortho...(cutter)")
        
        # if self._model.show_cut_views["yz"]:
        #     self.reslice_YZ.Update()
        # if self._model.show_cut_views["xz"]:
        #     self.reslice_XZ.Update()
        # if self._model.show_cut_views["xy"]:
        #     self.reslice_XY.Update()
        

        # self.clip_plane_widget_X.SetOrigin([self._model.slice_pos["x"], self._model.mesh.center[1], self._model.mesh.center[2]])
        # self.clip_plane_widget_Y.SetOrigin([self._model.mesh.center[0], self._model.slice_pos["y"], self._model.mesh.center[2]])
        # self.clip_plane_widget_Z.SetOrigin([self._model.mesh.center[0], self._model.mesh.center[2], self._model.slice_pos["z"]])
        # self.clip_plane_widget_R.SetOrigin([self._model.slice_pos["r_x"], self._model.slice_pos["r_y"], 0])
        
        # self.plotter_ortho_view_yz.camera.reset_clipping_range()
        # self.plotter_ortho_view_xz.camera.reset_clipping_range()
        # self.plotter_ortho_view_xy.camera.reset_clipping_range()
        # self.plotter_ortho_view_r.camera.reset_clipping_range()
        
        # print("update plot 3D ortho...ok")
        
        
    
    def update_mesh(self):   
                     
        if self._model.mesh is None:
            return
        print("update mesh...")
        
        
        self.ortho_views['xy'].set_input([self._model.mesh, self._model.mesh_threshed], [Luts.get_standard_lut(),Luts.get_threshed_lut()])
        self.ortho_views['xz'].set_input([self._model.mesh, self._model.mesh_threshed], [Luts.get_standard_lut(),Luts.get_threshed_lut()])
        self.ortho_views['yz'].set_input([self._model.mesh, self._model.mesh_threshed], [Luts.get_standard_lut(),Luts.get_threshed_lut()])
        
        """
        # self.mesh_actor = self.plotter3D.add_mesh(self._model.mesh, name = "mesh3Doverview", opacity = 0.5, show_scalar_bar = False)
        # self.plotter3D.show_axes_all()
        # self.plotter3D.set_scale(self._model.mesh_scale[0], self._model.mesh_scale[1], self._model.mesh_scale[2], True)

        self.reslice_YZ.SetInputData(self._model.mesh.GetOutputPort())
        self.reslice_YZ.SetCutFunction(self.plane_YZ)        
        self.plane_YZ.SetOrigin(self._model.mesh.GetOutput.GetCenter())
        self.plane_YZ.SetNormal(1, 0, 0)
        
        self.reslice_XZ.SetInputData(self._model.mesh.GetOutputPort())
        self.reslice_XZ.SetCutFunction(self.plane_XZ)        
        self.plane_XZ.SetOrigin(self._model.mesh.GetOutput.GetCenter())
        self.plane_XZ.SetNormal(0, 1, 0)
        
        self.reslice_XY.SetInputData(self._model.mesh.GetOutputPort())
        self.reslice_XY.SetCutFunction(self.plane_XY)        
        self.plane_XY.SetOrigin(self._model.mesh.GetOutput.GetCenter())
        self.plane_XY.SetNormal(0, 0, 1)
        
        self.reslice_R.SetInputData(self._model.mesh.GetOutputPort())
        self.reslice_R.SetCutFunction(self.plane_R)        
        self.plane_R.SetOrigin(self._model.mesh.GetOutput.GetCenter())
        self.plane_R.SetNormal(0, 0, 1)
        
        self.reslice_RC.SetInputData(self._model.mesh.GetOutputPort())
        self.reslice_RC.SetCutFunction(self.plane_RC)        
        self.plane_RC.SetOrigin(self._model.mesh.GetOutput.GetCenter())
        self.plane_RC.SetNormal(0, 0, 1)
        
        
        font_scale = 1.5
        self.cut_YZ_actor = self.plotter_ortho_view_yz.add_mesh(self.reslice_YZ, name = "cutter_YZ", show_scalar_bar = False)
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
        
        self.cut_XZ_actor = self.plotter_ortho_view_xz.add_mesh(self.reslice_XZ, name = "cutter_XZ", show_scalar_bar = False)
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
        
        
        self.cut_XY_actor = self.plotter_ortho_view_xy.add_mesh(self.reslice_XY, name = "cutter_XY", show_scalar_bar = False)
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

        self.cut_R_actor_actor = self.plotter_ortho_view_r.add_mesh(self.reslice_R, name = "cutter_R", show_scalar_bar = False)
        self.plotter_ortho_view_r.view_xy()
        self.plotter_ortho_view_r.enable_parallel_projection()
        
        self.cut_RC_actor_actor = self.plotter_ortho_view_rc.add_mesh(self.reslice_RC, name = "cutter_RC", show_scalar_bar = False)
        self.plotter_ortho_view_rc.view_vector([0,1,0])
        self.plotter_ortho_view_rc.enable_parallel_projection()
        
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
        """

        self.update()
        self.update_plots()

        print("update mesh...ok")
        
        
    def closeEvent(self, QCloseEvent):
        super().closeEvent(QCloseEvent)
        # self.plotter_ortho_view_yz.Finalize()
        # self.plotter_ortho_view_xz.Finalize()
        # self.plotter_ortho_view_xy.Finalize()
        # self.plotter_ortho_view_r.Finalize()
        # self.plotter_ortho_view_rc.Finalize()
        # self.plotter3D.Finalize()  TODO 

