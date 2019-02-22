"""
Script Name:        ForecastsTab.py

Description:        'ForecastsTab.py' is a PyQt5 GUI for the NextFlow application. 
                    The GUI includes all the visual aspects of the Forecasts Tab (menus,
                    plots, tables, buttons, webmaps, etc.) as well as the functionality
                    to add data to the plots, tables, and webmaps.
"""
from    PyQt5   import  QtWidgets, \
                        QtCore, \
                        QtGui

import  sys
import  os
from    resources.GUI.CustomWidgets     import  DatasetBoxView

class ForecastsTab(QtWidgets.QWidget):
    """
    """
    def __init__(self, parent=None):
        QtWidgets.QWidget.__init__(self)
        layout = QtWidgets.QVBoxLayout()

        splitter = QtWidgets.QSplitter(QtCore.Qt.Horizontal)

        forecastListPane = QtWidgets.QWidget()
        layout_ = QtWidgets.QVBoxLayout()
        label = QtWidgets.QLabel('<b style="font-size: 20px">Selected Forecasts</b>')
        label.setTextFormat(QtCore.Qt.RichText)
        self.selectedForecastsLabel = QtWidgets.QLabel("0 forecasts have been selected:")



        self.setLayout(layout)