import pyvista
from PyQt5.QtWidgets import QWidget
from PyQt5.QtCore import Qt, QObject, pyqtSignal
import pyvista as pv
from model.knot_data import KnotData 

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
        self._threshold = 0
        self._slice_bounds = {  "x": {"min": 0, "max": 0},
                                "y": {"min": 0, "max": 0},
                                "z": {"min": 0, "max": 0} }
        self._slice_pos = {"x": 0, "y": 0, "z": 0}

        
    
    def load_imagedata(self, filename):
        print ("loading file:", filename)
                      
        reader = pyvista.get_reader(filename)
        reader.show_progress()
        mesh = reader.read() 
        # mesh = mesh.threshold(10)  
        
        # obtain new bounds
        xmin, xmax, ymin, ymax, zmin, zmax = mesh.bounds 
        xmin = int(xmin)
        xmax = int(xmax)
        ymin = int(ymin)
        ymax = int(ymax)
        zmin = int(zmin)
        zmax = int(zmax)
        self.slice_bounds = {   "x": {"min": xmin, "max": xmax},
                                "y": {"min": ymin, "max": ymax},
                                "z": {"min": zmin, "max": zmax} }
        self.slice_pos = {  "x": int(mesh.center[0]),
                            "y": int(mesh.center[1]),
                            "z": int(mesh.center[2]) }
        self.mesh = mesh # set new mesh here to trigger also setting new bounds
        self.knotdata = KnotData(filename)
        
   
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
    def knotdata(self, filename):        
        self._knotData = KnotData(filename)
        self.knotdata_changed.emit(self._knotData)       
    
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
        self._slice_pos = pos
        self.slice_pos_changed.emit(self._slice_pos)
    
    @property 
    def slice_bounds(self):
        return self._slice_bounds
    @slice_bounds.setter
    def slice_bounds(self, bounds):
        self._slice_bounds = bounds
        self.slice_bounds_changed.emit(self._slice_bounds)
        
  

    