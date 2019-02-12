from PyQt5.QtCore import QAbstractItemModel, QModelIndex, QVariant, Qt, pyqtSignal

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

    changedDataSignal = pyqtSignal(list)

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


    def load_new_dataset(self, dataset, suppress_column_names = True, display_index_col = False, index_col_name='Index'):
        """
        loads a new pandas or numpy dataset into the model. The 
        dataset must be able to be expressed in a 2-D numpy array (for 
        example, a multi-index pandas dataframe won't work). 

        dataset: 2-D dataframe or numpy array, the entire dataframe must be dtype 'object'

        keyword args:
            suppress_column_names (True/False): ignores column headers in pandas dataframe, default True
            display_index_col (True/False): displays the dataframe index as first column, default False
            index_col_name: Column header to apply to the index column if applicable

        """
        # Begin model reset
        self.beginResetModel()

        # Set the class variables
        self.suppress_column_names = suppress_column_names
        self.display_index_col = display_index_col
        self.numRows, self.numColumns = dataset.shape
        self.index_col_name = index_col_name
        self.formulaArray = np.array(np.full(dataset.shape, '', dtype='U256'))
        self.case = self.case_()

        dataset = pd.DataFrame(dataset)
        self.dataArray = np.array(dataset.values, dtype='object')

        # Case 1: suppress_column_names, no index column
        if self.case == 1:
            self.indexArray = np.array([[self.createIndex(i, j, self.dataArray[i, j]) for j in range(len(row))] for i, row in enumerate(self.dataArray)])

        # Case 2: column names and no index column
        elif self.case == 2:
            self.numRows += 1
            self.headerArray = np.array(dataset.columns.values)
            self.indexArray = np.array([[self.createIndex(0, i, val) for i, val in enumerate(self.headerArray)]] + [[self.createIndex(i+1, j, self.dataArray[i, j]) for j in range(len(row))] for i, row in enumerate(self.dataArray)])

        # Case 3: column names and  index column
        elif self.case == 3:
            self.numColumns += 1
            self.numRows += 1
            self.headerArray = np.array([index_col_name] + list(dataset.columns.values), dtype='<U64')
            self.datasetIndexArray = np.array(dataset.index.get_level_values(0))
            self.indexArray = np.array([[self.createIndex(0, i, val) for i, val in enumerate(self.headerArray)]] + [[self.createIndex(i+1, 0, self.datasetIndexArray[i])] + [self.createIndex(i+1, j+1, self.dataArray[i, j]) for j in range(len(row))] for i, row in enumerate(self.dataArray)])
        
        # Case 4: index column but no column names
        elif self.case == 4:
            self.numColumns += 1
            self.datasetIndexArray = np.array(dataset.index.get_level_values(0))
            self.indexArray = np.array([[self.createIndex(i, 0, self.datasetIndexArray[i])] + [self.createIndex(i, j+1, self.dataArray[i, j]) for j in range(len(row))] for i, row in enumerate(self.dataArray)])

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

            # 4 possible cases:
            # Case 1: suppress_column_names, no index column
            if self.case == 1:
                return str(self.dataArray[index.row()][index.column()])

            # Case 2: column names and no index column
            elif self.case == 2:
                if index.row() == 0:
                    return str(self.headerArray[index.column()])
                return str(self.dataArray[index.row() - 1][index.column()])

            # Case 3: column names and  index column
            elif self.case == 3:
                if index.row() == 0:
                    return str(self.headerArray[index.column()])
                if index.column() == 0:
                    return str(self.datasetIndexArray[index.row()-1])
                return str(self.dataArray[index.row()-1][index.column()-1])

            # Case 4: index column but no column names
            elif self.case == 4:
                if index.column() == 0:
                    return str(self.datasetIndexArray[index.row()-1])
                return str(self.dataArray[index.row()][index.column()-1])
        
        elif role == Qt.EditRole:

            # Case 1: suppress_column_names, no index column
            if self.case == 1:
                if self.formulaArray[index.row()][index.column()] != '':
                    return str(self.formulaArray[index.row()][index.column()])
            
            # Case 2: column names and no index column
            elif self.case == 2:
                if index.row() == 0:
                    return QVariant()
                if self.formulaArray[index.row()-1][index.column()] != '':
                    return str(self.formulaArray[index.row()-1][index.column()])

            # Case 3: column names and  index column
            elif self.case == 3:
                if index.row() == 0 or index.column() == 0:
                    return QVariant()
                if self.formulaArray[index.row()-1][index.column()-1] != '':
                    return str(self.formulaArray[index.row()-1][index.column()-1])

            # Case 4: index column but no column names
            elif self.case == 4:
                if index.column() == 0:
                    return QVariant()
                if self.formulaArray[index.row()][index.column()-1] != '':
                    return str(self.formulaArray[index.row()][index.column()-1])

        else:
            return QVariant()
        
        return

    def case_(self):
        """
        Returns the state of the table (index cols, header cols)
        """
        if self.suppress_column_names == True and self.display_index_col == False:
            return 1
        elif self.suppress_column_names == False and self.display_index_col == False:
            return 2
        elif self.suppress_column_names == False and self.display_index_col == True:
            return 3
        elif self.suppress_column_names == True and self.display_index_col == True:
            return 4

    def setData(self, index, value, role = Qt.DisplayRole):
        """
        This function sets the data in the model associated with the
        index (row/column) and the specified role (Display/Edit/Formula).
        """
        oldValue = self.data(index)

        if self.case == 1:
            idx = index.row()
            col = index.column()

        elif self.case == 2:
            idx = index.row() - 1
            col = self.headerArray[index.column()]

        elif self.case == 3:
            idx = self.datasetIndexArray[index.row() - 1]
            col = self.headerArray[index.column() - 1]

        elif self.case == 4:
            idx = self.datasetIndexArray[index.row()]
            col = index.column() - 1

        if value == '':
            if self.case == 1:
                self.dataArray[index.row()][index.column()] == ''
                self.formulaArray[index.row()][index.column()] = ''
                

            elif self.case == 2:
                self.dataArray[index.row()-1][index.column()] == ''
                self.formulaArray[index.row()-1][index.column()] = ''
                
                
            elif self.case == 3:
                self.dataArray[index.row()-1][index.column()-1] == ''
                self.formulaArray[index.row()-1][index.column()-1] = ''
                

            elif self.case == 4:
                self.dataArray[index.row()][index.column()-1] == ''
                self.formulaArray[index.row()-1][index.column()-1] = ''
            
            self.changedDataSignal.emit([idx, col, oldValue, ''])
            return True
        
        if isinstance(value, str) and value[0] == '=':
            try:
                formula = value

                if self.case == 1:
                    self.formulaArray[index.row()][index.column()] = formula
                    value = self.parse_excel_computation(formula)
                    self.dataArray[index.row()][index.column()] = value

                elif self.case == 2:
                    self.formulaArray[index.row()-1][index.column()] = formula
                    value = self.parse_excel_computation(formula)
                    self.dataArray[index.row()-1][index.column()] = value

                elif self.case == 3:
                    self.formulaArray[index.row()-1][index.column()-1] = formula
                    value = self.parse_excel_computation(formula)
                    self.dataArray[index.row()-1][index.column()-1] = value

                elif self.case == 4:
                    self.formulaArray[index.row()][index.column()-1] = formula
                    value = self.parse_excel_computation(formula)
                    self.dataArray[index.row()][index.column()-1] = value

                self.changedDataSignal.emit([idx, col, oldValue, value])
                return True

            except Exception as E:
                print(E)
                traceback.print_exc()
                if self.case == 1:
                    self.dataArray[index.row()][index.column()] = 'ERROR'

                elif self.case == 2:
                    self.dataArray[index.row()-1][index.column()] = 'ERROR'

                elif self.case == 3:
                    self.dataArray[index.row()-1][index.column()-1] = 'ERROR'

                elif self.case == 4:
                    self.dataArray[index.row()][index.column()-1] = 'ERROR'

                self.changedDataSignal.emit([idx, col, oldValue, np.nan])
                return True

        if value == '%DELETEDATA%':
            if self.case == 1:
                self.dataArray[index.row()][index.column()] = ''
                self.formulaArray[index.row()][index.column()] = ''

            elif self.case == 2:
                self.dataArray[index.row()-1][index.column()] = ''
                self.formulaArray[index.row()-1][index.column()] = ''

            elif self.case == 3:
                self.dataArray[index.row()-1][index.column()-1] = ''
                self.formulaArray[index.row()-1][index.column()-1] = ''

            elif self.case == 4:
                self.dataArray[index.row()][index.column()] = ''
                self.formulaArray[index.row()][index.column()-1] = ''

            self.changedDataSignal.emit([idx, col, oldValue, ''])
            return True
    
        try:
            value = float(value)
            if value%int(value) == 0:
                value = int(value)

                if self.case == 1:
                    self.dataArray[index.row()][index.column()] = value
                    self.formulaArray[index.row()][index.column()] = ''

                elif self.case == 2:
                    self.dataArray[index.row()-1][index.column()] = value
                    self.formulaArray[index.row()-1][index.column()] = ''

                elif self.case == 3:
                    self.dataArray[index.row()-1][index.column()-1] = value
                    self.formulaArray[index.row()-1][index.column()-1] = ''

                elif self.case == 4:
                    self.dataArray[index.row()][index.column()-1] = value
                    self.formulaArray[index.row()][index.column()-1] = ''

                self.changedDataSignal.emit([idx, col, oldValue, value])
                return True

            else:

                if self.case == 1:
                    self.dataArray[index.row()][index.column()] = value
                    self.formulaArray[index.row()][index.column()] = ''

                elif self.case == 2:
                    self.dataArray[index.row()-1][index.column()] = value
                    self.formulaArray[index.row()-1][index.column()] = ''

                elif self.case == 3:
                    self.dataArray[index.row()-1][index.column()-1] = value
                    self.formulaArray[index.row()-1][index.column()-1] = ''

                elif self.case == 4:
                    self.dataArray[index.row()][index.column()-1] = value
                    self.formulaArray[index.row()][index.column()-1] = ''

                self.changedDataSignal.emit([idx, col, oldValue, value])
                return True

        except:
            if self.case == 1:
                self.dataArray[index.row()][index.column()] = str(value)
                self.formulaArray[index.row()][index.column()] = ''

            elif self.case == 2:
                self.dataArray[index.row()-1][index.column()] = str(value)
                self.formulaArray[index.row()-1][index.column()] = ''

            elif self.case == 3:
                self.dataArray[index.row()-1][index.column()-1] = str(value)
                self.formulaArray[index.row()-1][index.column()-1] = ''

            elif self.case == 4:
                self.dataArray[index.row()][index.column()-1] = str(value)
                self.formulaArray[index.row()][index.column()-1] = ''

            self.changedDataSignal.emit([idx, col, oldValue, str(value)])
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
        if self.case == 1:
            return Qt.ItemIsEnabled | Qt.ItemIsEditable | Qt.ItemIsSelectable 
        elif self.case == 2:
            if index.row() == 0:
                return Qt.ItemIsEnabled
            return Qt.ItemIsEnabled | Qt.ItemIsEditable | Qt.ItemIsSelectable 
        elif self.case == 3:
            if index.row() == 0 or index.column() == 0:
                return Qt.ItemIsEnabled
            return Qt.ItemIsEnabled | Qt.ItemIsEditable | Qt.ItemIsSelectable 
        elif self.case == 4:
            if index.column() == 0:
                return Qt.ItemIsEnabled
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
            if self.case == 1:
                parse_string = parse_string.replace(range_, ef.create_range(range_, self.dataArray, case = self.case))
            elif self.case == 2:
                parse_string = parse_string.replace(range_, ef.create_range(range_, self.dataArray, header_array = self.headerArray, case = self.case))
            elif self.case == 3:
                parse_string = parse_string.replace(range_, ef.create_range(range_, self.dataArray, header_array = self.headerArray, index_array = self.datasetIndexArray, case = self.case))
            elif self.case == 4:
                parse_string = parse_string.replace(range_, ef.create_range(range_, self.dataArray, index_array = self.datasetIndexArray, case = self.case))

        # Find individual cells in the parse_string
        cell_names = re.findall(r'[a-zA-Z]+[0-9]+', parse_string)
        for cell in cell_names:
            if cell in re.findall(r'{0}(?=\()'.format(cell), parse_string):
                continue
            if self.case == 1:
                parse_string = parse_string.replace(cell, ef.replace_cell_with_value(cell, self.dataArray, case = self.case))
            elif self.case == 2:
                parse_string = parse_string.replace(cell, ef.replace_cell_with_value(cell, self.dataArray, header_array = self.headerArray, case = self.case))
            elif self.case == 3:
                parse_string = parse_string.replace(cell, ef.replace_cell_with_value(cell, self.dataArray, header_array = self.headerArray, index_array = self.datasetIndexArray, case = self.case))
            elif self.case == 4:
                parse_string = parse_string.replace(cell, ef.replace_cell_with_value(cell, self.dataArray, index_array = self.datasetIndexArray, case = self.case))


        value = float(eval(parse_string))
        if int(value) == 0:
            return value
        elif value%int(value) == 0:
            value = int(value)
            return value
        else:
            return value   
