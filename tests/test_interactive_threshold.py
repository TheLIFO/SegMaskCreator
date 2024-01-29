import sys

# Setting the Qt bindings for QtPy
import os
os.environ["QT_API"] = "pyqt5"

from qtpy import QtWidgets

import numpy as np

import pyvista as pv
from pyvistaqt import QtInteractor, MainWindow
import vtk
from vtk.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor

class MyMainWindow(MainWindow):

    def __init__(self, parent=None, show=True):
        QtWidgets.QMainWindow.__init__(self, parent)


        # get 3D image
        filename = "data\Drydisk07.6.nrrd"
        reader = pv.get_reader(filename)
        reader.show_progress()
        self.dataset = reader.read() 
        
        # create the frame
        self.frame = QtWidgets.QFrame()
        grid_layout = QtWidgets.QGridLayout()

        # add the pyvista interactor object
        self.plotter = QtInteractor(self.frame)
        self.plotter.enable_surface_point_picking(callback = self.cell_picked, show_message = False, picker = 'cell')
        grid_layout.addWidget(self.plotter, 0, 0)
        
        self.plotter_cut_view = QtInteractor(self.frame)
        self.plotter_cut_view.enable_image_style()
        self.plotter_cut_view.enable_surface_point_picking(callback = self.cell_picked, show_message = False, picker = 'cell')
        grid_layout.addWidget(self.plotter_cut_view, 0, 1)
        
        widget = QVTKRenderWindowInteractor(self.frame)
        self.plotter_2 = 
        self.plotter_2.enable_image_style()
        self.plotter_2.enable_surface_point_picking(callback = self.cell_picked, show_message = False, picker = 'cell')
        grid_layout.addWidget(self.plotter_2, 0, 2)
        self.plotter_2.view_xy()
        
        self.picker = vtk.vtkCellPicker()
        
        
        
        # self.cutter = vtk.vtkCutter()
        # self.plane = vtk.vtkPlane()
        
        
        self.clip_plane_widget = vtk.vtkImagePlaneWidget()
        self.clip_plane_widget.SetInteractor(self.plotter)
        # self.clip_plane_widget.SetInputData(self.dataset)
        self.clip_plane_widget.SetInputConnection(self.dataset.GetOutput())
        self.clip_plane_widget.SetPlaneOrientationToZAxes()
        self.clip_plane_widget.SetSliceIndex(32)
        self.clip_plane_widget.SetPicker(self.picker)
        self.clip_plane_widget.On()
        self.clip_plane_widget.AddObserver('EndInteractionEvent', self.on_clip_plane_changed)
        # self.clip_plane_widget.SetCallback , test_callback = False, callback = self.on_clip_plane_changed, interaction_event="always",)
        # slicer = self.clip_plane_widget.GetReslice()
        self.slice = self.clip_plane_widget.GetResliceOutput()
        self.plotter_2.add_mesh(self.slice)
        
        self.signal_close.connect(self.plotter.close)
        
        self.ui_spinbox_threshold_dataset_clean = QtWidgets.QSpinBox()
        self.ui_spinbox_threshold_dataset_clean.setMaximum(3000)
        self.ui_spinbox_threshold_dataset_clean.setMinimum(0)
        grid_layout.addWidget(self.ui_spinbox_threshold_dataset_clean, 1, 0, 1, 1)
        
        self.ui_spinbox_threshold_low = QtWidgets.QSpinBox()
        self.ui_spinbox_threshold_low.setMaximum(3000)
        self.ui_spinbox_threshold_low.setMinimum(0)
        grid_layout.addWidget(self.ui_spinbox_threshold_low, 2, 0, 1, 1)
        
        self.ui_spinbox_threshold_high = QtWidgets.QSpinBox()
        self.ui_spinbox_threshold_high.setMaximum(3000)
        self.ui_spinbox_threshold_high.setMinimum(0)
        grid_layout.addWidget(self.ui_spinbox_threshold_high, 3, 0, 1, 1)
        
        
        self.frame.setLayout(grid_layout)
        self.setCentralWidget(self.frame)

        # simple menu to demo functions
        mainMenu = self.menuBar()
        fileMenu = mainMenu.addMenu('File')
        exitButton = QtWidgets.QAction('Exit', self)
        exitButton.setShortcut('Ctrl+Q')
        exitButton.triggered.connect(self.close)
        fileMenu.addAction(exitButton)

        # allow adding a sphere
        # meshMenu = mainMenu.addMenu('Mesh')
        
        # self.add_sphere_action = QtWidgets.QAction('Add Sphere', self)
        # self.add_sphere_action.triggered.connect(self.add_sphere)
        # meshMenu.addAction(self.add_sphere_action)
        
       
        
       
        self.threshed_clean = 600
        self.threshold_low = 1000
        self.threshold_high = 1200
        self.ui_spinbox_threshold_dataset_clean.setValue(self.threshed_clean)        
        self.ui_spinbox_threshold_low.setValue(self.threshold_low)
        self.ui_spinbox_threshold_high.setValue(self.threshold_high)
        
        self.dataset_clean = self.dataset.threshold(self.threshed_clean)                
        self.clip_plane_widget.PlaceWidget(self.dataset.bounds[0], self.dataset.bounds[1], self.dataset.bounds[2], self.dataset.bounds[3], self.dataset.bounds[4], self.dataset.bounds[5])
        
        # self.cutter.SetInputData(self.dataset_clean)
        # self.cutter.SetCutFunction(self.plane)        
        # self.plane.SetOrigin(self.dataset.center)
        # self.plane.SetNormal(0, 0, 1)
        
        # self.cut_YZ_actor = self.plotter_cut_view.add_mesh(self.cutter, name = "cutter", show_scalar_bar = False)
        # self.plotter_cut_view.view_xy()
        # self.plotter_cut_view.enable_parallel_projection()
        
        self.ui_spinbox_threshold_dataset_clean.textChanged.connect(self.update_threshold)        
        
        self.ui_spinbox_threshold_low.textChanged.connect(self.update_threshold)
        self.ui_spinbox_threshold_high.textChanged.connect(self.update_threshold)
        # self.update_threshold()
        
        lower_threshold = self.ui_spinbox_threshold_low.value()
        higher_threshold = self.ui_spinbox_threshold_high.value()
        
        threshed = self.dataset.image_threshold([lower_threshold, higher_threshold])
        outline = self.dataset.outline()
        # self.plotter.add_mesh(outline, name= "outline", color="k", pickable = False)
        
        self.plotter.add_mesh(self.dataset_clean, name= "mesh_overview", opacity = 0.65, color=True)
        threshed = threshed.threshold(1)
        self.plotter.add_mesh(threshed, name= "threshed", color="r")
        # self.plane_2 = self.clip_plane_widget.GetTexture()
        # self.plotter_2.add_mesh(self.plane_2)
        
        
        # self.update_plot()
        if show:
            self.show()


    def on_clip_plane_changed(self, caller = None, event = None ): 
        print("new origin for plane ")
        # print(origin, " ...")
        # self.plane.SetOrigin(origin)
        # self.cutter.Update()
        # self.plotter_cut_view.update()
        self.plotter.update()
        self.clip_plane_widget.UpdatePlacement()
        
        self.slice.Modified()
        self.plotter_2.Render()
        self.plotter_2.ProcessEvents()
        print("new origin for plane...ok")
           
    def set_dataset_clean(self):
        pass
        
    def update_threshold(self):
        print("set threshold to ", self.ui_spinbox_threshold_low.value(), " - ", self.ui_spinbox_threshold_high.value())
        """
        self.dataset_clean = self.dataset.threshold(self.ui_spinbox_threshold_dataset_clean.value())
        # threshed = self.dataset.threshold([self.ui_spinbox_threshold_low.value(), self.ui_spinbox_threshold_high.value()])
        
        lower_threshold = self.ui_spinbox_threshold_low.value()
        higher_threshold = self.ui_spinbox_threshold_high.value()
        if lower_threshold > higher_threshold:
            higher_threshold = lower_threshold
        self.ui_spinbox_threshold_high.setValue(higher_threshold)
        
        threshed = self.dataset.image_threshold([lower_threshold, higher_threshold])
        outline = self.dataset.outline()
        # self.plotter.add_mesh(outline, name= "outline", color="k", pickable = False)
        print("set threshold - update..")
        
        self.plotter.add_mesh(self.dataset_clean, name= "mesh_overview", opacity = 0.65, color=True)
        threshed = threshed.threshold(1)
        self.plotter.add_mesh(threshed, name= "threshed", color="r")
        
        self.plotter.update()
        self.on_clip_plane_changed([0,0,1], self.plane.GetOrigin())
        """
        print("set threshold - update...ok")
        
        
        
    def cell_picked(self, cell):        
        print("cell picked = ", cell)
        
        
    
    def closeEvent(self, QCloseEvent):
        super().closeEvent(QCloseEvent)
        # fail -> apparently these are NONE objects?????
        # self.plotter.Finalize()  
        # self.plotter_cut_view.Finalize()
        
    

if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    window = MyMainWindow()
    sys.exit(app.exec_())