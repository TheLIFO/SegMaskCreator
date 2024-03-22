
import sys

import pretty_errors

from PyQt5 import QtWidgets
import pyvista as pv
from views.main_view import MainView
from controllers.main_controller import MainController
from model.model import Model
import settings

title = "Segment Mask Creator v0.0.1"
pv.global_theme.allow_empty_mesh = True

class App(QtWidgets.QApplication):
    def __init__(self, sys_argv):
        super(App, self).__init__(sys_argv)
        
        self.applicationName = title
        
        settings.init() 
        self.model = Model()
        self.main_controller = MainController(self.model)
        self.main_view = MainView(self.model, self.main_controller, title)



if __name__ == '__main__':
    app = App(sys.argv)
    app.main_view.show()
    app.exec()
    sys.exit()
    
