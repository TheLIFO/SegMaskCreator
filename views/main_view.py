import sys
import random

from PyQt5 import QtWidgets
from PyQt5 import QtCore
from PyQt5 import uic
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QWidget
import pyvista as pv
from pyvistaqt import QtInteractor

from views.view_3D import View3D
from views.knot_table_view import KnotTableView
from views.ortho_view import OrthoView

from model.model import Model
from controllers.main_controller import MainController
from views.ui_view_control import Ui_ViewControl

          
# this class contains the mainFrame of the segmentcreator
# functions for 
#   - load data (CT image files ".nrrd")
#   - manipulate the (automatic) segmentation
#   - export/save data (segmentation mask) 

class MainView(QtWidgets.QMainWindow):
    def __init__(self, model, main_controller, title):
        super(MainView, self).__init__()
        
        
        self.central_widget = QtWidgets.QWidget()
        self.setCentralWidget(self.central_widget)
        
        self.setWindowTitle(title)
        self.resize(1400, 1000)
        self._model = model
        self._main_controller = main_controller
        
        # self.frame = QtWidgets.QFrame(self)
        # self.frame.setStyleSheet('background-color: rgba(0,0,0,1);')
        layout = QtWidgets.QGridLayout()
        self.central_widget.setLayout(layout)
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
               
        # add orthoview control
        
        self.show()
        self.view_control = Ui_ViewControl()
        self.view_control.setupUi(self)
        
        
        layout.addWidget(self.view_control.layoutWidget, 0, 2, 1, 1)
        
        # add and show view Frame
        self.view3D = View3D(model, main_controller)        
        layout.addWidget(self.view3D, 0, 0, 1, 1)
                       
        self.ortho_view = OrthoView(model, main_controller)        
        layout.addWidget(self.ortho_view, 0, 1, 1, 1)
                      
        # add table including knotdata
        self.knot_table_view = KnotTableView(True)        
        layout.addWidget(self.knot_table_view, 2, 0, 1, 3)        
 

    
    def closeEvent(self, QCloseEvent):
        super().closeEvent(QCloseEvent)
        self.view3D.close()
        self.ortho_view.close()
        
   
        
        