from PyQt5 import QtWidgets
from model.knot_data import KnotData


class KnotTableView(QtWidgets.QTableWidget):
    def __init__(self, parent, is_visible = False ):
        super().__init__(parent)        
        
        self.frame = QtWidgets.QFrame(parent)
        self._is_visible = is_visible
        
        self.setRowCount(10)
        labels = ["KnotNo", "KnotID", "Diameter\n[mm]", "Azimuth/[°]", "KnotType", "R1\n[mm]", "L1a\n[mm]", "L1b\n[mm]", "D1\n[mm]", "L2\n[mm]", "L3\n[mm]", "L4\n[mm]", "L5\n[mm]", "Count 1"]        
        self.setColumnCount(len(labels))
        self.setHorizontalHeaderLabels(labels)       
        self.setRowHeight(1,30)         
        self._knotData = KnotData()
    
    def show_knottable(self):   
        self._is_visible = True
        pass # TODO go through data and update row
    
    