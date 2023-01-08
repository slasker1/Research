import matplotlib as mpl
import pandas as pd
import numpy as np  # we're using this for various math operations
from scipy import stats  # using this for the reg slope
import yfinance as yf
import matplotlib.pyplot as plt


def wwma(values, n):
    """
     J. Welles Wilder's EMA
    """
    return values.ewm(alpha=1/n, adjust=False).mean()

def atr(df, n=14):
    data = df.copy()
    high = data["High"]
    low = data["Low"]
    close = data["Close"]
    data['tr0'] = abs(high - low)
    data['tr1'] = abs(high - close.shift())
    data['tr2'] = abs(low - close.shift())
    tr = data[['tr0', 'tr1', 'tr2']].max(axis=1)
    atr = wwma(tr, n)
    return atr

def get_returns():

    ticker_data = yf.download(  # or pdr.get_data_yahoo(...
        # tickers list or string as well
        tickers="BTC-USD CELO-USD",
        period="max",
        interval="1d",
        group_by='ticker',
        auto_adjust=True,
        prepost=True,
        threads=True,
        proxy=None
    )

    dfSPY = ticker_data["BTC-USD"]
    dfTLT = ticker_data["CELO-USD"]

    return dfSPY, dfTLT

#calculate moving averages
#data['SMA100'] = data['Adj Close'].rolling(100).mean()
#data['SMA200'] = data['Adj Close'].rolling(200).mean()

#set to 1 if SPY is above SMA100
#data['Position'] = np.where(data['Adj Close'] > data['SMA100'], 1, 0)

# get spy and tlt time series from yahoo
dfSPY, dfTLT = get_returns()

print (dfSPY["Close"])

#plot the result
plt.style.use('seaborn-darkgrid')
plt.figure(figsize=(8,8))
#plt.plot(data['SMA100'], 'r--', label="SMA100")
#plt.plot(data['SMA200'], 'g--', label="SMA100")
#plt.plot(data['Adj Close'], label="close")
#plt.plot(data['Strategy'], 'g', Label= "Strategy")

rolling_correlation = dfSPY["Close"].pct_change().rolling(60).corr(dfTLT["Close"].pct_change())

change_in_corr = rolling_correlation.pct_change(periods = 5)



myATR = atr(dfTLT)

print(myATR)


#Position = np.where(rolling_correlation < sma100, "S", "B")


dfSPY['SMA100'] = dfSPY['Close'].rolling(100).mean()
PositionBear = np.where(dfSPY['Close'] < dfSPY['SMA100'], 1, 0)
#PositionWeight = np.where(stdev > meanSTD, "S", "B")
#PositionWeight= stdev


dfTLT['Price'] = dfTLT['Close']
#dfTLT['Position'] = Position
dfTLT['PositionBEAR'] = PositionBear
dfTLT['PositionWeight'] = rolling_correlation
print(dfTLT)

#dfTLT.to_excel("/Users/samlasker/PycharmProjects/AlphaGeneration/output2.xlsx")

#plt.plot(sma100, 'r--', label="SMA100")
#plt.plot(change_in_corr, 'g', label="SMA100")

plt.plot(rolling_correlation)
plt.xlabel('Day')
plt.ylabel('60-day Rolling Correlation')

plt.legend()
plt.show()