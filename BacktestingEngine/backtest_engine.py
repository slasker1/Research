import zipline, matplotlib.pyplot as plt, pyfolio as pf, pandas as pd, numpy as np, yfinance as yf, warnings, csv
from zipline.api import order_target_percent, symbol, set_commission, set_slippage, schedule_function, date_rules, \
    time_rules, set_long_only, set_max_leverage
from scipy import stats
from zipline.finance.commission import PerDollar
from zipline.finance.slippage import VolumeShareSlippage, FixedSlippage
from bbridge import BB
warnings.filterwarnings("ignore", category=DeprecationWarning)

intial_portfolio = 100000
momentum_window = 125
minimum_momentum = 40
portfolio_size = 30
vola_window = 20

enable_trend_filter = True
trend_filter_symbol = 'SPY'
trend_filter_window = 100

enable_commission = False
commission_pct = 0.001
enable_slippage = False
slippage_volume_limit = 0.025
slippage_impact = 0.05

def momentum_score(ts):
    x = np.arange(len(ts))
    log_ts = np.log(ts)
    slope, intercept, r_value, p_value, std_err = stats.linregress(x, log_ts)
    annualized_slope = (np.power(np.exp(slope), 252) - 1) * 100
    score = annualized_slope * (r_value ** 2)
    return score

def volatility(ts):
    return ts.pct_change().rolling(vola_window).std().dropna().iloc[-1]

def check_bb(ts):
    my_bb = BB(a=0, b=0, T=125)[21]
    my_ret = ts.pct_change(vola_window).iloc[-1]
    if my_ret > my_bb:
        return 1
    else:
        return 0

def trend_filter1():
    today = zipline.api.get_datetime().date()
    data = yf.download(tickers="SPY",start="1994-01-01", end=today,
                       interval="1d",group_by='ticker',
                       auto_adjust=True,prepost=True,threads=True,proxy=None
        )

    data['SMA100'] = data['Close'].rolling(100).mean()

    data['Position'] = np.where(data['Close'] > data['SMA100'], 1, 0)

    current_trend = data['Position'].iloc[-1]

    trend = "BULL"
    if current_trend == 0:
        trend = "BEAR"
    elif current_trend == 1:
        trend = "BULL"
    return trend

def initialize(context):
    set_long_only(on_error='fail')
    #set_max_leverage(1.1)

    if enable_commission:
        comm_model = PerDollar(cost=commission_pct)
    else:
        comm_model = PerDollar(cost=0.0)
    set_commission(comm_model)

    if enable_slippage:
        slippage_model = VolumeShareSlippage(volume_limit=slippage_volume_limit, price_impact=slippage_impact)
        set_slippage(slippage_model)
    else:
        slippage_model = FixedSlippage(spread=0.0)

    context.last_month = intial_portfolio
    schedule_function(
        func=rebalance,
        date_rule=date_rules.week_end(days_offset=3),
        time_rule=time_rules.market_open()
    )

def output_progress(context):
    today = zipline.api.get_datetime().date()
    print(today)

    perf_pct = (context.portfolio.portfolio_value / context.last_month) - 1

    print("{} - Last Day's Result: {:.2%}".format(today, perf_pct))

    fields = [str(today),str(context.portfolio.portfolio_value)]

    # with open(r'portfolio_value.csv', 'a') as f:
    #     writer = csv.writer(f)
    #     writer.writerow(fields)

    context.last_month = context.portfolio.portfolio_value

def rebalance(context, data):
    output_progress(context)

    today = zipline.api.get_datetime()  # .date()

    dt64 = np.datetime64(today)

    date = pd.to_datetime(str(today))

    sp500_const = pd.read_csv('sp500_const.csv')
    todays_universe = [symbol(ticker) for ticker in sp500_const['symbol']]
    hist_window = momentum_window

    hist = data.history(todays_universe, "close", hist_window+5, "1d")[:-5]

    #hist.to_csv("testhist.csv")

    momentum_hist = hist[:momentum_window]
    momentum_list = momentum_hist.apply(momentum_score)
    ranking_table = momentum_list.sort_values(ascending=False)
    ranking_table = ranking_table.dropna(axis='rows')

    #ranking_table.to_csv("myranktest.csv")

    if enable_trend_filter:
        trend_filter = trend_filter1()
        if trend_filter == "BULL":
            kept_positions = list(context.portfolio.positions.keys())
            for security in context.portfolio.positions:
                if (security not in ranking_table):
                    #print("selling: " + str(security))
                    order_target_percent(security, 0.0)
                    kept_positions.remove(security)
                elif ranking_table[security] < minimum_momentum:
                    #print("selling: " + str(security))
                    order_target_percent(security, 0.0)
                    kept_positions.remove(security)

            replacement_stocks = portfolio_size - len(kept_positions)
            buy_list = ranking_table.loc[
                           ~ranking_table.index.isin(kept_positions)][:replacement_stocks]

            new_portfolio = pd.concat(
                (buy_list,
                 ranking_table.loc[ranking_table.index.isin(kept_positions)])
            )
            #print(new_portfolio)

            vola_table = hist[new_portfolio.index].apply(volatility)
            inv_vola_table = 1 / vola_table
            sum_inv_vola = np.sum(inv_vola_table)
            vola_target_weights = (inv_vola_table / sum_inv_vola) * 0.90
            vola_target_weights.to_csv("vola_test.csv")

            if today == '2001-05-25' or today == '2001-05-29' or today == '2001-05-30':
                pass
            else:
                for security, rank in new_portfolio.iteritems():
                    weight = vola_target_weights[security]
                    #check_bb = check_bb_filter[security]
                    if security in kept_positions:
                        if check_bb(hist[security]) == 0:
                            #print("rebalancing: " + str(security)+ ' -> Target%: '+ "{:.6%}".format(weight))
                            if weight > 0:
                                order_target_percent(security, (weight))
                        else:
                            order_target_percent(security, 0.0)
                    else:
                        if check_bb(hist[security]) == 0:
                            #print("buying: " + str(security)+ ' -> Target%: '+ "{:.6%}".format(weight))
                            if ranking_table[security] > minimum_momentum:
                                if weight > 0:
                                    order_target_percent(security, (weight))
                        else:
                            order_target_percent(security, 0.0)
        elif trend_filter == "BEAR":
            #print("Selling everything")
            """
            Sell Logic
            """
            for security in context.portfolio.positions:
                order_target_percent(security, 0.0)
            #order_target_percent("TLT",1)

def analyze(context, perf):
    perf['max'] = perf.portfolio_value.cummax()
    perf['dd'] = (perf.portfolio_value / perf['max']) - 1
    maxdd = perf['dd'].min()

    ann_ret = (np.power((perf.portfolio_value.iloc[-1] / perf.portfolio_value.iloc[0]), (252 / len(perf)))) - 1

    print("Annualized Return: {:.2%} Max Drawdown: {:.2%}".format(ann_ret, maxdd))

    return

#start = pd.Timestamp('1994-08-01', tz='utc')
start = pd.Timestamp('1994-08-01', tz='utc')
end = pd.Timestamp('2022-08-18', tz='utc')

perf = zipline.run_algorithm(
    start=start, end=end,
    initialize=initialize,
    analyze=analyze,
    capital_base=intial_portfolio,
    data_frequency='daily',
    bundle='yahoo_NYSE')

returns, positions, transactions = pf.utils.extract_rets_pos_txn_from_zipline(perf)
pf.create_full_tear_sheet(returns, positions=positions, transactions=transactions, benchmark_rets=None)

perf.portfolio_value.to_csv('125d version.csv')

plt.savefig('my_backtest.pdf')

plt.show()


