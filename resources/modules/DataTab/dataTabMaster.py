from resources.modules.Miscellaneous import loggingAndErrors
from resources.modules.DataTab import downloadData
import time
import pandas as pd
import numpy as np
from datetime import datetime

class dataTab(object):
    """
    """
    def setupDataTab(self):
        """
        Initializes the data tab and connect the data tab events.
        """
        self.dataTab.porT2.setText(datetime.strftime(pd.to_datetime(self.applicationPrefsConfig['GENERAL']['application_datetime']), '%Y'))
        self.dataTab.downloadButton.clicked.connect(self.downloadData)
        self.dataTab.updateButton.clicked.connect(lambda: self.downloadData(option="UpdateStaleData"))
        self.currentlyPlottedColumns = []

        return


    def resetDataTab(self):
        """
        """
        if self.dataTable.empty:
            return
        self.displayDataInTable()
        self.dataTab.porT2.setText(datetime.strftime(pd.to_datetime(self.applicationPrefsConfig['GENERAL']['application_datetime']), '%Y'))
        self.currentlyPlottedColumns = self.userOptionsConfig['DATA TAB']['current_plotted_columns'].split(',')
        self.plotClickedColumns(self.currentlyPlottedColumns)
        current_bounds = self.userOptionsConfig['DATA TAB']['current_plot_bounds'].split(',')
        self.dataTab.dataPlot.p1.vb.setRange(xRange = [float(current_bounds[0]),float(current_bounds[1])], yRange = [float(current_bounds[2]),float(current_bounds[3])])

        return
    

    def storeDataTabInformation(self):
        """
        Stores the current settings for the plot and datetimes that the user has set. 
        """
        self.userOptionsConfig['DATA TAB']['por_start'] = self.dataTab.porT1.text()
        self.userOptionsConfig['DATA TAB']['current_plotted_columns'] = ','.join(self.currentlyPlottedColumns)
        self.userOptionsConfig['DATA TAB']['current_plot_bounds'] = ','.join(str(x) for x in self.dataTab.dataPlot.p1.vb.viewRange()[0]) + ',' + ','.join(str(x) for x in self.dataTab.dataPlot.p1.vb.viewRange()[1])
        
        return
        

    def downloadData(self, option='FreshDownload'):
        """
        1. Validates the POR input.
        2. Validates the Datasets Table
        3. Instantiates a Progress Bar
        4. Downloads data for each dataset in datasets table and appends to dataTable
            4.1. If 'UpdateStaleData' is specified, compare new data to old data and, if different, create a new version in data table. 

        option (passed to postProcessNewData):
            FreshDownload: Overwrite any existing data and download up to current date ("application_datetime" from config)
            UpdateStaleData: Append any updated or changed data to the datatable, including new datasets
        """

        # 1. Validate POR input
        porT1 = self.dataTab.porT1.text()
        porT2 = self.dataTab.porT2.text()
        try:
            porT1 = pd.to_datetime(porT1+'-10-01')
            porT2 = pd.to_datetime(self.applicationPrefsConfig['GENERAL']['application_datetime'])
        except Exception as E:
            loggingAndErrors.showErrorMessage(self, 'Could not parse POR input: {0}'.format(E))
            return

        # 2. Validate Dataset Table
        if self.datasetTable.empty:
            loggingAndErrors.showErrorMessage(self, 'No datasets Selected')
            return
        
        # 3. Instantiate Progress Bar
        self.dataTab.downloadProgressBar.show()

        # 4. Download Data For each dataset and append to dataTable
        try:
            downloadWorker = downloadData.alternateThreadWorker(self.datasetTable, porT1, porT2)
            downloadWorker.signals.updateProgBar.connect(self.dataTab.downloadProgressBar.setValue)
            downloadWorker.signals.returnNewData.connect(lambda x: self.postProcessNewData(x, option))
            downloadWorker.signals.finished.connect(self.downloadFinished)
            self.threadPool.start(downloadWorker)
        except Exception as E:
            loggingAndErrors.showErrorMessage(self, 'Could not download data: {0}'.format(E))
            self.dataTab.downloadProgressBar.hide()

        return


    def downloadFinished(self):
        """
        Hide the progress bar after the data finishes downloading
        """
        self.dataTab.downloadProgressBar.hide()

        return


    def postProcessNewData(self, newDataTable, option):
        """
        """

        # First create a merged dataTable
        merged = pd.merge(left=self.dataTable, right=newDataTable, on=['Datetime','DatasetInternalID'], suffixes=('_old','_new'), indicator=True, how='outer')
        
        # Filter to only get the changed data
        merged = merged[merged.Value_old != merged.Value_new]

        # Add brand new data to the datatable
        newValues = pd.DataFrame(merged[(np.isnan(merged['Value_old'])) & (merged['_merge'] == 'right_only')]['Value_new'])
        newValues.columns = ['Value']
        newValues.set_index([newValues.index, pd.Index(len(newValues)*[0])], inplace=True)
        newValues.index.names = ['Datetime','DatasetInternalID','Version']
        self.dataTable = self.dataTable.append(newValues)
        self.dataTable = self.dataTable[~self.dataTable.index.duplicated(keep='last')]

        # Add the updated data to the datatable
        updatedValuesNew = pd.DataFrame(merged[merged['_merge'] == 'both']['Value_new'])
        updatedValuesOld = pd.DataFrame(merged[merged['_merge'] == 'both']['Value_old'])
        updatedValuesNew.columns = ['Value']
        updatedValuesOld.columns = ['Value']
        updatedValuesNew.set_index([updatedValuesNew.index, pd.Index(len(updatedValuesNew)*[0])], inplace=True)
        updatedValuesOld.set_index([updatedValuesOld.index, pd.Index(len(updatedValuesOld)*[1])], inplace=True)
        updatedValuesNew.index.names = ['Datetime','DatasetInternalID','Version']
        updatedValuesOld.index.names = ['Datetime','DatasetInternalID','Version']
        self.dataTable = self.dataTable.append(updatedValuesNew)
        self.dataTable = self.dataTable.append(updatedValuesOld)
        self.dataTable = self.dataTable[~self.dataTable.index.duplicated(keep='last')]
        self.displayDataInTable()

        return

    
    def displayDataInTable(self):
        """
        This function takes the dataTable and converts it into a spreadsheet-like datatable. 
        """
        if self.dataTable.empty:
            return
        self.dataDisplayTable = self.dataTable.loc[pd.IndexSlice[:,:,0], :] # Returns only the "0"-version data
        self.dataDisplayTable.set_index([self.dataDisplayTable.index.get_level_values(0), self.dataDisplayTable.index.get_level_values(1)], inplace=True) # Remove the version index
        self.dataDisplayTable = self.dataDisplayTable.unstack(level=1)['Value'] # Pivot table to columned-datasets / datetime index
        self.dataDisplayTable.columns = [self.datasetTable.loc[i]['DatasetName'] for i in list(self.dataDisplayTable.columns)]
        self.dataTab.table.model().load_new_dataset(self.dataDisplayTable, suppress_column_names=False, display_index_col=True, index_col_name='Datetime')
        self.dataTab.table.model().changedDataSignal.connect(self.userChangedData)
        self.dataTab.table.horizontalHeader().sectionClicked.connect(lambda x: self.plotClickedColumns())
        self.plotClickedColumns([self.dataDisplayTable.columns[0]])

        return


    def userChangedData(self, dataChanges):
        """
        This function is triggered whenever a user changes the data in the table. 
        It updates the global data table and triggers updates in the resmapled tables
        as well as in any associated forecasts. 

        dataChanges: list of changed data, i.e [date, columnName, oldValue, newValue]
        """
        old_value = self.dataDisplayTable.loc[dataChanges[0]][dataChanges[1]]
        if dataChanges[2] == old_value:
            self.dataDisplayTable.loc[dataChanges[0]][dataChanges[1]] = dataChanges[3]
            try:
                value = float(dataChanges[3])
            except:
                value = np.nan
            self.dataTable.loc[pd.IndexSlice[dataChanges[0], dataChanges[1], 1]] = old_value
            self.dataTable.loc[pd.IndexSlice[dataChanges[0], dataChanges[1], 0]] = value
        self.plotClickedColumns(displayColumns=self.currentlyPlottedColumns, keep_current_bounds=True, changed_col=dataChanges[1])

        return


    def plotClickedColumns(self, displayColumns = None, keep_current_bounds = False, changed_col = None):
        """
        This function plots the columns that the user selects
        """
        currentDataset = self.dataTab.table.getCurrentDataFrame()
        if displayColumns != None:
            self.currentlyPlottedColumns = displayColumns
        else:
            self.currentlyPlottedColumns = self.dataTab.table.getSelectedColumns()
            if self.currentlyPlottedColumns == [] or self.currentlyPlottedColumns == None:
                return
        dataset = currentDataset[self.currentlyPlottedColumns]
        self.dataTab.dataPlot.add_data_to_plots(dataset, keep_bounds = keep_current_bounds, changed_col = changed_col)

        return
            