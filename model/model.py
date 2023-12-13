import pyvista
from PyQt5.QtWidgets import QWidget
from PyQt5.QtCore import Qt, QObject, pyqtSignal
import pyvista as pv
from model.knot_data import KnotData 

class Model(QObject):
    # signals when model changes
    knotdata_changed = pyqtSignal(KnotData)
    mesh_changed = pyqtSignal(pv.DataSet)
    # constructor
    def __init__(self): 
        super().__init__()
        
        self._knotdata = None    
        self._mesh = None
        self._threshold = 0
    
    def load_imagedata(self, filename):
        print ("loading file:", filename)
                      
        reader = pyvista.get_reader(filename)
        reader.show_progress()
        self.mesh = reader.read()        
    
        
        self._knotdata = KnotData(filename)
        
   
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
    def setThreshold(self, threshold):  
        self._threshold = threshold

    
            

    