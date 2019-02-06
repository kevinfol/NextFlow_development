from resources.modules.Miscellaneous import ConfigurationParsing, loggingAndErrors
import time
import pandas as pd
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

        option:
            FreshDownload: Overwrite any existing data and download up to current date ("application_datetime" from config)
            UpdateStaleData: Append any updated or changed data to 
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
        i = 0
        while True:
            time.sleep(1)
            i = i + 10
            self.dataTab.downloadProgressBar.setValue(i)
            if i == 100:
                break
        self.dataTab.downloadProgressBar.hide()

        # 4. Download Data For each dataset and append to dataTable

        return
