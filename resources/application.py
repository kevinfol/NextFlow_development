"""

Script Name:        application.py
Script Author:      Kevin Foley, Civil Engineer, Reclamation
Last Modified:      Nov 13, 2018

Description:        'application.py' is the main processing script for the 
                    NextFlow application. This script loads the GUI and directs
                    all events and function calls. This script also handles loading
                    and saving documents, as well as exporting tables.

Disclaimer:         This script, and the overall NextFlow Application have been
                    reviewed and the methodology has been deemed sound. However, 
                    the resulting forecasts and forecast equations generated from 
                    this program are not in any way guarnateed to be reliable or accurate, 
                    and should be used in conjuction with other forecasts and forecast methods. 

"""

from PyQt5 import QtWidgets, QtCore
from datetime import datetime
from resources.GUI import NextFlowGUI
from resources.modules.DatasetTab import datasetTabMaster 
from resources.modules.DataTab import dataTabMaster
from resources.modules.MenuBar import menuBarMaster
from resources.modules.Miscellaneous import initUserOptions
from datetime import datetime
import configparser
import pandas as pd


class mainWindow(QtWidgets.QMainWindow, NextFlowGUI.UI_MainWindow, datasetTabMaster.datasetTab, dataTabMaster.dataTab, menuBarMaster.menuBar):
    """
    GLOBAL APPLICATION INITIALIZATION
    This section of the script deals with the initialization of the software. These subroutines 
    run immediately after the software begins.
    """

    def __init__(self):
        """
        The __init__ method runs when the GUI is first instantiated. Here we define the 'self' variable as a 
        reference to the mainWindow class, as well as build the GUI and connect all the functionality to the buttons
        and events in the GUI.

        """

        # Initialize the class as a QMainWindow and setup its User Interface
        super(self.__class__, self).__init__()
        self.setUI()
        pd.set_option('display.max_rows', 25)
        

        # Create the data structures.
        # The dataset table stores information about all the datasets being used in the forecast file.
        self.datasetTable = pd.DataFrame(
            index = pd.Index([], dtype=int, name='DatasetInternalID'),
            columns = [
            'DatasetType', # e.g. STREAMGAGE, or RESERVOIR
            'DatasetExternalID', # e.g. "GIBR" or "06025500"
            'DatasetName', # e.g. Gibson Reservoir
            'DatasetAgency', # e.g. USGS
            'DatasetParameter', # e.g. Temperature
            'DatasetUnits', # e.g. CFS
            'DatasetDefaultResampling', # e.g. average 
            'DatasetDataloader', # e.g. RCC_ACIS
            'DatasetHUC8', # e.g. 10030104
            'DatasetLatitude',  # e.g. 44.352
            'DatasetLongitude', # e.g. -112.324
            'DatasetElevation', # e.g. 3133 (in ft)
            'DatasetPORStart', # e.g. 1/24/1993
            'DatasetPOREnd',# e.g. 1/22/2019
            'DatasetAdditionalOptions']) 

        # The data table stores all of the raw data associated with the selected datasets.
        # Edited data is versioned as -1 and unedited data is versioned as 0
        self.dataTable = pd.DataFrame(
            index = pd.MultiIndex(
                levels=[[],[],[]],
                codes = [[],[],[]],
                names = ['Datetime','DatasetInternalID','Version']
            ),
            columns = ["Value"],
            dtype=float)

        self.forecastEquationsTable = pd.DataFrame(
            index = pd.Index([], dtype=int, name='ForecastEquationID'),
            columns = [
                "EquationSource", # E.g. NextFlow, NRCS, COE, etc
                "EquationComment", # E.g. Calib. per. 1981-2015, excluding 2011.  JR2=.143, R2=.220.  D. Garen 25 Feb 2016
                "EquationCoefficients", # E.g. [2.8, 1.2, 44.3, ...]
                "EquationPredictors", # E.g. [100234, 101423, 102334, ...] List of DatasetInternalIDs

            ]
        )

        self.forecastsTable = pd.DataFrame(
            columns = [
                "ForecastEquationID",
                "ForecastValues", # in order of 0-100% exceedance
                "Year", # e.g. 2019
                "ForecastIssuedOn" # e.g. 2019-03-04
            ]
        )
        
        initUserOptions.initOptions()
        self.userOptionsConfig = configparser.ConfigParser()
        self.userOptionsConfig.read('resources/temp/user_set_options.txt')
        self.applicationPrefsConfig = configparser.ConfigParser()
        self.applicationPrefsConfig.read('resources/application_prefs.ini')

        self.setupDatasetTab()
        self.setupDataTab()
        self.setupMenuBar()

        # Intiate a threadpool
        self.threadPool = QtCore.QThreadPool()

        # Show the application
        self.showMaximized()

        return