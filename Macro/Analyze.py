import pandas as pd, numpy as np, yfinance as yf, matplotlib.pyplot as plt, tabulate
from scipy import stats
from pandas.tseries.offsets import BMonthEnd, BusinessDay
from datetime import date
from Initialize import Initialize
from dash import Dash, dash_table


break_str = '#' * 100

def vola_calc(ts):
    vola_window = 20
    return ts.pct_change().rolling(vola_window).std().dropna().iloc[-1]

def analyze(selection):
    total_hist = yf.download(tickers=selection.ticker_list, period="1y",
                             interval="1d", group_by='ticker',
                             auto_adjust=True, prepost=True,
                             threads=True, proxy=None)

    d=date.today()
    idx = pd.IndexSlice
    year_start = total_hist.loc['2021-12-31',idx[:,'Close']]

    offset = BusinessDay(n=0)
    curr_bd = (d - offset).strftime('%Y-%m-%d')
    current = total_hist.loc[curr_bd,idx[:,'Close']]

    ytd_df = pd.merge(year_start,current, right_index = True, left_index = True)
    ytd_df['YTD Return %'] = (ytd_df[curr_bd]- ytd_df['2021-12-31']) / ytd_df['2021-12-31']

    offset = BMonthEnd()

    prev_mtd = offset.rollback(d).strftime('%Y-%m-%d')
    prev_mtd_srs = total_hist.loc[prev_mtd,idx[:,'Close']]

    mtd_df = pd.merge(prev_mtd_srs,current, right_index = True, left_index = True)
    mtd_df['MTD Return %'] = (mtd_df[curr_bd]- mtd_df[prev_mtd]) / mtd_df[prev_mtd]

    returns_df = pd.DataFrame(index=mtd_df.index)

    returns_df['MTD Return %'],returns_df['YTD Return %'] = mtd_df['MTD Return %'],ytd_df['YTD Return %']

    returns_df = returns_df.droplevel(level=1).sort_values(by = 'YTD Return %', ascending = False)

    returns_df.to_csv("returns_df_Comm.csv")

    dict_cols = {20: '1-Month',
                 60: '3-Months',
                 125: '6-Months',
                 '20-corr': '1-Month Corr',
                 '60-corr': '3-Months Corr',
                 '125-corr': '6-Months Corr'}

    time_list = [20, 60, 125]
    r2_table = pd.DataFrame(columns=time_list, index=selection.ticker_list).sort_index()

    for time in time_list:
        ranking_t, hist_for_corr = Initialize.returnAlpha(selection, time, total_hist)

        r2_ranks = pd.DataFrame(ranking_t).sort_index()
        r2_table[time] = r2_ranks[0] / (125 / time)

        r2_table[str(time) + '-corr'] = np.nan

        for tick in selection.ticker_list:
            r2_table.loc[tick, str(time) + '-corr'] = hist_for_corr.corr()[tick].drop(tick).mean()

    r2_table.insert(3, 'Avg Alpha-Factor', r2_table[time_list].mean(axis=1))
    r2_table = r2_table.rename(columns=dict_cols)
    r2_table = r2_table.sort_values(by='Avg Alpha-Factor', ascending=False)

    vola_table = hist_for_corr.apply(vola_calc)

    r2_table['1-Month Vol'] = vola_table
    r2_table.to_csv("r2_table_Comm.csv")

    pd.set_option('display.max_columns', 1000000)
    pd.set_option('display.max_rows', 1000000)

    plt.rcParams.update({'figure.max_open_warning': 0})

    return r2_table

if __name__ == '__main__':
    print(break_str)
    print('Welcome User! To begin your analysis please follow the input instructions:\n')
    print('Please select a universe to research:\n' +
          '1: World ETFs\n'+'2: US Sector ETFs\n'+'3: Commodity ETFs\n')

    universe = input('Select your universe: ')

    print('\nPlease select an alpha factor to research:\n' +
          '1: Momentum\n')

    a_factor = input('Select your alpha factor: ')

    #default universe selected = 1 , World
    universe_selected = 'World'
    if universe == 1:
        universe_selected = 'World'
    elif universe == 2:
        universe_selected = 'US'
    elif universe == 3:
        universe_selected = 'Commodities'
    else:
        'User returned the wrong input value! Defaulting to World ETFs selection...'

    # default universe selected = 1 , World
    a_factor_selected = 'Momentum'
    if a_factor == 1:
        a_factor_selected = 'Momentum'
    else:
        'User returned the wrong input value! Defaulting to Momentum selection...'



    selection = Initialize(universe_selected, 'Momentum')

    print('\n' + break_str + '\nDisplaying your research selections: ')
    Initialize.displaySelection(selection)

    print(selection.ticker_list)

    r2_table = analyze(selection)
    print(tabulate.tabulate(r2_table, headers=r2_table.columns))

    r2_table.reset_index().set_index('index', drop=False)

    app = Dash(__name__)

    app.layout = dash_table.DataTable(
        data=r2_table.to_dict('records'),
        columns=[{'id': c, 'name': c} for c in r2_table.columns],
    )

    app.run_server(debug=True)
