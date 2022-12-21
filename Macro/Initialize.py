import numpy as np, pandas as pd
from scipy import stats

class Initialize:
   #Research topic selection
   def __init__(self, universe, a_factor):
      self.universe = universe
      self.a_factor = a_factor
      self.ticker_list = self.returnUniverse()
   def displaySelection(self):
      print("Universe: ", self.universe, "\nETF List: ", self.ticker_list, "\nAlpha Factor: ", self.a_factor)

   def returnAlpha(self, momentum_window, total_hist):
      if self.a_factor == 'Momentum':
         return self.build_mom_list(momentum_window, self.ticker_list, total_hist)
      else:
         return None

   def returnUniverse(self):
      if self.universe == 'Commodities':
         universe = pd.read_excel("Comm_Universe.xlsx", engine='openpyxl')
         tickers_list = universe["Symbol"].values.tolist()
         return tickers_list
      elif self.universe == 'World':
         universe = pd.read_excel("World_Universe.xlsx", engine='openpyxl')
         tickers_list = universe["Symbol"].values.tolist()
         return tickers_list
      elif self.universe == 'US':
         universe = pd.read_excel("Sector_Universe.xlsx", engine='openpyxl')
         tickers_list = universe["Symbol"].values.tolist()
         return tickers_list
      else:
         return None

   def slope(self, ts):
      x = np.arange(len(ts))
      log_ts = np.log(ts)
      slope, intercept, r_value, p_value, std_err = stats.linregress(x, log_ts)
      annualized_slope = (np.power(np.exp(slope), 252) - 1) * 100
      score = annualized_slope * (r_value ** 2)
      return score

   def build_mom_list(self, momentum_window, tickers_list, total_hist):
      hist = pd.DataFrame(columns=tickers_list)

      hist_window = momentum_window
      for ticker in tickers_list:
         ticker = str(ticker)
         hist[ticker] = total_hist[ticker]["Close"].tail(hist_window)
         # volume[ticker] = total_hist[ticker]["Volume"].tail(200+2)[:-2]

      hist = hist.dropna()

      momentum1_start = -1 * momentum_window
      momentum_hist1 = hist[momentum1_start:-1]

      momentum_list = momentum_hist1.apply(self.slope)

      ranking_table = momentum_list.sort_values(ascending=False)

      return ranking_table, hist