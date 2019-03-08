"""
Script Name:    dataTabMaster.py
Description:    This script contains all the functionality behind the User interface of the Data Tab.
"""
from resources.modules.Miscellaneous import loggingAndErrors
from resources.modules.DataTab import downloadData
from resources.GUI.Dialogs.conflictReviewDialog import conflictReviewDialog
import time
import pandas as pd
import numpy as np
from datetime import datetime

class dataTab(object):

    def setupDataTab(self):
        """
        Initializes the data tab and connect the data tab events.
        """
        self.dataTab.porT2.setText(datetime.strftime(pd.to_datetime(self.applicationPrefsConfig['GENERAL']['application_datetime']), '%Y'))
        self.dataTab.downloadButton.clicked.connect(self.downloadData)
        self.currentlyPlottedColumns = []

        return

    def resetDataTab(self):
        """
        Resets the data tab to a previous configuration based on the data in the 'userOptionsConfig'
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
        

    def downloadData(self):
        """
        1. Validates the POR input.
        2. Validates the Datasets Table
        3. Instantiates a Progress Bar
        4. Downloads data for each dataset in datasets table and appends to dataTable
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
            downloadWorker.signals.returnNewData.connect(lambda x: self.postProcessNewData(x))
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

    def importDataset(self):
        """
        """

        return

    def postProcessNewData(self, newDataTable):
        """
        """

        # First create a merged dataTable
        merged = pd.merge(left=self.dataTable, right=newDataTable, on=['Datetime','DatasetInternalID'], suffixes=('_old','_new'), indicator=True, how='outer')
        
        # Filter to only get the changed data
        merged = merged[merged.Value_old != merged.Value_new]

        # Add brand new data to the datatable
        newValues = pd.DataFrame(merged[(np.isnan(merged['Value_old'])) & (merged['_merge'] == 'right_only')][['Value_new', 'EditFlag']])
        newValues.columns = ['Value', 'EditFlag']
        newValues['EditFlag'] = [False] * len(newValues)
        self.dataTable = self.dataTable.append(newValues)
        self.dataTable = self.dataTable[~self.dataTable.index.duplicated(keep='last')]

        # Figure out which values are updated and don't need to be validated by the user
        updatedValuesNew = pd.DataFrame(merged[(merged['_merge'] == 'both') & (merged['Value_new'] != merged['Value_old']) & (merged['EditFlag'] == False)][['Value_new', 'EditFlag']])
        updatedValuesNew.columns = ['Value', 'EditFlag']
        self.dataTable = self.dataTable.append(updatedValuesNew)
        self.dataTable = self.dataTable[~self.dataTable.index.duplicated(keep='last')]

        # find the updated values that are replacing unedited original data
        #updatedValuesNew_need_validation = pd.DataFrame(merged[(merged['_merge'] == 'both') & (merged['Value_new'] != merged['Value_old']) & (merged['EditFlag'] == True)][['Value_old', 'Value_new', 'EditFlag']])
        #if loggingAndErrors.displayDialog("We've downloaded data that conflicts with your edited data. Would you like to review the conflicts? If not, we'll overwrite your edits with the new data."):
            #self.conflictReviewDialog = conflictReviewDialog(df=updatedValuesNew_need_validation, datasets = self.datasetTable)
            # This part still needs work. Theres a lot of moving parts with checkboxes/etc. 

        #TEMPORARY
        updatedValuesNew_need_validation = pd.DataFrame(merged[(merged['_merge'] == 'both') & (merged['Value_new'] != merged['Value_old']) & (merged['EditFlag'] == True)][['Value_new', 'EditFlag']])
        updatedValuesNew_need_validation.columns = ['Value', 'EditFlag']
        self.dataTable = self.dataTable.append(updatedValuesNew_need_validation)
        self.dataTable = self.dataTable[~self.dataTable.index.duplicated(keep='last')]

        self.displayDataInTable()

        return

    
    def displayDataInTable(self):
        """
        This function takes the dataTable and converts it into a spreadsheet-like datatable. 
        """
        if self.dataTable.empty:
            return
        self.dataDisplayTable = pd.DataFrame(self.dataTable['Value']) 
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
        It updates the global data table and triggers updates in any associated forecasts. 

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

        # NOTE, NEED TO UPDATE ANY FORECASTS BASED ON THIS DATA

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
            