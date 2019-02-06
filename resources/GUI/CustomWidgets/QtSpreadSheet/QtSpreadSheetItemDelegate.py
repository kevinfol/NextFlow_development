from PyQt5.QtWidgets import QStyledItemDelegate
from PyQt5.QtCore import Qt, pyqtSignal

class QSpreadSheetItemDelegate(QStyledItemDelegate):

    textEditedSignal = pyqtSignal(str)

    def __init__(self, parent=None):
        QStyledItemDelegate.__init__(self)
    
    def createEditor(self, parent, option, index):
        self.index = index
        self.editor = QStyledItemDelegate.createEditor(self, parent, option, index)
        self.editor.textEdited.connect(self.emitText)
        return self.editor
    
    def emitText(self, textToEmit):
        self.textEditedSignal.emit(textToEmit)