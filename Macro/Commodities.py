import pandas as pd, numpy as np, yfinance as yf, matplotlib.pyplot as plt
from scipy import stats
from pandas.tseries.offsets import BMonthEnd, BusinessDay
from datetime import date
from Selection import Selection, Alpha_Factor

def analyze(total_hist):
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
    r2_table = pd.DataFrame(columns=time_list, index=tickers_list).sort_index()

    for time in time_list:
        ranking_t, hist_for_corr = build_mom_list(time, tickers_list, total_hist)

        r2_ranks = pd.DataFrame(ranking_t).sort_index()
        r2_table[time] = r2_ranks[0] / (125 / time)

        r2_table[str(time) + '-corr'] = np.nan

        for tick in tickers_list:
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

    dfSectors = pd.read_excel("Comm_Universe.xlsx", engine='openpyxl')
    tickers_list = dfSectors["Symbol"].values.tolist()

    comm_research = Selection('Commodities', 'Momentum', tickers_list)

    Selection.displaySelection(comm_research)

    comm_momentum = Alpha_Factor('')

    total_hist = yf.download(tickers=comm_research.universe, period="1y",
                            interval="1d", group_by='ticker',
                            auto_adjust=True, prepost=True,
                            threads=True, proxy=None)

    r2_table = analyze(total_hist)