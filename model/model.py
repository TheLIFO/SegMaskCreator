import pyvista
from PyQt5.QtWidgets import QWidget
from PyQt5.QtCore import Qt, QObject, pyqtSignal
import pyvista as pv
from model.knot_data import KnotData 
import nrrd
import copy
    
class Model(QObject):
    # signals when model changes
    knotdata_changed = pyqtSignal(KnotData)
    mesh_changed = pyqtSignal(pv.DataSet)
    slice_bounds_changed = pyqtSignal(object)
    slice_pos_changed = pyqtSignal(object)
    show_cut_views_changed = pyqtSignal(object)
    threshold_changed = pyqtSignal(object)
    threshold_bounds_changed = pyqtSignal(object)
    

    
    # constructor
    def __init__(self): 
        super().__init__()
        
        self._knotdata = None    
        self._mesh = None
        self.mesh_actor = None
        
        
        self.mesh_scale = None
        self._threshold = 0  
        self._threshold_active = False      
        self._slice_bounds = { "x": {"min": 0, "max": 0},
                               "y": {"min": 0, "max": 0},
                               "z": {"min": 0, "max": 0},
                               "r": {"min": 0, "max": 0},
                               "r_x": {"min": 0, "max": 0},
                               "r_z": {"min": 0, "max": 0},
                               "r_a": {"min": 0.0, "max": 360.0}}
        self._slice_pos =    { "x": 0, "y": 0, "z": 0, "r": 0, "r_x": 0, "r_y": 0, "r_a": 0  }

        self.show_cut_views = {"x": False,
                               "y": False,
                               "z": False,
                               "r": False }
        
        # self.threshold_changed.connect(self.on_threshold_changed)
        
    def on_threshold_changed(self):
        if (self.threshold_active and self.mesh != None):
            print ("Threshold changed to ", self.threshold, " ...")
            self.mesh.threshold(self.threshold)
            print ("Threshold changed...ok")
        
        
    def load_imagedata(self, filename):
        print ("loading file:", filename)
                      
        reader = pyvista.get_reader(filename)
        reader.show_progress()
        self.mesh_orig = reader.read() 
        
        mesh = copy.deepcopy(self.mesh_orig)
        mesh = mesh.threshold(100)
        self.threshold = 100
        
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
                                "z": {"min": zmin, "max": zmax},
                                "r": {"min": 0, "max": max(round((xmax-xmin)/2), round((ymax-ymin)/2))},
                                "r_a": {"min": 0, "max": 360},
                                "r_x": {"min": xmin, "max": xmax},
                                "r_y": {"min": ymin, "max": ymax} }
        self.slice_pos = {  "x": round(mesh.center[0] * 2) / 2,
                            "y": round(mesh.center[1] * 2) / 2,
                            "z": round(mesh.center[2] * 2) / 2, 
                            "r": max(round((xmax-xmin)/2), round((ymax-ymin)/2)) / 2,
                            "r_x": round(mesh.center[0] * 2) / 2,
                            "r_y": round(mesh.center[1] * 2) / 2,
                            "r_a": 0.0}
        
        self.threshold_bounds = { "min": 0, "max": 3000}
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
        return int(self._threshold)
    @threshold.setter
    def threshold(self, threshold):  
        self._threshold = int(threshold)
        self.on_threshold_changed()        
        self.threshold_changed.emit(int(threshold))   
        # do actual thresholding with mesh
        
    @property
    def threshold_active(self):
        return self._threshold_active
    @threshold_active.setter
    def threshold_active(self, threshold_active):  
        self._threshold_active = threshold_active
        self.on_threshold_changed()
        self.threshold_changed.emit(self.threshold)
        # do actual thresholding with mesh
        
    @property
    def threshold_bounds(self):
        return self._threshold_bounds
    @threshold_bounds.setter
    def threshold_bounds(self, threshold_bounds):  
        self._threshold_bounds = threshold_bounds
        self.threshold_bounds_changed.emit(threshold_bounds)        
        
        

    @property 
    def slice_pos(self):
        return self._slice_pos
    @slice_pos.setter
    def slice_pos(self, pos):
        # only change and emit signal if values have really changed
        if not (self._slice_pos == pos):
            self._slice_pos = pos    
            if self._slice_pos["r_a"] == 360:
                self._slice_pos["r_a"] = 0        
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
    
    @property
    def show_cut_views(self):
        return self._show_cut_views
    @show_cut_views.setter
    def show_cut_views(self, values):
        self._show_cut_views = values  
        self.show_cut_views_changed.emit(values)
    