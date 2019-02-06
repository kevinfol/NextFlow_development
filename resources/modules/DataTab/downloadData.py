from PyQt5 import QtCore, QtWidgets
import json
import pandas as pd
import numpy as np
import importlib
from datetime import datetime, timedelta
import multiprocessing as mp
import sys

# Data Table Reference
# self.dataTable = pd.DataFrame(
#             index = pd.MultiIndex(
#                 levels=[[],[],[]],
#                 codes = [[],[],[]],
#                 names = ['Datetime','DatasetInternalID','Version']
#             ),
#             columns = [
#                 "Value", # e.g. 24.5
#                 "EditedFlag"]) # e.g. 1 or 0 (edited or not edited)

# Define a class that will contain all the signals as objects
class alternateThreadWorkerSignals(QtCore.QObject):

    # Define the signals emitted from this script
    updateProgBar = QtCore.pyqtSignal(int) # Signal to update the progress bar on the data tab
    finished = QtCore.pyqtSignal(bool) # Signal to tell the parent thread that the worker is done
    returnNewData = QtCore.pyqtSignal(object) # returns the new data dataframe back to the main thread

# Define the main alternate thread worker that will actually run the download algorithm
class alternateThreadWorker(QtCore.QRunnable):

    def __init__(self, datasets, startDate, endDate):
        super(alternateThreadWorker, self).__init__()

        # Load argument
        self.datasets = datasets
        self.startDate = startDate
        self.endDate = endDate

        # Get the total number of stations
        self.totalStations = len(self.datasets)

        # Load the signals into the worker object
        self.signals = alternateThreadWorkerSignals()

        # set up a dataframe to store all the new data
        mi = pd.MultiIndex(levels=[[],[]], codes=[[],[]], names=['Datetime','DatasetInternalID'])
        self.df = pd.DataFrame(index = mi, columns = ['Value'])

    @QtCore.pyqtSlot()
    def run(self):

        self.signals.updateProgBar.emit(0)

        queue = mp.Queue()
        processes = []
        returned = []

        for i in range(self.totalStations):
            proc = mp.Process(target = worker, args = (queue, self.datasets.loc[i], self.startDate, self.endDate))
            processes.append(proc)
            proc.start()

        for i, proc in enumerate(processes):
            returnValue = queue.get()
            returned.append(returnValue)
            progress = int(100*(i+1)/self.totalStations)
            self.signals.updateProgBar.emit(progress)

        for proc in processes:
            proc.join()
        
        for returnValue in returned:
            if returnValue.empty:
                continue
            self.df = pd.concat([self.df, returnValue])
            
            
        self.df = self.df.drop_duplicates()
        self.signals.returnNewData.emit(self.df)
        self.signals.finished.emit(True)

        return


def worker(queue, dataset, startDate, endDate):
    """
    This multiprocessing worker retrieves data for a dataset
    and stores it in a dataframe which it then appends to the 
    multiprocessing queue. 
    """

    # Get the dataloader
    dataloader = dataset['DatasetDataloader']
    modName = "resources.DataLoaders." + dataloader

    # Don't attempt to load imported data
    if dataloader == 'IMPORT':
        retval = pd.DataFrame()
        queue.put(retval)
        return
    
    # Load in the dataloader if it's not yet loaded
    if modName not in sys.modules:
        mod = importlib.import_module(modName)
        dataGetFunction = getattr(mod, 'dataLoader')
    else:
        mod = sys.modules[modName]
        dataGetFunction = getattr(mod, 'dataLoader')
    
    # use the dataloader to get the data
    try:
        data = dataGetFunction(dataset, startDate, endDate)
        data.columns =['Value']
        data.set_index([data.index, pd.Index(len(data)*[dataset['DatasetInternalID']])], inplace=True)
        data.index.names = ['Datetime','DatasetInternalID']
    except:
        retval = pd.DataFrame()
        queue.put(retval)
        return
    
    # rput the dataframe into the queue
    retval = data
    queue.put(retval)
    return
