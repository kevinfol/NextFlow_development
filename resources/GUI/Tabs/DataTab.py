from    PyQt5   import  QtWidgets, \
                        QtCore, \
                        QtGui
from resouces.GUI.CustomWidgets.MatplotlibPlots import TimeSeriesDataPlot
import  sys
import  os

class DataTab(QtWidgets.QWidget):
    """
    """
    def __init__(self, parent=None):
        QtWidgets.QWidget.__init__(self)
        layout = QtWidgets.QVBoxLayout()
        splitter = QtWidgets.QSplitter(QtCore.Qt.Horizontal)
        
        dataPlot = TimeSeriesDataPlot()
        splitter.addWidget(dataPlot)


