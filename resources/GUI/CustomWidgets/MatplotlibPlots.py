import os
import platform

from PyQt5 import QtWidgets

import matplotlib
matplotlib.use('Qt5Agg')
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT
from matplotlib.widgets import TextBox
from matplotlib.figure import Figure
import matplotlib.patches as patches
import matplotlib.dates as mdates
import matplotlib.font_manager as fm


class NavigationToolbar(NavigationToolbar2QT):
    """
    Define a class to add a Nevigation bar to the bottom of plots
    """
    toolitems = [t for t in NavigationToolbar2QT.toolitems if t[0] in ( 'Home', 'Pan', 'Zoom', 'Save')]

class TimeSeriesDataPlot(FigureCanvas):
    """
    This Plot displays 1-d time series data on the data tab.
    """
    def __init__(self, parent=None):

        self.fig = Figure()
        self.axes = self.fig.add_subplot(111)
        FigureCanvas.__init__(self, self.fig)
        FigureCanvas.setSizePolicy(self, QtWidgets.QSizePolicy.Maximum, QtWidgets.QSizePolicy.Maximum)
        FigureCanvas.updateGeometry(self)
        self.add_data([0],[0],'No Data')
        self.draw_plot()
    
    def add_data(self, X, Y, label, fill_below = False):
        if fill_below:
            self.axes.fill_between(X, 0, Y)
        else:
            self.axes.plot(X, Y)
    
    def draw_plot(self):
        self.axes.legend(loc=2)
        self.fig.tight_layout()
        self.draw()
