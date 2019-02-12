import pyqtgraph as pg
from pyqtgraph.Qt import QtGui, QtCore
from pyqtgraph.Point import Point
from PyQt5 import QtWidgets
import numpy as np
import pandas as pd
from datetime import datetime

pg.setConfigOption('background', 'w')
pg.setConfigOption('foreground', 'k')

class TimeAxisItem(pg.AxisItem):
    """
    """
    def __init__(self, *args, **kwargs):
        """
        """
        super(TimeAxisItem, self).__init__(*args, **kwargs)

    def tickSpacing(self, minVal, maxVal, size):
        """
        """
        if maxVal - minVal >= 10*365.24*86400:
            return [(10*365.24*86400, 0), (10*365.24*86400, 0)]
        elif maxVal - minVal >= 365.24*86400:
            return [(365.24*86400, 0), (365.24*86400, 0)]
        elif maxVal - minVal >= 45*86400:
            return [(31*86400, 0), (31*86400, 0)]
        elif maxVal - minVal >= 26*86400:
            return [(20*86400, 0), (20*86400, 0)]
        elif maxVal - minVal < 100:
            return [(10,0), (1, 0)]
        elif maxVal - minVal >= 15*86400:
            return [(12*86400, 0), (12*86400, 0)]
        elif maxVal - minVal >= 8*86400:
            return [(4*86400, 0), (4*86400, 0)]
        else:
            return [(86400,0), (86400,0)]

    def tickStrings(self, values, scale, spacing):
        """
        Rename the tick strings from EPOCH integers to datetime strings
        """
        return [datetime.utcfromtimestamp(value).strftime('%Y-%m-%d') for value in values]

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
        self.p1.addLegend()
        self.p2.addLegend()
        self.p2.addItem(self.region, ignoreBounds=True)
        #self.p1.setAutoVisible(y=True)

        self.region.sigRegionChanged.connect(self.update)
        self.p1.sigRangeChanged.connect(self.updateRegion)

        self.vline = pg.InfiniteLine(angle=90, movable=False)
        self.hline = pg.InfiniteLine(angle=0, movable=False)
        self.p1.addItem(self.vline, ignoreBounds=True)
        self.p1.addItem(self.hline, ignoreBounds=True)

        self.p1.scene().sigMouseMoved.connect(self.mouseMoved)

    def mouseMoved(self, event):
        pos = QtCore.QPoint(event.x(), event.y())
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
        self.region.setZValue(10)
        self.region.setRegion(rgn)
    
    def add_data_to_plots(self, dataFrame, types = None, fill_below=True):
        """
        """
        [self.p1.removeItem(i) for i in self.p1.listDataItems()]
        [self.p2.removeItem(i) for i in self.p2.listDataItems()]
        self.p1.legend.scene().removeItem(self.p1.legend)
        self.p2.legend.scene().removeItem(self.p2.legend)
        self.p1.addLegend()
        self.p2.addLegend()
        cc = colorCycler()
        dataFrame = dataFrame.apply(lambda x: pd.to_numeric(x, errors='coerce'))
        dataFrame.set_index(pd.Int64Index(dataFrame.index.astype(np.int64)), inplace=True)
        dataFrame.index = dataFrame.index/1000000000
        if types == None:
            types = ['line' for col in dataFrame.columns]
        if len(types) != len(dataFrame.columns):
            return
        for i, col in enumerate(dataFrame.columns):
            y = np.array(dataFrame[col].values, dtype="float")
            x = np.array(dataFrame.index.get_level_values(0), dtype="int64")
            missing = np.isnan(y)
            x_ = x[~missing]
            y_ = y[~missing]
            if types[i] == 'bar':
                x_ = np.append(x_, x_[-1])
                self.p2.plot(x=x_, y=y_, pen='k', stepMode = True, fillLevel=0,  brush=cc.getColor(i), name=col)
                self.p1.plot(x=x_, y=y_, pen='k', stepMode = True, fillLevel=0,  brush=cc.getColor(i), name=col)
            elif types[i] == 'line' and fill_below==True:
                self.p2.plot(x=x_, y=y_, pen='k', fillLevel = 0, brush=cc.getColor(i), name=col)
                self.p1.plot(x=x_, y=y_, pen='k', fillLevel = 0, brush=cc.getColor(i), name=col)
            elif types[i] == 'scatter':
                self.p2.plot(x=x_, y=y_, pen='k', symbol='o', name=col)
                self.p1.plot(x=x_, y=y_, pen='k', symbol='o', name=col)
            
        self.region.setRegion([x_[0], x_[-1]])
        self.region.setZValue(10)

        return

class colorCycler():
    def __init__(self):
        self.colors = [
            (228,26,28,150),
            (55,126,184,150),
            (77,175,74,150),
            (152,78,163,150),
            (255,127,0,150),
            (255,255,51,150),
            (166,86,40,150),
            (247,129,191,150)]

    def getColor(self, i):
        return self.colors[i%len(self.colors)]

if __name__ == '__main__':
    import sys
    
    app = QtWidgets.QApplication(sys.argv)
    mw = TimeSeriesSliderPlot()
    df = pd.DataFrame(np.random.random((31,3)), columns=['A','B','C'], index=pd.date_range('2018-10-01','2018-10-31'))
    df['C'] = 3*df['C']
    df['B'] = -2*df['B']-1
    df['A'] = -1*df['A']
    mw.add_data_to_plots(df, types = ['scatter','line','bar'])
    mw.show()
    sys.exit(app.exec_())