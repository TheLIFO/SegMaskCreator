import vtk

class Luts:
    def __init__(self):
        pass        
    
    def get_standard_lut(scalar_range = [0, 2000], tablerange = [0, 255], opacity = 1.0):        
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
        
        return lut
    
    def get_threshed_lut(color = [1,0,0], opacity = .8):
        
        # Create a vtkLookupTable from the vtkColorTransferFunction
        lut = vtk.vtkLookupTable()
        lut.SetNumberOfColors(2) # Set the number of colors
        lut.SetNumberOfTableValues(2)
        lut.SetTableValue(0, 0.0, 0.0, 0.0, 0.0)  # Set the RGBA values for each color
        lut.SetTableValue(1, color[0], color[1], color[2], opacity)  # Set the RGBA values for each color
        lut.Build()
        
        return lut