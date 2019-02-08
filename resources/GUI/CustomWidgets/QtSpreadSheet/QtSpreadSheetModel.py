from PyQt5.QtCore import QAbstractItemModel, QModelIndex, QVariant, Qt

import traceback
from resources.GUI.CustomWidgets.QtSpreadSheet import ExcelFunctionality as ef
import numpy as np
import pandas as pd
import re

class QSpreadSheetModel(QAbstractItemModel):
    """
    QSpreadSheetModel class is a subclass of QAbstractItemModel that
    provides additional functionality to the itemmodel.
    """

    def __init__(self, parent = None, *args, **kwargs):
        """
        Constructor of the class.
        """
        QAbstractItemModel.__init__(self)
        self.parent = parent

        # Initialize arrays
        self.dataArray = np.array([[]])
        self.indexArray = np.array([[]])
        self.formulaArray = np.array([[]])
        self.headerArray = None

        # class variables
        self.numColumns = 0
        self.numRows = 0
        self.suppress_column_names = True

        self.load_new_dataset(np.full((200,30), ''))

        return


    def load_new_dataset(self, dataset, suppress_column_names = True, display_index_col = False):
        """
        loads a new pandas or numpy dataset into the model. The 
        dataset must be able to be expressed in a 2-D numpy array (for 
        example, a multi-index pandas dataframe won't work). 

        dataset: 2-D dataframe or numpy array, the entire dataframe must be dtype 'object'

        keyword args:
            suppress_column_names (True/False): ignores column headers in pandas dataframe, default True
            display_index_col (True/False): displays the dataframe index as first column, default False

        """
        # Begin model reset
        self.beginResetModel()

        # Set the class variables
        self.suppress_column_names = suppress_column_names
        self.display_index_col = display_index_col
        self.numRows, self.numColumns = dataset.shape
        self.formulaArray = np.full(dataset.shape, '', dtype='U256')

        # Figure out if 'dataset' is pandas or numpy and create the data and index arrays
        if isinstance(dataset, pd.DataFrame):
            self.dataArray = dataset.values
            self.indexArray = np.array([[self.createIndex(i, j, self.dataArray[i, j]) for j in range(len(row))] for i, row in enumerate(self.dataArray)])
            if display_index_col:
                self.numColumns += 1
                self.datasetIndexArray = np.array(dataset.index.get_level_values(0))
                self.formulaArray = np.array(np.insert(self.formulaArray, 0, ['' for i in self.datasetIndexArray], axis=1), dtype='U256')
                self.indexArray = np.array([[self.createIndex(i, 0, self.datasetIndexArray[i])] + [self.createIndex(i, j+1, self.dataArray[i,j]) for j in range(len(row))] for i, row in enumerate(self.dataArray)])
            if suppress_column_names == False:
                self.headerArray = dataset.columns.values
                self.numRows += 1
                if display_index_col:
                    self.headerArray = np.array(np.insert(self.headerArray, 0, 'Datetime'))
                self.formulaArray = np.array(np.insert(self.formulaArray, 0, ['' for i in self.headerArray], axis=0), dtype='U256')
                self.indexArray = np.array([[self.createIndex(0, i, headerValue) for i, headerValue in enumerate(self.headerArray)]])
                if display_index_col:
                    self.indexArray = np.append(self.indexArray, np.array([[self.createIndex(i, 0, self.datasetIndexArray[i])] + [self.createIndex(i, j+1, self.dataArray[i,j]) for j in range(len(row))] for i, row in enumerate(self.dataArray)]), axis = 0)
                else:
                    self.indexArray = np.append(self.indexArray, [[self.createIndex(i+1, j, self.dataArray[i, j]) for j in range(len(row))] for i, row in enumerate(self.dataArray)], axis = 0)
        else:
            self.dataArray = dataset
            self.indexArray = np.array([[self.createIndex(i, j, self.dataArray[i, j]) for j in range(len(row))] for i, row in enumerate(self.dataArray)])

        # End model reset
        self.endResetModel()

        return


    def index(self, row, column, parent = QModelIndex()):
        """
        This function returns the index for the specified row and 
        columns arguments. 
        """
        return self.indexArray[row][column]


    def columnCount(self, parent = QModelIndex()):
        """
        This function returns the number of columns in the dataset
        """
        return self.numColumns

    
    def rowCount(self, parent = QModelIndex()):
        """
        This function returns the number of rows in the dataset, or
        if the number is larger than the pagination, it returns the
        pagination maximum.
        """
        return self.numRows
        

    def data(self, index, role = Qt.DisplayRole):
        """
        This function returns the data associated with the provided
        index (row/column) and role (Display/Edit/Formula). If 
        unsuccessful, it returns nothing.
        """
        if not index.isValid():
            return QVariant()
        
        elif role == Qt.DisplayRole:
            if self.suppress_column_names:
                if self.display_index_col:
                    if index.column() == 0:
                        return str(self.datasetIndexArray[index.row()])
                    return str(self.dataArray[index.row()][index.column()-1]) 
                return str(self.dataArray[index.row()][index.column()])
            if index.row() == 0:
                return str(self.headerArray[index.column()])
            else:
                if index.column() == 0:
                    return str(self.datasetIndexArray[index.row()-1])
                return str(self.dataArray[index.row()-1][index.column()-1])
        
        elif role == Qt.EditRole:
            if self.formulaArray[index.row()][index.column()] != '':
                return str(self.formulaArray[index.row()][index.column()])
            else:
                if self.suppress_column_names:
                    return str(self.dataArray[index.row()][index.column()])
                if index.row() == 0:
                    return str(self.headerArray[index.column()])
                return str(self.dataArray[index.row()-1][index.column()])
        
        else:
            return QVariant()
        
        return


    def setData(self, index, value, role = Qt.DisplayRole):
        """
        This function sets the data in the model associated with the
        index (row/column) and the specified role (Display/Edit/Formula).
        """
        if value == '':
            if self.suppress_column_names:
                self.dataArray[index.row()][index.column()] = ''
            elif index.row() == 0:
                return False
            else:
                self.dataArray[index.row()-1][index.column()] = ''
            self.formulaArray[index.row()][index.column()] = ''
            return True
        
        if isinstance(value, str) and value[0] == '=':
            try:
                formula = value
                self.formulaArray[index.row()][index.column()] = formula
                value = self.parse_excel_computation(formula)
                if self.suppress_column_names:
                    self.dataArray[index.row()][index.column()] = value
                elif index.row() == 0:
                    return False
                else:
                    self.dataArray[index.row()-1][index.column()] = value
                return True
            except Exception as E:
                print(E)
                traceback.print_exc()
                if self.suppress_column_names:
                    self.dataArray[index.row()][index.column()] = 'ERROR'
                elif index.row() == 0:
                    return False
                else:
                    self.dataArray[index.row()-1][index.column()] = 'ERROR'
                self.formulaArray[index.row()][index.column()] = value
                return True

        if value == '%DELETEDATA%':
            if self.suppress_column_names:
                self.dataArray[index.row()][index.column()] = ''
            elif index.row() == 0:
                return False
            else:
                self.dataArray[index.row()-1][index.column()] = ''
            self.formulaArray[index.row()][index.column()] = ''
            return True
    
        try:
            value = float(value)
            if value%int(value) == 0:
                value = int(value)
                if self.suppress_column_names:
                    self.dataArray[index.row()][index.column()] = value
                elif index.row() == 0:
                    return False
                else:
                    self.dataArray[index.row()-1][index.column()] = value
                self.formulaArray[index.row()][index.column()] = ''
                return True
            else:
                if self.suppress_column_names:
                    self.dataArray[index.row()][index.column()] = value
                elif index.row() == 0:
                    return False
                else:
                    self.dataArray[index.row()-1][index.column()] = value
                self.formulaArray[index.row()][index.column()] = ''
                return True
        except:
            if self.suppress_column_names:
                self.dataArray[index.row()][index.column()] = str(value)
            elif index.row() == 0:
                return False
            else:
                self.dataArray[index.row()-1][index.column()] = str(value)
            self.formulaArray[index.row()][index.column()] = ''
            return True

        return False


    def headerData(self, section, orientation, role = Qt.DisplayRole):
        """
        Returns the data for the model header having orientation equal
        to 'orientation' at the specified section having role = 'role'
        """

        if role != Qt.DisplayRole:
            return QVariant()

        if orientation == Qt.Vertical and role == Qt.DisplayRole:
            value = section + 1
            return QVariant(str(value))
        elif orientation == Qt.Horizontal and role == Qt.DisplayRole:
            value = ef.col_num_to_string(int(section)+1)
            return QVariant(str(value))
        else:
            return QVariant('')
        

    def flags(self, index = QModelIndex()):
        """
        This function returns the flag associated with the model data
        at the given index (row/column)
        """
        return Qt.ItemIsEnabled | Qt.ItemIsEditable | Qt.ItemIsSelectable 
        

    def parse_excel_computation(self, parse_string):
        """
        When a user enters in a value like '=SUM(A1:A5)', this function will
        attempt to parse the input and return the value. 
        """
        parse_string = parse_string[1:].replace(' ', '')
        parse_string = parse_string.replace('^','**')

        # Find function calls in the parse_string
        expressions = re.findall(r'[a-zA-Z]+\(', parse_string)
        for expression in expressions:
            parse_string = parse_string.replace(expression[:-1], ef.excel_to_python(expression[:-1]))
        
        # Find function calls that look like 'LOG10' in the parse_string
        expressions = re.findall(r'[a-zA-Z]+[0-9]+\(', parse_string)
        for expression in expressions:
            parse_string = parse_string.replace(expression[:-1], ef.excel_to_python(expression[:-1]))
        
        # Find ranges in the parse string (A34:B55)
        ranges = re.findall(r'[a-zA-Z]+[0-9]+:[a-zA-Z]+[0-9]+', parse_string)
        for range_ in ranges:
            parse_string = parse_string.replace(range_, ef.create_range(range_, self.dataArray, self.suppress_column_names, self.display_index_col))
        
        # Find individual cells in the parse_string
        cell_names = re.findall(r'[a-zA-Z]+[0-9]+', parse_string)
        for cell in cell_names:
            if cell in re.findall(r'{0}(?=\()'.format(cell), parse_string):
                continue
            parse_string = parse_string.replace(cell, ef.replace_cell_with_value(cell, self.dataArray, self.suppress_column_names, self.display_index_col))

        value = float(eval(parse_string))
        if int(value) == 0:
            return value
        elif value%int(value) == 0:
            value = int(value)
            return value
        else:
            return value   
