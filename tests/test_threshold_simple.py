import pyvista as pv


sphere = pv.Sphere(center=(1, 0, 0))
cube = pv.Cube()




def callback(mesh):
    """Shrink the mesh each time it's clicked."""
    shrunk = mesh.shrink(0.9)
    mesh.copy_from(shrunk)  # make operation "in-place" by replacing the original mesh


pl = pv.Plotter()
pl.add_mesh(sphere, color='r')
pl.add_mesh(cube, color='b')
pl.enable_mesh_picking(callback=callback, show=False)
pl.show()