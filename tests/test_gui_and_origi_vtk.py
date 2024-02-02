
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
        
        
        self.center = None
        self.reader = None
        
        self.reslicer = None

        # Start by loading some data.
        self.reader = vtk.vtkNrrdReader()
        filename = "data\Drydisk07.6.nrrd"
        self.reader.SetFileName(filename)
        

        # Calculate the center of the volume
        self.reader.Update()
        (xMin, xMax, yMin, yMax, zMin, zMax) = self.reader.GetExecutive().GetWholeExtent(self.reader.GetOutputInformation(0))
        (xSpacing, ySpacing, zSpacing) = self.reader.GetOutput().GetSpacing()
        (x0, y0, z0) = self.reader.GetOutput().GetOrigin()

        
        self.center = [x0 + xSpacing * 0.5 * (xMin + xMax),
                y0 + ySpacing * 0.5 * (yMin + yMax),
                z0 + zSpacing * 0.5 * (zMin + zMax)]
        
        
        self.threshold = vtk.vtkImageThreshold()
        self.threshold.SetInputConnection(self.reader.GetOutputPort()) # Set your input vtkImageData
        self.threshold.ThresholdByLower(1000) # Set the threshold value
        self.threshold.ReplaceInOn() # Set the operation to replace
        self.threshold.SetInValue(0) # Set the value for inside the threshold
        self.threshold.SetOutValue(2000) # Set the value for inside the threshold
        # self.threshold.ReplaceOutOff() # Set to not replace the outside value
        self.threshold.Update()

        
        self.combined =  vtk.vtkImageAppend()
        self.combined.AddInputConnection(self.reader.GetOutputPort())                 
        self.combined.AddInputConnection(self.threshold.GetOutputPort()) 
        
        
        # self.reslicer, self.actor, self.mapToColors = self.extract_slice(self.combined)
        # self.reslicer, self.actor, self.mapToColors = self.extract_slice(self.threshold)
        self.reslicer, self.actor, self.mapToColors = self.extract_slice(self.reader)

        # self.reslicerSphere, self.actorSpeher, self.sphere = self.extract_sphere(self.reader)

        # Display the image
        self.ren = vtk.vtkRenderer()
        # self.renderer.AddActor(self.actor)
        self.ren.SetBackground(1,1,1)

        self.vtkWidget = QVTKRenderWindowInteractor(self)
        self.vtkWidget.GetRenderWindow().AddRenderer(self.ren)
        self.iren = self.vtkWidget.GetRenderWindow().GetInteractor()
        
        # Set up layout
        self.layout = QtWidgets.QVBoxLayout()
        self.layout.addWidget(self.vtkWidget)
        
        # Create a central widget and set the layout
        self.centralWidget = QtWidgets.QWidget()
        self.centralWidget.setLayout(self.layout)
        self.setCentralWidget(self.centralWidget)

        self.actorAssembly = vtk.vtkAssembly()
        self.actorAssembly.AddPart(self.actor)
        
         # Create source
        source = vtk.vtkSphereSource()
        source.SetCenter(0, 0, 0)
        source.SetRadius(5.0)

        # Create a mapper
        mapper = vtk.vtkPolyDataMapper()
        mapper.SetInputConnection(source.GetOutputPort())

        # Create an actor
        coneActor = vtk.vtkActor()
        coneActor.SetMapper(mapper)
        
        self.actorAssembly.AddPart(coneActor)
        
        self.ren.AddActor(self.actorAssembly)
        # self.ren.AddActor(self.actor) 

        # Set up the interaction        
        self.interactorStyle = vtk.vtkInteractorStyleImage()
        
        
        self.iren.SetInteractorStyle(self.interactorStyle)
        
        # self.renderWindow.SetInteractor(self.interactor)
        

        self.interactorStyle.AddObserver("MouseMoveEvent", self.MouseMoveCallback)
        self.interactorStyle.AddObserver("LeftButtonPressEvent", self.ButtonCallback)
        self.interactorStyle.AddObserver("LeftButtonReleaseEvent", self.ButtonCallback)

        self.interactorStyle.AddObserver("RightButtonPressEvent", self.ButtonCallback)

        self.iren.Initialize()
        
        
        
    def CloseEvent(self, QCloseEvent):
        pass

    
    def get_table(self):
            # Create a greyscale lookup table
        table = vtk.vtkLookupTable()
        table.SetRange(0, 2000) # image intensity range
        table.SetValueRange(0.0, 1.0) # from black to white
        table.SetSaturationRange(0.0, 1.0) # no color saturation
        table.SetRampToLinear()
        table.Build()
        return table

    def get_table_viridis(self):
        # Create a vtkColorTransferFunction
        color_tf = vtk.vtkColorTransferFunction()
        color_tf.AddRGBPoint(0.0, 0.267004, 0.004874, 0.329415)  # Dark blue
        color_tf.AddRGBPoint(0.25, 0.253935, 0.265254, 0.529983)  # Purple
        color_tf.AddRGBPoint(0.5, 0.163625, 0.471133, 0.558148)  # Teal
        color_tf.AddRGBPoint(0.75, 0.993248, 0.906157, 0.143936)  # Yellow
        color_tf.AddRGBPoint(1.0, 0.993248, 0.906157, 0.143936)  # Yellow

        # Create a vtkLookupTable from the vtkColorTransferFunction
        lut = vtk.vtkLookupTable()
        lut.SetNumberOfTableValues(256)  # Set the number of colors
        lut.Build()

        for i in range(256):
            val = i / 255.0
            color = color_tf.GetColor(val)
            lut.SetTableValue(i, color[0], color[1], color[2], 1.0)  # Set the RGBA values for each color

        # Set the range of scalar values
        lut.SetTableRange(0, 2000)  # Assuming your scalar values range from 0 to 1
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
        
    def extract_slice(self, input):

        # Extract a slice in the desired orientation
        reslice = vtk.vtkImageReslice()
        reslice.SetInputConnection(input.GetOutputPort())
        reslice.SetOutputDimensionality(2)
        sagittal = vtk.vtkMatrix4x4()
        sagittal.DeepCopy((0, 0,-1, self.center[0],
                        1, 0, 0, self.center[1],
                        0,-1, 0, self.center[2],
                        0, 0, 0, 1))
        reslice.SetResliceAxes(sagittal)
        reslice.SetInterpolationModeToLinear()
        

        # Update the vtkImageReslice
        reslice.Update()

        # Create an instance of vtkImageMapToColors
        mapToColors = vtk.vtkImageMapToColors()
        mapToColors.SetInputConnection(reslice.GetOutputPort())  # Set the input as the extracted slice from vtkImageReslice
        # table = get_table()
        # table = get_table_coloured()
        table=self.get_table_viridis()
        mapToColors.SetLookupTable(table)

        # Update the vtkImageMapToColors
        mapToColors.Update()

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
            self.mapToColors.SetLookupTable(self.get_table())
            self.ren.SetBackground(0,0,0)
            
            self.reader().Get
            
            self.iren.Render()
            pass

    def MouseMoveCallback(self, obj, event):
        
        (lastX, lastY) = self.iren.GetLastEventPosition()
        (mouseX, mouseY) = self.iren.GetEventPosition()
        if self.actions["Slicing"] == 1:
            deltaY = mouseY - lastY
            # reslice.Update()
            
            # sphere.SetRadius(sphere.GetRadius()+deltaY)
            
            print ("slice...", deltaY)
            sliceSpacing = self.reslicer.GetOutput().GetSpacing()[2]
            matrix = self.reslicer.GetResliceAxes()
            print ("matrix = ", matrix)
            # move the center point that we are slicing through
            center = matrix.MultiplyPoint((0, 0, sliceSpacing*deltaY, 1))
            matrix.SetElement(0, 3, center[0])
            matrix.SetElement(1, 3, center[1])
            matrix.SetElement(2, 3, center[2])
            self.reslicer.Update()
            
            self.iren.Render()
        else:
            self.interactorStyle.OnMouseMove()


    def SweepLine(self, line, direction, distance, cols):
        """
        Create a surface by sweeping a line with a given direction and distance.
        
        Parameters:
            line (vtkPolyData) : The input line.
            direction (list) : The direction to sweep the line.
            distance (float) : The distance to sweep the line.
            cols (int) : The number of columns for the surface.
        
        Returns:
            vtkPolyData : The resulting surface created by sweeping the line.
        """
        rows = line.GetNumberOfPoints()
        spacing = distance / cols
        surface = vtk.vtkPolyData()
        cols += 1
        numberOfPoints = rows * cols
        numberOfPolys = (rows - 1) * (cols - 1)
        points = vtk.vtkPoints()
        points.Allocate(numberOfPoints)
        polys = vtk.vtkCellArray()
        polys.Allocate(numberOfPolys * 4)
        x = [0.0, 0.0, 0.0]
        cnt = 0
        for row in range(rows):
            for col in range(cols):
                p = [0.0, 0.0, 0.0]
                line.GetPoint(row, p)
                x[0] = p[0] + direction[0] * col * spacing
                x[1] = p[1] + direction[1] * col * spacing
                x[2] = p[2] + direction[2] * col * spacing
                points.InsertPoint(cnt, x)
                cnt += 1
        pts = [0, 0, 0, 0]
        for row in range(rows - 1):
            for col in range(cols - 1):
                pts[0] = col + row * (cols)
                pts[1] = pts[0] + 1
                pts[2] = pts[0] + cols + 1
                pts[3] = pts[0] + cols
                polys.InsertNextCell(4, pts)
        surface.SetPoints(points)
        surface.SetPolys(polys)
        return surface

if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    window = MyMainWindow()
    window.show()
    sys.exit(app.exec_())