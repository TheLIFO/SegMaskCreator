import pyvista as pv
from pyvista import examples

mesh = examples.download_embryo()
mesh.bounds

slices = mesh.slice_orthogonal(x=100, z=75)

cpos = [
    (540.9115516905358, -617.1912234499737, 180.5084853429126),
    (128.31920055083387, 126.4977720785509, 111.77682599082095),
    (-0.1065160140819035, 0.032750075477590124, 0.9937714884722322),
]




dargs = dict(cmap='gist_ncar_r')



p2 = pv.Plotter()
p2.add_mesh(slices, **dargs)
p2.show_grid()
p2.show(cpos =cpos)


# p = pv.Plotter(shape=(2, 2))
# # XYZ - show 3D scene first
# p.subplot(1, 1)
# p.add_mesh(slices, **dargs)
# p.show_grid()
# p.camera_position = cpos
# # XY
# p.subplot(0, 0)
# p.add_mesh(slices, **dargs)
# p.show_grid()
# p.camera_position = 'xy'
# p.enable_parallel_projection()
# # ZY
# p.subplot(0, 1)
# p.add_mesh(slices, **dargs)
# p.show_grid()
# p.camera_position = 'zy'
# p.enable_parallel_projection()
# # XZ
# p.subplot(1, 0)
# p.add_mesh(slices, **dargs)
# p.show_grid()
# p.camera_position = 'xz'
# p.enable_parallel_projection()

# p.show()