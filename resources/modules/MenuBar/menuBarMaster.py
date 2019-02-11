from resources.modules.Miscellaneous import ConfigurationParsing, loggingAndErrors
from resources.GUI.Dialogs import PreferencesGUI
from datetime import datetime

class menuBar(object):
    """
    """
    def setupMenuBar(self):
        """
        """
        self.appMenu.preferencesAction.triggered.connect(self.openPreferencesGUI)
        return
    
    def openPreferencesGUI(self):
        """
        """
        self.preferences = PreferencesGUI.preferencesDialog()
        #self.preferences.signals.returnNewPreferences.connect(self.applyNewPreferences)

    def applyNewPreferences(self):
        """
        """
        return

    