import pandas as pd
from datetime import datetime, timedelta
import isodate
import numpy as np

def resampleDataSet(dailyData, resampleString, resampleMethod, customFunction = None):
    """
    This function resamples a dataset (daily timestep) into
    a time series based on the resample string

    resample strings are formatted as follows (follwing ISO 8601)
    
    R/ -> specifies repeating interval
    YYYY-MM-DD/ -> specifies start date of repeating interval
    PnM/ -> specifies duration of repeating interval in months
    FnM -> specifies frequency of repetition (e.g. once a year)

    For example, to represent a parameter that would be resampled from daily data 
    into a March Average timeseries with one value per year, you could use:

    R/1978-03-01/P1M/F12M

    Or if you wanted a period in February that always left out February 29th, you could specify:
    
    R/1984-02-01/P28D/F1Y    (Note the frequency F12M is the same as frequency F1Y)

    Input: 
        dailyData -> pandas Series of daily-intervaled data
        resampleString -> ISO8601 formatted resampling string (e.g. R/1978-02-01/P1M/F1Y)
        resampleMethod -> One of 'accumulation', 'average', 'first', 'last', 'max', 'min', 'custom'

        customFunction (optional) ->  if 'resampleMethod' is 'custom', you can enter a custom written 
                                      python function (as a string) to be applied to the series. Use 
                                      the variable "x" to represent the time series. 

                                      I.e. "np.mean(x) / np.std(x)" would return z-scores
    
    Output:
        resampledData -> data resampled based on format string
    """

    # Create a new empty series
    resampleData = pd.Series([], index = pd.DatetimeIndex([]))

    # Parse the resample string
    resampleList = resampleString.split('/') # Converts 'R/1978-10-01/P1M/F1Y' into ['R', '1978-10-01', 'P1M', 'F1Y']

    # Validate the list
    if len(resampleList) != 4 or resampleList[0] != 'R' or len(resampleList[1]) != 10 or resampleList[2][0] != 'P' or resampleList[3][0] != 'F':
        return resampleData, 1, 'Invalid Resample String. Format should be similar to R/1978-10-01/P1M/F1Y'
    
    # Validate the resample method
    if resampleMethod not in ['accumulation', 'average', 'first', 'last', 'max', 'min', 'custom']:
        return resampleData, 1, "Invalid resampling method. Provide one of 'accumulation', 'average', 'first', 'last', 'max', 'min', 'custom'"

    # Parse into values
    startDate = datetime.strptime(resampleList[1], '%Y-%m-%d') # >>> datetime.date(1978, 10, 1)
    period = isodate.parse_duration(resampleList[2]) # >>> isodate.duration.Duration(0, 0, 0, years=0, months=1)
    frequency = isodate.parse_duration(resampleList[3].replace('F', 'P')) # >>> isodate.duration.Duration(0, 0, 0, years=1, months=1)

    # Create all the periods
    periods = []
    tracker = startDate
    while tracker <= datetime.now(): # >>> periods = [(datetime.datetime(1978-10-01), datetime.datetime(1978-11-01))]
        periods.append((tracker, tracker+period))#-timedelta(1)))
        tracker += frequency

    # Parse the function
    func = lambda x: np.nanmean(x) if resampleMethod == 'average' else (
        np.nansum(x) if resampleMethod == 'accumulation' else (
            x.iloc[0][0] if resampleMethod == 'first' else (
                x.iloc[-1][0] if resampleMethod == 'last' else eval(customFunction))))

    # Resample the data
    for idx in pd.IntervalIndex.from_tuples(periods):
        resampleData.loc[idx.left] = func(dailyData.loc[idx.left:idx.right])

    return resampleData, 0, 'Procedure Exited Normally'