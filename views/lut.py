import vtk

class Luts:
    def __init__(self):
        pass        
    
    def get_standard_lut(scalar_range = [0, 2000], tablerange = [0, 255], opacity = 1.0):        
        # Create a vtkColorTransferFunction
        color_tf = vtk.vtkColorTransferFunction()
        # color_tf.AddRGBPoint(0.0, 0.267004, 0.004874, 0.329415)  # Dark blue
        # color_tf.AddRGBPoint(0.25, 0.253935, 0.265254, 0.529983)  # Purple
        # color_tf.AddRGBPoint(0.5, 0.163625, 0.471133, 0.558148)  # Teal
        # color_tf.AddRGBPoint(0.75, 0.993248, 0.906157, 0.143936)  # Yellow
        # color_tf.AddRGBPoint(1.0, 0.993248, 0.906157, 0.143936)  # Yellow

        color_tf.AddRGBPoint(0.0,  68/255,   1/255,  84/255)  
        color_tf.AddRGBPoint(0.25, 59/255,  82/255, 139/255)  
        color_tf.AddRGBPoint(0.5,  33/255, 145/255, 140/255)  
        color_tf.AddRGBPoint(0.75, 94/255, 201/255,  98/255)          
        color_tf.AddRGBPoint(1.0, 253/255, 231/255,  37/255)  

        # Create a vtkLookupTable from the vtkColorTransferFunction
        lut = vtk.vtkLookupTable()
        lut.SetTableRange(tablerange[0], tablerange[1])  # Set the number of colors
        lut.SetRange(scalar_range[0], scalar_range[1])  

        for i in range(tablerange[1]+1): # 0 .. 255
            val = i / tablerange[1]
            color = color_tf.GetColor(val)
            lut.SetTableValue(i, color[0], color[1], color[2], opacity)  # Set the RGBA values for each color
        
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