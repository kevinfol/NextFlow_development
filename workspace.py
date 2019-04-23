dateparser = lambda x: pd.to_datetime(x) if x != '2019-02-29' else pd.to_datetime(np.nan)
dataframe = pd.read_csv(url, parse_dates=True, date_parser=dateparser)