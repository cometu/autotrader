import krakenex
import pandas as pd
import pickle
import numpy as np
from matplotlib.finance import candlestick2_ochl
import matplotlib.pyplot as plt

import time
import datetime

import urllib
import json

from mpl_toolkits.mplot3d import Axes3D
import matplotlib.pyplot as plt
import random
from matplotlib import cm


def fetchKrakenOhlc(krakenApi, pair, interval, since=0):
    data1 = krakenApi.query_public('OHLC', {'pair': pair, 'interval': interval, 'since': since})
    data = data1['result'][pair]
    df = pd.DataFrame(data)
    df.columns = ['time', 'open', 'high', 'low', 'close', 'vwap', 'volume', 'count']
    df = df.apply(pd.to_numeric)
    return df

# Fetch Kraken Recent trades
# Returns the trades hostory for a given currency pair, since a specified timestamp
# this timestamp is expressed in ns, to obtain a timestamps from time.time(), it has to be multiplicated by 10^9
# Returns a tuple with a df containing trades data & the id (timestamp in ns) of the last fetched trade
def fetchKrakenRecentTrades(krakenApi, pair, since=0):
    data1 = krakenApi.query_public('Trades', {'pair': pair, 'since': since})
    data = data1['result'][pair]
    last = data1['result']['last']
    df = pd.DataFrame(data)
    df.columns = ['price', 'volume', 'time', 'buy/sell', 'market/limit', 'misc']
    return df, last

def estimateLongProfits(data, signals, fee):
    profit = 0
    soldEur = 100
    soldEth = 0
    stepInvestment = 100

    for i in range(len(signals)):
        if signals.action.iloc[i] == 2:
            # Stop loop if it's the last buy
            if i == len(signals)-1:
                break
            # print(data.value.loc[signals.index[i]])
            soldEth += stepInvestment/data.value.loc[signals.index[i]]
            soldEur -= stepInvestment
            soldEur -= fee*stepInvestment

        else:
            soldEur += (1-fee)*soldEth*data.value.loc[signals.index[i]]
            soldEth = 0

    soldEur += soldEth*data.value.iloc[-1]

    profit += soldEur - 100

    return profit


def estimateShortProfits(data, signals, fee):

    debtBankEth = 0
    profit = 0
    soldEur = 100
    stepInvestment = 100

    for i in range(len(signals)):
        if signals.action.iloc[i] == 2:
            soldEur -= (1+fee)*debtBankEth*data.value.loc[signals.index[i]]
            debtBankEth = 0
        else:  # sell
            if i == len(signals)-1:
                break
            debtBankEth += stepInvestment/data.value[signals.index[i]]
            soldEur += stepInvestment
            soldEur -= fee*stepInvestment

    soldEur -= debtBankEth*data.value.iloc[-1]

    profit += soldEur - 100

    return profit


def estimateProfitsOnOhlcUsingEma(period1, period2, ohlcData, fee,
                                  trainOnOpen=True, testOnClose=False):
    if trainOnOpen is True:
        ema1 = pd.ewma(ohlcData.open, span=period1)
        ema2 = pd.ewma(ohlcData.open, span=period2)
    else:
        ema1 = pd.ewma(ohlcData.close, span=period1)
        ema2 = pd.ewma(ohlcData.close, span=period2)

    signals = pd.DataFrame(columns=['action'],
                           index=ohlcData.loc[np.where(np.diff(np.sign((ema1-ema2))))[0]].index)
    signals.action = np.diff(np.sign((ema1-ema2)))[signals.index]

    data = pd.DataFrame(columns=['value'])

    if testOnClose is False:
        data.value = ohlcData.close
    elif testOnClose is True:
        data.value = ohlcData.open

    profit = 0
    profit += estimateLongProfits(data=data, signals=signals, fee=fee)
    profit += estimateShortProfits(data=data, signals=signals, fee=fee)
    return profit

result = pd.DataFrame(columns=['pair', 'interval', 'p1', 'p2', 'profit'])

pair = 'XXBTZEUR'


def brutforceEma(ohlcData, fee=0.0026, trainDataShare=0.8,
                 p1Min=1, p1Max=50, p2Min=1, p2Max=50,
                 trainOnOpen=True, testOnClose=True):
    result = pd.DataFrame(columns=['p1', 'p2', 'profit'])
    for p2 in range(p2Min, p2Max):
        for p1 in range(p1Min, p1Max):
            if p1 == p2:
                profit = 0
            else:
                profit = estimateProfitsOnOhlcUsingEma(p1, p2, ohlcData, fee=fee)
            result = result.append(
                {
                    'p1': p1,
                    'p2': p2,
                    'profit': profit
                },
                ignore_index=True)

    return result


