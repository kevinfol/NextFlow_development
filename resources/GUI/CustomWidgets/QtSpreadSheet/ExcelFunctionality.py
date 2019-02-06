"""
Includes functions to assist in spreadsheet functionality
"""
import re
from PyQt5.QtCore import QDateTime
import datetime
import numpy as np
import difflib

global lists 
"""
'lists' contains pre-defined sequences that autofill when using the fill-handle
"""
lists = [
    ['SUN','MON','TUE','WED','THU','FRI','SAT','SUN','MON','TUE','WED','THU','FRI','SAT'],
    ['SUNDAY','MONDAY','TUESDAY','THURSDAY','FRIDAY','SATURDAY','SUNDAY','MONDAY','TUESDAY','THURSDAY','FRIDAY','SATURDAY'],
    ['JAN','FEB','MAR','APR','MAY','JUN','JUL','AUG','SEP','OCT','NOV','DEC','JAN','FEB','MAR','APR','MAY','JUN','JUL','AUG','SEP','OCT','NOV','DEC'],
    ['JANUARY','FEBRUARY','MARCH','APRIL','MAY','JUNE','JULY','AUGUST','SEPTEMBER','OCTOBER','NOVEMBER','DECEMBER','JANUARY','FEBRUARY','MARCH','APRIL','MAY','JUNE','JULY','AUGUST','SEPTEMBER','OCTOBER','NOVEMBER','DECEMBER']
]
def is_sublist(smallList, bigList):
    """
    Checks if smallList is a sublist of bigList
    """
    def n_slices(n, list_):
        for i in range(len(list_)+1-n):
            yield(list_[i:i+n])
    for slice_ in n_slices(len(smallList), bigList):
        if slice_ == smallList:
            return True
    return False

def propogate_values(values, direction='down'):
    """
    This function is responsible for 
    propogating values when using the 
    fill handle. It can propogate formulas,
    dates/times, sequences (integers, floats), and 
    static text (strings, floats)
    """

    moving_range_types = []
    for value in values:
        if isinstance(value, str):
            if value[0] == '=':
                moving_range_types.append('formula')
            else:
                moving_range_types.append('str')
        elif isinstance(value, float):
            moving_range_types.append('numeric')
        elif isinstance(value, int):
            moving_range_types.append('numeric')
        elif isinstance(value, QDateTime):
            moving_range_types.append('date')
        else:
            moving_range_types.append('str')

    if len(list(set(moving_range_types))) != 1:
        """
        Mismatch of types, cant really do anything except return the 
        first value in the moving range
        """
        return values[0]


    type_ = moving_range_types[0]

    if type_ == 'numeric':
        """
        Simplest case, we check for a defined sequence,
        and if there isn't one, we simply use the first value
        """
        diff = np.diff(values)
        diff = [np.round(value,9) for value in diff]
        if len(list(set(diff))) != 1:
            return values[0]
        new_val = np.round(values[-1] + diff[0], 9)
        if new_val%np.floor(new_val) != 0:
            return float(new_val)
        else:
            return int(new_val)

    elif type_ == 'formula':
        """
        Check direction and use new formula values
        unless they are escaped with a '$'
        """
        formula = values[-1].upper()
        new_formula = formula
        cells_to_update = re.findall(r'[\$]?[a-zA-Z]+[\$]?[0-9]+', formula)
        for cell in cells_to_update:
            if cell in re.findall(r'{0}(?=\()'.format(cell), formula):
                continue
            column = re.findall(r'[\$]?[a-zA-Z]+', cell)[0]
            row = re.findall(r'[\$]?[0-9]+', cell)[0]
            if '$' not in column:
                if direction == 'right':
                    column = col_num_to_string(col_to_num(column)+1)
                if direction == 'left':
                    column = col_num_to_string(col_to_num(column)-1)
            if '$' not in row:
                if direction == 'down':
                    row = str(int(row) + 1)
                if direction == 'up':
                    row = str(int(row) - 1)
            new_formula = new_formula.replace(cell, column + row)
        
        return new_formula

    elif type_ == 'date':
        """
        Check for defined sequence of datetimes
        """
        values = [value.toPyDateTime() for value in values]
        diff = np.diff(values)
        if len(list(set(diff))) != 1:
            return values[0]
        return values[-1] + diff[0]

    elif type_ == 'str':
        """
        First checks for pattern matching 'lists', then
        check if there are any integers in 
        the string and if there are (and they're in
        a predifined sequence), increment them.
        """
        list_values = [value.upper() for value in values]
        for list_ in lists:
            if is_sublist(list_values, list_):
                ind = list_.index(list_values[-1])
                return list_[ind+1]

        int_list = []
        str_list = []
        for value in values:
            a = re.findall(r'[-+]?[0-9]+', value)
            if  a != []:
                int_list.append(int(a[0]))
                str_list.append(a[0])
            else:
                return values[0]
        diff = np.diff(int_list)
        if len(list(set(diff))) != 1:
            return values[0]
        next_val = int_list[-1] + diff[0]
        return values[-1].replace(str_list[-1], str(next_val))


def replace_cell_with_value(cell, array_, headers_suppresed = True):
    """
    Replaces cells with format 'AA23' with 
    thier respective model array value
    """
    # Cell in format AA32
    column = re.search(r'[a-zA-Z]+', cell).group()
    column = col_to_num(column)
    row = re.search(r'\d+', cell).group()
    row = int(row)

    if headers_suppresed:
        value = str(array_[row-1][column-1])
    else:
        value = str(array_[row-2][column-1])
    return value


def col_num_to_string(n):
    """
    Converts a column number (e.g. 3) into an excel-like column name (e.g. C)
    """
    string = ""
    while n > 0:
        n, remainder = divmod(n - 1, 26)
        string = chr(65 + remainder) + string
    return string


def col_to_num(col):
    """
    Converts an excel-like column name (e.g. AA) into a number (e.g. 27)
    """
    num = 0
    for c in col:
        num = num * 26 + (ord(c.upper()) - ord('A')) + 1
    return int(num)
    
def create_range(range_, arrayTest, headers_suppresed = True):
    """
    Creates a range string from a start and end value
    'A1','A4' becomes 'A1,A2,A3,A4'
    """
    result_string = []
    first_cell = range_.split(':')[0]
    last_cell = range_.split(':')[1]
    column_start = re.search(r'[a-zA-Z]+', first_cell).group()
    column_end = re.search(r'[a-zA-Z]+', last_cell).group()
    row_start = int(re.search(r'\d+', first_cell).group())
    row_end = int(re.search(r'\d+', last_cell).group())
    for i in range(col_to_num(column_start), col_to_num(column_end)+1):
        for j in range(row_start, row_end+1):
            if headers_suppresed:
                result_string.append(str(arrayTest[j-1][i-1]))
            else:
                result_string.append(str(arrayTest[j-2][i-1]))
            
    return '[' + ','.join(result_string) + ']'

def excel_to_python(command_string):
    """
    Returns the python equivalent of many excel formula names
    """
    d = {
        'SUM'       :   'np.sum',
        'AVERAGE'   :   'np.mean',
        'MAX'       :   'np.max',
        'MIN'       :   'np.min',
        'MEDIAN'    :   'np.median',
        'MODE'      :   'sp.stats.mode',
        'STDEV'     :   'np.std',
        'TAN'       :   'np.tan',
        'ATAN'      :   'np.arctan',
        'SIN'       :   'np.sin',
        'ASIN'      :   'np.arcsin',
        'COS'       :   'np.cos',
        'ACOS'      :   'np.arccos',
        'TANH'      :   'np.tanh',
        'SINH'      :   'np.sinh',
        'COSH'      :   'np.cosh',
        'LOG'       :   'np.log10',
        'LOG10'     :   'np.log10',
        'LN'        :   'np.log',
        'POWER'     :   'np.power',
        'EXP'       :   'np.exp',
        'COUNT'     :   'np.ma.size',
        'ABS'       :   'abs',
        'CEILING'   :   'np.ceil',
        'DEGREES'   :   'np.degrees',
        'RADIANS'   :   'np.radians',
        'ERF'       :   'sp.special.erf',
        'FACT'      :   'sp.misc.factorial',
        'FLOOR'     :   'np.floor',
        'GAMMA'     :   'sp.special.gamma',
        'INT'       :   'int',
        'PRODUCT'   :   'np.prod',
        'RAND'      :   'np.random.rand',
        'RANDBETWEEN':  'np.random.uniform',
        'ROUND'     :   'np.round',
        'SQRT'      :   'np.sqrt'
    }

    return d[command_string]