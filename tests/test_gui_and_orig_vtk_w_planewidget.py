
import sys
import math
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
        self.center = []
        # Create callbacks for slicing the image
        self.actions = {}
        self.actions["Slicing"] = 0
        
        colors = vtk.vtkNamedColors()
        self.z_pos = 0
        self.center = None
        
        self.reslicer = None

        self.reader = vtk.vtkNrrdReader()
        self.reader.SetFileName("")
        self.xMin = 0
        self.xMax = 0
        self.yMin = 0
        self.yMax = 0
        self.zMin = 0
        self.zMax = 0
        
        self.center = [0,0,0]
        
        self.thresholdVal = 900
        self.threshed = vtk.vtkImageThreshold()
        self.threshed.SetInputConnection(self.reader.GetOutputPort()) # Set your input vtkImageData
        self.threshed.ThresholdByUpper(self.thresholdVal) # Set the threshold value
        self.threshed.ReplaceInOn() # Set the operation to replace in values
        self.threshed.SetInValue(1) # Set the value for inside the threshold
        self.threshed.ReplaceOutOn() # Set the operation to replace out values
        self.threshed.SetOutValue(0) # Set the value for outside the threshold
        # self.threshed.Update()
  
        # self.threshold = vtk.vtkImageThreshold()
        # self.threshold.SetInputConnection(self.reader.GetOutputPort()) # Set your input vtkImageData
        # self.threshold.ThresholdByUpper(500) # Set the threshold value
        # self.threshold.ReplaceInOn() # Set the operation to replace in values
        # self.threshold.SetInValue(1) # Set the value for inside the threshold
        # self.threshold.ReplaceOutOn() # Set the operation to replace out values
        # self.threshold.SetOutValue(0) # Set the value for outside the threshold
        # self.threshold.Update()

        # self.combined = vtk.vtkImageBlend()
        # # self.combined.AddInputConnection(self.mesh.GetOutputPort())                 
        # self.combined.AddInputConnection(self.threshold.GetOutputPort()) 
        # self.combined.SetOpacity(0, 0.5)
        # self.combined.SetOpacity(1, 1)
        # self.combined.Update()
        
        
        scalarBar = vtk.vtkScalarBarActor()
        scalarBar.SetLookupTable(self.get_my_table())
        scalarBar.SetTitle("Title")
        scalarBar.SetNumberOfLabels(5)
        
        # self.reslicer, self.actor, self.mapToColors = self.extract_slice(self.combined)
        # self.reslicer, self.actor, self.mapToColors = self.extract_slice(self.threshold)
        # self.reslicer, self.actor, self.mapper = self.extract_slice(self.reader, self.get_my_table())
        # self.reslicerThreshed, self.actorThreshed, self.mapperThreshed = self.extract_slice(self.threshed, self.get_my_table_threshed())

        self.ren3D = vtk.vtkRenderer()
        self.vtkWidget3D = QVTKRenderWindowInteractor(self)
        self.vtkWidget3D.GetRenderWindow().AddRenderer(self.ren3D)
        self.iren3D = self.vtkWidget3D.GetRenderWindow().GetInteractor()

        self.planeWidget = vtk.vtkImagePlaneWidget()
        self.planeWidget.SetInteractor(self.iren3D)        
        self.planeWidget.SetResliceInterpolateToCubic()   
        self.planeWidget.SetMarginSizeX(0)
        self.planeWidget.SetMarginSizeY(0)
        self.planeWidget.AddObserver('InteractionEvent', self.on_clip_plane_changed)
        self.planeWidget.SetCurrentRenderer(self.ren3D)
        self.planeWidget.TextureVisibilityOn()
        # self.planeWidget.GetTexturePlaneProperty().SetColor(1,0,0)
        # self.planeWidget.GetTexturePlaneProperty().SetOpacity(1)
        # self.planeWidget.GetTexturePlaneProperty().SetColor(colors.GetColor3d("Green"))
        
        
        # prop = self.planeWidget.GetPlaneProperty()
        # prop.SetOpacity(0.2)
        # prop.SetColor(colors.GetColor3d("Green"))  
        # self.planeWidget.SetPlaneProperty(prop)
        
        
        self.reslicer = self.planeWidget.GetReslice()
        self.reslicer.SetOutputSpacing(.5,.5,.5)
        
        mapper = vtk.vtkImageMapToColors()
        mapper.SetInputConnection(self.reslicer.GetOutputPort())  # Set the input as the extracted slice from vtkImageReslice
        mapper.SetLookupTable(self.get_my_table())        

        self.actor = vtk.vtkImageActor()
        self.actor.GetMapper().SetInputConnection(mapper.GetOutputPort())
        
        self.sphere = vtk.vtkSphereSource()
        self.sphere.SetRadius(0.5)  
        mapper = vtk.vtkPolyDataMapper()
        mapper.SetInputConnection(self.sphere.GetOutputPort())
        sphereactor = vtk.vtkActor()
        sphereactor.SetMapper(mapper)
        sphereactor.GetProperty().SetColor(colors.GetColor3d("Gold"))
        
        
        self.reslicer_threshed = vtk.vtkImageReslice()
        # self.reslicer_threshed.SetOutputDimensionality(2)
        self.reslicer_threshed.SetOutputSpacing(self.reslicer.GetOutputSpacing())
        self.reslicer_threshed.SetOutputOrigin(self.reslicer.GetOutputOrigin())
        self.reslicer_threshed.SetResliceAxes(self.reslicer.GetResliceAxes())
        self.reslicer_threshed.SetInputConnection(self.threshed.GetOutputPort())
        
        
        # Create an instance of vtkImageMapToColors
        self.mapperThreshed = vtk.vtkImageMapToColors()
        self.mapperThreshed.SetInputConnection(self.reslicer_threshed.GetOutputPort())  # Set the input as the extracted slice from vtkImageReslice
        self.mapperThreshed.SetLookupTable(self.get_my_table_threshed())

        self.actorThreshed = vtk.vtkImageActor()
        self.actorThreshed.GetMapper().SetInputConnection(self.mapperThreshed.GetOutputPort())
                
        
        # self.reslicerThreshed, self.actorThreshed, self.mapperThreshed = self.extract_slice(self.threshed, self.get_my_table_threshed())
        
        """
        # reslicer shape cylinder:
        # rotate the image so that the cylinder cuts through it as desired
        rotate = vtk.vtkImageReslice()
        rotate.SetInputConnection(self.reader.GetOutputPort())
        rotate.SetResliceAxesDirectionCosines(
        -1, 0, 0,
        0, -1, 0,
        0, 0, 1 )
        rotate.Update()
        
        # get the image geometry
        o = rotate.GetOutput().GetOrigin()
        s = rotate.GetOutput().GetSpacing()
        ex = rotate.GetOutput().GetExtent()
        
        # new information for cylindrical coordinate geometry
        self.radialSize = 64
        origin = [ 0.0, 0.0, o[2] ]
        spacing = [ s[0], 2*math.pi/self.radialSize, s[2] ]
        extent = [  ex[0], (ex[1] + 1)/2 - 1,
                    0, self.radialSize - 1,
                    ex[4], ex[5]     ]
        # Unwrap with a cylindrical transform
        transform = vtk.vtkCylindricalTransform()

        self.reslice_cyl = vtk.vtkImageReslice()
        self.reslice_cyl.SetInputConnection(rotate.GetOutputPort())
        self.reslice_cyl.SetInterpolationModeToCubic()
        self.reslice_cyl.SetResliceTransform(transform)
        self.reslice_cyl.SetOutputOrigin(origin)
        self.reslice_cyl.SetOutputSpacing(spacing)        
        extent  = [int(np.round(x)) for x in extent]        
        self.reslice_cyl.SetOutputExtent(extent)
        self.reslice_cyl.Update()

        
        # Multiply angular spacing by the radius
        r = 100.0
        stretch = vtk.vtkImageChangeInformation()
        stretch.SetInputConnection(self.reslice.GetOutputPort())
        stretch.SetOutputSpacing(spacing[0], r*spacing[1], spacing[2])
        
        
        mapper = vtk.vtkImageMapToColors()
        mapper.SetInputConnection(self.reslice_cyl.GetOutputPort())  # Set the input as the extracted slice from vtkImageReslice
        mapper.SetLookupTable(self.get_my_table())        
        

        self.actor_cyl = vtk.vtkImageActor()
        self.actor_cyl.GetMapper().SetInputConnection(mapper.GetOutputPort())
        
        """
        # Display the images
        
        self.ren = vtk.vtkRenderer()
        camera = vtk.vtkCamera()
        camera.ParallelProjectionOn()
        self.ren.SetActiveCamera(camera)
        self.vtkWidget = QVTKRenderWindowInteractor(self)
        self.vtkWidget.GetRenderWindow().AddRenderer(self.ren)
        self.iren = self.vtkWidget.GetRenderWindow().GetInteractor()
        
        
        self.actorAssembly = vtk.vtkAssembly()
        self.actorAssembly.AddPart(self.actorThreshed)
        self.actorAssembly.AddPart(self.actor)
        
       
        self.ren.AddActor(self.actorAssembly)
        self.ren.AddActor2D(scalarBar)
        self.ren.AddActor(sphereactor)
        # self.ren.AddActor(self.actor_cyl)
        
        axisActorX = vtk.vtkAxisActor2D()
        axisActorX.SetPoint1(-10, 250)
        axisActorX.SetPoint2(-10, 250)
        axisActorX.GetTitleTextProperty().SetColor(colors.GetColor3d("banana"))
        axisActorX.SetTitle("X-Axis")
        axisActorX.SetNumberOfLabels(5)
        axisActorX.AxisVisibilityOn()
        axisActorX.LabelVisibilityOn()
        axisActorX.TickVisibilityOn()
        axisActorX.TitleVisibilityOn()
        self.ren.AddActor2D(axisActorX) 
        
        axisActorY = vtk.vtkAxisActor2D()
        axisActorY.SetPoint1(0, -10)
        axisActorY.SetPoint2(250, -10)
        axisActorY.SetTitle("Y-Axis")
        axisActorY.SetNumberOfLabels(5)
        axisActorY.AxisVisibilityOn()
        self.ren.AddActor2D(axisActorY) 
        
        
        
        # Set up the interaction        
        self.interactorStyle = vtk.vtkInteractorStyleImage()
        self.iren.SetInteractorStyle(self.interactorStyle)  

        self.interactorStyle.AddObserver("MouseMoveEvent", self.mouseMoveCallback)
        self.interactorStyle.AddObserver("LeftButtonPressEvent", self.buttonCallback)
        self.interactorStyle.AddObserver("LeftButtonReleaseEvent", self.buttonCallback)
        self.interactorStyle.AddObserver("RightButtonPressEvent", self.buttonCallback)        
  
        
        
    
        


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
        
        self.interactorStyle3D.AddObserver("MouseMoveEvent", self.mouseMoveCallback3D)
        self.interactorStyle3D.AddObserver("RightButtonPressEvent", self.buttonCallback3D)
        self.interactorStyle3D.AddObserver("RightButtonReleaseEvent", self.buttonCallback3D)
        
        
        
        buttonWidget = QtWidgets.QToolButton()
        buttonWidget.setText("Load")
        buttonWidget.clicked.connect(self.load_button_clicked)
        # Set up layout
        self.layout = QtWidgets.QVBoxLayout()
        self.layout.addWidget(self.vtkWidget)
        self.layout.addWidget(self.vtkWidget3D)
        self.layout.addWidget(buttonWidget)
        
        
        # Create a central widget and set the layout
        self.centralWidget = QtWidgets.QWidget()
        self.centralWidget.setLayout(self.layout)
        self.setCentralWidget(self.centralWidget)
                
        
    def buttonCallback3D(self, obj, event):
    
        print ("button cb called, event ", event)
        if event == "RightButtonPressEvent":
            self.buttonpressed3D = 1
        else:
            self.buttonpressed3D = 0
            

    def mouseMoveCallback3D(self, obj, event):
        
        
        (lastX, lastY) = self.iren3D.GetLastEventPosition()
        (mouseX, mouseY) = self.iren3D.GetEventPosition()        
        
        if self.buttonpressed3D == 1:
            deltaY = mouseY - lastY
            # reslice.Update()
            
            # sphere.SetRadius(sphere.GetRadius()+deltaY)
            
            self.thresholdVal = self.thresholdVal + deltaY
            print ("threshold...", self.thresholdVal)
        
            self.threshed.ThresholdByUpper(self.thresholdVal) # Set the threshold value    
            self.threshed.Update()
            
            self.iren3D.Render()
            self.iren.Render()
        else:
            self.interactorStyle3D.OnMouseMove()
        
        
        
    def closeEvent(self, QCloseEvent):
        super().closeEvent(QCloseEvent)
        self.vtkWidget.Finalize()   
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
        
    def extract_slice(self, input, lut_table):

        # Extract a slice in the desired orientation
        reslice = vtk.vtkImageReslice()
        reslice.SetInputConnection(input.GetOutputPort())
        reslice.SetOutputDimensionality(2)
        sagittal = vtk.vtkMatrix4x4()
        sagittal.DeepCopy((1, 0, 0, self.center[0],
                           0, 1, 0, self.center[1],
                           0, 0, 1, self.center[2],
                           0, 0, 0, 1))
        
        # sagittal.DeepCopy((1, 0, 0, self.center[0],
        #                    0, 0, 1, self.center[1],
        #                    0, 1, 0, self.center[2],
        #                    0, 0, 0, 1))
        
        reslice.SetResliceAxes(sagittal)
        reslice.SetInterpolationModeToLinear()
        

        # Update the vtkImageReslice
        # reslice.Update()

        # Create an instance of vtkImageMapToColors
        mapToColors = vtk.vtkImageMapToColors()
        mapToColors.SetInputConnection(reslice.GetOutputPort())  # Set the input as the extracted slice from vtkImageReslice
        mapToColors.SetLookupTable(lut_table)
        # mapToColors.Update() # Update the vtkImageMapToColors

        actor = vtk.vtkImageActor()
        actor.GetMapper().SetInputConnection(mapToColors.GetOutputPort())
        
        
        
        return reslice, actor, mapToColors

    


    
    def buttonCallback(self, obj, event):
        print ("button cb called, event ", event)
        if event == "LeftButtonPressEvent":
            self.actions["Slicing"] = 1
        else:
            self.actions["Slicing"] = 0
        
        
        if event == "RightButtonPressEvent":
            
            
            # self.ren.SetBackground(1, 1, 1)
            
            # self.iren.Render()
            pass

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
        # resliceaxes = self.reslicer.GetResliceAxes()
        # print("orientation:", resliceaxes)
        # coord = (coord[0], coord[1], resliceaxes.GetElement(2,3))
        
        # now the same thinf with proper matrix transformation
        origin = self.reslicer.GetOutput().GetOrigin()
        pixel = [coord[0], coord[1]]
        resliceAxes = self.reslicer.GetResliceAxes()
        coord = resliceAxes.MultiplyDoublePoint([pixel[0]+origin[0], pixel[1]+origin[1], origin[2], 1])
        
        
        # translate coordinates into array indices
        x = round(coord[0]/self.xSpacing)
        y = round(coord[1]/self.ySpacing)
        z = round(coord[2]/self.zSpacing)
        
        if (x < self.xMin) or (x > self.xMax) or (y < self.yMin) or (y > self.yMax) or (z < self.zMin) or (z > self.zMax):            
            value = 0
            value_threshed = 0
        else:
            value          = self.reader.GetOutput().GetScalarComponentAsDouble(x, y, z, 0)
            value_threshed = self.threshed.GetOutput().GetScalarComponentAsDouble(x, y, z, 0)
                
        print("x mouse: ", mouseX, " y mouse: ", mouseY, "world-x: ",coord[0], " world-y: ", coord[1],"world-z: ", coord[2],"   Scalar: ", value, "threshed: ", value_threshed)
        
        
        
        
        if self.actions["Slicing"] == 1:
            print("slicing")
            deltaY = mouseY - lastY
            # reslice.Update()
            
            # sphere.SetRadius(sphere.GetRadius()+deltaY)
            
            # print ("slice...", deltaY)
            sliceSpacing = self.reslicer.GetOutput().GetSpacing()[2]
            
          
            position = self.planeWidget.GetSlicePosition()
            self.planeWidget.SetSlicePosition(position + deltaY)
            
            
            self.reslicer.Update()
            self.reslicer_threshed.Update()
            self.reslicer_threshed.SetOutputOrigin(self.reslicer.GetOutputOrigin())
            self.reslicer_threshed.SetResliceAxes(self.reslicer.GetResliceAxes())
            self.iren.Render()
            self.iren3D.Render()
        else:
            self.interactorStyle.OnMouseMove()

    def load_button_clicked(self):
        self.load_data()
        self.threshed.Update()
        self.ren3D.ResetCameraClippingRange()
        self.ren3D.ResetCamera()
        self.iren3D.Start()
        
        self.planeWidget.SetInputConnection(self.reader.GetOutputPort())
        # self.planeWidget.SetPlaneOrientationToZAxes()
        self.planeWidget.SetPlaneOrientationToYAxes()
        (self.xMin, self.xMax, self.yMin, self.yMax, self.zMin, self.zMax) = self.reader.GetExecutive().GetWholeExtent(self.reader.GetOutputInformation(0))
        (self.xSpacing, self.ySpacing, self.zSpacing) = self.reader.GetOutput().GetSpacing()
        
        self.planeWidget.PlaceWidget(self.xMin*self.xSpacing, self.xMax*self.xSpacing, self.yMin*self.ySpacing, self.yMax*self.ySpacing, self.zMin*self.zSpacing, self.zMax*self.zSpacing)
        

        self.iren3D.Render()
        
        self.ren.ResetCamera()
        self.ren.ResetCameraClippingRange()        
        self.iren.Start()
        self.iren.Render()
    
    
    def on_clip_plane_changed(self, caller = None, event = None ): 
        # print("plane position changed, caller = ", caller, " and event = " , event)
        
        
        # self.slice = caller.GetResliceOutput()
        # caller.GetReslice().UpdatePlacement()
        # caller.GetReslice().UpdatePlane()
        # caller.UpdatePlane()
        self.reslicer.Update()
        # self.reslicer_threshed.SetOutputOrigin(self.reslicer.GetOutputOrigin())
        # self.reslicer_threshed.SetResliceAxes(self.reslicer.GetResliceAxes())
        self.iren.Render()
        
        
        
        
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