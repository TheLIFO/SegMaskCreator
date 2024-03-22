# import pyvista
from PyQt5.QtWidgets import QWidget
from PyQt5.QtCore import Qt, QObject, pyqtSignal
# import pyvista as pv
from model.knot_data import KnotData 
import nrrd
import copy
import vtk
    
class Model(QObject):
    # signals when model changes
    knotdata_changed = pyqtSignal(KnotData)
    mesh_changed = pyqtSignal()
    slice_bounds_changed = pyqtSignal(object)
    slice_pos_changed = pyqtSignal(object)
    show_cut_views_changed = pyqtSignal(object)
    threshold_changed = pyqtSignal(object)
    threshold_bounds_changed = pyqtSignal(object)
    

    
    # constructor
    def __init__(self): 
        super().__init__()
        
        self._knotdata = None    
        
        self.mesh = vtk.vtkNrrdReader()
        self.mesh.SetFileName("")
        
        self.mesh_threshed = vtk.vtkImageThreshold()
        self.mesh_threshed.SetInputConnection(self.mesh.GetOutputPort()) # Set your input vtkImageData
       
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

        self.show_cut_views = {"yz": False,
                               "xz": False,
                               "xy": False }
        
        # self.threshold_changed.connect(self.on_threshold_changed)
        
    def on_threshold_changed(self):
        if (self.threshold_active and self.mesh != None):
            print ("Threshold changed to ", self.threshold_val, " ...")
            self.mesh_threshed.ThresholdByUpper(self.threshold_val)
            self.mesh_threshed.Update()
            # TODO emit signal for other views to update            
            print ("Threshold changed...ok")
        
        
    def load_imagedata(self, filename):
        print ("loading file:", filename)
                      
        
        self.mesh.SetFileName(filename)
        
        self.mesh.Update()
        
       
        
        # set default values
        # self.mesh_origin = (0, 0, 0)        
        self.mesh_scale = (1, 1, 1)
        
        (self.xMin, self.xMax, self.yMin, self.yMax, self.zMin, self.zMax) = self.mesh.GetExecutive().GetWholeExtent(self.mesh.GetOutputInformation(0))
        self.mesh_scale = self.mesh.GetOutput().GetSpacing()
        (self.x0, self.y0, self.z0) = self.mesh.GetOutput().GetOrigin()
               
        
        self.threshold_val = 900        
        self.mesh_threshed.ThresholdByUpper(self.threshold_val) # Set the threshold value
        self.mesh_threshed.ReplaceInOn() # Set the operation to replace in values
        self.mesh_threshed.SetInValue(1) # Set the value for inside the threshold
        self.mesh_threshed.ReplaceOutOn() # Set the operation to replace out values
        self.mesh_threshed.SetOutValue(0) # Set the value for outside the threshold
        
        
        # obtain new bounds
        # xmin, xmax, ymin, ymax, zmin, zmax = self.mesh.GetOutput().GetBounds() 
        xmin = round(self.xMin * self.mesh_scale[0]) / self.mesh_scale[0]
        xmax = round(self.xMax * self.mesh_scale[0]) / self.mesh_scale[0]
        ymin = round(self.yMin * self.mesh_scale[1]) / self.mesh_scale[1]
        ymax = round(self.yMax * self.mesh_scale[1]) / self.mesh_scale[1]
        zmin = round(self.zMin * self.mesh_scale[2]) / self.mesh_scale[2]
        zmax = round(self.zMax * self.mesh_scale[2]) / self.mesh_scale[2]
        self.slice_bounds = {   "x": {"min": xmin, "max": xmax},
                                "y": {"min": ymin, "max": ymax},
                                "z": {"min": zmin, "max": zmax},
                                "r": {"min": 0, "max": max(round((xmax-xmin)/self.mesh_scale[0]), round((ymax-ymin)/self.mesh_scale[1]))},
                                "r_a": {"min": 0, "max": 360},
                                "r_x": {"min": xmin, "max": xmax},
                                "r_y": {"min": ymin, "max": ymax} }
        self.slice_pos = {  "x": round(self.mesh.GetOutput().GetCenter()[0] * self.mesh_scale[0]) / self.mesh_scale[0],
                            "y": round(self.mesh.GetOutput().GetCenter()[1] * self.mesh_scale[1]) / self.mesh_scale[1],
                            "z": round(self.mesh.GetOutput().GetCenter()[2] * self.mesh_scale[2]) / self.mesh_scale[2], 
                            "r": max(round((xmax-xmin)/2), round((ymax-ymin) / self.mesh_scale[0])) / self.mesh_scale[0],
                            "r_x": round(self.mesh.GetOutput().GetCenter()[0] * self.mesh_scale[0]) / self.mesh_scale[0],
                            "r_y": round(self.mesh.GetOutput().GetCenter()[1] * self.mesh_scale[1]) / self.mesh_scale[1],
                            "r_a": 0.0 }
        
        self.threshold_bounds = { "min": 0, "max": 3000 }
        self.knotdata = KnotData(filename)
        
        
        self.mesh_changed.emit()
   
    @property
    def mesh(self):
        return self._mesh
    @mesh.setter
    def mesh(self, mesh):
        self._mesh = mesh
    
    @property
    def knotdata(self):
        return self._knotdata
    @knotdata.setter
    def knotdata(self, value):        
        self._knotdata = value
        self.knotdata_changed.emit(value)       
    
    @property
    def threshold_val(self):
        return int(self._threshold)
    @threshold_val.setter
    def threshold_val(self, threshold):  
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
        self.threshold_changed.emit(self.threshold_val)
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
    