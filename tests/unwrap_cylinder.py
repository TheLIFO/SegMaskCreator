#!/usr/bin/env python

# Use a cylindrical transform to extract a cylinder from an image
# and display it as a slice.

import math
import vtk
import numpy as np

def buttonCallback(obj, event):
  
  global slicing
  print ("button cb called, event ", event)
  if event == "RightButtonPressEvent":
      slicing = 1
  else:
      slicing = 0
  
  
  
      
      
def mouseMoveCallback(obj, event):
  
  if slicing:
    global iren
    global reslice
    (lastX, lastY) = iren.GetLastEventPosition()
    (mouseX, mouseY) = iren.GetEventPosition()        
    deltaY = mouseY - lastY  
    
    print("deltaY: ",deltaY)
    
    radialSize = 360
    origin = [ 0.0, 0.0, o[2] ]
    spacing = [ s[0], 2*math.pi/radialSize, s[2] ]
    extent = [
      ex[0], (ex[1] + 1)/2 - 1,
      0, radialSize - 1,
      ex[4], ex[5]
    ]
    # Unwrap with a cylindrical transform
    transform = vtk.vtkCylindricalTransform()

    # reslice = vtk.vtkImageReslice()
    reslice.SetInputConnection(rotate.GetOutputPort())
    reslice.SetInterpolationModeToLinear()
    reslice.SetResliceTransform(transform)
    reslice.SetOutputOrigin(origin)
    reslice.SetOutputSpacing(spacing)
    extent  = [int(np.round(x)) for x in extent]
    reslice.SetOutputExtent(extent)
    reslice.Update()
    
    iren.Render()
  # coordinate = vtk.vtkCoordinate()
  # coordinate.SetCoordinateSystemToDisplay()
  # coordinate.SetValue(mouseX, mouseY)
  # coord = coordinate.GetComputedWorldValue(self.ren)
  # print("coord:", coord)

  
  # # now the same thing with proper matrix transformation
  # origin = self.reslicer.GetOutput().GetOrigin()
  # pixel = [coord[0], coord[1]]
  # resliceAxes = self.reslicer.GetResliceAxes()
  # coord = resliceAxes.MultiplyDoublePoint([pixel[0]+origin[0], pixel[1]+origin[1], origin[2], 1])


  # # translate coordinates into array indices
  # x = round(coord[0]/self.xSpacing)
  # y = round(coord[1]/self.ySpacing)
  # z = round(coord[2]/self.zSpacing)

  # if (x < self.xMin) or (x > self.xMax) or (y < self.yMin) or (y > self.yMax) or (z < self.zMin) or (z > self.zMax):            
  #     value = 0
  #     value_threshed = 0
  # else:
  #     value          = self.reader.GetOutput().GetScalarComponentAsDouble(x, y, z, 0)
  #     value_threshed = self.threshed.GetOutput().GetScalarComponentAsDouble(x, y, z, 0)
          
  # print("x mouse: ", mouseX, " y mouse: ", mouseY, "world-x: ",coord[0], " world-y: ", coord[1],"world-z: ", coord[2],"   Scalar: ", value, "threshed: ", value_threshed)




  # if self.actions["Slicing"] == 1:
  #     print("slicing")
  #     deltaY = mouseY - lastY
  #     # reslice.Update()
      
  #     # sphere.SetRadius(sphere.GetRadius()+deltaY)
      
  #     # print ("slice...", deltaY)
  #     sliceSpacing = self.reslicer.GetOutput().GetSpacing()[2]
      
    
  #     position = self.planeWidget.GetSlicePosition()
  #     self.planeWidget.SetSlicePosition(position + deltaY)
      
      
  #     self.reslicer.Update()
  #     self.reslicer_threshed.Update()
  #     self.reslicer_threshed.SetOutputOrigin(self.reslicer.GetOutputOrigin())
  #     self.reslicer_threshed.SetResliceAxes(self.reslicer.GetResliceAxes())
  #     self.iren.Render()
  #     self.iren3D.Render()
  # else:
  #     self.interactorStyle.OnMouseMove()

global slicing
slicing = 0

global iren
global reslice
reader = vtk.vtkNrrdReader()
filename = "data\Drydisk07.6.nrrd"
reader.SetFileName(filename)
# reader = vtk.vtkImageReader()
# reader.ReleaseDataFlagOff()
# reader.SetDataByteOrderToLittleEndian()
# reader.SetDataMask(0x7fff)
# reader.SetDataExtent(0,63,0,63,1,93)
# reader.SetDataSpacing(3.2,3.2,1.5)
# reader.SetFilePrefix("" + str(VTK_DATA_ROOT) + "/Data/headsq/quarter")
reader.Update()

# center the image
centering = vtk.vtkImageChangeInformation()
centering.SetInputConnection(reader.GetOutputPort())
centering.CenterImageOn()

# rotate the image so that the cylinder cuts through it as desired
rotate = vtk.vtkImageReslice()
rotate.SetInputConnection(centering.GetOutputPort())
rotate.SetResliceAxesDirectionCosines(
  -1, 0, 0,
  0, -1, 0,
  0, 0, 1 )
rotate.SetResliceAxesOrigin(0,0,0)
rotate.Update()

# get the image geometry
global o
global s
global ex
o = rotate.GetOutput().GetOrigin()
s = rotate.GetOutput().GetSpacing()
ex = rotate.GetOutput().GetExtent()
print ("o: ",o)
print ("s: ",s)
print ("ex: ",ex)
# new information for cylindrical coordinate geometry
radialSize = 64
origin = [ 0.0, 0.0, o[2] ]
spacing = [ s[0], 2*math.pi/radialSize, s[2] ]
extent = [
  ex[0], (ex[1] + 1)/2 - 1,
  0, radialSize - 1,
  ex[4], ex[5]
]

print ("origin: ",origin)
print ("spacing: ",spacing)
print ("extent: ",extent)

# Unwrap with a cylindrical transform
transform = vtk.vtkCylindricalTransform()

reslice = vtk.vtkImageReslice()
reslice.SetInputConnection(rotate.GetOutputPort())
reslice.SetInterpolationModeToLinear()
reslice.SetResliceTransform(transform)
reslice.SetOutputOrigin(origin)
reslice.SetOutputSpacing(spacing)
extent  = [int(np.round(x)) for x in extent]
reslice.SetOutputExtent(extent)
reslice.Update()

# Multiply angular spacing by the radius
r = 100.0
stretch = vtk.vtkImageChangeInformation()
stretch.SetInputConnection(reslice.GetOutputPort())
stretch.SetOutputSpacing(spacing[0], r*spacing[1], spacing[2])

# Create the RenderWindow, Renderer
ren1 = vtk.vtkRenderer()
renWin = vtk.vtkRenderWindow()
renWin.AddRenderer(ren1)
iren = vtk.vtkRenderWindowInteractor()
iren.SetRenderWindow(renWin)

im = vtk.vtkImageSliceMapper()
im.SetInputConnection(stretch.GetOutputPort())
im.SliceFacesCameraOn()
im.SliceAtFocalPointOn()
im.BorderOn()

ip = vtk.vtkImageProperty()
ip.SetColorWindow(2000)
ip.SetColorLevel(1000)
ip.SetAmbient(0.0)
ip.SetDiffuse(1.0)
ip.SetOpacity(1.0)
ip.SetInterpolationTypeToLinear()

ia = vtk.vtkImageSlice()
ia.SetMapper(im)
ia.SetProperty(ip)

ren1.AddViewProp(ia)
ren1.SetBackground(0.1, 0.2, 0.4)
renWin.SetSize(600, 600)

iren = vtk.vtkRenderWindowInteractor()
style = vtk.vtkInteractorStyleImage()
style.SetInteractionModeToImageSlicing()
iren.SetInteractorStyle(style)
interactorStyle3D = vtk.vtkInteractorStyleTrackballCamera()
buttonpressed3D = 0
        
interactorStyle3D.AddObserver("MouseMoveEvent", mouseMoveCallback)
interactorStyle3D.AddObserver("RightButtonPressEvent", buttonCallback)
interactorStyle3D.AddObserver("RightButtonReleaseEvent", buttonCallback)

iren.SetInteractorStyle(interactorStyle3D)
renWin.SetInteractor(iren)

# render the image, be sure to get the view direction correct
renWin.Render()
cam1 = ren1.GetActiveCamera()
cam1.Azimuth(90)
cam1.SetViewUp(0.0, 0.0, -1.0)
cam1.ParallelProjectionOn()
ren1.ResetCameraClippingRange()
renWin.Render()

iren.Start()

