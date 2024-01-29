import pyvista as pv
import vtk

 
p = pv.Plotter(shape=(2, 2))

p.enable_image_style()
p.window_size = (1000, 1000)

cutter_x = vtk.vtkCutter()
plane_x = vtk.vtkPlane()


cutter_y = vtk.vtkCutter()
plane_y = vtk.vtkPlane()

def callback_x(normal, origin):
    print("origin: ", origin)
    plane_x.SetOrigin(origin)
    plane_x.SetNormal(normal)
    cutter_x.Update()
    
    
    # apperently not necessary:
    # p.subplot(0, 1)
    # widget.SetOrigin(origin)
    p.camera.reset_clipping_range()


def callback_y(normal, origin):
    print("origin: ", origin)
    plane_y.SetOrigin(origin)
    plane_y.SetNormal(normal)
    cutter_y.Update()
    
    
    # apperently not necessary:
    # p.subplot(1, 1)
    # widget.SetOrigin(origin)
    p.camera.reset_clipping_range()


# get 3D image
filename = "data\Drydisk07.6.nrrd"
reader = pv.get_reader(filename)
reader.show_progress()
mesh = reader.read()  
mesh = mesh.threshold(200)
# mesh = mesh.threshold([10,20000])

p.subplot(0, 0)
widget_x = p.add_plane_widget(callback=callback_x, test_callback = False, interaction_event="always", assign_to_axis='x')
widget_y = p.add_plane_widget(callback=callback_y, test_callback = False, interaction_event="always", assign_to_axis='y')

#update mesh
p.add_mesh(mesh, opacity=0.5)

xmin, xmax, ymin, ymax, zmin, zmax = mesh.bounds 

widget_x.PlaceWidget(xmin, xmax, ymin, ymax, zmin, zmax)
cutter_x.SetInputData(mesh)
cutter_x.SetCutFunction(plane_x)
plane_x.SetOrigin(mesh.center)
plane_x.SetNormal((1, 0, 0))
p.subplot(0, 1)
p.add_mesh(cutter_x)
p.view_yz()
p.enable_parallel_projection()


# widget_y.PlaceWidget(xmin, xmax, ymin, ymax, zmin, zmax)
# cutter_y.SetInputData(mesh)
# cutter_y.SetCutFunction(plane_y)
# plane_y.SetOrigin(mesh.center)
# plane_y.SetNormal((0, 1, 0))
# p.subplot(1, 1)
# p.add_mesh(cutter_y)
# p.view_yz()
# p.enable_parallel_projection()



p.show()

