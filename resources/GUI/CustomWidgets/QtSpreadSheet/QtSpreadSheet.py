from PyQt5.QtWidgets    import  (QTableView,
                                QHeaderView,
                                QAbstractItemView,
                                QStyledItemDelegate)
from PyQt5.QtCore       import  (Qt,
                                QMimeData,
                                QModelIndex,
                                QRect,
                                QAbstractItemModel,
                                QVariant,
                                QDateTime,
                                pyqtSignal)
from PyQt5.QtGui        import  (QColor,
                                QPainter,
                                QBrush,
                                QPen,
                                QCursor,
                                QPixmap,
                                QDrag)
from resources.GUI.CustomWidgets.QtSpreadSheet.QtSpreadSheetModel import QSpreadSheetModel
from resources.GUI.CustomWidgets.QtSpreadSheet.QtSpreadSheetItemDelegate import QSpreadSheetItemDelegate
from resources.GUI.CustomWidgets.QtSpreadSheet.functions import paintEvent, mouse
from resources.GUI.CustomWidgets.QtSpreadSheet import ExcelFunctionality as ef
import datetime
import traceback
import numpy as np
import pandas as pd
import re
import os
import time

class QSpreadSheetWidget(QTableView):
    """
    The QSpreadSheetWidget class is a subclass of QTableView that provides 
    additional functionality to the tableview in order to get it to behave like an
    excel spreadsheet.
    """

    def __init__(self, parent = None, *args, **kwargs):
        """
        Constructor for the class. Here we initialize an empty model,
        and initialize the stylesheet for the widget.

        kwargs:
            'highlightColor': RGB color [#ffffff or (255, 255, 255) format] 
        """
        QTableView.__init__(self)
        self.parent = parent

        # Create new, empty QAbstractItemModel for the spreadsheet
        self.setModel(QSpreadSheetModel())

        # Set the default cursor
        self.cursor_ = QCursor(QPixmap(os.path.abspath('resources/GUI/CustomWidgets/QtSpreadSheet/cursor.bmp')))
        self.setCursor(self.cursor_)
        self.setMouseTracking(True)

        # State Variable
        # N: Normal Operation
        # D: Dragging Selection
        # E: Editing cell value 
        # EF: Editing cell value with formula
        # EFS: Selecting Range in cell edit
        # F: Filling Using Fill Handle
        self.state_ = 'N'

        # Set an item delegate
        self.delegate = QSpreadSheetItemDelegate(self)
        self.setItemDelegate(self.delegate)
        #self.delegate.textEditedSignal.connect(self.editorTextEdited)

        # Set the higlight color
        if 'highlightColor' in list(kwargs.keys()):
            color = kwargs['highlightColor']
            if isinstance(color, tuple):
                self.highlightColor = QColor(*color)
            else:
                self.highlightColor = QColor(color)
        else:
            self.highlightColor = QColor(66, 134, 244)

        # Set the widgets' stylesheet
        colorCode = '#%02x%02x%02x' % (self.highlightColor.red(), self.highlightColor.green(), self.highlightColor.blue())
        self.setStyleSheet(open(os.path.abspath('resources/GUI/CustomWidgets/QtSpreadSheet/style.qss'), 'r').read().format(colorCode))
        self.setFocusPolicy(Qt.StrongFocus)
        return

    def getSelectedRows(self):
        """
        Returns the selected rows
        """
        return list(set([i.row() for i in self.selectedIndexes]))

    def getSelectedColumns(self):
        """
        Returns the selected columns (either from headerArray, or from column number)
        """
        if self.model().case == 1 or self.model().case == 4:
            cols = [i.column() for i in self.selectedIndexes()]
            while 0 in cols:
                cols.pop(cols.index(0))
            return list(set(cols))
        else:
            cols = [self.model().headerArray[i.column()] for i in self.selectedIndexes()]
            while 'Datetime' in cols:
                cols.pop(cols.index('Datetime'))
            return list(set(cols))
            
    def getCurrentDataFrame(self):
        """
        Returns the current data in the table as a formatted datatable
        """
        case = self.model().case
        if case == 1:
            return pd.DataFrame(self.model().dataArray)
        elif case == 2:
            return pd.DataFrame(self.model().dataArray, columns=self.model().headerArray)
        elif case == 3:
            idx = self.model().datasetIndexArray
            if all(isinstance(x, datetime.datetime) for x in idx):
                idx = pd.DatetimeIndex(idx)
            return pd.DataFrame(self.model().dataArray, columns=self.model().headerArray[1:], index=idx)
        elif case == 4:
            idx = self.model().datasetIndexArray
            if all(isinstance(x, datetime.datetime) for x in idx):
                idx = pd.DatetimeIndex(idx)
            return pd.DataFrame(self.model().dataArray, index=idx)

    def getCurrentDataArrays(self):
        """
        Returns the current data in the table as a list of [dataArray, headerArray, indexArray]
        """
        case = self.model().case
        if case == 1:
            return np.array(self.model().dataArray), None, None
        elif case == 2:
            return np.array(self.model().dataArray), np.array(self.model().headerArray()), None
        elif case == 3:
            return np.array(self.model().dataArray), np.array(self.model().headerArray()), np.array(self.model().datasetIndexArray)
        elif case == 4:
            return np.array(self.model().dataArray), None, np.array(self.model().datasetIndexArray)

    def paintEvent(self, event):
        paintEvent.paintEvent(self, event)

 

def ctime():
    return time.strftime('%Y-%m-%d %H-%M-%S', time.localtime(time.time()))

def logMsg(msg):
    print(ctime(), ": ", msg)

if __name__ == '__main__':
    from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout
    import sys
    data = pd.read_excel('resources/GUI/CustomWidgets/QtSpreadSheet/tests/PointDatasets.xlsx').astype('object')
    application = QApplication(sys.argv)
    mw = QSpreadSheetWidget(highlightColor='#4baf90')
    mw.show()
    mw.model().load_new_dataset(data, suppress_column_names=False, display_index_col=True)
    def run_():
        return_value = application.exec_()
        print(data)
        return return_value
    sys.exit(run_())




