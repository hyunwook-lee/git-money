import time
import pyupbit
import datetime
import numpy as np
import requests
from bs4 import BeautifulSoup
import time

access = "AvgwKrDgZmTSwsmQHTxpno9UzZa0ePOUVx6ULMUv"
secret = "pvXS0u1VMALxNFQ26Mmc2oEWgk49gMexklvcxZgv"

def get_target_price(ticker, k):
    """변동성 돌파 전략으로 매수 목표가 조회"""
    df = pyupbit.get_ohlcv(ticker, interval="day", count=2)
    target_price = df.iloc[0]['close'] + (df.iloc[0]['high'] - df.iloc[0]['low']) * k
    return target_price

def get_start_time(ticker):
    """시작 시간 조회"""
    df = pyupbit.get_ohlcv(ticker, interval="day", count=1)
    start_time = df.index[0]
    return start_time

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



# 로그인
upbit = pyupbit.Upbit(access, secret)
print("autotrade start")

#자동매매 시작

bought_list = []
bought_list1 = []
while True:
    try:
      now = datetime.datetime.now()
      start_time = get_start_time("KRW-WAVES")
      end_time = start_time + datetime.timedelta(days=1)
      
      if start_time < now < end_time - datetime.timedelta(minutes=5):
        url = "https://www.coingecko.com/ko/거래소/upbit"
        bs = BeautifulSoup(requests.get(url).text,'html.parser')
        interest = []
        ticker_temp = bs.find_all("a", attrs={"rel":"nofollow noopener", "class":"mr-1"})
        for j in range(10):
          interest.append('KRW-' + list(ticker_temp[j])[0][1:-5])
        for i in interest:
          bestk=get_bestk(i)
          target_price = get_target_price(i, bestk)
          ma15 = get_ma15(i)
          current_price = get_current_price(i)
          if len(bought_list) < 5 :
            if i not in bought_list:
              if target_price < current_price and ma15 < current_price:
                bought_list.append(i)
                bought_list1.append(i)
                krw = get_balance("KRW")
                krw = krw/(6-len(bought_list))
                if krw > 5000:
                  upbit.buy_market_order(i, krw*0.9995)                     
      else:
        search = 'KRW-'
        for i, word in enumerate(bought_list):
            if search in word: 
                bought_list[i] = word.strip(search)
        for j in range(len(bought_list1)):
            waves = get_balance(bought_list[j])
            upbit.sell_market_oreder(bought_list1[j],waves*0.9995)
        bought_list = []
        bought_list1 = []

      time.sleep(1)

    except Exception as e:
        print(e)
        time.sleep(1)