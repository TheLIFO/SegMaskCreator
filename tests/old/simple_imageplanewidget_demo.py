
import sys

import vtk
from vtkmodules.vtkFiltersCore import vtkCutter
from vtkmodules.vtkCommonDataModel import vtkSphere

from vtkmodules.vtkImagingCore import vtkImageReslice
from PyQt5 import QtWidgets
from vtk.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor
import numpy as np


class MyMainWindow(QtWidgets.QMainWindow):

    def __init__(self, parent=None, show=True):
        super().__init__() 
        
        colors = vtk.vtkNamedColors()
        self.center = []
        
        self.reader = vtk.vtkNrrdReader()
                # Start by loading some data.
        filename = "data\Drydisk07.6.nrrd"
        self.reader.SetFileName(filename)
        self.reader.Update()

        self.thresholdVal = 900
        self.threshed = vtk.vtkImageThreshold()
        self.threshed.SetInputConnection(self.reader.GetOutputPort()) # Set your input vtkImageData
        self.threshed.ThresholdByUpper(self.thresholdVal) # Set the threshold value
        self.threshed.ReplaceInOn() # Set the operation to replace in values
        self.threshed.SetInValue(1) # Set the value for inside the threshold
        self.threshed.ReplaceOutOn() # Set the operation to replace out values
        self.threshed.SetOutValue(0) # Set the value for outside the threshold
        
        # Calculate the center of the volume
        (self.xMin, self.xMax, self.yMin, self.yMax, self.zMin, self.zMax) = self.reader.GetExecutive().GetWholeExtent(self.reader.GetOutputInformation(0))
        (self.xSpacing, self.ySpacing, self.zSpacing) = self.reader.GetOutput().GetSpacing()
        (self.x0, self.y0, self.z0) = self.reader.GetOutput().GetOrigin()
        (self.x_mid, self.y_mid, self.z_mid) = self.reader.GetOutput().GetOrigin()
        
        # Create callbacks for slicing the image

        self.ren3D = vtk.vtkRenderer()
        self.vtkWidget3D = QVTKRenderWindowInteractor(self)
        self.vtkWidget3D.GetRenderWindow().AddRenderer(self.ren3D)
        self.iren3D = self.vtkWidget3D.GetRenderWindow().GetInteractor()

        self.planeWidget = vtk.vtkImagePlaneWidget()
        self.planeWidget.SetInteractor(self.iren3D)        
        self.planeWidget.SetResliceInterpolateToCubic()        
        self.planeWidget.SetInputConnection(self.reader.GetOutputPort())
        self.planeWidget.SetPlaneOrientationToZAxes()
        self.planeWidget.On()
        self.planeWidget.SetMarginSizeX(0)
        self.planeWidget.SetMarginSizeY(0)
        self.planeWidget.AddObserver('InteractionEvent', self.on_clip_plane_changed)
        self.planeWidget.SetCurrentRenderer(self.ren3D)
        
        
        
        self.planeWidget.PlaceWidget(self.xMin*self.xSpacing, self.xMax*self.xSpacing, self.yMin*self.ySpacing, self.yMax*self.ySpacing, self.zMin*self.zSpacing, self.zMax*self.zSpacing)
        print("placeWidget: ", self.xMin*self.xSpacing, self.xMax*self.xSpacing, self.yMin*self.ySpacing, self.yMax*self.ySpacing, self.zMin*self.zSpacing, self.zMax*self.zSpacing)
        
        
        
        print("#1 origin: ", self.planeWidget.GetOrigin(), " - normal: ", self.planeWidget.GetNormal())
        self.planeWidget.SetSlicePosition(100)
        print("#2 origin: ", self.planeWidget.GetOrigin(), " - normal: ", self.planeWidget.GetNormal())
        
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
        volumeMapper.SetInputConnection(self.reader.GetOutputPort())
        
        # The volume holds the mapper and the property and
        # can be used to position/orient the volume.
        volume = vtk.vtkVolume()
        volume.SetMapper(volumeMapper)
        volume.SetProperty(volumeProperty)

            # The mapper / ray cast function know how to render the data.
        volumeThreshedMapper = vtk.vtkFixedPointVolumeRayCastMapper()
        volumeThreshedMapper.SetInputConnection(self.threshed.GetOutputPort())

      
        # The volume holds the mapper and the property and
        # can be used to position/orient the volume.
        volumeThreshed = vtk.vtkVolume()
        volumeThreshed.SetMapper(volumeThreshedMapper)
        volumeThreshed.SetProperty(volumeThreshedProperty)

        self.ren3D.AddVolume(volume)
        self.ren3D.AddVolume(volumeThreshed)
        self.ren3D.SetBackground(colors.GetColor3d('Wheat'))
        self.ren3D.GetActiveCamera().Azimuth(45)
        self.ren3D.GetActiveCamera().Elevation(30)
        
                    
        self.interactorStyle3D = vtk.vtkInteractorStyleTrackballCamera()
        self.iren3D.SetInteractorStyle(self.interactorStyle3D)
        self.buttonpressed3D = 0
        
        self.interactorStyle3D.AddObserver("MouseMoveEvent", self.MouseMoveCallback3D)
        self.interactorStyle3D.AddObserver("RightButtonPressEvent", self.ButtonCallback3D)
        self.interactorStyle3D.AddObserver("RightButtonReleaseEvent", self.ButtonCallback3D)
        
        
        
        # buttonWidget = QtWidgets.QToolButton()
        # buttonWidget.setText("Load")
        # buttonWidget.clicked.connect(self.load_button_clicked)
        # Set up layout
        self.layout = QtWidgets.QVBoxLayout()
        # self.layout.addWidget(self.vtkWidget)
        self.layout.addWidget(self.vtkWidget3D)
        # self.layout.addWidget(buttonWidget)
        
        
        # Create a central widget and set the layout
        self.centralWidget = QtWidgets.QWidget()
        self.centralWidget.setLayout(self.layout)
        self.setCentralWidget(self.centralWidget)
        
        self.ren3D.ResetCameraClippingRange()
        self.ren3D.ResetCamera()
        self.iren3D.Start()
                
        
    def ButtonCallback3D(self, obj, event):
    
        print ("button cb called, event ", event)
        
        if event == "RightButtonPressEvent":
            self.buttonpressed3D = 1
        else:
            self.buttonpressed3D = 0
            

    def MouseMoveCallback3D(self, obj, event):
        
        
        (lastX, lastY) = self.iren3D.GetLastEventPosition()
        (mouseX, mouseY) = self.iren3D.GetEventPosition()        
        
        if self.buttonpressed3D == 1:
            deltaY = mouseY - lastY
            # reslice.Update()
            
            # sphere.SetRadius(sphere.GetRadius()+deltaY)
            
            # self.thresholdVal = self.thresholdVal + deltaY
            # print ("threshold...", self.thresholdVal)
        
            # self.threshed.ThresholdByUpper(self.thresholdVal) # Set the threshold value    
            # self.threshed.Update()
            position = self.planeWidget.GetSlicePosition()
            self.planeWidget.SetSlicePosition(position + deltaY)
            
            
            print("origin: ", self.planeWidget.GetOrigin(), " - normal: ", self.planeWidget.GetNormal())
            self.iren3D.Render()
            # self.iren.Render()
        else:
            self.interactorStyle3D.OnMouseMove()
        
        
        
    def closeEvent(self, QCloseEvent):
        super().closeEvent(QCloseEvent)

        self.vtkWidget3D.Finalize()   

    
    def get_table(self):
            # Create a greyscale lookup table
        table = vtk.vtkLookupTable()
        table.SetRange(0, 2000) # image intensity range
        table.SetValueRange(0.0, 1.0) # from black to white
        table.SetSaturationRange(0.0, 1.0) # no color saturation
        table.SetRampToLinear()
        table.Build()
        return table

    def get_my_table_threshed(self):
        
        # Create a vtkLookupTable from the vtkColorTransferFunction
        lut = vtk.vtkLookupTable()
        lut.SetNumberOfColors(2) # Set the number of colors
        lut.SetNumberOfTableValues(2)  
        

       
        lut.SetTableValue(0, 0.0, 0.0, 0.0, 0.0)  # Set the RGBA values for each color
        lut.SetTableValue(1, 1.0, 0.0, 0.0, 0.8)  # Set the RGBA values for each color
        lut.Build()
        
        # Set the range of scalar values
        return lut
    
    def get_my_table(self):
        # Create a vtkColorTransferFunction
        color_tf = vtk.vtkColorTransferFunction()
        color_tf.AddRGBPoint(0.0, 0.267004, 0.004874, 0.329415)  # Dark blue
        color_tf.AddRGBPoint(0.25, 0.253935, 0.265254, 0.529983)  # Purple
        color_tf.AddRGBPoint(0.5, 0.163625, 0.471133, 0.558148)  # Teal
        color_tf.AddRGBPoint(0.75, 0.993248, 0.906157, 0.143936)  # Yellow
        color_tf.AddRGBPoint(1.0, 0.993248, 0.906157, 0.143936)  # Yellow

        # Create a vtkLookupTable from the vtkColorTransferFunction
        lut = vtk.vtkLookupTable()
        lut.SetTableRange(0, 255)  # Set the number of colors
        lut.SetRange(1, 2000)  # Assuming your scalar values range from 0 to 2000

        for i in range(256): # 0 .. 255
            val = i / 255.0
            color = color_tf.GetColor(val)
            lut.SetTableValue(i, color[0], color[1], color[2], 1.0)  # Set the RGBA values for each color

        lut.Build()

        # Set the range of scalar values
        return lut

    def get_table_coloured(self):
        # Create a vtkLookupTable
        lut = vtk.vtkLookupTable()
        lut.SetNumberOfColors(256)  # Set the number of colors

        # Set the range of scalar values
        lut.SetTableRange(0, 2000)

        # Set the color interpolation
        lut.SetHueRange(0.66667, 0.0)
        lut.SetSaturationRange(1.0, 1.0)
        lut.SetValueRange(1.0, 1.0)

        # Set the scale to linear
        lut.SetScaleToLinear()

        # Build the lookup table
        lut.Build()
        return lut
        

    


    
    def ButtonCallback(self, obj, event):
        print ("button cb called, event ", event)
        if event == "LeftButtonPressEvent":
            self.actions["Slicing"] = 1
        else:
            self.actions["Slicing"] = 0
        
        
        if event == "RightButtonPressEvent":
            # self.actor.GetMapper().GetInputConnection().SetLookupTable(self.get_table()) 
            self.mapper.SetLookupTable(self.get_table())
            self.ren.SetBackground(1, 1, 1)
            
            # self.mesh().Get
            
            self.iren.Render()
            pass

  
    
    
    def on_clip_plane_changed(self, caller = None, event = None ): 
        # print("plane position changed, caller = ", caller, " and event = " , event)
        
        
        # self.slice = caller.GetResliceOutput()
        # caller.GetReslice().UpdatePlacement()
        # caller.GetReslice().UpdatePlane()
        # caller.UpdatePlane()
  
        # self.reslicer_threshed.SetOutputOrigin(self.reslicer.GetOutputOrigin())
        # self.reslicer_threshed.SetResliceAxes(self.reslicer.GetResliceAxes())
  
        
        print("origin: ", self.planeWidget.GetOrigin(), " - normal: ", self.planeWidget.GetNormal())
        # print("point1:", self.planeWidget.GetPoint1())
        # print("point2:", self.planeWidget.GetPoint2())
        
        
        print("new origin for plane...ok")   

    def load_data(self):
        # Start by loading some data.
        filename = "data\Drydisk07.6.nrrd"
        self.reader.SetFileName(filename)
        self.reader.Update()

        
        
        # Calculate the center of the volume
        (self.xMin, self.xMax, self.yMin, self.yMax, self.zMin, self.zMax) = self.reader.GetExecutive().GetWholeExtent(self.reader.GetOutputInformation(0))
        (self.xSpacing, self.ySpacing, self.zSpacing) = self.reader.GetOutput().GetSpacing()
        (self.x0, self.y0, self.z0) = self.reader.GetOutput().GetOrigin()
        

if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    window = MyMainWindow()
    window.show()
    app.exec_()