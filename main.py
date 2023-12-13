
import sys

from PyQt5 import QtWidgets

from views.main_view import MainView
from controllers.main_controller import MainController
from model.model import Model

title = "Segment Mask Creator v0.0.1"
    
class App(QtWidgets.QApplication):
    def __init__(self, sys_argv):
        super(App, self).__init__(sys_argv)
        self.applicationName = title
        
        self.model = Model()
        self.main_controller = MainController(self.model)
        self.main_view = MainView(self.model, self.main_controller, title)
        self.main_view.show()


if __name__ == '__main__':
    app = App(sys.argv)
    sys.exit(app.exec_())
