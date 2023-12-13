import nrrd

class KnotData():    
    def __init__(self, filename = None):
        # empty data
        self._data = {}
        if filename:
            self._header = self.load_knotdata(filename)
        self.knottable = self.to_knottable()
        
    def to_knottable(self):
        # translate header to usable knottable        
        self._knottable = {}
        return self._knottable
    
    def load_knotdata(self, filename):
        isOk = False
        try:
            self._header = nrrd.read_header(filename)        
        except:            
            return None
        
        print (self._header)
        
        return self._header
    
    @property 
    def knottable(self):
        # return
        return self._knottable
    
    @knottable.setter
    def knottable(self, data):
        self._knottable = data