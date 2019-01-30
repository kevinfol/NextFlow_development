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

import sys
import os
import pickle
import time
import subprocess
import traceback
import pandas as pd
import numpy as np
from PyQt5 import QtWidgets, QtCore, QtGui
from datetime import datetime
from resources.GUI import NextFlowGUI
from resources.modules import gisFunctions
from fuzzywuzzy.fuzz import WRatio 
import multiprocessing as mp
import itertools
import ast

class mainWindow(QtWidgets.QMainWindow, NextFlowGUI.UI_MainWindow):
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
        self.showMaximized()

        # Create the data structures.
        self.datasetTable = pd.DataFrame(columns = [
            'DatasetInternalID', # As assigned by software or taken from master list of default datasets
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
        self.dataTable = pd.DataFrame(columns = [
            "Datetime", # e.g. 2019-01-05
            "DatasetInternalID", # e.g. 100104
            "Value", # e.g. 24.5
            "EditedFlag"]) # e.g. 1 or 0 (edited or not edited)
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

        self.setupDatasetTab()

        return


    
    # MENU BAR
    # This section of code deals with user interaction with the menu bar options. This includes opening and saving files,
    # editing options, exporting and importing data.
    


    
    # DATASETS TAB
    # This section of code deals with user interaction with the Datasets Tab. This includes viewing and searching for available 
    # datasets, loading external datasets for watershed averages and climate parameters, and importing datasets from custom dataloaders.
    
    def setupDatasetTab(self):
        """
        Initialize the datasets Tab
        """
        self.loadSelectedDatasets(self.datasetTable, self.datasetTab.selectedDatasetsWidget)
        self.loadAdditionalDatasetLists()
        self.connectEventsDatasetTab()
        self.loadGISDataToWebMap()

        return

    def loadAdditionalDatasetLists(self):
        """
        Loads the additional datasets list located at resources/GIS/AdditionalDatasets.xlsx into a dataframe, and load the 
        various drop-downs into the datasets tab.
        """
        self.additionalDatasetsList = pd.read_excel("resources/GIS/AdditionalDatasets.xlsx", dtype={'DatasetExternalID':str})
        self.datasetTab.climInput.addItems(list(self.additionalDatasetsList[self.additionalDatasetsList['DatasetType'] == 'CLIMATE INDICE']['DatasetName']))
        self.datasetTab.pdsiInput.addItems(list(self.additionalDatasetsList[self.additionalDatasetsList['DatasetType'] == 'PDSI']['DatasetName']))

        return

    def validateHUCInput(self, hucNumber):
        """
        This function ensures that the user has entered a valid 8-digit watershed ID (HUC) into a HUC input field. 
        """
        print(hucNumber)
        validHUCs = list(self.additionalDatasetsList[self.additionalDatasetsList['DatasetType'] == 'WATERSHED']['DatasetExternalID'])
        if hucNumber in validHUCs:
            return True
        return False

    def connectEventsDatasetTab(self):
        """
        Connect Events within the datasets tab.
        """
        self.datasetTab.keywordSearchButton.clicked.connect(lambda x: self.searchAndReturnSearchResults(self.datasetTab.keywordSearchBox.text()))
        self.datasetTab.keywordSearchBox.returnPressed.connect(lambda: self.searchAndReturnSearchResults(self.datasetTab.keywordSearchBox.text()))
        self.datasetTab.searchResultsBox.itemDoubleClicked.connect(self.navigateMapToSelectedItem)
        self.datasetTab.selectedDatasetsWidget.itemDoubleClicked.connect(self.navigateMapToSelectedItem)
        self.datasetTab.boxHucResultsBox.itemDoubleClicked.connect(self.navigateMapToSelectedItem)
        self.datasetTab.searchResultsBox.addSignal.connect(self.addDatasetToSelectedDatasets)
        self.datasetTab.boxHucResultsBox.addSignal.connect(self.addDatasetToSelectedDatasets)
        self.datasetTab.selectedDatasetsWidget.removeSignal.connect(self.datasetRemovedFromDatasetTable)
        self.datasetTab.prismButton.clicked.connect(lambda x:self.addAdditionalDatasetToSelectedDatasets('PRISM'))
        self.datasetTab.nrccButton.clicked.connect(lambda x:self.addAdditionalDatasetToSelectedDatasets('NRCC'))
        self.datasetTab.pdsiButton.clicked.connect(lambda x:self.addAdditionalDatasetToSelectedDatasets('PDSI'))
        self.datasetTab.climButton.clicked.connect(lambda x:self.addAdditionalDatasetToSelectedDatasets('CLIM'))
        self.datasetTab.boundingBoxButton.clicked.connect(lambda x: self.beginAreaSearch("bounding"))
        self.datasetTab.hucSelectionButton.clicked.connect(lambda x: self.beginAreaSearch("watershed"))
        self.datasetTab.boxHucSearchButton.clicked.connect(self.areaSearchForDatasets)

    def beginAreaSearch(self, type_):
        self.datasetTab.boundingBoxButton.setEnabled(False)
        self.datasetTab.hucSelectionButton.setEnabled(False)
        self.datasetTab.boxHucSearchButton.setEnabled(True)
        if type_ == 'bounding':
            self.areaSearchType = 'bounding'
            self.datasetTab.webMapView.page.runJavaScript("enableBBSelect()")
        if type_ == 'watershed':
            self.areaSearchType = 'watershed'
            self.datasetTab.webMapView.page.runJavaScript("enableHUCSelect()")

    def areaSearchForDatasets(self):
        self.datasetTab.boundingBoxButton.setEnabled(True)
        self.datasetTab.hucSelectionButton.setEnabled(True)
        self.datasetTab.boxHucSearchButton.setEnabled(False)
        if self.areaSearchType == 'bounding':
            self.datasetTab.webMapView.page.runJavaScript("getBBCoords()", self.searchUsingCoords)
        else:
            self.datasetTab.webMapView.page.runJavaScript("getSelectedHUCs()", self.searchUsingHUCS)

    def searchUsingCoords(self, coords):
        n, w, s, e = [float(i) for i in str(coords).split(':')[1].split('|')]
        results = self.searchableDatasetsTable[(self.searchableDatasetsTable['DatasetLongitude'] <= e) & (self.searchableDatasetsTable['DatasetLongitude'] >= w) & (self.searchableDatasetsTable['DatasetLatitude'] >= s) & (self.searchableDatasetsTable['DatasetLatitude'] <= n)] 
        self.loadSelectedDatasets(results, self.datasetTab.boxHucResultsBox)

    def searchUsingHUCS(self, hucs):
        hucs = ast.literal_eval(str(hucs))
        results = self.searchableDatasetsTable[(self.searchableDatasetsTable['DatasetHUC8'].isin(hucs))]
        self.loadSelectedDatasets(results, self.datasetTab.boxHucResultsBox)

    def addAdditionalDatasetToSelectedDatasets(self, type_):
        if type_ == 'PRISM':
            huc = self.datasetTab.prismInput.text()
            if self.validateHUCInput(huc):
                dataset = self.additionalDatasetsList[(self.additionalDatasetsList['DatasetAgency'] == 'PRISM') & (self.additionalDatasetsList['DatasetExternalID'] == huc)]
                self.datasetTable = self.datasetTable.append(dataset, ignore_index=True)
                self.datasetTab.prismInput.clear()
            else:
                self.showErrorMessage("HUC number is invalid")
                
        elif type_ == 'NRCC':
            huc = self.datasetTab.nrccInput.text()
            if self.validateHUCInput(huc):
                dataset = self.additionalDatasetsList[(self.additionalDatasetsList['DatasetAgency'] == 'NRCC') & (self.additionalDatasetsList['DatasetExternalID'] == huc)]
                self.datasetTable = self.datasetTable.append(dataset, ignore_index=True)
                self.datasetTab.nrccInput.clear()
            else:
                self.showErrorMessage("HUC number is invalid")

        elif type_ == 'PDSI':
            division = self.datasetTab.pdsiInput.currentText()
            dataset = self.additionalDatasetsList[(self.additionalDatasetsList['DatasetName'] == division) & (self.additionalDatasetsList['DatasetType'] == 'PDSI')]
            self.datasetTable = self.datasetTable.append(dataset, ignore_index=True)

        elif type_ == 'CLIM':
            index_ = self.datasetTab.climInput.currentText()
            dataset = self.additionalDatasetsList[(self.additionalDatasetsList['DatasetName'] == index_) & (self.additionalDatasetsList['DatasetType'] == 'CLIMATE INDICE')]
            self.datasetTable = self.datasetTable.append(dataset, ignore_index=True)

        elif type_ == 'USERDEFINE':
            pass

        else:
            return

        self.datasetTable.drop_duplicates(keep='first', inplace=True)
        self.loadSelectedDatasets(self.datasetTable, self.datasetTab.selectedDatasetsWidget)

        numDatasets = len(self.datasetTable)
        self.datasetTab.selectedDatasetsLabel.setText("{0} datasets have been selected:".format(numDatasets))

    def loadGISDataToWebMap(self):
        """
        This function is responsible for loading the GIS data located 
        """
        if not hasattr(self, "searchableDatasetsTable"):
            self.searchableDatasetsTable = pd.read_excel("resources/GIS/PointDatasets.xlsx")

        geojson_ = gisFunctions.dataframeToGeoJSON(self.searchableDatasetsTable)
        self.datasetTab.webMapView.page.loadFinished.connect(lambda x: self.datasetTab.webMapView.page.runJavaScript("loadJSONData({0})".format(geojson_)))
        self.datasetTab.webMapView.page.java_msg_signal.connect(lambda x: self.addDatasetToSelectedDatasets(int(x.split(':')[1])) if "ID:" in x else None)

    def datasetRemovedFromDatasetTable(self, datasetID):

        datasetToRemove = self.datasetTable[self.datasetTable['DatasetInternalID'] == datasetID]
        self.datasetTable.drop(datasetToRemove.index, inplace=True)
        numDatasets = len(self.datasetTable)
        self.datasetTab.selectedDatasetsLabel.setText("{0} datasets have been selected:".format(numDatasets))
        self.datasetTab.searchResultsBox.updateAddedStatus(datasetID)
        self.datasetTab.boxHucResultsBox.updateAddedStatus(datasetID)

    def addDatasetToSelectedDatasets(self, datasetID):
        """
        input:  datasetID
                - The ID (DatasetInternalID) of the dataset that is to be added to the selected datasets
        """

        if datasetID in list(self.datasetTable['DatasetInternalID']):
            return

        dataset = self.searchableDatasetsTable[self.searchableDatasetsTable['DatasetInternalID']==datasetID]
        self.datasetTable = self.datasetTable.append(dataset, ignore_index=True)
        self.loadSelectedDatasets(self.datasetTable, self.datasetTab.selectedDatasetsWidget)

        numDatasets = len(self.datasetTable)
        self.datasetTab.selectedDatasetsLabel.setText("{0} datasets have been selected:".format(numDatasets))

        for result in self.datasetTable.iterrows():
            if result[1]['DatasetInternalID'] in list(self.datasetTable['DatasetInternalID']):
                self.datasetTab.searchResultsBox.updateAddedStatus(result[1]['DatasetInternalID'], 'added')

        return

    def navigateMapToSelectedItem(self, item):
        """
        This function moves the map to the selected dataset (if it can be displayed on the map) that corresponds to the double-clicked item
        """
        lat = item.dataset['DatasetLatitude']
        lng = item.dataset['DatasetLongitude']
        self.datasetTab.webMapView.page.runJavaScript("moveToMarker({0},{1})".format(lat, lng))

        return

    def searchAndReturnSearchResults(self, searchTerm):
        """
        Searched the default dataset list and returns any potential matches

        input:  searchTerm
                - The keyword or keywords to search the default dataset list for.
                  example: 'Yellowstone River Billings'
        
        output: results
                - a dataframe of results which is a subset of the searchableDatasetsTable
        """
        self.datasetTab.keywordSearchButton.setEnabled(False)
        if len(searchTerm) < 4:
            """
            Only perform a search if the search term is longer than 4 characters.
            """
            self.datasetTab.keywordSearchButton.setEnabled(True)
            return

        if not hasattr(self, "searchableDatasetsTable"):
            self.searchableDatasetsTable = pd.read_excel("resources/GIS/PointDatasets.xlsx")

        searchTable = self.searchableDatasetsTable.copy()
        searchTable['DatasetExternalID'] = searchTable['DatasetExternalID'].astype(str)
        searchTable['searchRow'] = searchTable[['DatasetName', 'DatasetType','DatasetAgency','DatasetExternalID']].apply(lambda x: ' '.join(x), axis=1)
        
        pool = mp.Pool(mp.cpu_count() - 1)
        searchTable['Score'] = list(pool.starmap(WRatio, zip(searchTable['searchRow'], itertools.repeat(searchTerm, len(searchTable['searchRow'])))))
        print(searchTable['Score'])
        pool.close()
        pool.join()
        
        searchTable.sort_values(by=['Score'], inplace=True, ascending=False)
        del searchTable['Score'], searchTable['searchRow']
        searchTable = searchTable[:20]
        self.loadSelectedDatasets(searchTable, self.datasetTab.searchResultsBox)

        for result in searchTable.iterrows():
            if result[1]['DatasetInternalID'] in list(self.datasetTable['DatasetInternalID']):
                self.datasetTab.searchResultsBox.updateAddedStatus(result[1]['DatasetInternalID'], 'added')
        self.datasetTab.keywordSearchButton.setEnabled(True)
        return 

    def loadSelectedDatasets(self, datasetsToLoad, widgetToLoadTo):
        """
        Creates entries for the user's selected datasets
        in the selected datasets tab.

        input:  datasetsToLoad
                - The dataframe containing the datasets to load into the dataset widget

                widgetToLoadTo
                - The sepecific widget where we are going to load the list of datasets.
        """

        if datasetsToLoad is None:
            return

        widgetToLoadTo.clear()
        
        for dataset in datasetsToLoad.iterrows():
            widgetToLoadTo.addEntry(dataset[1])

        return

    
    # DATA TAB
    # This section of code deals with user interaction on the data tab. This includes downloading and updating 
    # daily data for selected datasets, pre-processing data, editing avilable data.
    


    
    # PREDICTORS TAB
    # This section of code deals with user interaction with the predictors tab. This includes viewing predictor data 
    # downsampled from the daily data, viewing the predictand data downsampled from daily inflow data, and assigning
    # predictors to specific equations.
    


    
    # REGRESSION TAB
    # This section of code deals with user interaction with the regression tab. This includes generating regression 
    # equations using CV and SFFS. 
    
    # FORECASTS TAB
    # 
    # 
    #...This tab will summarize all the selected forecasts, notify the user when 2 or more equations are too similar
    #...and allow the user to generate forecasts for the coming water year. 

    # FORECAST ANALYSIS TAB
    #
    #
    #...This tab will include kernel density estimation, NRCS/CORPS forecast loader tool, what-if scenarios, 

    # MISCELLANEOUS FUNCTIONS
    #
    #
    #

    def showErrorMessage(self, msg):
        """
        """
        self.errorMsg = QtWidgets.QMessageBox.warning(self, "Error", msg)