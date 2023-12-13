import sys
import random

from PyQt5 import QtWidgets
import pyvista as pv
from pyvistaqt import QtInteractor
from model.model import Model


# this class contains the viewFrame depicting the loaded CT image in 3D


class OrthoView(QtWidgets.QWidget):
    def __init__(self, parten, is_visible = False):
        pass  # TODO implement
