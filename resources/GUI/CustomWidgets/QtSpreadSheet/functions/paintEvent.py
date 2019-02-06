from PyQt5.QtGui        import  (QColor,
                                QPainter,
                                QBrush,
                                QPen)

from PyQt5.QtCore       import  (Qt,
                                QModelIndex,
                                QRect)

from PyQt5.QtWidgets    import  (QTableView)

def paintEvent(self, event):
        """
        This function is responsible for drawing borders around the selection and
        adding the fill handle to selections.
        """
        
        QTableView.paintEvent(self, event)
        painter = QPainter(self.viewport()) # Get the widget's QPainter
        painter.save()
        selections = self.selectionModel().selection()
        if selections == []:
            return
        for selection in selections:
            # Paint a border around all selections
            cell_top_left = self.visualRect(QModelIndex(selection.topLeft()))
            cell_bottom_right = self.visualRect(QModelIndex(selection.bottomRight()))
            new_rect = QRect(cell_top_left.topLeft(), cell_bottom_right.bottomRight())
            new_rect.setLeft(new_rect.left()-1)
            new_rect.setRight(new_rect.right()+1)
            new_rect.setTop(new_rect.top()-1)
            new_rect.setBottom(new_rect.bottom()+1)
            pen = QPen(QBrush(self.highlightColor), 2, join=Qt.MiterJoin)
            painter.setBrush(Qt.NoBrush)
            painter.setPen(pen)
            painter.drawRect(new_rect)

        if len(selections) == 1:
            # Paint a fill handle on the bottom of selection
            self.fillHandleRect = QRect(cell_bottom_right.bottomRight().x() - 2, cell_bottom_right.bottomRight().y() - 2, 6, 6)
            painter.setBrush(self.highlightColor)
            pen = QPen(QBrush(QColor(255,255,255)), 1, join=Qt.MiterJoin)
            painter.setPen(pen)
            painter.drawRect(self.fillHandleRect)

        painter.restore()
        self.viewport().update()

        return
