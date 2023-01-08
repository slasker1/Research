import numpy as np, pandas as pd, yfinance as yf, simple_interpolation.simple_interpolation as si
# Samples a Brownian bridge in the [a,b] interval, see https://en.wikipedia.org/wiki/Brownian_bridge#General_case
def BB(
    T: int = 125,
    a: float = 0,
    b: float = 0,
    alpha: float = 0,
    sigma: float = 1
) -> pd.Series:
    X0 = a
    X = pd.Series([X0])
    t1 = 0
    t2 = T
    for i in np.arange(1, T):
        t = i
        mu = (a + (t - t1)/(t2 - t1)*(b - a))
        s = ((t2 - t)*(t - t1)/(t2 - t1))
        ei = np.random.normal(alpha+mu, sigma+s)
        X.loc[i] = ((T - t)/T**0.5)*ei*((t/(T-t))**0.5)
    XT = b
    X[T] = XT
    return X/1250

# my_bb = BB(a=0,b=0, T=125)
#
# print(my_bb[21])
#
# from matplotlib import pyplot as plt
#
# plt.plot(my_bb, 'b')
#
# #plt.show()
#
# data = yf.download(tickers="AAPL",start="2022-02-17", end='2022-08-18',
#                        interval="1d",group_by='ticker',
#                        auto_adjust=True,prepost=True,threads=True,proxy=None
#         )
#
# data = data.reset_index()
#
# print(data)
#
# my_close_data = data[['Date','Close']]
#
# print(my_close_data)
#
# my_close_returns = (my_close_data['Close'].pct_change()+1).cumprod()-1
#
# from matplotlib import pyplot as plt
# plt.plot(my_close_returns, 'r')
#
# plt.show()
#
# # patched_df = si.interpolate_gaps(my_close_data, plot=True)
# #
# # print(patched_df)
# #
# # patched_df.to_csv('patched_df_bbridge.csv')
# #
# # import simple_interpolation.prophet_sensibility as ps
# #
# # # This also plots the thing below
# # models = ps.prophet_sensibility(my_close_data, slicing_threshold=5000)