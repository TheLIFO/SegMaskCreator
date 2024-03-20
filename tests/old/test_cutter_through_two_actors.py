import vtk



# Start by loading some data.
reader = vtk.vtkNrrdReader()
filename = "data\Drydisk07.6.nrrd"
reader.SetFileName(filename)
reader.Update()

# threshed = 

# imageData.SetExtent(0, 50, 0, 50, 0, 1)
# imageData.SetSpacing(1, 1, 1)
# imageData.SetOrigin(0, 0, 0)
# imageData.AllocateScalars(vtk.VTK_FLOAT, 3)
# for i in range(50):
#     for j in range(50):
#         imageData.SetScalarComponentFromFloat(i, j, 0, 1, 255)


# Create a vtkColorTransferFunction
color_tf = vtk.vtkColorTransferFunction()
color_tf.AddRGBPoint(0.0, 0.267004, 0.004874, 0.329415)  # Dark blue
color_tf.AddRGBPoint(0.25, 0.253935, 0.265254, 0.529983)  # Purple
color_tf.AddRGBPoint(0.5, 0.163625, 0.471133, 0.558148)  # Teal
color_tf.AddRGBPoint(0.75, 0.993248, 0.906157, 0.143936)  # Yellow
color_tf.AddRGBPoint(1.0, 0.993248, 0.906157, 0.143936)  # Yellow


lut = vtk.vtkLookupTable()
lut.SetSaturationRange(0,0)
lut.SetTableRange(1, 256)  # Set the number of colors
lut.SetRange(0, 2000)  # Assuming your scalar values range from 0 to 2000
lut.SetValueRange(0, 1)
lut.SetRampToLinear()

for i in range(256): # 0 .. 255
    val = i / 255.0
    color = color_tf.GetColor(val)
    lut.SetTableValue(i, color[0], color[1], color[2], .5)  # Set the RGBA values for each color
lut.Build()

scalarBar = vtk.vtkScalarBarActor()
scalarBar.SetLookupTable(lut)
scalarBar.SetTitle("Title")
scalarBar.SetNumberOfLabels(5)

color = vtk.vtkImageMapToColors()
color.SetLookupTable(lut)
color.SetInputConnection(reader.GetOutputPort())

opacity_tf = vtk.vtkPiecewiseFunction()
opacity_tf.AddPoint(0, 0.0)
opacity_tf.AddPoint(450/2000, 0.0)
opacity_tf.AddPoint(500/2000, 0.5)
opacity_tf.AddPoint(1, 0.5)

volProperty = vtk.vtkVolumeProperty()
volProperty.SetColor(color_tf)
volProperty.SetScalarOpacity(opacity_tf)
volProperty.ShadeOn()
volProperty.SetInterpolationTypeToLinear()

mapper = vtk.vtkGPUVolumeRayCastMapper()
mapper.SetBlendModeToComposite()
mapper.SetInputConnection(color.GetOutputPort())


volume = vtk.vtkVolume()
volume.SetMapper(mapper)
volume.SetProperty(volProperty)




renderer = vtk.vtkRenderer()
renderWindow = vtk.vtkRenderWindow()
renderWindow.AddRenderer(renderer)
renderWindowInteractor = vtk.vtkRenderWindowInteractor()
renderWindowInteractor.SetRenderWindow(renderWindow)

renderer.AddVolume(volume)
renderer.AddActor2D(scalarBar)
renderer.SetBackground(1, 1, 1)
renderWindow.Render()
renderWindowInteractor.Start()