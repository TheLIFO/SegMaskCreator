
from PyQt5 import QtWidgets
from PyQt5 import QtCore

class MainController:
    def __init__(self, model):
        super().__init__()
        
        self._model = model               
        
    
    def open_file(self):        
        dlg = QtWidgets.QFileDialog()
        dlg.setFileMode(QtWidgets.QFileDialog.ExistingFile)        
        dlg.setNameFilters(["3D-Image file (*.nrrd)"])
        filename = QtCore.QStringListModel()

        if dlg.exec_():
            filename = dlg.selectedFiles()
            self._model.load_imagedata(filename[0])
                
     
    
    def export_segmentationmask(self):        
        # TODO
        print("TODO implement!!\n")
        
    def set_threshold_clicked(self):
        pass # TODO