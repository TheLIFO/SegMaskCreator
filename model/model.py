import pyvista
from PyQt5.QtWidgets import QWidget
from PyQt5.QtCore import Qt, QObject, pyqtSignal
import pyvista as pv
from model.knot_data import KnotData 
import nrrd
    
class Model(QObject):
    # signals when model changes
    knotdata_changed = pyqtSignal(KnotData)
    mesh_changed = pyqtSignal(pv.DataSet)
    slice_bounds_changed = pyqtSignal(object)
    slice_pos_changed = pyqtSignal(object)

    
    # constructor
    def __init__(self): 
        super().__init__()
        
        self._knotdata = None    
        self._mesh = None
        self.mesh_scale = None
        self._threshold = 0        
        self._slice_bounds = { "x": {"min": 0, "max": 0},
                               "y": {"min": 0, "max": 0},
                               "z": {"min": 0, "max": 0} }
        self._slice_pos =    { "x": 0, "y": 0, "z": 0 }

        
    
    def load_imagedata(self, filename):
        print ("loading file:", filename)
                      
        reader = pyvista.get_reader(filename)
        reader.show_progress()
        mesh = reader.read() 
        mesh = mesh.threshold(100)  
        
        self.mesh_scale = (1, 1, 1)
        self.mesh_origin = (0, 0, 0)
        
        
        header = nrrd.read_header(filename)
        try:
            spacing_dirs = header["space directions"]
            self.mesh_scale = (spacing_dirs[0, 0], spacing_dirs[1, 1], spacing_dirs[2, 2])
            self.mesh_origin = header["space origin"]
        except:
            pass
        
        mesh = mesh.translate(self.mesh_origin)
        mesh = mesh.scale(self.mesh_scale)
        # obtain new bounds
        xmin, xmax, ymin, ymax, zmin, zmax = mesh.bounds 
        xmin = round(xmin * 2) / 2
        xmax = round(xmax * 2) / 2
        ymin = round(ymin * 2) / 2
        ymax = round(ymax * 2) / 2
        zmin = round(zmin * 2) / 2
        zmax = round(zmax * 2) / 2
        self.slice_bounds = {   "x": {"min": xmin, "max": xmax},
                                "y": {"min": ymin, "max": ymax},
                                "z": {"min": zmin, "max": zmax} }
        self.slice_pos = {  "x": round(mesh.center[0] * 2) / 2,
                            "y": round(mesh.center[1] * 2) / 2,
                            "z": round(mesh.center[2] * 2) / 2 }
        
        self.knotdata = KnotData(filename)
        self.mesh = mesh # set new mesh here to trigger also setting new bounds
        
   
    @property
    def mesh(self):
        return self._mesh
    @mesh.setter
    def mesh(self, mesh):
        self._mesh = mesh
        self.mesh_changed.emit(mesh)
    
    @property
    def knotdata(self):
        return self._knotdata
    @knotdata.setter
    def knotdata(self, value):        
        self._knotdata = value
        self.knotdata_changed.emit(value)       
    
    @property
    def threshold(self):
        return self._threshold
    @threshold.setter
    def threshold(self, threshold):  
        self._threshold = threshold

    @property 
    def slice_pos(self):
        return self._slice_pos
    @slice_pos.setter
    def slice_pos(self, pos):
        # only change and emit signal if values have really changed
        if not (self._slice_pos == pos):
            self._slice_pos = pos            
            self.slice_pos_changed.emit(self._slice_pos)
    
    @property 
    def slice_bounds(self):
        return self._slice_bounds
    @slice_bounds.setter
    def slice_bounds(self, bounds):
        # only change and emit signal if values have really changed
        if not (self._slice_bounds == bounds):
            self._slice_bounds = bounds
            self.slice_bounds_changed.emit(self._slice_bounds)
            
    
        
  

    