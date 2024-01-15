from PyQt5 import QtWidgets
from PyQt5.QtCore import pyqtSignal

class KnotTableView(QtWidgets.QTableWidget):
    
    cb_show_knot_changed = pyqtSignal()
    
    
    def __init__(self, model):
        super(KnotTableView, self).__init__()        
        self._model = model
        self.frame = QtWidgets.QFrame(self)
        
        num_labels = len(self.knot_data_map.keys())
        labels = list(range(num_labels))
        self.setRowCount(num_labels)
        for key in self.knot_data_map.keys():
            col = self.knot_data_map[key]["col"]
            labels[col] = self.knot_data_map[key]["label"]
        self.setColumnCount(len(labels))
        self.setHorizontalHeaderLabels(labels)       
        self.setRowHeight(1,20)  
        for col in range(self.columnCount()):
            self.horizontalHeader().setSectionResizeMode(col, QtWidgets.QHeaderView.ResizeToContents)
        self.setMaximumHeight(300)
        
        self._model.knotdata_changed.connect(self.on_knotdata_changed)       
        
     
    #hash table for knotdata
    knot_data_map = {   
                        "KNOT NO.":               { "label": "KnotNo",          "col": 0 },
                        "Knot ID in database":    { "label": "KnotID",          "col": 1 },
                        "Knot Diam":              { "label": "Diameter\n[mm]",  "col": 2 },
                        "Azimuth":                { "label": "Azimuth/[°]",     "col": 3 },
                        "Knot type":              { "label": "KnotType",        "col": 4 },
                        "R1":                     { "label": "R1\n[mm]",        "col": 5 },
                        "L1 a":                   { "label": "L1a\n[mm]",       "col": 6 },
                        "L1 b":                   { "label": "L1b\n[mm]",       "col": 7 },
                        "D1":                     { "label": "D1\n[mm]",        "col": 8 },
                        "L2":                     { "label": "L2\n[mm]",        "col": 9 },
                        "L3":                     { "label": "L3\n[mm]",        "col": 10 },
                        "L4":                     { "label": "L4\n[mm]",        "col": 11 },
                        "L5":                     { "label": "L5\n[mm]",        "col": 12 },
                        "Count 1":                { "label": "Count 1",         "col": 13 },
                        "Show":                   { "label": "Show",            "col": 14 }
                    }
    
    
    
    def show_knottable(self):
        self.clearContents()
        for key, values in self._model.knotdata.table.items():
            col = self.knot_data_map[key]["col"]             
            for row,(value) in enumerate(values):                
                if not isinstance(value, str):
                    value = str(value)
                item = QtWidgets.QTableWidgetItem(value)
                self.setItem(row, col, item)
        
        # add checkbox widgets to show resp. knot
        len_values = len(self._model.knotdata.table['Knot ID in database'])
        self.cb_knot_show_list = []
        
        for row in range(len_values):
            cb_knot_show = QtWidgets.QCheckBox()
            cb_knot_show.stateChanged.connect(self.on_knot_show_changed)
            self.cb_knot_show_list.append(cb_knot_show)
            col = self.knot_data_map["Show"]["col"]
            self.setCellWidget(row, col, self.cb_knot_show_list[row])            
        
    
    def on_knot_show_changed(self):        
        print("TODO")
        self.cb_show_knot_changed.emit()
        
        
    
    def on_knotdata_changed(self):
        self.show_knottable()
        
    def closeEvent(self, QCloseEvent):
        super().closeEvent(QCloseEvent)
        