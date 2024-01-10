import sys
import random

from PyQt5 import QtWidgets
from PyQt5 import QtCore
from PyQt5 import uic
from PyQt5.QtCore import Qt, pyqtSlot
from PyQt5.QtWidgets import QWidget
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
    def __init__(self, model, main_controller, title):
        super(MainView, self).__init__()
        
        self._model = model
        self._main_controller = main_controller
        
        self.setWindowTitle(title)
        self.resize(1400, 1000)
        self.central_widget = QtWidgets.QWidget()
        self.setCentralWidget(self.central_widget)
        self.create_menus()
        self.create_views()
        self.show()
        
        #listen if slice_pos changed
        self._model.slice_pos_changed.connect(self.on_slice_pos_changed)
        
    
    def create_menus(self):   
        # create menu and connect trigger to actions   
        # menu  bar
        main_menu = self.menuBar()
        
        # file menu        
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
        
        # view menu            
        view_menu = main_menu.addMenu('&View')
        
        bt_view_image = QtWidgets.QAction('&View 3D Image', self)        
        bt_view_image.setCheckable(True)
        # bt_view_image.triggered.connect()
        view_menu.addAction(bt_view_image)
       
      
    
    def create_views(self):
        layout = QtWidgets.QGridLayout()
        self.central_widget.setLayout(layout)
        # create widgets and connect them to controller
        # add additional frames such as buttons and the 3D view
        
        self.ui_view = uic.loadUi("views/ui_view.ui")        
        layout.addWidget(self.ui_view.layoutWidget, 0, 2, 1, 1)

        # connect changing slider to slice_pos change
        self.ui_view.horizontal_slider_x.valueChanged.connect(self.slice_pos_changed)
        self.ui_view.horizontal_slider_y.valueChanged.connect(self.slice_pos_changed)
        self.ui_view.horizontal_slider_z.valueChanged.connect(self.slice_pos_changed)
        
        # connect changing models slice position to slice_pos
        # self._model.slice_pos_changed.connect(self.on_slice_pos_slider_changed)
        
        # listen to changing mesh to change bounds of slider 
        self._model.mesh_changed.connect(self.on_slice_bounds_changed)

        
        # add and show view Frame
        self.view3D = View3D(self._model, self._main_controller)        
        layout.addWidget(self.view3D, 0, 0, 1, 1)
                       
        # add orthoview control
        self.ortho_view = OrthoView(self._model, self._main_controller)        
        layout.addWidget(self.ortho_view, 0, 1, 1, 1)
                      
        # add table including knotdata
        self.knot_table_view = KnotTableView(self._model)        
        layout.addWidget(self.knot_table_view, 2, 0, 1, 3)
    
        
    def slice_pos_changed(self):
        self._model.slice_pos = {   "x": self.ui_view.horizontal_slider_x.value(),
                                    "y": self.ui_view.horizontal_slider_y.value(),
                                    "z": self.ui_view.horizontal_slider_z.value() }
    
    def on_slice_pos_changed(self):
        self.ui_view.horizontal_slider_x.setValue(self._model.slice_pos["x"])
        self.ui_view.horizontal_slider_y.setValue(self._model.slice_pos["y"])
        self.ui_view.horizontal_slider_z.setValue(self._model.slice_pos["z"])
        
    def on_slice_bounds_changed(self):
        self.ui_view.horizontal_slider_x.setMinimum(self._model.slice_bounds["x"]["min"])
        self.ui_view.horizontal_slider_x.setMaximum(self._model.slice_bounds["x"]["max"])
        self.ui_view.horizontal_slider_y.setMinimum(self._model.slice_bounds["y"]["min"])
        self.ui_view.horizontal_slider_y.setMaximum(self._model.slice_bounds["y"]["max"])
        self.ui_view.horizontal_slider_z.setMinimum(self._model.slice_bounds["z"]["min"])
        self.ui_view.horizontal_slider_z.setMaximum(self._model.slice_bounds["z"]["max"])
        
        self.ui_view.spinBox_x.setMinimum(self._model.slice_bounds["x"]["min"])
        self.ui_view.spinBox_x.setMaximum(self._model.slice_bounds["x"]["max"])
        self.ui_view.spinBox_y.setMinimum(self._model.slice_bounds["y"]["min"])
        self.ui_view.spinBox_y.setMaximum(self._model.slice_bounds["y"]["max"])
        self.ui_view.spinBox_z.setMinimum(self._model.slice_bounds["z"]["min"])
        self.ui_view.spinBox_z.setMaximum(self._model.slice_bounds["z"]["max"])

    def closeEvent(self, QCloseEvent):
        # it is necessary to finalize the vtk elements when window gets closed
        self.view3D.close()
        self.ortho_view.close()
        super().closeEvent(QCloseEvent)
    
      
   
        
        