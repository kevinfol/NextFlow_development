from resources.modules.Miscellaneous import ConfigurationParsing, loggingAndErrors
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
        """
        self.dataTab.porT2.setText(datetime.strftime(pd.to_datetime(ConfigurationParsing.readConfig('application_datetime')), '%Y'))
        self.dataTab.downloadButton.clicked.connect(self.downloadData)
        self.dataTab.updateButton.clicked.connect(lambda: self.downloadData(option="UpdateStaleData"))

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
            porT2 = pd.to_datetime(ConfigurationParsing.readConfig('application_datetime'))
        except Exception as E:
            loggingAndErrors.showErrorMessage('Could not parse POR input: {0}'.format(E))
            return

        # 2. Validate Dataset Table
        if self.datasetTable.empty:
            loggingAndErrors.showErrorMessage('No datasets Selected')
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
            loggingAndErrors.showErrorMessage('Could not download data: {0}'.format(E))
            self.dataTab.downloadProgressBar.hide()

        return

    def downloadFinished(self):
        """
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
        self.dataTable.append(newValues, inplace=True)

        # Add the updated data to the datatable
        updatedValues = pd.DataFrame(merged[merged['_merge'] == 'both']['Value_new'])

        # update the original data table with the changed data
        #for data_row in merged.iterrows():
        for i in range(len(merged)):
            idx = merged.index[i]
            data_row = (idx, merged.loc[idx])
            if i == len(merged) - 1:
                print(data_row[1]['Value_old'] == np.nan)
                print(data_row[1]['_merge'] == 'right_only')
            
            if np.isnan(data_row[1]['Value_old']) and data_row[1]['_merge'] == 'right_only':
                # This is a new value that was not in the original data table. We append it directly with a version of '0'
                self.dataTable.loc[tuple([data_row[0][0], data_row[0][1], 0]), 'Value'] = [data_row[1]['Value_new']]
                continue
            
            if data_row[1]['_merge'] == 'both':
                # We have an updated value for a dataset. We set the old data value to version 1 and append the new value with version 0
                self.dataTable.loc[tuple([data_row[0][0], data_row[0][1], 1]), 'Value'] = [data_row[1]['Value_old']]
                self.dataTable.loc[tuple([data_row[0][0], data_row[0][1], 0]), 'Value'] = [data_row[1]['Value_new']]
                continue
            
        print(self.dataTable)
        return