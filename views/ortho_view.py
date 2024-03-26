import pretty_errors
from PyQt5 import QtWidgets
from PyQt5.QtCore import pyqtSlot

import vtk
from vtk.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor
import numpy as np


# from pyvistaqt import QtInteractor
from model.model import Model
from datetime import datetime
from views.lut import Luts

# this class contains the viewFrame depicting the loaded CT image in 3D
class OrthoViewSlice():
    def __init__(self, model, name, parent, inputs, luts, origin, normal, direction, overview_iren, overview_ren):
                    
        self.name = name
        self.direction = direction
        if  self.direction == 'x':
            self.axis = 0
        elif self.direction == 'y':
            self.axis = 1
        elif self.direction == 'z': 
            self.axis = 2
            
        self.normal = normal
        self._model = model        
                
        self.ren = vtk.vtkRenderer()
        camera = vtk.vtkCamera()
        camera.ParallelProjectionOn()
        self.ren.SetActiveCamera(camera)
        self.vtkWidget = QVTKRenderWindowInteractor(parent)
        self.vtkWidget.GetRenderWindow().AddRenderer(self.ren)
        self.iren = self.vtkWidget.GetRenderWindow().GetInteractor()
        
        # Set up the interaction        
        self.interactorStyle = vtk.vtkInteractorStyleImage()        
        self.iren.SetInteractorStyle(self.interactorStyle)  
        # this is a cursor of sort
        self.sphere = vtk.vtkSphereSource()
        
        self.sphere.SetRadius(1.0)  
        mapper = vtk.vtkPolyDataMapper()
        mapper.SetInputConnection(self.sphere.GetOutputPort())
        sphereactor = vtk.vtkActor()
        sphereactor.SetMapper(mapper)
        sphereactor.GetProperty().SetColor(vtk.vtkNamedColors().GetColor3d("Gold"))
        self.ren.AddActor(sphereactor)
        
        # initialize planewidget and connect it to the renderer and interactor from ortho_overview
        self.planeWidget = vtk.vtkImagePlaneWidget()        
        # self.planeWidget.SetResliceInterpolateToCubic()   
        # self.planeWidget.SetResliceInterpolateToLinear() 
        self.planeWidget.SetResliceInterpolateToNearestNeighbour() 
        # setting margin size to 0 in order to disable rotating plane
        self.planeWidget.SetMarginSizeX(0)
        self.planeWidget.SetMarginSizeY(0)
        self.planeWidget.SetRestrictPlaneToVolume(True)
        
        self.planeWidget.AddObserver('InteractionEvent', self.on_clip_plane_changed)
        self.planeWidget.TextureVisibilityOn()    
        self.planeWidget.SetInteractor(overview_iren)
        self.planeWidget.SetCurrentRenderer(overview_ren)
        
        self.inputs = inputs
        
       
        # resize 'mapper', 'self.actor' and 'self.reslicer' to fit len(inputs)
        self.mapper = [None] * len(inputs)
        self.reslicer = [None] * len(inputs)
        self.actor = [None] * len(inputs)
        self.planeWidget.On()
        
        self.actorAssembly = vtk.vtkAssembly()
                
        for idx in range(len(inputs)):
            if idx == 0:                
                self.reslicer[idx] = self.planeWidget.GetReslice()        
                
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
            self.actorAssembly.AddPart(self.actor[idx])
        
        self.ren.AddActor(self.actorAssembly)
        # interactors        
        self.interactorStyle.AddObserver("MouseMoveEvent", self.mouseMoveCallback)
        self.interactorStyle.AddObserver("LeftButtonPressEvent", self.buttonCallback)
        self.interactorStyle.AddObserver("LeftButtonReleaseEvent", self.buttonCallback)
        self.interactorStyle.AddObserver("RightButtonPressEvent", self.buttonCallback)  
        self.interactorStyle.AddObserver("RightButtonReleaseEvent", self.buttonCallback)  
        self.interactorStyle.AddObserver("MiddleButtonPressEvent", self.buttonCallback)  
        self.interactorStyle.AddObserver("MiddleButtonReleaseEvent", self.buttonCallback)  
        
          
    
    def on_clip_plane_changed(self, caller, event):
        
        position = caller.GetSlicePosition()
                        
        
        self._model.slice_pos[self.direction] = position
        # also emit slice position changed (hard to implement via setter function, therefore it has to be done this way)
        self._model.slice_pos_changed.emit(self._model.slice_pos)
        caller.GetReslice().Update()
        
        
        # for reslicer in self.reslicer:
        #     reslicer.Update()
        self.iren.Render()
            
    
    def get_widget(self):
        return self.vtkWidget 

    def update_mesh(self):
        
        self.inputs[0].Update()
        self.planeWidget.SetInputData(self.inputs[0].GetOutput())
        self.planeWidget.PlaceWidget(self._model.slice_bounds['x']['min'], self._model.slice_bounds['x']['max'] , 
                                     self._model.slice_bounds['y']['min'], self._model.slice_bounds['y']['max'] ,
                                     self._model.slice_bounds['z']['min'], self._model.slice_bounds['z']['max'] )

        
        if self.normal[0] == 1:
            self.planeWidget.SetPlaneOrientation(0)
        if self.normal[1] == 1:
            self.planeWidget.SetPlaneOrientation(1)
        if self.normal[2] == 1:
            self.planeWidget.SetPlaneOrientation(2)

        self.sphere.SetRadius(self._model.mesh_scale[0] / 2)  
        self.ren.ResetCamera() 
        
        self.ren.ResetCameraClippingRange()        
        self.iren.Start()
        self.update()
    
    def set_normal(self, normal):
        self.normal = normal
        self.update()
    
    def update(self):
        # in case update is called without having the mesh updated return
        if self._model.mesh_scale == None:
            return
        # before new rendering update make sure the two or more reslicers have the same orientation and position
        for idx in range(len(self.reslicer)):
            if idx == 0:
                self.reslicer[idx].SetOutputSpacing(self._model.mesh_scale)
            else:
                self.reslicer[idx].SetOutputSpacing(self.reslicer[0].GetOutputSpacing())
                self.reslicer[idx].SetOutputOrigin(self.reslicer[0].GetOutputOrigin())
                self.reslicer[idx].SetResliceAxes(self.reslicer[0].GetResliceAxes())
        self.iren.Render()                
        
    def set_position(self, position):
        # VTK issue:
        # position "formaly" refers to the position of the plane near the beginning of the grid !!!
        # therefore adding one half of a cell and subtracting a small number will result in actually slicing through the middle of the cell
        self.planeWidget.SetSlicePosition(position+self._model.mesh_scale[self.axis]/2-0.01)
        
    def buttonCallback(self, obj, event):
        print ("button cb called, event ", event)
        if event == "MiddleButtonPressEvent":
            self.interactorStyle.OnMiddleButtonDown()
        if event == "MiddleButtonReleaseEvent":
            self.interactorStyle.OnMiddleButtonUp()
        # if event == "LeftButtonPressEvent":
        #     self.actions["Slicing"] = 1
        # else:
        #     self.actions["Slicing"] = 0
        
        
    def mouseMoveCallback(self, obj, event):
        
        (lastX, lastY) = self.iren.GetLastEventPosition()
        mouse_coord = [None] * 2
        (mouse_coord[0], mouse_coord[1]) = self.iren.GetEventPosition()        
        
        
        coordinate = vtk.vtkCoordinate()
        coordinate.SetCoordinateSystemToDisplay()
        coordinate.SetValue(mouse_coord[0], mouse_coord[1])
        world_coord = coordinate.GetComputedWorldValue(self.ren)
        print("coord:", world_coord)
        
        self.sphere.SetCenter(world_coord[0], world_coord[1], 0)
        self.iren.Render()
        #transform coordinates from local orientation to global one according to resliceorientation
        origin = self.reslicer[0].GetOutput().GetOrigin()
        pixel = [world_coord[0], world_coord[1]]
        resliceAxes = self.reslicer[0].GetResliceAxes()
        world_coord = np.array(resliceAxes.MultiplyDoublePoint([pixel[0]+origin[0], pixel[1]+origin[1], origin[2], 1]))[0:3]
     
        # translate coordinates into array indices
        mesh_indices = np.floor(np.divide(world_coord, self._model.mesh_scale)).astype(int)
        
        
        if  (world_coord[0] < self._model.slice_bounds['x']["min"]) or (world_coord[0] > self._model.slice_bounds['x']["max"]) or \
            (world_coord[1] < self._model.slice_bounds['y']["min"]) or (world_coord[1] > self._model.slice_bounds['y']["max"]) or \
            (world_coord[2] < self._model.slice_bounds['z']["min"]) or (world_coord[2] > self._model.slice_bounds['z']["max"]):            
            value = -1
            value_threshed = -1
        else:
            value          = self._model.mesh.GetOutput().GetScalarComponentAsDouble(mesh_indices[0], mesh_indices[1], mesh_indices[2], 0)
            value_threshed = self._model.mesh_threshed.GetOutput().GetScalarComponentAsDouble(mesh_indices[0], mesh_indices[1], mesh_indices[2], 0)
        
        np.set_printoptions(formatter={'float': lambda x: f"{x:2f}"})      
        
        print(f'{mouse_coord =} {world_coord =} {mesh_indices =}  {value =} {value_threshed =}')
        
        self.interactorStyle.OnMouseMove()


     
    
class OrthoViewOverview():   
      
    def __init__(self, model, name, parent):
        
            
        self.name = name        
        self._model = model   
        
        self.ren = vtk.vtkRenderer()
        self.vtkWidget = QVTKRenderWindowInteractor(parent)
        self.vtkWidget.GetRenderWindow().AddRenderer(self.ren)
        
        self.iren = self.vtkWidget.GetRenderWindow().GetInteractor()
        self.interactorStyle3D = vtk.vtkInteractorStyleTrackballCamera()
        self.iren.SetInteractorStyle(self.interactorStyle3D)
        
        
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
        volumeProperty.SetInterpolationTypeToNearest()

        # The property describes how the data will look.
        volumeThreshedProperty = vtk.vtkVolumeProperty()
        volumeThreshedProperty.SetColor(colorThreshedTransferFunction)
        volumeThreshedProperty.SetScalarOpacity(opacityThreshedTransferFunction)
        volumeThreshedProperty.ShadeOn()
        volumeThreshedProperty.SetInterpolationTypeToNearest()


        # The mapper / ray cast function know how to render the data.
        self.volumeMapper = vtk.vtkFixedPointVolumeRayCastMapper()
        self.volumeMapper.SetInputConnection(self._model.mesh.GetOutputPort())
        
        # The volume holds the mapper and the property and
        # can be used to position/orient the volume.
        volume = vtk.vtkVolume()
        volume.SetMapper(self.volumeMapper)
        volume.SetProperty(volumeProperty)

            # The mapper / ray cast function know how to render the data.
        self.volumeThreshedMapper = vtk.vtkFixedPointVolumeRayCastMapper()
        self.volumeThreshedMapper.SetInputConnection(self._model.mesh_threshed.GetOutputPort())

      
        # The volume holds the mapper and the property and
        # can be used to position/orient the volume.
        volumeThreshed = vtk.vtkVolume()
        volumeThreshed.SetMapper(self.volumeThreshedMapper)
        volumeThreshed.SetProperty(volumeThreshedProperty)

        axes = vtk.vtkAxesActor()
        self.axes_widget = vtk.vtkOrientationMarkerWidget()
        rgba = [0] * 4
        colors.GetColor('Carrot', rgba)
        self.axes_widget.SetOutlineColor(rgba[0], rgba[1], rgba[2])
        self.axes_widget.SetOrientationMarker(axes)
        self.axes_widget.SetInteractor(self.iren)
        self.axes_widget.SetViewport(0.0, 0.0, 0.2, 0.2)
        self.axes_widget.SetEnabled(1)
        self.axes_widget.SetInteractive(False)

        self.ren.AddVolume(volume)
        self.ren.AddVolume(volumeThreshed)
        self.ren.AddActor(self.outlineActor)
        self.ren.SetBackground(colors.GetColor3d('Wheat'))
        self.ren.GetActiveCamera().Azimuth(45)
        self.ren.GetActiveCamera().Elevation(30)
                    

    
    def get_widget(self):
        return self.vtkWidget 

    def update_mesh(self):
        
        self._model.mesh.Update()
        self.ren.ResetCameraClippingRange()  
        self.ren.ResetCamera()  
        self.iren.Start()
            

        
    def update(self):
        self.iren.Render()
    
    
class OrthoView(QtWidgets.QWidget):
    def __init__(self, model, main_controller):
        super(OrthoView, self).__init__()
        
        self._model = model
        
        self.ortho_overview    = OrthoViewOverview(self._model, "OrthoOverview", self)
        
        self.ortho_view_slices = {}
        self.ortho_view_slices['xy'] = OrthoViewSlice(self._model, 'xy', self, [self._model.mesh, self._model.mesh_threshed], [Luts.get_standard_lut(), Luts.get_threshed_lut([1,0,0], 0.8)], [0,0,0], [0,0,1], 'z', self.ortho_overview.iren, self.ortho_overview.ren)
        self.ortho_view_slices['xz'] = OrthoViewSlice(self._model, 'xz', self, [self._model.mesh, self._model.mesh_threshed], [Luts.get_standard_lut(), Luts.get_threshed_lut([1,0,0], 0.8)], [0,0,0], [0,1,0], 'y', self.ortho_overview.iren, self.ortho_overview.ren)
        self.ortho_view_slices['yz'] = OrthoViewSlice(self._model, 'yz', self, [self._model.mesh, self._model.mesh_threshed], [Luts.get_standard_lut(), Luts.get_threshed_lut([1,0,0], 0.8)], [0,0,0], [1,0,0], 'x', self.ortho_overview.iren, self.ortho_overview.ren)
        
        layout = QtWidgets.QGridLayout()        
        self.setLayout(layout)           
        
        
        # make sure widgets do not move when they  setVisible(False) 
        self.ortho_overview.get_widget().sizePolicy().setRetainSizeWhenHidden(True)
        self.ortho_view_slices['yz'].get_widget().sizePolicy().setRetainSizeWhenHidden(True)
        self.ortho_view_slices['xz'].get_widget().sizePolicy().setRetainSizeWhenHidden(True)
        self.ortho_view_slices['xy'].get_widget().sizePolicy().setRetainSizeWhenHidden(True)
        
        # plotter for overview        
        layout.addWidget(self.ortho_overview.get_widget(), 0, 0)
                
        # plotter for several cut 2D views
        layout.addWidget(self.ortho_view_slices['yz'].get_widget(), 0, 1)
        layout.addWidget(self.ortho_view_slices['xz'].get_widget(), 1, 0)
        layout.addWidget(self.ortho_view_slices['xy'].get_widget(), 1, 1)
        
        # listen to model event signals     
        self._model.mesh_changed.connect(self.on_mesh_changed)
        self._model.slice_pos_changed.connect(self.on_slice_pos_changed)
        self._model.slice_bounds_changed.connect(self.on_slice_bounds_changed)
        self._model.show_cut_views_changed.connect(self.on_show_cut_views_changed)

        
        #update visibility of widgets
        self.on_show_cut_views_changed(self._model.show_cut_views)
        
                 
    @pyqtSlot()
    def on_mesh_changed(self):
        if self._model.mesh is None:
            return
        self.update_mesh()
    
    def on_slice_pos_changed(self):
        
        if self._model.mesh is None:
            return
        print ('on slice pos changed (ortho view)')
        for ortho_view_slice in self.ortho_view_slices.values():
            ortho_view_slice.set_position(self._model.slice_pos[ortho_view_slice.direction])
        self.update_plots()
    
    
    def on_slice_bounds_changed(self, slice_bounds):
        
        
        self.ortho_overview.update_mesh()
        
        self.ortho_view_slices['xy'].update_mesh()
        self.ortho_view_slices['xz'].update_mesh()
        self.ortho_view_slices['yz'].update_mesh()
    
    def on_show_cut_views_changed(self, show_cut_views):
        for ortho_view_slice in self.ortho_view_slices.values():
            ortho_view_slice.get_widget().setVisible(show_cut_views[ortho_view_slice.name])
        
        # if there is a mesh, update all plot windowss
        if not self._model.mesh == None:
            self.update_plots()
        
        
    def update_plots(self):
        
        print("update views...")
        self.ortho_overview.update()

        self.ortho_view_slices['xy'].update()
        self.ortho_view_slices['xz'].update()
        self.ortho_view_slices['yz'].update()
        
        print("update views...ok")        
        
    
    def update_mesh(self):   
                     
        if self._model.mesh is None:
            return
        print("update mesh...")
        
        self.ortho_overview.update_mesh()
        
        self.ortho_view_slices['xy'].update_mesh()
        self.ortho_view_slices['xz'].update_mesh()
        self.ortho_view_slices['yz'].update_mesh()
        
        print("update mesh...ok")

        
        self.update_plots()

        
        
    def closeEvent(self, QCloseEvent):
        super().closeEvent(QCloseEvent)
        self.ortho_view_slices['xy'].get_widget().Finalize()
        self.ortho_view_slices['xz'].get_widget().Finalize()
        self.ortho_view_slices['yz'].get_widget().Finalize()
        self.ortho_overview.get_widget().Finalize()


