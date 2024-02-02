
import vtk

def get_table_viridis():
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

reader = vtk.vtkNrrdReader()
filename = "data\Drydisk07.6.nrrd"
reader.SetFileName(filename)
reader.Update()


# does not work !!!!  TODO
# selector = vtk.vtkThreshold()
# selector.SetInputConnection(reader.GetOutputPort())

# selector.SetLowerThreshold(200)
# selector.SetUpperThreshold(2000)

# data_alpha_range  = [0.0, 28.0]
data_alpha_range  = [0, 2000]
data_colour_range = [0, 2000]

# how do we create zero opacity?????

opacity_transfer_function = vtk.vtkPiecewiseFunction()
opacity_transfer_function.AddPoint(data_alpha_range[0], 1)
opacity_transfer_function.AddPoint(data_alpha_range[1], 1)

colour_transfer_function = vtk.vtkColorTransferFunction()
colour_transfer_function.AddRGBPoint(data_colour_range[0], 0.0, 0.0, 0.0)
colour_transfer_function.AddRGBPoint(data_colour_range[1], 1.0, 0.5, 0.7)

volume_property = vtk.vtkVolumeProperty()
volume_property.SetColor(colour_transfer_function)
volume_property.SetScalarOpacity(opacity_transfer_function)
volume_property.SetInterpolationTypeToLinear()

volume_mapper = vtk.vtkGPUVolumeRayCastMapper()
volume_mapper.SetInputConnection(reader.GetOutputPort())
volume_mapper.SetBlendModeToMaximumIntensity()

volume = vtk.vtkVolume()
volume.SetMapper(volume_mapper)
volume.SetProperty(volume_property)

ren1 = vtk.vtkRenderer()
ren1.SetBackground(1.0, 1.0, 1.0)
ren1.AddActor(volume)
ren1.ResetCamera()

renWin = vtk.vtkRenderWindow()
renWin.AddRenderer(ren1)
renWin.SetSize(800, 800)

iren = vtk.vtkRenderWindowInteractor()
iren.SetRenderWindow(renWin)

iren.Initialize()
iren.Start()


