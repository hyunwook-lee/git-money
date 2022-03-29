from re import search
from webbrowser import get
import pyupbit
from datetime import datetime,timedelta
import numpy as np
import requests
from bs4 import BeautifulSoup
import time

access = "yKxp6uyD7sCNAfkxVvD8S1d841hw00SZWKoasdl7"
secret = "gnZD2uyxdgjbxt0L7tmHj6esKYw9xJMNYM53xj4c"

def get_target_price(ticker, k):
    """변동성 돌파 전략으로 매수 목표가 조회"""
    df = pyupbit.get_ohlcv(ticker, interval="day", count=2)
    target_price = df.iloc[0]['close'] + (df.iloc[0]['high'] - df.iloc[0]['low']) * k
    return target_price


def get_ma15(ticker):
    """15일 이동 평균선 조회"""
    df = pyupbit.get_ohlcv(ticker, interval="day", count=15)
    ma15 = df['close'].rolling(15).mean().iloc[-1]
    return ma15

def get_balance(ticker):
    """잔고 조회"""
    balances = upbit.get_balances()
    for b in balances:
        if b['currency'] == ticker:
            if b['balance'] is not None:
                return float(b['balance'])
            else:
                return 0
    return 0

def get_current_price(ticker):
    """현재가 조회"""
    return pyupbit.get_orderbook(ticker=ticker)["orderbook_units"][0]["ask_price"]

def get_ror(ticker,k=0.5):
    df = pyupbit.get_ohlcv(ticker,count=7)
    df['range'] = (df['high'] - df['low']) * k
    df['target'] = df['open'] + df['range'].shift(1)

    df['ror'] = np.where(df['high'] > df['target'],
                         df['close'] / df['target'],
                         1)

    ror = df['ror'].cumprod()[-2]
    return ror

def get_bestk(ticker):
    bestk =[]
    for k in np.arange(0.1, 1.0, 0.1):
        ror = get_ror(ticker,k)
        bestk.append(ror)
    realk=(bestk.index(max(bestk))+1)/10
    return realk

def get_start_time(ticker):
    """시작 시간 조회"""
    df = pyupbit.get_ohlcv(ticker, interval="day", count=1)
    start_time = df.index[0]
    return start_time

# 로그인
upbit = pyupbit.Upbit(access, secret)
print("autotrade start")

#자동매매 시작

bought_list = []
bought_list1 = []
bought_list2 = []

while True:
    try:
        now = datetime.now()
        start_time = get_start_time("KRW-BTC")
        start_time1 = now.replace(hour=9, minute=15, second=0, microsecond=0)
        start_time2 = start_time.replace(hour=21,minute=30,second=0,microsecond=0)
        end_time1 = start_time.replace(hour=11, minute=0, second=0, microsecond=0)
        end_time2 = start_time1 + timedelta(days=1)

        if start_time1<now<end_time1 :
            url = "https://www.coingecko.com/ko/거래소/upbit"
            bs = BeautifulSoup(requests.get(url).text,'html.parser')
            interest = []
            ticker_temp = bs.find_all("a", attrs={"rel":"nofollow noopener", "class":"mr-1"})
            for j in range(15):
                interest.append('KRW-' + list(ticker_temp[j])[0][1:-5])
            for i in interest:
                bestk = get_bestk(i)
                target_price = get_target_price(i,bestk)
                ma15 = get_ma15(i)
                current_price = get_current_price(i)
                print(i,target_price)
                if len(bought_list) < 5 :
                    if i not in bought_list:
                        if target_price < current_price and ma15 < current_price:
                            bought_list.append(i)
                            bought_list1.append(i)
                            bought_list2.append(i)
                            krw = get_balance('KRW')
                            krw = krw/(6-len(bought_list))
                            if krw > 5000:
                                upbit.buy_market_order(i, krw*0.9995)

        elif start_time2<now<end_time2 - timedelta(minutes=20):
            url = "https://www.coingecko.com/ko/거래소/upbit"
            bs = BeautifulSoup(requests.get(url).text,'html.parser')
            interest = []
            ticker_temp = bs.find_all("a", attrs={"rel":"nofollow noopener", "class":"mr-1"})
            for j in range(15):
                interest.append('KRW-' + list(ticker_temp[j])[0][1:-5])
            for i in interest:
                bestk = get_bestk(i)
                target_price = get_target_price(i,bestk)
                ma15 = get_ma15(i)
                current_price = get_current_price(i)
                print(i,target_price)
                if len(bought_list) < 5 :
                    if i not in bought_list2:
                        if target_price < current_price and ma15 < current_price:
                            bought_list.append(i)
                            bought_list1.append(i)
                            bought_list2.append(i)
                            krw = get_balance('KRW')
                            krw = krw/(6-len(bought_list))
                            if krw > 5000:
                                upbit.buy_market_order(i, krw*0.9995)
        elif len(bought_list2) == 10 and now == end_time2 - timedelta(minutes=20):
            bought_list2 = []

        else:
            search = 'KRW-'
            for i, word in enumerate(bought_list):
                if search in word:
                    bought_list[i] = word.strip(search)
            
            for j in range(len(bought_list1)):
                waves = get_balance(bought_list[j])
                upbit.sell_market_order(bought_list[j],waves*0.9995)
            bought_list = []
            bought_list1 = []
        time.sleep(2)         
    except Exception as e:
        print(e)
        time.sleep(1)