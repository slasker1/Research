import numpy as np, pandas as pd
from scipy import stats

class Initialize:
   #Research topic selection
   def __init__(self, name, a_factor, universe):
      self.name = name
      self.a_factor = a_factor
      self.universe = universe
   def displaySelection(self):
      print("Name: ", self.name, "\nAlpha Factor: ", self.a_factor, "\nUniverse: ", self.universe)

   def returnAlpha(self, momentum_window, total_hist):
      if self.a_factor == 'Momentum':
         return self.build_mom_list(momentum_window, self.universe, total_hist)

   def slope(self, ts):
      x = np.arange(len(ts))
      log_ts = np.log(ts)
      slope, intercept, r_value, p_value, std_err = stats.linregress(x, log_ts)
      annualized_slope = (np.power(np.exp(slope), 252) - 1) * 100
      score = annualized_slope * (r_value ** 2)
      return score

   def build_mom_list(self, momentum_window, tickers_list, total_hist):
      exclude_days = 0
      hist = pd.DataFrame(columns=tickers_list)

      hist_window = momentum_window + exclude_days
      for ticker in tickers_list:
         ticker = str(ticker)
         hist[ticker] = total_hist[ticker]["Close"].tail(hist_window)
         # volume[ticker] = total_hist[ticker]["Volume"].tail(200+2)[:-2]

      data_end = -1 * (exclude_days + 1)  # exclude most recent data

      hist = hist.dropna()

      momentum1_start = -1 * (momentum_window + exclude_days)
      momentum_hist1 = hist[momentum1_start:data_end]

      momentum_list = momentum_hist1.apply(self.slope)  # Mom Window 1

      ranking_table = momentum_list.sort_values(ascending=False)

      return ranking_table, hist