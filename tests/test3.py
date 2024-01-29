import pyvista as pv
import vtk

mesh = pv.Cone()
mesh = mesh.translate((2,2,2),inplace=False)
p = pv.Plotter(shape=(1, 2))
p.window_size = (1000, 1000)
p.set_background('black', all_renderers=True)

cutter = vtk.vtkCutter()
plane = vtk.vtkPlane()
cutter.SetInputData(mesh)
cutter.SetCutFunction(plane)

plane.SetOrigin(1,1,1)
origin = plane.GetOrigin()
print("origin: ", origin) 
plane.SetNormal((1, 0, 0))

def callback(normal, origin):
    print("origin: ", origin)
    plane.SetOrigin(origin)
    plane.SetNormal(normal)
    cutter.Update()
    p.subplot(0, 1)
    p.camera.reset_clipping_range()

p.subplot(0, 1)
p.add_mesh(cutter)
p.view_yz()

p.subplot(0, 0)
p.add_mesh(mesh, opacity=0.5)
widget = p.add_plane_widget(callback=callback, interaction_event="always", assign_to_axis='x')
widget.SetOrigin(1,1,1)
p.show()