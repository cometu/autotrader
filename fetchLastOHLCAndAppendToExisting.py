import krakenex
import pandas as pd
import pickle
from autotrader import *
import csv
import time


def avoidApiCallExcess(lastApiCallTime, apiCount, increment, maxApiCount=13):

    newTime = time.monotonic()

    if newTime - lastApiCallTime < 1.0:
        time.sleep(1)

    newApiCount = apiCount - int((newTime - lastApiCallTime) / 3)

    if newApiCount + increment > maxApiCount:
        time.sleep(increment*3)
        newApiCount = newApiCount - increment

    if newApiCount < 0:
        newApiCount = 0
    return newTime, newApiCount


def run():

    intervals = [1, 5, 15, 30, 60, 240, 1440, 10080, 21600]

    pairs = ['BCHEUR', 'DASHEUR',
             'EOSETH', 'EOSXBT', 'GNOETH', 'GNOXBT', 'XETCXETH',
             'XETCXXBT', 'XETCZEUR', 'XETCZUSD', 'XETHXXBT', 'XETHZCAD',
             'XETHZEUR', 'XICNXETH',
             'XICNXXBT', 'XLTCZEUR', 'XMLNXETH',
             'XMLNXXBT', 'XREPZEUR',
             'XXBTZEUR', 'XXDGXXBT',
             'XXLMXXBT', 'XXMRXXBT', 'XXMRZEUR',
             'XXRPZEUR', 'XZECZEUR', ]

    lastApiCallTime = time.monotonic()
    apiCount = 0

    for interval in intervals:

        for pair in pairs:

            path = str(interval) + '-' + pair + '.csv'
            print(path)

            # Try to load already existing data
            try:
                df = pd.read_csv(path, index_col=0)
            except FileNotFoundError:
                print('File not found creating one')
                df = None

            if df is None:
                # if no matching csv found fetch all possible data
                since = 0 
            else:
                since = df.time.max()

            while True:
                lastApiCallTime, apiCount = avoidApiCallExcess(lastApiCallTime, apiCount, increment=1)
                try:
                    print('since: ', since)
                    recentOhlc = fetchKrakenOhlc(krakenApi=k, pair=pair, interval=interval, since=since)
                    break
                except:
                    print('Error')
                    time.sleep(3)
                    pass

            if df is None:
                df = recentOhlc
            else:
                df = df.append(recentOhlc, ignore_index=True)

            df.to_csv(path)
