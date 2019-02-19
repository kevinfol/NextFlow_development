import pandas as pd
from resources.modules.Miscellaneous import loggingAndErrors
from resources.modules.DatasetTab import gisFunctions
from fuzzywuzzy.fuzz import WRatio 
import multiprocessing as mp
import itertools
from time import sleep
import ast


class datasetTab(object):
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
    
    def resetDatasetTab(self):
        """
        Resets the tab to reflect any backend changes to the datasettables, views, etc.
        """
        loc = self.userOptionsConfig['DATASETS TAB']['current_map_location'].split(":")[1].split("|")
        print(loc)
        layers = self.userOptionsConfig['DATASETS TAB']['current_map_layers'].split(":")[1]

        self.datasetTab.webMapView.page.runJavaScript("zoomToLoc({0},{1},{2})".format(loc[0], loc[1], loc[2]))
        self.datasetTab.webMapView.page.runJavaScript("setActiveLayers({0})".format(layers))
        self.loadSelectedDatasets(self.datasetTable, self.datasetTab.selectedDatasetsWidget)
    
    def storeMapInformation(self):
        """
        """
        self.userOptionsConfig['DATASETS TAB']['current_map_location'] = self.datasetTab.webMapView.webClass.loc
        self.userOptionsConfig['DATASETS TAB']['current_map_layers'] = self.datasetTab.webMapView.webClass.layers

        return

    def loadAdditionalDatasetLists(self):
        """
        Loads the additional datasets list located at resources/GIS/AdditionalDatasets.xlsx into a dataframe, and load the 
        various drop-downs into the datasets tab.
        """
        self.additionalDatasetsList = pd.read_excel("resources/GIS/AdditionalDatasets.xlsx", dtype={'DatasetExternalID':str}, index_col=0)
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
                self.datasetTable = self.datasetTable.append(dataset, ignore_index=False)
                self.datasetTab.prismInput.clear()
            else:
                loggingAndErrors.showErrorMessage("HUC number is invalid")
                
        elif type_ == 'NRCC':
            huc = self.datasetTab.nrccInput.text()
            if self.validateHUCInput(huc):
                dataset = self.additionalDatasetsList[(self.additionalDatasetsList['DatasetAgency'] == 'NRCC') & (self.additionalDatasetsList['DatasetExternalID'] == huc)]
                self.datasetTable = self.datasetTable.append(dataset, ignore_index=False)
                self.datasetTab.nrccInput.clear()
            else:
                loggingAndErrors.showErrorMessage("HUC number is invalid")

        elif type_ == 'PDSI':
            division = self.datasetTab.pdsiInput.currentText()
            dataset = self.additionalDatasetsList[(self.additionalDatasetsList['DatasetName'] == division) & (self.additionalDatasetsList['DatasetType'] == 'PDSI')]
            self.datasetTable = self.datasetTable.append(dataset, ignore_index=False)

        elif type_ == 'CLIM':
            index_ = self.datasetTab.climInput.currentText()
            dataset = self.additionalDatasetsList[(self.additionalDatasetsList['DatasetName'] == index_) & (self.additionalDatasetsList['DatasetType'] == 'CLIMATE INDICE')]
            self.datasetTable = self.datasetTable.append(dataset, ignore_index=False)

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
            self.searchableDatasetsTable = pd.read_excel("resources/GIS/PointDatasets.xlsx", index_col=0)
            self.searchableDatasetsTable.index.name = 'DatasetInternalID'

        geojson_ = gisFunctions.dataframeToGeoJSON(self.searchableDatasetsTable)
        self.datasetTab.webMapView.page.loadFinished.connect(lambda x: self.datasetTab.webMapView.page.runJavaScript("loadJSONData({0})".format(geojson_)))
        self.datasetTab.webMapView.page.java_msg_signal.connect(lambda x: self.addDatasetToSelectedDatasets(int(x.split(':')[1])) if "ID:" in x else self.addDatasetToSelectedDatasets(str(x.split(':')[1])))

    def datasetRemovedFromDatasetTable(self, datasetID):
        print(datasetID)
        datasetToRemove = self.datasetTable.loc[datasetID]
        self.datasetTable.drop(datasetToRemove.name, inplace=True)
        numDatasets = len(self.datasetTable)
        self.datasetTab.selectedDatasetsLabel.setText("{0} datasets have been selected:".format(numDatasets))
        self.datasetTab.searchResultsBox.updateAddedStatus(datasetID)
        self.datasetTab.boxHucResultsBox.updateAddedStatus(datasetID)
        # ###########################################
        # NEED TO REMOVE ANY DATA ASSOCIATED WITH THIS STATION, ALSO ANY PREDICTORS OR FORECASTS THAT RELY ON THIS STATION
        # ########################################################################
        

    def addDatasetToSelectedDatasets(self, datasetID):
        """
        input:  datasetID
                - The ID (DatasetInternalID) of the dataset that is to be added to the selected datasets
        """
        
        if isinstance(datasetID, str):
            print(datasetID)
            """
            This is a HUC addition, not a point addition
            """
            datasets = self.additionalDatasetsList[self.additionalDatasetsList['DatasetExternalID'] == datasetID]
            if 'PRISM' in list(datasets['DatasetAgency']):
                datasets = datasets[datasets['DatasetAgency'] == 'PRISM']
            elif 'NRCC' in list(datasets['DatasetAgency']):
                datasets = datasets[datasets['DatasetAgency'] == 'NRCC']
            else:
                print('no res')
                return
            print(datasets)
            self.datasetTable = self.datasetTable.append(datasets, ignore_index=False)
            self.datasetTable.drop_duplicates(keep='first', inplace=True)
            self.loadSelectedDatasets(self.datasetTable, self.datasetTab.selectedDatasetsWidget)
            numDatasets = len(self.datasetTable)
            self.datasetTab.selectedDatasetsLabel.setText("{0} datasets have been selected:".format(numDatasets))
            return

        if datasetID in list(self.datasetTable.index):
            return

        dataset = self.searchableDatasetsTable.loc[datasetID]
        self.datasetTable = self.datasetTable.append(dataset, ignore_index=False)
        self.loadSelectedDatasets(self.datasetTable, self.datasetTab.selectedDatasetsWidget)

        numDatasets = len(self.datasetTable)
        self.datasetTab.selectedDatasetsLabel.setText("{0} datasets have been selected:".format(numDatasets))

        for result in self.datasetTable.iterrows():
            self.datasetTab.searchResultsBox.updateAddedStatus(result[0], 'added')

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
            self.searchableDatasetsTable = pd.read_excel("resources/GIS/PointDatasets.xlsx", index_col=0)

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
            if result[0] in list(self.datasetTable.index):
                self.datasetTab.searchResultsBox.updateAddedStatus(result[0], 'added')
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