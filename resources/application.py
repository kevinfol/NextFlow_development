"""

Script Name:        application.py
Script Author:      Kevin Foley, Civil Engineer, Reclamation
Last Modified:      Nov 13, 2018

Description:        'application.py' is the main processing script for the 
                    FlowCast application. This script loads the GUI and directs
                    all events and function calls. This script also handles loading
                    and saving documents, as well as exporting tables.

Disclaimer:         This script, and the overall FlowCast Application have been
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
import pandas as pd

class mainWindow(QtWidgets.QMainWindow, NextFlowGUI.UI_MainWindow, datasetTabMaster.datasetTab, dataTabMaster.dataTab):
    """
    GLOBAL APPLICATION SETTINGS
    This section of the script deals with the initialization of the software. These subroutines 
    run immediately after the software begins.
    """

    def __init__(self, customDateTime = datetime.strftime(datetime.now(), '%Y-%m-%d')):
        """
        The __init__ method runs when the GUI is first instantiated. Here we define the 'self' variable as a 
        reference to the mainWindow class, as well as build the GUI and connect all the functionality to the buttons
        and events in the GUI.

        Keyword Arguments:
        customDateTime -- Date in the form 'YYYY-mm-dd', used to spoof the date in FlowCast.
        """

        # Initialize the class as a QMainWindow and setup its User Interface
        super(self.__class__, self).__init__()
        self.setUI()
        pd.set_option('display.max_rows', 25)
        

        # Create the data structures.
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
            'DatasetPOREnd']) # e.g. 1/22/2019
        self.dataTable = pd.DataFrame(
            index = pd.MultiIndex(
                levels=[[],[],[]],
                codes = [[],[],[]],
                names = ['Datetime','DatasetInternalID','Version']
            ),
            columns = ["Value"],
            dtype=float)
        self.resampledTable = pd.DataFrame(columns = [
            "DatasetInternalID",
            "ResampledDataID",
            "ResampledDataType",
            "PeriodStart",
            "PeriodEnd",
            "Year",
            "Value",
            "Units"])
        self.equationPoolsTable = pd.DataFrame(columns = [
            "EquationID", # e.g. "JAN01"
            "Key", # e.g. 'PREDICTOR', 'PREDICTAND'
            "Identifier", # e.g. 'ID', '2001'
            "Value",
            "Units"]) # if applicable 
        self.forecastEquationsTable = pd.DataFrame(columns = [
            "ForecastEquationID",
            "Key",
            "Identifier",
            "Value"]) 
        self.forecastsTable = pd.DataFrame(columns = [
            "ForecastEquationID",
            "Year",
            "Key",
            "Identifier",
            "Value"])

        # Set up tabs
        self.setupDatasetTab()
        self.setupDataTab()

        # Intiate a threadpool
        self.threadPool = QtCore.QThreadPool()

        # Show the application
        self.showMaximized()

        return


    
    # MENU BAR
    # This section of code deals with user interaction with the menu bar options. This includes opening and saving files,
    # editing options, exporting and importing data.
    


    
    

    
    # DATA TAB
    # This section of code deals with user interaction on the data tab. This includes downloading and updating 
    # daily data for selected datasets, pre-processing data, editing avilable data.
    
    

    
    # PREDICTORS TAB
    # This section of code deals with user interaction with the predictors tab. This includes viewing predictor data 
    # downsampled from the daily data, viewing the predictand data downsampled from daily inflow data, and assigning
    # predictors to specific equations.

    def setupPredictorsTab(self):
        """
        Initialize the predictors Tab
        """
        

        return
    


    
    # REGRESSION TAB
    # This section of code deals with user interaction with the regression tab. This includes generating regression 
    # equations using CV and SFFS. 

    def setupRegressionTab(self):
        """
        Initialize the regression Tab
        """
        

        return
    
    # FORECASTS TAB
    # 
    # 
    #...This tab will summarize all the selected forecasts, notify the user when 2 or more equations are too similar
    #...and allow the user to generate forecasts for the coming water year. 

    def setupForecastsTab(self):
        """
        Initialize the Forecasts Tab
        """
        

        return
    

    # FORECAST ANALYSIS TAB
    #
    #
    #...This tab will include kernel density estimation, NRCS/CORPS forecast loader tool, what-if scenarios, 

    def setupForecastAnalysisTab(self):
        """
        Initialize the Forecast Analysis Tab
        """
        

        return

    # MISCELLANEOUS FUNCTIONS
    #
    #
    #

    