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
        
        # listen if slice_pos changed
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
        layout.addWidget(self.ui_view.gridLayoutWidget, 0, 2, 1, 1)


        self.ui_view.spinBox_r.setDecimals(1)
        self.ui_view.spinBox_t.setDecimals(1)
        self.ui_view.spinBox_c.setDecimals(1)
        
        self.ui_view.spinBox_r.setSingleStep(0.5)
        self.ui_view.spinBox_t.setSingleStep(0.5)
        self.ui_view.spinBox_c.setSingleStep(0.5)
        
        # connect changing slider to slice_pos change
        self.ui_view.horizontal_slider_r.valueChanged.connect  (self.slice_pos_slider_r_changed)
        self.ui_view.horizontal_slider_t.valueChanged.connect  (self.slice_pos_slider_t_changed)
        self.ui_view.horizontal_slider_c.valueChanged.connect  (self.slice_pos_slider_c_changed)
        
        
        self.ui_view.horizontal_slider_r_a.valueChanged.connect(self.slice_pos_slider_r_a_changed)
        self.ui_view.horizontal_slider_r_x.valueChanged.connect(self.slice_pos_slider_r_x_changed)
        self.ui_view.horizontal_slider_r_y.valueChanged.connect(self.slice_pos_slider_r_y_changed)
        
        
        # connect changing spinbox to slice_pos
        self.ui_view.spinBox_r.textChanged.connect  (self.slice_pos_spinBox_r_changed)
        self.ui_view.spinBox_t.textChanged.connect  (self.slice_pos_spinBox_t_changed)
        self.ui_view.spinBox_c.textChanged.connect  (self.slice_pos_spinBox_c_changed)
        
        
        self.ui_view.spinBox_r_a.textChanged.connect(self.slice_pos_spinBox_r_a_changed)
        self.ui_view.spinBox_r_x.textChanged.connect(self.slice_pos_spinBox_r_x_changed)
        self.ui_view.spinBox_r_y.textChanged.connect(self.slice_pos_spinBox_r_y_changed)
        
        # conncect checkboxes for cut_views to show_cut_views_changed
        
        self.ui_view.checkBox_show_r.stateChanged.connect(self.show_cut_views_changed)
        self.ui_view.checkBox_show_t.stateChanged.connect(self.show_cut_views_changed)
        self.ui_view.checkBox_show_c.stateChanged.connect(self.show_cut_views_changed)
        
        
        # listen to changing mesh to change bounds of slider         
        self._model.slice_bounds_changed.connect(self.on_slice_bounds_changed)

        
        # add and show view Frame
        self.view3D = View3D(self._model, self._main_controller)        
        layout.addWidget(self.view3D, 0, 0, 1, 1)
                       
        # add orthoview control
        self.ortho_view = OrthoView(self._model, self._main_controller)        
        layout.addWidget(self.ortho_view, 0, 1, 1, 1)
                      
        # add table including knotdata
        self.knot_table_view = KnotTableView(self._model)        
        layout.addWidget(self.knot_table_view, 2, 0, 1, 3)
    
    # changes of the sliders    
    def slice_pos_slider_r_changed(self):
        self._model.slice_pos["r"] = self.ui_view.horizontal_slider_r.value()/2
        self._model.slice_pos_changed.emit(self._model.slice_pos)                                  
   
    
    def slice_pos_slider_t_changed(self):        
        self._model.slice_pos["t"] = self.ui_view.horizontal_slider_t.value()/2,
        self._model.slice_pos_changed.emit(self._model.slice_pos)                                    
    
    
    def slice_pos_slider_c_changed(self):   
        self._model.slice_pos["c"] = self.ui_view.horizontal_slider_c.value()/2
        self._model.slice_pos_changed.emit(self._model.slice_pos)
        
    
    def slice_pos_slider_r_a_changed(self):
        self._model.slice_polar_pos["r_a"] = self.ui_view.horizontal_slider_r_a.value()
        self._model.slice_polar_pos_changed.emit(self._model.slice_polar_pos)
        
        
    def slice_pos_slider_r_x_changed(self):
        self._model.slice_polar_pos["r_x"] = self.ui_view.horizontal_slider_r_x.value()/2
        self._model.slice_polar_pos_changed.emit(self._model.slice_polar_pos)
                                   
    def slice_pos_slider_r_y_changed(self):
        self._model.slice_polar_pos ["r_y"] = self.ui_view.horizontal_slider_r_y.value()/2
        self._model.slice_polar_pos_changed.emit(self._model.slice_polar_pos)
    
    
    # changes of the spinboxes
    def slice_pos_spinBox_r_changed(self):
        self._model.slice_pos ["r"] = self.ui_view.spinBox_r.value()
        self._model.slice_pos_changed.emit(self._model.slice_pos)
    
    def slice_pos_spinBox_t_changed(self):        
        self._model.slice_pos["t"] = self.ui_view.spinBox_t.value()        
        self._model.slice_pos_changed.emit(self._model.slice_pos)
    
    def slice_pos_spinBox_c_changed(self):        
        self._model.slice_pos["c"] = self.ui_view.spinBox_c.value()
        self._model.slice_pos_changed.emit(self._model.slice_pos)
    
        
    def slice_pos_spinBox_r_a_changed(self):
        self._model.slice_polar_pos["r_a"] = self.ui_view.spinBox_r_a.value()
        self._model.slice_polar_pos_changed.emit(self._model.slice_polar_pos)
        
    def slice_pos_spinBox_r_x_changed(self):
        self._model.slice_polar_pos["r_x"] = self.ui_view.spinBox_r_x.value()
        self._model.slice_polar_pos_changed.emit(self._model.slice_polar_pos)
        
        
    def slice_pos_spinBox_r_y_changed(self):
        self._model.slice_polar_pos["r_y"] = self.ui_view.spinBox_r_y.value()
        self._model.slice_polar_pos_changed.emit(self._model.slice_polar_pos)

    
    def show_cut_views_changed(self):
        self._model.show_cut_views = {  "r": self.ui_view.checkBox_show_r.isChecked(),
                                        "t": self.ui_view.checkBox_show_t.isChecked(),
                                        "c": self.ui_view.checkBox_show_c.isChecked() }
        
    
    
    def on_slice_pos_changed(self, slice_pos):
        self.ui_view.horizontal_slider_r.setValue(round(slice_pos["r"] * 2))
        self.ui_view.horizontal_slider_t.setValue(round(slice_pos["t"] * 2))
        self.ui_view.horizontal_slider_c.setValue(round(slice_pos["c"] * 2))
        
        self.ui_view.spinBox_r.setValue(slice_pos["r"])
        self.ui_view.spinBox_t.setValue(slice_pos["t"])
        self.ui_view.spinBox_c.setValue(slice_pos["c"])
                
        
    def on_slice_polar_pos_changed(self, slice_polar_pos):
        self.ui_view.horizontal_slider_r_a.setValue(round(slice_polar_pos["r_a"]))
        self.ui_view.horizontal_slider_r_x.setValue(round(slice_polar_pos["r_x"] * 2))
        self.ui_view.horizontal_slider_r_y.setValue(round(slice_polar_pos["r_y"] * 2))
        
        
        self.ui_view.spinBox_r_a.setValue(slice_polar_pos["r_a"])
        self.ui_view.spinBox_r_x.setValue(slice_polar_pos["r_x"])
        self.ui_view.spinBox_r_y.setValue(slice_polar_pos["r_y"])

        
        
        
    def on_slice_bounds_changed(self, slice_bounds):
        self.ui_view.horizontal_slider_r.setMinimum(round(slice_bounds["r"]["min"] * 2))
        self.ui_view.horizontal_slider_r.setMaximum(round(slice_bounds["r"]["max"] * 2))
        self.ui_view.horizontal_slider_t.setMinimum(round(slice_bounds["t"]["min"] * 2))
        self.ui_view.horizontal_slider_t.setMaximum(round(slice_bounds["t"]["max"] * 2))
        self.ui_view.horizontal_slider_c.setMinimum(round(slice_bounds["c"]["min"] * 2))
        self.ui_view.horizontal_slider_c.setMaximum(round(slice_bounds["c"]["max"] * 2))
        
        self.ui_view.spinBox_r.setMinimum(slice_bounds["r"]["min"])
        self.ui_view.spinBox_r.setMaximum(slice_bounds["r"]["max"])
        self.ui_view.spinBox_t.setMinimum(slice_bounds["t"]["min"])
        self.ui_view.spinBox_t.setMaximum(slice_bounds["t"]["max"])
        self.ui_view.spinBox_c.setMinimum(slice_bounds["c"]["min"])
        self.ui_view.spinBox_c.setMaximum(slice_bounds["c"]["max"])
        
        
    def on_slice_polar_bounds_changed(self, slice_polar_bounds):
        self.ui_view.horizontal_slider_r_a.setMinimum(round(slice_polar_bounds["r_a"]["min"]))
        self.ui_view.horizontal_slider_r_a.setMaximum(round(slice_polar_bounds["r_a"]["max"]))        
        self.ui_view.horizontal_slider_r_x.setMinimum(round(slice_polar_bounds["r_x"]["min"] * 2))
        self.ui_view.horizontal_slider_r_x.setMaximum(round(slice_polar_bounds["r_x"]["max"] * 2))
        self.ui_view.horizontal_slider_r_y.setMinimum(round(slice_polar_bounds["r_y"]["min"] * 2))
        self.ui_view.horizontal_slider_r_y.setMaximum(round(slice_polar_bounds["r_y"]["max"] * 2))
        
        
        self.ui_view.spinBox_r_a.setMinimum(slice_polar_bounds["r_a"]["min"])
        self.ui_view.spinBox_r_a.setMaximum(slice_polar_bounds["r_a"]["max"])
        self.ui_view.spinBox_r_x.setMinimum(slice_polar_bounds["r_x"]["min"])
        self.ui_view.spinBox_r_x.setMaximum(slice_polar_bounds["r_x"]["max"])
        self.ui_view.spinBox_r_y.setMinimum(slice_polar_bounds["r_y"]["min"])
        self.ui_view.spinBox_r_y.setMaximum(slice_polar_bounds["r_y"]["max"])

    def closeEvent(self, QCloseEvent):
        # it is necessary to finalize the vtk elements when window gets closed
        self.view3D.close()
        self.ortho_view.close()
        super().closeEvent(QCloseEvent)
    
      
   
        
        