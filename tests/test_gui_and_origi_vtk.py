
import sys

import vtk
from vtkmodules.vtkFiltersCore import vtkCutter
from vtkmodules.vtkCommonDataModel import vtkSphere

from vtkmodules.vtkImagingCore import vtkImageReslice
from PyQt5 import QtWidgets
from vtk.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor


class MyMainWindow(QtWidgets.QMainWindow):

    def __init__(self, parent=None, show=True):
        super().__init__() 
        self.center = []
        # Create callbacks for slicing the image
        self.actions = {}
        self.actions["Slicing"] = 0
        
        self.z_pos = 0
        self.center = None
        
        self.reslicer = None

        # Start by loading some data.
        self.reader = vtk.vtkNrrdReader()
        filename = "data\Drydisk07.6.nrrd"
        self.reader.SetFileName(filename)
        self.reader.Update()

        
        
        # Calculate the center of the volume
        (self.xMin, self.xMax, self.yMin, self.yMax, self.zMin, self.zMax) = self.reader.GetExecutive().GetWholeExtent(self.reader.GetOutputInformation(0))
        (self.xSpacing, self.ySpacing, self.zSpacing) = self.reader.GetOutput().GetSpacing()
        (self.x0, self.y0, self.z0) = self.reader.GetOutput().GetOrigin()

        
        self.center = [0,0,0]
        
        self.thresholdVal = 900
        self.threshed = vtk.vtkImageThreshold()
        self.threshed.SetInputConnection(self.reader.GetOutputPort()) # Set your input vtkImageData
        self.threshed.ThresholdByUpper(self.thresholdVal) # Set the threshold value
        self.threshed.ReplaceInOn() # Set the operation to replace in values
        self.threshed.SetInValue(1) # Set the value for inside the threshold
        self.threshed.ReplaceOutOn() # Set the operation to replace out values
        self.threshed.SetOutValue(0) # Set the value for outside the threshold
        self.threshed.Update()
  
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
        self.reslicer, self.actor, self.mapper = self.extract_slice(self.reader, self.get_my_table())
        self.reslicerThreshed, self.actorThreshed, self.mapperThreshed = self.extract_slice(self.threshed, self.get_my_table_threshed())

        # self.reslicerSphere, self.actorSpeher, self.sphere = self.extract_sphere(self.reader)

        # Display the image
        self.ren = vtk.vtkRenderer()
        self.camera = vtk.vtkCamera()
        self.camera.ParallelProjectionOn()
        self.ren.SetActiveCamera(self.camera)
        
        # self.renderer.AddActor(self.actor)
        # self.ren.SetBackground(1, 1, 1)

        

        self.vtkWidget = QVTKRenderWindowInteractor(self)
        self.vtkWidget.GetRenderWindow().AddRenderer(self.ren)
        self.iren = self.vtkWidget.GetRenderWindow().GetInteractor()
        
        
        self.actorAssembly = vtk.vtkAssembly()
        self.actorAssembly.AddPart(self.actor)
        self.actorAssembly.AddPart(self.actorThreshed)
        
       
        self.ren.AddActor(self.actorAssembly)
        # self.ren.AddActor2D(scalarBar)
        
        axisActorX = vtk.vtkAxisActor2D()
        axisActorX.SetPoint1(-10, 250)
        axisActorX.SetPoint2(-10, 250)
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
        
        
        self.ren.ResetCamera()
        self.ren.ResetCameraClippingRange()
        # Set up the interaction        
        self.interactorStyle = vtk.vtkInteractorStyleImage()
        self.iren.SetInteractorStyle(self.interactorStyle)  

        self.interactorStyle.AddObserver("MouseMoveEvent", self.MouseMoveCallback)
        self.interactorStyle.AddObserver("LeftButtonPressEvent", self.ButtonCallback)
        self.interactorStyle.AddObserver("LeftButtonReleaseEvent", self.ButtonCallback)
        self.interactorStyle.AddObserver("RightButtonPressEvent", self.ButtonCallback)        
        # self.iren.Initialize()
        self.iren.Start()
        
        
        self.ren3D = vtk.vtkRenderer()
        # camera3D = vtk.vtkCamera()
        # self.ren3D.SetActiveCamera(camera3D)
        self.vtkWidget3D = QVTKRenderWindowInteractor(self)
        self.vtkWidget3D.GetRenderWindow().AddRenderer(self.ren3D)
        self.iren3D = self.vtkWidget3D.GetRenderWindow().GetInteractor()

        
        

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

        colors = vtk.vtkNamedColors()
        self.ren3D.AddVolume(volume)
        self.ren3D.AddVolume(volumeThreshed)
        self.ren3D.SetBackground(colors.GetColor3d('Wheat'))
        self.ren3D.GetActiveCamera().Azimuth(45)
        self.ren3D.GetActiveCamera().Elevation(30)
        self.ren3D.ResetCameraClippingRange()
        self.ren3D.ResetCamera()
                    
        self.interactorStyle3D = vtk.vtkInteractorStyleTrackballCamera()
        self.iren3D.SetInteractorStyle(self.interactorStyle3D)
        self.buttonpressed3D = 0
        
        self.interactorStyle3D.AddObserver("MouseMoveEvent", self.MouseMoveCallback3D)
        self.interactorStyle3D.AddObserver("RightButtonPressEvent", self.ButtonCallback3D)
        self.interactorStyle3D.AddObserver("RightButtonReleaseEvent", self.ButtonCallback3D)
        # self.iren3D.Initialize()
        self.iren3D.Start()
        
        # Set up layout
        self.layout = QtWidgets.QVBoxLayout()
        self.layout.addWidget(self.vtkWidget)
        self.layout.addWidget(self.vtkWidget3D)
        
        
        # Create a central widget and set the layout
        self.centralWidget = QtWidgets.QWidget()
        self.centralWidget.setLayout(self.layout)
        self.setCentralWidget(self.centralWidget)
                
        
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
        reslice.Update()

        # Create an instance of vtkImageMapToColors
        mapToColors = vtk.vtkImageMapToColors()
        mapToColors.SetInputConnection(reslice.GetOutputPort())  # Set the input as the extracted slice from vtkImageReslice
        mapToColors.SetLookupTable(lut_table)
        mapToColors.Update() # Update the vtkImageMapToColors

        actor = vtk.vtkImageActor()
        actor.GetMapper().SetInputConnection(mapToColors.GetOutputPort())
        
        return reslice, actor, mapToColors

    def extract_sphere(self, reader):

        """
        # Create an instance of vtkCutter
        cutter = vtkCutter()

        # Set the input data to the cutter
        cutter.SetInputConnection(reader.GetOutputPort())

        # Set the cut function using vtkSphere as an example
        sphere = vtkSphere()
        sphere.SetCenter(center[0], center[1], center[2])  # Set the center of the sphere
        sphere.SetRadius(50)  # Set the radius of the sphere
        
        cutter.SetCutFunction(sphere)

        # Update the cutter to generate the output
        cutter.Update()

        
        # here is the magic:
        # Create an instance of vtkPolyDataToImageStencil
        polyDataToImageStencil = vtk.vtkPolyDataToImageStencil()
        polyDataToImageStencil.SetInputConnection(cutter.GetOutputPort())
        polyDataToImageStencil.Update()

        # Create an instance of vtkImageStencil
        imageStencil = vtk.vtkImageStencil()
        imageStencil.SetInputConnection(reader.GetOutputPort())
        imageStencil.SetStencilConnection(polyDataToImageStencil.GetOutputPort())
        imageStencil.ReverseStencilOn()  # This may be necessary depending on your specific use case
        imageStencil.Update()

        # Now you can use the result of the imageStencil as input for vtkImageMapToColors
        mapToColors.SetInputData(imageStencil.GetOutput())  # Set the input as the extracted slice from vtkImageReslice
        """

        # create surface
        surface = vtk.vtkCylinderSource()
        surface.SetCenter(reader.GetOutput().GetCenter()[0], reader.GetOutput().GetCenter()[1], reader.GetOutput().GetCenter()[2])
        surface.SetRadius(50.0)
        surface.SetHeight(200.0)
        surface.SetResolution(1000)
            
        
        
        # Create points for the plane
        points = vtk.vtkPoints()
        points.InsertNextPoint(0, 0, 100)  # Define the first point
        points.InsertNextPoint(200, 0, 100)  # Define the second point
        points.InsertNextPoint(200, 200, 100)  # Define the third point
        points.InsertNextPoint(0, 200, 100)  # Define the fourth point

        # Create a grid to represent the plane
        plane = vtk.vtkPolyData()
        plane.SetPoints(points)
        plane.Allocate(1, 1)
        idlist = vtk.vtkIdList()
        idlist.SetArray([0, 1, 2, 3], 4)
        plane.InsertNextCell(vtk.VTK_QUAD, idlist)  # Define the quad cell using the point IDs

        # Create a data source from the polydata
        planeDataSource = vtk.vtkPolyDataAlgorithm()
        planeDataSource.SetOutput(plane)

        sample_volume = vtk.vtkProbeFilter()
        sample_volume.SetSourceConnection(reader.GetOutputPort())
        sample_volume.SetInputData(planeDataSource.GetOutput())
        
        
        mapper = vtk.vtkImageMapper()
        # mapper.SetInputConnection(sample_volume.GetOutputPort())
        
        mapper.SetInputConnection(reader.GetOutputPort())
        actor = vtk.vtkImageActor()
        # actor.GetProperty().SetColorWindow(colors.GetColor3d("Cornsilk").GetData())
        # actor.SetMapper(mapper)
        # actor.GetMapper().SetInputConnection(mapToColors.GetOutputPort())  

        return sample_volume, actor, plane



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

    def MouseMoveCallback(self, obj, event):
        
        (lastX, lastY) = self.iren.GetLastEventPosition()
        (mouseX, mouseY) = self.iren.GetEventPosition()        
        
        coordinate = vtk.vtkCoordinate()
        coordinate.SetCoordinateSystemToDisplay()
        coordinate.SetValue(mouseX, mouseY)
        coord = coordinate.GetComputedWorldValue(self.ren)
        #transform coordinates from local orientation to global one according to resliceorientation
        resliceaxes = self.reslicer.GetResliceAxes()
        print("coord:", coord)
        print("orientation:", resliceaxes)
        coord = (coord[0], coord[1], resliceaxes.GetElement(2,3))
        
        
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
                
        print("x: ", mouseX, " y: ", mouseY, "world-x: ",coord[0], " world-y: ", coord[1],"world-z: ", coord[2],"   Scalar: ", value, "threshed: ", value_threshed)
        if self.actions["Slicing"] == 1:
            deltaY = mouseY - lastY
            # reslice.Update()
            
            # sphere.SetRadius(sphere.GetRadius()+deltaY)
            
            # print ("slice...", deltaY)
            sliceSpacing = self.reslicer.GetOutput().GetSpacing()[2]
            axes = self.reslicer.GetResliceAxes()
            # move the center point that we are slicing through
            center = axes.MultiplyPoint((0, 0, sliceSpacing*deltaY, 1))
            print ("new Z = ", center[2])
            
            axes.SetElement(0, 3, center[0])
            axes.SetElement(1, 3, center[1])
            axes.SetElement(2, 3, center[2])
            self.reslicer.Update()
            
            
            
            self.reslicerThreshed.SetResliceAxes(axes)            
            self.reslicerThreshed.Update()
            
            self.iren.Render()
        else:
            self.interactorStyle.OnMouseMove()


   

if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    window = MyMainWindow()
    window.show()
    app.exec_()