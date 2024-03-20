from pyvista import Plotter, set_plot_theme, wrap
from astropy.io import fits
import numpy as np

set_plot_theme("document")
data=fits.open('lya_cube_merged_with_artificial_source_CU_1pc.fits')[0].data#[:n,:n,:n]
data = np.log10(data[:,:,:])

mask = np.ones(len(data.ravel()),dtype=bool)#
mask=np.isfinite(data.ravel())#>np.nanpercentile(data,2)
mask=(data.ravel()>np.nanpercentile(data,0.1)) & (data.ravel()<np.nanpercentile(data,99.9))

print(np.sum(mask)/len(mask))
xx, yy, zz = np.indices(data.shape)#np.me 
starting_mesh = wrap(np.array([yy.ravel()[mask],zz.ravel()[mask],xx.ravel()[mask]]).T)   
starting_mesh['Intensity']= data.ravel()[mask]#np.log10(data.ravel()[mask])#exp(-((yy-yy.mean())**2+(xx-xx.mean())**2+(zz-zz.mean())**2)/100).ravel()

def createMesh(DensityMin=0.5,DensityMax=0.5,StretchingFactor=0.5):
    mask = (data.ravel()>DensityMin) & (data.ravel()<DensityMax)
    mesh =  wrap(np.array([yy.ravel()[mask],zz.ravel()[mask],StretchingFactor*xx.ravel()[mask]-np.nanmean(StretchingFactor*xx.ravel()[mask])]).T)
    mesh['Intensity']= data.ravel()[mask]#np.log10(data.ravel()[mask])#exp(-((yy-yy.mean())**2+(xx-xx.mean())**2+(zz-zz.mean())**2)/100).ravel()
    return mesh


class Change3dMesh():
    def __init__(self, mesh):
        self.input = mesh
        self.mesh = mesh.copy()
        self.kwargs = {
            'DensityMin': 0.5,
            'DensityMax': 0.5,
            'StretchingFactor': 0.5,
        }
        self._last_normal = 'z'
        self._last_origin = self.mesh.center

    def __call__(self, param, value):
        self.kwargs[param] = value
        self.update()

    def update(self):
        result = createMesh(**self.kwargs)
        self.mesh.overwrite(result)
        self.update_clip(self._last_normal, self._last_origin)
        return
    
    def update_clip(self, normal, origin):
        self.mesh.overwrite(self.mesh.clip(normal=normal, origin=origin, invert=True))
        self._last_normal = normal
        self._last_origin = origin
        


engine = Change3dMesh(starting_mesh)


p = Plotter(notebook=False,window_size=[2*1024, 2*768], title='3D')

p.add_mesh(engine.mesh, show_edges=True,
           nan_opacity=0, cmap='jet')

p.add_plane_widget(
    callback=lambda n, o: engine.update_clip(n, o), normal='z', 
)

m = p.add_slider_widget(
    callback=lambda value: engine('DensityMin', int(value)),
    rng=[np.nanmin(data[np.isfinite(data)]),np.nanmax(data[np.isfinite(data)])],
    value=np.nanmin(data[np.isfinite(data)]),
    title="Density Threshold Min",
    pointa=(.025, .9), pointb=(.31, .9),
)
p.add_slider_widget(
    callback=lambda value: engine('DensityMax', int(value)),
    rng=[np.nanmin(data[np.isfinite(data)]),np.nanmax(data[np.isfinite(data)])],
    value=np.nanmax(data[np.isfinite(data)]),
    title="Density Threshold Max",
    pointa=(.35, .9), pointb=(.64, .9),
)
p.add_slider_widget(
    callback=lambda value: engine('StretchingFactor', value),
    rng=[0, 1],
    value=0.5,
    title="Stretching Factor",
    pointa=(.67, .9), pointb=(.98, .9),
)
p.show()