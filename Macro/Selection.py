

class Selection:
   'Common base class for selected asset class and alpha factor'
   def __init__(self, name, a_factor, universe):
      self.name = name
      self.a_factor = a_factor
      self.universe = universe
   def displaySelection(self):
      print("Name: ", self.name, "\nAlpha Factor: ", self.a_factor, "\nUniverse: ", self.universe)

class Alpha_Factor:
   'Common base class for all macro research'
   def __init__(self, name, a_factor, universe):
      self.minimum_momentum = name
      self.number_of_stocks = a_factor
      self.exclude_days = universe

   # calculate R^2
   def slope(ts):
      x = np.arange(len(ts))
      log_ts = np.log(ts)
      slope, intercept, r_value, p_value, std_err = stats.linregress(x, log_ts)
      annualized_slope = (np.power(np.exp(slope), 252) - 1) * 100
      score = annualized_slope * (r_value ** 2)
      return score

   # Setting Params for Momentum
   def get_params():
      minimum_momentum = 0  # momentum score cap
      number_of_stocks = 27
      exclude_days = 0
      return minimum_momentum, number_of_stocks, exclude_days

   def build_mom_list(momentum_window, tickers_list, total_hist):
      minimum_momentum, number_of_stocks, exclude_days = self.minimum_momentum, self.number_of_stocks, self.exclude_days

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

      momentum_list = momentum_hist1.apply(slope)  # Mom Window 1

      ranking_table = momentum_list.sort_values(ascending=False)

      ranking_table.to_csv("sector_ranking_table.csv")
      return ranking_table, hist