from    PyQt5   import  QtWidgets, \
                        QtCore, \
                        QtGui
from resources.GUI.CustomWidgets.MatplotlibPlots import TimeSeriesDataPlot, NavigationToolbar
import  sys
import  os

class DataTab(QtWidgets.QWidget):
    """
    """
    def __init__(self, parent=None):
        QtWidgets.QWidget.__init__(self)
        layout = QtWidgets.QVBoxLayout()

        hlayout = QtWidgets.QHBoxLayout()
        porLabel = QtWidgets.QLabel("Period of Record:")
        self.porT1 = QtWidgets.QLineEdit()
        self.porT2 = QtWidgets.QLineEdit()
        self.porT2.setDisabled(True)
        self.porT1.setFixedWidth(50)
        self.porT2.setFixedWidth(50)
        self.downloadButton = QtWidgets.QPushButton("Download")
        self.updateButton = QtWidgets.QPushButton("Update")
        self.importButton = QtWidgets.QPushButton("Import")
        self.viewMissingButton = QtWidgets.QPushButton("View Missing")
        hlayout.addWidget(porLabel)
        hlayout.addWidget(self.porT1)
        hlayout.addWidget(self.porT2)
        hlayout.addWidget(self.downloadButton)
        hlayout.addWidget(self.updateButton)
        hlayout.addWidget(self.importButton)
        hlayout.addSpacerItem(QtWidgets.QSpacerItem(500, 10, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum))
        hlayout.addWidget(self.viewMissingButton)
        layout.addLayout(hlayout)

        splitter = QtWidgets.QSplitter(QtCore.Qt.Horizontal)

        self.dataPlot = TimeSeriesDataPlot()
        dataNav = NavigationToolbar(self.dataPlot, self)
        dataNav.setSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Minimum)
        widg = QtWidgets.QWidget()
        layout_ = QtWidgets.QVBoxLayout()
        layout_.addWidget(self.dataPlot)
        layout_.addWidget(dataNav)
        widg.setLayout(layout_)
        splitter.addWidget(widg)

        table = QtWidgets.QTableWidget()
        splitter.addWidget(table)

        layout.addWidget(splitter)

        self.setLayout(layout)

if __name__ == '__main__':
    print(os.listdir())
    app = QtWidgets.QApplication(sys.argv)
    widg = DataTab()
    widg.show()
    sys.exit(app.exec_())


