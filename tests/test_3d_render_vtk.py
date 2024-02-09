#!/usr/bin/env python

# noinspection PyUnresolvedReferences
import vtkmodules.vtkInteractionStyle
from vtkmodules.vtkCommonColor import vtkNamedColors
from vtkmodules.vtkCommonDataModel import vtkPiecewiseFunction
# from vtkmodules.vtkIOLegacy import 
from vtkmodules.vtkRenderingCore import (
    vtkColorTransferFunction,
    vtkRenderWindow,
    vtkRenderWindowInteractor,
    vtkRenderer,
    vtkVolume,
    vtkVolumeProperty
)
from vtkmodules.vtkRenderingVolume import vtkFixedPointVolumeRayCastMapper
# noinspection PyUnresolvedReferences
from vtkmodules.vtkRenderingVolumeOpenGL2 import vtkOpenGLRayCastImageDisplayHelper
import vtk

threshed = None
iren = None
interactorStyle = None
threshold = 1000
slicing = 0
def main():
    fileName = "data\Drydisk07.6.nrrd"

    colors = vtkNamedColors()

    # This is a simple volume rendering example that
    # uses a vtkFixedPointVolumeRayCastMapper

    # Create the standard renderer, render window
    # and interactor.
    ren1 = vtkRenderer()

    renWin = vtkRenderWindow()
    renWin.AddRenderer(ren1)

    global iren
    iren = vtkRenderWindowInteractor()
    iren.SetRenderWindow(renWin)

    # Create the reader for the data.
    reader = vtk.vtkNrrdReader()
    reader.SetFileName(fileName)
    
    global threshold 
    global threshed
    threshed = vtk.vtkImageThreshold()
    threshed.SetInputConnection(reader.GetOutputPort()) # Set your input vtkImageData
    threshed.ThresholdByUpper(threshold) # Set the threshold value
    threshed.ReplaceInOn() # Set the operation to replace in values
    threshed.SetInValue(1) # Set the value for inside the threshold
    threshed.ReplaceOutOn() # Set the operation to replace out values
    threshed.SetOutValue(0) # Set the value for outside the threshold
    threshed.Update()

    # Create transfer mapping scalar value to opacity.
    opacityTransferFunction = vtkPiecewiseFunction()
    opacityTransferFunction.AddPoint(0, 0.0)
    opacityTransferFunction.AddPoint(450, 0.0)
    opacityTransferFunction.AddPoint(451, 0.2)
    
    opacityThreshedTransferFunction = vtkPiecewiseFunction()
    opacityThreshedTransferFunction.AddPoint(0, 0)
    opacityThreshedTransferFunction.AddPoint(1, 1)
    opacityThreshedTransferFunction.AddPoint(2500, 1)
    
    # Create transfer mapping scalar value to color.
    colorTransferFunction = vtkColorTransferFunction()
    colorTransferFunction.AddRGBPoint(0.0, 0.0, 0.0, 0.0)
    colorTransferFunction.AddRGBPoint(255.0, 1.0, 1.0, 1.0)

    colorThreshedTransferFunction = vtkColorTransferFunction()
    colorThreshedTransferFunction.AddRGBPoint(0.0, 1.0, 0.0, 0.0)
    colorThreshedTransferFunction.AddRGBPoint(255.0, 1.0, 0.0, 0.0)
    
    # The property describes how the data will look.
    volumeProperty = vtkVolumeProperty()
    volumeProperty.SetColor(colorTransferFunction)
    volumeProperty.SetScalarOpacity(opacityTransferFunction)
    volumeProperty.ShadeOn()
    volumeProperty.SetInterpolationTypeToLinear()

    # The property describes how the data will look.
    volumeThreshedProperty = vtkVolumeProperty()
    volumeThreshedProperty.SetColor(colorThreshedTransferFunction)
    volumeThreshedProperty.SetScalarOpacity(opacityThreshedTransferFunction)
    volumeThreshedProperty.ShadeOn()
    volumeThreshedProperty.SetInterpolationTypeToLinear()

    

    # The mapper / ray cast function know how to render the data.
    volumeMapper = vtkFixedPointVolumeRayCastMapper()
    volumeMapper.SetInputConnection(reader.GetOutputPort())
    
    # The volume holds the mapper and the property and
    # can be used to position/orient the volume.
    volume = vtkVolume()
    volume.SetMapper(volumeMapper)
    volume.SetProperty(volumeProperty)

        # The mapper / ray cast function know how to render the data.
    volumeThreshedMapper = vtkFixedPointVolumeRayCastMapper()
    volumeThreshedMapper.SetInputConnection(threshed.GetOutputPort())

    
    
    # The volume holds the mapper and the property and
    # can be used to position/orient the volume.
    volumeThreshed = vtkVolume()
    volumeThreshed.SetMapper(volumeThreshedMapper)
    volumeThreshed.SetProperty(volumeThreshedProperty)


    ren1.AddVolume(volume)
    ren1.AddVolume(volumeThreshed)
    ren1.SetBackground(colors.GetColor3d('Wheat'))
    ren1.GetActiveCamera().Azimuth(45)
    ren1.GetActiveCamera().Elevation(30)
    ren1.ResetCameraClippingRange()
    ren1.ResetCamera()

    # scalarBar = vtk.vtkScalarBarActor()
    # scalarBar.SetLookupTable()
    # scalarBar.SetTitle("Title")
    # scalarBar.SetNumberOfLabels(5)


    renWin.SetSize(600, 600)
    renWin.SetWindowName('SimpleRayCast')
    renWin.Render()
    
    global interactorStyle
    interactorStyle = vtk.vtkInteractorStyleTrackballCamera()
    iren.SetInteractorStyle(interactorStyle)
        
    interactorStyle.AddObserver("MouseMoveEvent", MouseMoveCallback)
    interactorStyle.AddObserver("RightButtonPressEvent", ButtonCallback)
    interactorStyle.AddObserver("RightButtonReleaseEvent", ButtonCallback)
    # iren.Initialize()
    iren.Start()
  
   
def ButtonCallback(obj, event):
    global slicing
    global interactorStyle
    print ("button cb called, event ", event)
    if event == "RightButtonPressEvent":
        slicing = 1
    else:
        slicing = 0
        # interactorStyle.OnBu
        
        
        # if event == "RightButtonPressEvent":
            # self.mapToColors.SetLookupTable(self.get_table())
            # self.ren.SetBackground(1, 1, 1)
            
            # # self.mesh().Get
            
            # self.iren.Render()
            # pass

def MouseMoveCallback(obj, event):
    global slicing
    global iren
    global threshold
    global threshed
    global interactorStyle
    
    (lastX, lastY) = iren.GetLastEventPosition()
    (mouseX, mouseY) = iren.GetEventPosition()        
    
    # coordinate = vtk.vtkCoordinate()
    # coordinate.SetCoordinateSystemToDisplay()
    # coordinate.SetValue(mouseX, mouseY)
    # coord = coordinate.GetComputedWorldValue(self.ren)
    
    
    # value = self.mesh.GetOutput().GetScalarComponentAsDouble(round(coord[0]/self.xSpacing), round(coord[1]/self.ySpacing), round(self.z_pos/self.zSpacing), 0)
    # value_threshed = self.threshold.GetOutput().GetScalarComponentAsDouble(round(coord[0]/self.xSpacing), round(coord[1]/self.ySpacing), round(self.z_pos/self.zSpacing), 0)
    # self.source.SetCenter(coord[0], coord[1], 0)
    
    # self.iren.Render()
    
    
    # print("x: ", mouseX, " y: ", mouseY, "world-x: ",coord[0], " world-y: ", coord[1],"world-z: ", self.z_pos,"   Scalar: ", value, "threshed: ", value_threshed)
    if slicing == 1:
        deltaY = mouseY - lastY
        # reslice.Update()
        
        # sphere.SetRadius(sphere.GetRadius()+deltaY)
        
        threshold = threshold + deltaY
        print ("threshold...", threshold)
    
        threshed.ThresholdByUpper(threshold) # Set the threshold value    
        threshed.Update()
        
        
        
        iren.Render()
    else:
        interactorStyle.OnMouseMove()



if __name__ == '__main__':
    main()