import nrrd
import pandas as pd

class KnotData():    
    def __init__(self, filename = None):
        # empty data
        self._header = None
        self._data = {}
        if filename:
            self._header = self.load_knotdata(filename)
            self.table = self.to_knottable()
    
    #dataframe for knotdata
    _template_table = {  
            "KNOT NO.": [],
            "Knot ID in database": [],
            "Knot Diam": [],
            "Azimuth": [],
            "Knot type": [],
            "R1": [],
            "L1 a": [],
            "L1 b": [],
            "D1": [],
            "L2": [],
            "L3": [],
            "L4": [],
            "L5": [],
            "Count 1": []
    }
     
    def to_knottable(self):
        # filter header to usable knottable
        if self._header is None:
            return      
        # extract only necessary items from header (all that are listed in _template_table)
        self._table = {key: self._header[key] for key in self._header.keys() & self._template_table.keys()}        
        # split string data in several items
        for key, value_str in self._table.items():
            value_list = value_str.split(" ")
            values = []
            for value_str in value_list:                    
                try:
                    values.append(float(value_str))
                except ValueError:
                    values.append(value_str)
            self._table[key] = values
        return self._table
    
    def load_knotdata(self, filename):
        isOk = False
        try:
            self._header = nrrd.read_header(filename)        
        except:            
            return None
        
        print (self._header)
        
        return self._header
    
    @property 
    def table(self):
        # return
        return self._table
    
    @table.setter
    def table(self, data):
        self._table = data