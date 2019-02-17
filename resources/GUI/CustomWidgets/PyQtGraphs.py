import pyqtgraph as pg
from pyqtgraph.Qt import QtGui, QtCore
from pyqtgraph.Point import Point
from PyQt5 import QtWidgets
import numpy as np
import pandas as pd
from datetime import datetime
from pyqtgraph.graphicsItems.LegendItem import LegendItem, ItemSample

def updateSize_(self):
    if self.size is not None:
        return
        
    height = 0
    width = 0
    #print("-------")
    for sample, label in self.items:
        height += max(sample.boundingRect().height(), label.height()) + 3
        width = max(width, sample.boundingRect().width()+label.width())
        #print(width, height)
    #print width, height
    self.setGeometry(0, 0, width+25, height)

def addItem_(self, item, name):
    label = pg.LabelItem(name, justify='left')
    if isinstance(item, ItemSample):
        sample = item
    else:
        sample = ItemSample(item)        
    row = self.layout.rowCount()
    self.items.append((sample, label))
    self.layout.addItem(sample, row, 0)
    self.layout.addItem(label, row, 1)
    self.updateSize()

pg.setConfigOption('background', 'w')
pg.setConfigOption('foreground', 'k')

LegendItem.addItem = addItem_
LegendItem.updateSize = updateSize_
LegendItem.mouseDragEvent = lambda s, e: None

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
        if maxVal - minVal >= 15*365.24*86400:
            return [(10*365.24*86400, 0), (10*365.24*86400, 0)]
        elif maxVal - minVal >= 6*365.24*86400:
            return [(4*365.24*86400, 0), (4*365.24*86400, 0)]
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
        if spacing > 7*365.24*86400:
            return [datetime.utcfromtimestamp(value).strftime('%Y-%m') for value in values]
        return [datetime.utcfromtimestamp(value).strftime('%Y-%m-%d') for value in values]

class TimeSeriesSliderPlot(pg.GraphicsLayoutWidget):
    """
    Example taken from pyqtgraph/examples/crosshair.py
    """
    def __init__(self):
        super(TimeSeriesSliderPlot, self).__init__()
        
        
        # Create plots
        self.p1 = self.addPlot(row=0, col=0, rowspan=8, axisItems={"bottom":TimeAxisItem(orientation="bottom")})
        self.p2 = self.addPlot(row=8, col=0, axisItems={"bottom":TimeAxisItem(orientation="bottom")})
        
        [self.ci.layout.setRowMinimumHeight(i, 50) for i in range(9)]
        # Create the slider region
        self.region = pg.LinearRegionItem()
        self.region.setZValue(10)
        self.p1.addLegend()
        self.p2.addItem(self.region, ignoreBounds=True)
        self.p1.setMenuEnabled(False)
        self.p2.setMenuEnabled(False)
        
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
            x_ = mousePoint.x()
            y_ = mousePoint.y()
            idx = int(x_ - x_%86400)
            ts = datetime.utcfromtimestamp(idx).strftime('%Y-%m-%d')
            if hasattr(self, "crossHairText"):
                self.crossHairText.setText(ts + '\n' + str(np.round(y_,2)))
                self.crossHairText.setPos(x_, y_)
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
    
    def add_data_to_plots(self, dataFrame, types = None, fill_below=True, keep_bounds = False, changed_col = None):
        """
        """
        
        cc = colorCycler()
        self.dataFrame = dataFrame.apply(lambda x: pd.to_numeric(x, errors='coerce'))
        self.dataFrame.set_index(pd.Int64Index(self.dataFrame.index.astype(np.int64)), inplace=True)
        self.dataFrame.index = self.dataFrame.index/1000000000
        mn = min(self.dataFrame.min())
        mx = max(self.dataFrame.max())
        rg = mx - mn
        xmn = self.dataFrame.index.get_level_values(0)[0]
        xmx = self.dataFrame.index.get_level_values(0)[-1]
        xrg = xmx - xmn
        if keep_bounds:
            current_bounds = self.p1.vb.viewRange()
            y = np.array(self.dataFrame[changed_col].values, dtype="float")
            x = np.array(self.dataFrame.index.get_level_values(0), dtype="int64")
            missing = np.isnan(y)
            x_ = x[~missing]
            y_ = y[~missing]
            dataItemsP1 = self.p1.listDataItems()
            dataItemsP1Names = [item.opts['name'] for item in dataItemsP1]
            dataItemsP2 = self.p2.listDataItems()
            dataItemsP2Names = [item.opts['name'] for item in dataItemsP2]
            p1Item = dataItemsP1[dataItemsP1Names.index(changed_col)]
            p2Item = dataItemsP2[dataItemsP2Names.index(changed_col)]
            p1Item.setData(x_, y_, antialias=True)
            p2Item.setData(x_, y_, antialias=True)
            self.p1.vb.setRange(xRange = current_bounds[0], yRange = current_bounds[1])
            return

        [self.p1.removeItem(i) for i in self.p1.listDataItems()]
        [self.p2.removeItem(i) for i in self.p2.listDataItems()]
        self.p1.legend.scene().removeItem(self.p1.legend)
        if hasattr(self, "crossHairText"):
            self.p1.removeItem(self.crossHairText)
        self.p1.addLegend()
        self.p2.setLimits(  xMin = xmn, 
                            xMax = xmx, 
                            yMin = mn, 
                            yMax = mx,
                            minXRange = xrg,
                            minYRange = rg)
        self.p1.setLimits(  xMin = xmn, 
                            xMax = xmx, 
                            yMin = mn - rg/5, 
                            yMax = mx + rg/5,
                            maxYRange = rg + 2*rg/5)
        self.p1.setRange(yRange = [mn, mx])
        if types == None:
            types = ['line' for col in dataFrame.columns]
        if len(types) != len(dataFrame.columns):
            return
        for i, col in enumerate(self.dataFrame.columns):
            y = np.array(self.dataFrame[col].values, dtype="float")
            x = np.array(self.dataFrame.index.get_level_values(0), dtype="int64")
            missing = np.isnan(y)
            x_ = x[~missing]
            y_ = y[~missing]
            if types[i] == 'bar':
                x_ = np.append(x_, x_[-1])
                self.p2.plot(x=x_, y=y_, pen='k', stepMode = True, fillLevel=0,  brush=cc.getColor(i), name=col, antialias=True)
                self.p1.plot(x=x_, y=y_, pen='k', stepMode = True, fillLevel=0,  brush=cc.getColor(i), name=col, antialias=True)
            elif types[i] == 'line' and fill_below==True:
                self.p2.plot(x=x_, y=y_, pen='k', fillLevel = 0, brush=cc.getColor(i), name=col, antialias=True)
                self.p1.plot(x=x_, y=y_, pen='k', fillLevel = 0, brush=cc.getColor(i), name=col, antialias=True)
            elif types[i] == 'scatter':
                self.p2.plot(x=x_, y=y_, pen='k', symbol='o', name=col, antialias=True)
                self.p1.plot(x=x_, y=y_, pen='k', symbol='o', name=col, antialias=True)
            
        self.region.setRegion([x_[0], x_[-1]])
        self.region.setBounds([x_[0], x_[-1]])
        self.region.setZValue(10)
        self.crossHairText = pg.TextItem(anchor=(0,1), color = (45,45,45))
        self.p1.addItem(self.crossHairText)

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