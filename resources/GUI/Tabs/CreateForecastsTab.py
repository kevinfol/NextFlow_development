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

class CreateForecastsTab(QtWidgets.QWidget):
    """
    """
    def __init__(self, parent=None):
        QtWidgets.QWidget.__init__(self)
        layout = QtWidgets.QVBoxLayout()

        forecastInitPane = QtWidgets.QWidget()
        layout_ = QtWidgets.QVBoxLayout()
        label = QtWidgets.QLabel('<b style="font-size: 20px">Create New Forecasts</b>')
        label.setTextFormat(QtCore.Qt.RichText)
        subText = QtWidgets.QLabel("Use the following workflow to generate new forecasts for your target.")
        oldModel = QtWidgets.QLabel("Alternatively, start from a previously initialized model from this file.")
        layout_.addWidget(label)
        layout_.addWidget(subText)
        layout_.addWidget(oldModel)

        forecastInitPane.setLayout(layout_)



        layout.addWidget(forecastInitPane)
        self.setLayout(layout)

class predictionTargetSpecificationWidget(QtWidgets.QWidget):
    """
    """
    def __init__(self, parent=None):
        QtWidgets.QWidget.__init__(self)
        layout1 = QtWidgets.QVBoxLayout()
        
        label1 = QtWidgets.QLabel("Prediction Target")
        
        self.table = QtWidgets.QTableWidget()
        self.table.setRowCount(2)
        self.table.setColumnCount(3)
        comboBox_ = QtWidgets.QComboBox()
        plusMinusToggle_ = plusMinusToggle(self)
        self.table.setCellWidget(0, 0, plusMinusToggle_)
        self.table.setCellWidget(0, 1, comboBox_)
        item = QtWidgets.QTableWidgetItem('+')
        item.setFlags(QtCore.Qt.ItemIsEnabled)
        self.table.setItem(1, 0, item)
        label = QtWidgets.QLabel("Add Row")
        label.setStyleSheet("QLabel {color: gray}")
        self.table.setCellWidget(1, 1, label)
        self.table.cellDoubleClicked.connect(self.addRow)

        layout1.addWidget(label1)
        layout1.addWidget(self.table)
        self.setLayout(layout1)

    def addRow(self, row=None, col=None):
        numRows = self.table.rowCount()
        if row == numRows - 1:
            self.table.insertRow(row)
            plusMinusToggle_ = plusMinusToggle(self)
            comboBox_ = QtWidgets.QComboBox()
            self.table.setCellWidget(row, 0, plusMinusToggle_)
            self.table.setCellWidget(row, 1, comboBox_)
            item = QtWidgets.QTableWidgetItem(u"\u232B")
            self.table.setItem(row, 2, item)
            item = QtWidgets.QTableWidgetItem('+')
            item.setFlags(QtCore.Qt.ItemIsEnabled)
            self.table.setItem(row+1, 0, item)
            label = QtWidgets.QLabel("Add Row ...")
            label.setStyleSheet("QLabel {color: gray}")
            self.table.setCellWidget(row+1, 1, label)

        else:
            return


class plusMinusToggle(QtWidgets.QLabel):
    def __init__(self, parent=None):
        QtWidgets.QLabel.__init__(self)
        self.parent = parent
        self.setText('+')
        self.setStyleSheet("QLabel {font-size:18px}")
    
    def mouseDoubleClickEvent(self, event):
        QtWidgets.QLabel.mouseDoubleClickEvent(self, event)
        self.toggled()
        return

    def toggled(self):
        if self.text() == '+':
            self.setText('-')
        else:
            self.setText('+')

if __name__ == '__main__':
    from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout
    import sys
    application = QApplication(sys.argv)
    mw = predictionTargetSpecificationWidget()
    mw.show()
    def run_():
        return_value = application.exec_()
        return return_value
    sys.exit(run_())