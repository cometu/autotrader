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


k = krakenex.API()


def fetchKrakenOhlc(pair, interval, since=0):
    data1 = k.query_public('OHLC', {'pair': pair, 'interval': interval, 'since': since})
    data = data1['result'][pair]
    df = pd.DataFrame(data)
    df.columns = ['time', 'open', 'high', 'low', 'close', 'vwap', 'volume', 'count']
    return df


def estimateLongProfits(data, signals, fee):
    profit = 0
    soldEur = 100
    soldEth = 0
    stepInvestment = 100

    for i in range(len(signals)):
        if signals.action.iloc[i] == 'buy':
            # Stop loop if it's the last buy
            if i == len(signals)-1:
                break

            soldEth += stepInvestment/data[data.time == signals.time].value.iloc[0]
            soldEur -= stepInvestment
            soldEur -= fee*stepInvestment

        else:
            soldEur += (1-fee)*soldEth*data[data.time == signals.time].value.iloc[0]
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
        if signals.action.iloc[i] == 'buy':
            soldEur -= (1+fee)*debtBankEth*data[data.time == signals.time].value.iloc[0]
            debtBankEth = 0
        else:  # sell
            if i == len(signals)-1:
                break
            debtBankEth += stepInvestment/data[data.time == signals.time].value.iloc[0]
            soldEur += stepInvestment
            soldEur -= fee*stepInvestment

    soldEur -= debtBankEth*data.value.iloc[-1]

    profit += soldEur - 100

    return profit


def estimateProfitsOnOhlcUsingEma(period1, period2, ohlcData, fee, trainOnOpen=True, testOnOpen=False):
    if trainOnOpen is True:
        ema1 = pd.ewma(ohlcData.open, span=period1)
        ema2 = pd.ewma(ohlcData.open, span=period2)
    else:
        ema1 = pd.ewma(ohlcData.close, span=period1)
        ema2 = pd.ewma(ohlcData.close, span=period2)

    signals = pd.DataFrame(columns=['action', 'time'])

    signals.time = np.where(np.diff(np.sign((ema1-ema2))))[0]
    signals.action = np.diff(np.sign((ema1-ema2)))[signals.time]

    data = pd.DataFrame(columns=['time', 'value'])
    data.time = ohlcData.time

    if testOnOpen is False:
        data.value = ohlcData.close
    elif testOnOpen is True:
        data.value = ohlcData.open

    profit = 0
    profit += estimateLongProfits(data=data, signals=signals, fee=fee)
    profit += estimateShortProfits(data=data, signals=signals, fee=fee)
    return profit

profit = 0
result = pd.DataFrame(columns=['pair', 'interval', 'p1', 'p2', 'profit'])

p1Min = 1
p1Max = 50

p2Min = 1
p2Max = 50

pair = 'XXBTZEUR'

interval = 5
d = fetchKrakenOhlc(pair=pair, interval=interval, since=0)
pickle.dump(result, open(pair+"-"+str(interval)+".pkl", "wb"))
duration_5 = (d.time.iloc[-1]-d.time.iloc[0])/3600
for p2 in range(p2Min, p2Max):
    for p1 in range(p1Min, p1Max):
        profit = estimateProfitsOnOhlcUsingEma(p1, p2, d, fee=0.0026).values[0]
        result = result.append({'pair': pair, 'interval': interval, 'p1': p1, 'p2': p2, 'profit': profit}, ignore_index=True)

interval = 15
d = fetchKrakenOhlc(pair=pair, interval=interval, since=0)
duration_15 = (d.time.iloc[-1]-d.time.iloc[0])/3600
for p2 in range(p2Min, p2Max):
    for p1 in range(p1Min, p1Max):
        profit = estimateProfitsOnOhlcUsingEma(p1, p2, d, fee=0.0026).values[0]
        result = result.append({'pair': pair, 'interval': interval, 'p1': p1, 'p2': p2, 'profit': profit}, ignore_index=True)

interval = 30
d = fetchKrakenOhlc(pair=pair, interval=interval, since=0)
duration_30 = (d.time.iloc[-1]-d.time.iloc[0])/3600
for p2 in range(p2Min, p2Max):
    for p1 in range(p1Min, p1Max):
        profit = estimateProfitsOnOhlcUsingEma(p1, p2, d, fee=0.0026).values[0]
        result = result.append({'pair': pair, 'interval': interval, 'p1': p1, 'p2': p2, 'profit': profit}, ignore_index=True)

interval = 60
d = fetchKrakenOhlc(pair=pair, interval=interval, since=0)
duration_60 = (d.time.iloc[-1]-d.time.iloc[0])/3600
for p2 in range(p2Min, p2Max):
    for p1 in range(p1Min, p1Max):
        profit = estimateProfitsOnOhlcUsingEma(p1, p2, d, fee=0.0026).values[0]
        result = result.append({'pair': pair, 'interval': interval, 'p1': p1, 'p2': p2, 'profit': profit}, ignore_index=True)


# Compute per hour profit
r = result.copy()
r.profit_per_hour = r.apply(lambda x: x.profit/duration_60 if x.interval == 60 else x.profit, axis=1)
r.profit_per_hour = r.apply(lambda x: x.profit/duration_15 if x.interval == 15 else x.profit, axis=1)
r.profit_per_hour = r.apply(lambda x: x.profit/duration_30 if x.interval == 30 else x.profit, axis=1)
r.profit_per_hour = r.apply(lambda x: x.profit/duration_5 if x.interval == 5 else x.profit, axis=1)


# Plot
def fun(p1, p2):
    ret = result[result.interval==5][(result[result.interval==5].p1 == p1) & (result[result.interval==5].p2 == p2)].profit.iloc[0]
    return ret

fig = plt.figure()
ax = fig.add_subplot(111, projection='3d')

x = y = range(1,50)
X, Y = np.meshgrid(x, y)
zs = np.array([fun(x,y) for x,y in zip(np.ravel(X), np.ravel(Y))])
Z = zs.reshape(X.shape)

ax.plot_surface(X, Y, Z)

ax.set_xlabel('p1')
ax.set_ylabel('p2')
ax.set_zlabel('profit')

plt.show()


