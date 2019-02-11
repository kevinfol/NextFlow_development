import pyqtgraph as pg
from pyqtgraph.Qt import QtGui, QtCore
from pyqtgraph.Point import Point
from PyQt5 import QtWidgets
import numpy as np
import pandas as pd
import time

class TimeAxisItem(pg.AxisItem):
    """
    """
    def __init__(self, *args, **kwargs):
        """
        """
        super(TimeAxisItem, self).__init__(*args, **kwargs)
    
    def tickStrings(self, values, scale, spacing):
        """
        Rename the tick strings from EPOCH integers to datetime strings
        """
        return [time.strftime('%Y-%m-%d', time.localtime(value/1000000000)) for value in values]
        #return [value.strftime('%Y-%m-%d') for value in values]

class TimeSeriesSliderPlot(pg.GraphicsWindow):
    """
    Example taken from pyqtgraph/examples/crosshair.py
    """
    def __init__(self):
        super(TimeSeriesSliderPlot, self).__init__()
        
        # Create plots
        self.p1 = self.addPlot(row=0, col=0, axisItems={"bottom":TimeAxisItem(orientation="bottom")})
        self.p2 = self.addPlot(row=1, col=0, axisItems={"bottom":TimeAxisItem(orientation="bottom")})

        # Create the slider region
        self.region = pg.LinearRegionItem()
        self.region.setZValue(10)

        self.p2.addItem(self.region, ignoreBounds=True)
        self.p1.setAutoVisible(y=True)

        self.region.sigRegionChanged.connect(self.update)
        self.p1.sigRangeChanged.connect(self.updateRegion)

        self.vline = pg.InfiniteLine(angle=90, movable=False)
        self.hline = pg.InfiniteLine(angle=0, movable=False)
        self.p1.addItem(self.vline, ignoreBounds=True)
        self.p1.addItem(self.hline, ignoreBounds=True)

        proxy = pg.SignalProxy(self.p1.scene().sigMouseMoved, rateLimit=60, slot=self.mouseMoved)

    def mouseMoved(self, event):
        pos = event[0]
        if self.p1.sceneBoundingRect().contains(pos):
            mousePoint = self.p1.vb.mapSceneToView(pos)
            self.vline.setPos(mousePoint.x())
            self.hline.setPos(mousePoint.y())
        

    def update(self):
        self.region.setZValue(10)
        minX, maxX = self.region.getRegion()
        self.p1.setXRange(minX, maxX, padding=0)
    
    def updateRegion(self, window, viewRange):
        rgn = viewRange[0]
        self.region.setRegion(rgn)
    
    def add_data_to_plots(self, dataFrame, types = None):
        """
        """
        if len(types) != len(dataFrame.columns):
            return
        for col in dataFrame.columns:
            y = np.array(dataFrame[col].values, dtype="float")
            x = np.array(dataFrame.index.get_level_values(0), dtype="int64")
            print(y)
            missing = np.isnan(y)
            self.p2.plot(pen='w').setData(x=list(x[~missing]), y=list(y[~missing]))
        self.region.setRegion([x[0], x[-1]])

        return


if __name__ == '__main__':
    import sys
    
    app = QtWidgets.QApplication(sys.argv)
    mw = TimeSeriesSliderPlot()
    df = pd.DataFrame(np.random.random((31,3)), columns=['A','B','C'], index=pd.date_range('2018-10-01','2018-10-31'))
    df.set_index(pd.Int64Index(df.index.astype(np.int64)))
    df['C'] = 3*df['C']
    df['B'] = -2*df['B']-1
    mw.add_data_to_plots(df, types = ['scatter','line','bar'])
    mw.show()
    sys.exit(app.exec_())