from PyQt5 import QtWidgets
def showErrorMessage(parent, msg):
        """
        """
        print(msg)
        errorMsg = QtWidgets.QMessageBox.warning(parent, "Error", msg)