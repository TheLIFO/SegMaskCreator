
import sys

from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import Qt


class LoadModelWidget(QtWidgets.QWidget):
    def __init__(self, *args, **kwargs):
        super(LoadModelWidget, self).__init__(*args, **kwargs)

        # ------------------------ GUI Components ------------------------ #
        # self.setFixedHeight(100)
        self._container = QtWidgets.QGroupBox(self)
        self._container.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding))
        # self._container.setFixedHeight(100)
        # self._container.setFixedWidth(210)
        layout = QtWidgets.QGridLayout()

        self._model_to_select_label = QtWidgets.QLabel("Selected model")
        layout.addWidget(self._model_to_select_label, 0, 0)
        self._model_to_select_list = QtWidgets.QComboBox()
        layout.addWidget(self._model_to_select_list, 0, 1)
        _slice_method_label = QtWidgets.QLabel("Slice method")
        layout.addWidget(_slice_method_label, 1, 0)
        self._list_of_slicing_method = QtWidgets.QComboBox()
        layout.addWidget(self._list_of_slicing_method, 1, 1)

        self._bottom_radius_label = QtWidgets.QLabel("Bottom radius")
        layout.addWidget(self._bottom_radius_label, 2, 0)
        self._bottom_radius_edit = QtWidgets.QLineEdit()
        layout.addWidget(self._bottom_radius_edit, 2, 1)
        self._top_radius_label = QtWidgets.QLabel("Top radius")
        layout.addWidget(self._top_radius_label, 3, 0)
        self._top_radius_edit = QtWidgets.QLineEdit()
        layout.addWidget(self._top_radius_edit, 3, 1)
        self._height_label = QtWidgets.QLabel("Height")
        layout.addWidget(self._height_label, 4, 0)
        self._height_edit = QtWidgets.QLineEdit()
        layout.addWidget(self._height_edit, 4, 1)

        self._x_dir_label = QtWidgets.QLabel("X direction")
        layout.addWidget(self._x_dir_label, 5, 0)
        self._x_dir_edit = QtWidgets.QLineEdit()
        layout.addWidget(self._x_dir_edit, 5, 1)
        self._y_dir_label = QtWidgets.QLabel("Y direction")
        layout.addWidget(self._y_dir_label, 6, 0)
        self._y_dir_edit = QtWidgets.QLineEdit()
        layout.addWidget(self._y_dir_edit, 6, 1)
        self._z_dir_label = QtWidgets.QLabel("Z direction")
        layout.addWidget(self._z_dir_label, 7, 0)
        self._z_dir_edit = QtWidgets.QLineEdit()
        layout.addWidget(self._z_dir_edit, 7, 1)

        self._remove_btn = QtWidgets.QPushButton("Remove model")
        layout.addWidget(self._remove_btn, 8, 0)

        self._bottom_radius_label.setVisible(False)
        self._bottom_radius_edit.setVisible(False)
        self._top_radius_label.setVisible(False)
        self._top_radius_edit.setVisible(False)
        self._height_label.setVisible(False)
        self._height_edit.setVisible(False)
        self._x_dir_label.setVisible(False)
        self._x_dir_edit.setVisible(False)
        self._y_dir_label.setVisible(False)
        self._y_dir_edit.setVisible(False)
        self._z_dir_label.setVisible(False)
        self._z_dir_edit.setVisible(False)

        self._container.setLayout(layout)

        # -------------------- Other attributes -------------------- "
        self._filename = ""

        # -------------------- Assign slot and signal -------------------- "
        self._list_of_slicing_method.currentIndexChanged.connect(self.slice_method_changed)
        self._remove_btn.clicked.connect(self.remove_model)
        
        layout = QtWidgets.QVBoxLayout(self)
        layout.addWidget(self._container)

    def set_model_dir(self, filename, filedir, suggested_slicing_method="Parallel"):
        # Assign only the name of the file, not the whole stl model
        self._filename = filename
        self._filedir = filedir

        self._list_of_slicing_method.addItem("Parallel")
        self._list_of_slicing_method.addItem("Revolution")
        self._list_of_slicing_method.addItem("Radial")
        self._list_of_slicing_method.addItem("ParallelCurve")

        self._list_of_slicing_method.setCurrentText(suggested_slicing_method)

    def get_model_full_dir(self):
        return self._filedir + "\\" + self._filename

    def remove_model(self):
        self._filename = ""
        self._filedir = ""
        self._list_of_slicing_method.clear()

    def slice_method_changed(self):
        is_parallel = self._list_of_slicing_method.currentText() == "Parallel"
        is_radial = self._list_of_slicing_method.currentText() == "Radial"

        self._bottom_radius_label.setVisible(is_radial)
        self._bottom_radius_edit.setVisible(is_radial)
        self._top_radius_label.setVisible(is_radial)
        self._top_radius_edit.setVisible(is_radial)
        self._height_label.setVisible(is_radial)
        self._height_edit.setVisible(is_radial)

        self._x_dir_label.setVisible(is_parallel)
        self._x_dir_edit.setVisible(is_parallel)
        self._y_dir_label.setVisible(is_parallel)
        self._y_dir_edit.setVisible(is_parallel)
        self._z_dir_label.setVisible(is_parallel)
        self._z_dir_edit.setVisible(is_parallel)

        padding = 50
        minimum_height = 100
        new_height = (self._bottom_radius_label.height() + padding)*is_radial + (self._top_radius_edit.height() + padding)*is_radial + (self._height_label.height() + padding)*is_radial + (self._x_dir_label.height() + padding)*is_parallel + (self._y_dir_label.height() + padding)*is_parallel + (self._z_dir_label.height() + padding)*is_parallel
        # if (new_height > minimum_height):
            # self._container.setFixedHeight(new_height)
            # self.setFixedHeight(new_height)
        # else:
            # self._container.setFixedHeight(minimum_height)
            # self.setFixedHeight(minimum_height)

class LoadModelColumn(QtWidgets.QWidget):
    def __init__(self, *args, **kwargs):
        super(LoadModelColumn, self).__init__(*args, **kwargs)

        # ------------------------ GUI Components ------------------------ #
        self._layout = QtWidgets.QGridLayout()
        self._add_model_btn = QtWidgets.QPushButton("Add model(s)")
        self._layout.addWidget(self._add_model_btn, 0, 0)
        self._clear_all_btn = QtWidgets.QPushButton("Clear all")
        self._layout.addWidget(self._clear_all_btn, 0, 1)

        self._all_load_model_widgets = []

        self.verticalSpacer = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.MinimumExpanding)
        self._layout.addItem(self.verticalSpacer)

        self._load_model_group = QtWidgets.QGroupBox()
        self._load_model_group.setLayout(self._layout)

        self._scroll_area = QtWidgets.QScrollArea(self)
        self._scroll_area.setWidgetResizable(True)
        # self._scroll_area.setFixedHeight(600)
        # self._scroll_area.setFixedWidth(250)
        self._scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self._scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self._scroll_area.setWidget(self._load_model_group)

        # -------------------- Assign slot and signal -------------------- "
        self._clear_all_btn.clicked.connect(self._clear_all_models)
        self._add_model_btn.clicked.connect(self._add_models)
        
        layout = QtWidgets.QVBoxLayout(self)
        layout.addWidget(self._scroll_area)

    def _clear_all_models(self):
        for widget in self._all_load_model_widgets:
            self._layout.removeWidget(widget)
            widget.deleteLater()

        self._all_load_model_widgets = []

    def _add_models(self):
        widget = LoadModelWidget()
        widget.set_model_dir("hi", "hello")
        self._all_load_model_widgets.append(widget)
        self._layout.addWidget(widget, len(self._all_load_model_widgets), 0, 1, 0)
        
        


class App(QtWidgets.QApplication):
    def __init__(self, sys_argv):
        super(App, self).__init__(sys_argv)
        
        self.applicationName = "Test"
        
        self.main_view = LoadModelColumn()



if __name__ == '__main__':
    app = App(sys.argv)
    app.main_view.show()
    app.exec()
    sys.exit()
