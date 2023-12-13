import sys
import random

from PyQt5 import QtWidgets
from PyQt5 import QtCore
import pyvista as pv
from pyvistaqt import QtInteractor

from views.view_3D import View3D
from views.knot_table_view import KnotTableView
from views.ortho_view import OrthoView

from model.model import Model
from controllers.main_controller import MainController

# this class contains the mainFrame of the segmentcreator
# functions for 
#   - load data (CT image files ".nrrd")
#   - manipulate the (automatic) segmentation
#   - export/save data (segmentation mask) 

class MainView(QtWidgets.QMainWindow):
    def __init__(self, model, main_controller, title, is_visible = True):
        super().__init__()
        
        self.show()
        self.central_widget = QtWidgets.QWidget(self)
        self.setCentralWidget(self.central_widget)
        
        self.setWindowTitle(title)
        self.resize(1000, 600)
        self._model = model
        self._main_controller = main_controller
        
        # self.frame = QtWidgets.QFrame(self)
        # self.frame.setStyleSheet('background-color: rgba(0,0,0,1);')
        self.layout = QtWidgets.QGridLayout()
        self.central_widget.setLayout(self.layout)
            
        
        self.is_visible = is_visible          
        

        # create widgets and connect them to controller
     
        # menu  bar
        
        # file menu        
        main_menu = self.menuBar()
        
        file_menu = main_menu.addMenu('&File')
        
        bt_open_file = QtWidgets.QAction('&Load...', self)
        bt_open_file.setShortcut('Ctrl+O')
        bt_open_file.triggered.connect(self._main_controller.open_file)
        file_menu.addAction(bt_open_file)
        
        bt_export_segmentationmask = QtWidgets.QAction('&Export...', self)
        bt_export_segmentationmask.setShortcut('Ctrl+E')
        bt_export_segmentationmask.triggered.connect(self._main_controller.export_segmentationmask)
        file_menu.addAction(bt_export_segmentationmask)
        file_menu.addSeparator()
        
        bt_exit = QtWidgets.QAction('&Quit', self)
        bt_exit.setShortcut('Ctrl+Q')
        bt_exit.triggered.connect(self.close)
        file_menu.addAction(bt_exit)
        
        view_menu = main_menu.addMenu('&View')
        
        bt_view_image = QtWidgets.QAction('&View 3D Image', self)        
        bt_view_image.setCheckable(True)
        # btViewModel.triggered.connect()
        view_menu.addAction(bt_view_image)
       
        # add additional frames such as buttons and the 3D view
               
        # add and show view Frame
        self.view3D = View3D(self.central_widget, model, main_controller, True)
        self.layout.addWidget(self.view3D, 0, 0, 1, 1)
        
        # self.view3D.setVisible(True)
        # self.view3D.update()
        
        
        # add table including knotdata
        self.knot_table_view = KnotTableView(self.central_widget, True)
        self.layout.addWidget(self.knot_table_view, 1, 0, 1, 1)        
        

           