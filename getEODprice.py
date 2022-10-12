# from time import sleep
from time import sleep
import miniEnc as enc
import ast
import requests
import numpy as np
from datetime import datetime
import pandas_datareader.data as web

def chunks(l, n):
    ll = list(l)
    for i in range(0, len(ll), n):
        yield ll[i:i+n]

def less_than_32_symbols(symbols_in_8s, k) -> dict:
    url = "https://api.twelvedata.com/eod"
    count = 0
    close_price = {}
    for each_8_symbols in symbols_in_8s:
        params = {"symbol": ",".join(each_8_symbols), "apikey": k[count]}
        count += 1
        response = requests.get(url, params=params)
        r = response.json()
        for ticker in each_8_symbols:
            close_price[ticker] = r[ticker]["close"]
    return close_price


def getEODpriceUSA(L) -> dict:
    g = b'z4zZpKqmm9jAubi2gLF8d3ja2Kqgz56eyJhpxarIo6msqIyeen6NhYOBf3ikr6nY0aGenZtsmZqtx6uspabGo4qNtomEgW9xYqDarKOmm56XanGTpJunqainnaOTvbiHfoR6qnneqKXU05GThF1pw6rKqtasp5umjIqItrB_gad1qaylpNDNn8iaa8OolZrR'
    k = ast.literal_eval(enc.decode(enc.cccccccz, g))
    
    symbols_in_8s = list(chunks(set(L), 8)) # 8 symbols per request (12data free tier)
    usa_close_price = {}

    for i in range(0, int(len(symbols_in_8s)/(len(k)))+1):
        usa_close_price.update(less_than_32_symbols(symbols_in_8s[i*len(k): (i+1)*len(k)], k))
        if i>1:
            print(i, "sleeping for 60 seconds")
            sleep(60)
    return usa_close_price

def getEODpriceUK(L) -> dict:
    if datetime.now().hour < 16.5:
        last_business_day = np.busday_offset('today', -1, roll='backward')
    else:
        last_business_day = np.busday_offset('today', 0, roll='backward')
    
    uk_close_price = {}
    for i in L:
        close_price = web.DataReader(i, 'yahoo', last_business_day)['Adj Close'][-1]
        uk_close_price[i] = close_price/100
    return uk_close_price


def main():
    L1 = ['PAY.L', 'SDR.L']
    print(getEODpriceUK(L1))


if __name__ == "__main__":
    main()