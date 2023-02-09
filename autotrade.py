import pyupbit
import requests
from bs4 import BeautifulSoup
from pytz import timezone
from datetime import datetime, timedelta
import numpy as np
import time
import schedule 

access = "cpaPaCmTIDCqvxX6pFmI7DjStWREyVunKg8R6qs6"
secret = "JCclRlsEJb93TGeDRIEjbKLsTmyP8UapqGFmJBRA"

def get_target_price(ticker, k):
    """Fetch target purchase price using volatility breakout strategy"""
    df = pyupbit.get_ohlcv(ticker, interval="minute240", count=8)
    df1 = df.iloc[:-1]
    target_price = df.iloc[6]['close'] + (df1['high'].max() - df1['low'].min()) * k
    return target_price

def get_risk_price(ticker, k):
    """Fetch target purchase price using volatility breakout strategy"""
    df = pyupbit.get_ohlcv(ticker, interval="minute240", count=8)
    df1 = df.iloc[:-1]
    target_price = df.iloc[6]['close'] + (df1['high'].max() - df1['low'].min()) * k
    risk_price=(target_price + df1['low'].min())*0.5
    return risk_price

def get_ma15(ticker):
    """Fetch 15-day moving average"""
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

def sell_all(coin) :
    """전량매도"""
    balance = upbit.get_balance(coin)
    price = pyupbit.get_current_price(coin)
    if price * balance >= 5000 :
        print(upbit.sell_market_order(coin, balance))

def get_current_price(ticker):
    """Fetch the current price"""
    return pyupbit.get_orderbook(ticker=ticker)["orderbook_units"][0]["ask_price"]

def get_start_time(ticker):
    """Fetch the start time"""
    df = pyupbit.get_ohlcv(ticker, interval="day", count=1)
    start_time = df.index[0]
    return start_time

def get_ticker_list(url):
    """Fetch the ticker list from the specified URL"""
    try:
        res = requests.get(url)
        res.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"An error occurred while fetching the URL: {e}")
        return []

    bs = BeautifulSoup(res.text,'html.parser')
    selector = "tbody td div a"
    columns = bs.select(selector)

    ticker_list1 = [x.text.strip().replace('/','-') for x in columns]

    def change_pair(pair):
        """Reverse the order of symbols in each pair"""
        return "-".join(pair.split("-")[::-1])

    ticker_list = [change_pair(pair) for pair in ticker_list1]
    ticker_list = [x for x in ticker_list if x.strip()]
    
    return ticker_list

def reset():
    KRW_bought_list=[]
    KRWsv_bought_list=[]
    return KRW_bought_list,KRWsv_bought_list

# 로그인
upbit = pyupbit.Upbit(access, secret)
print("autotrade start")

#리스트 초기화
schedule.every().day.at("00:57").do(reset)
schedule.every().day.at("04:57").do(reset)
schedule.every().day.at("08:57").do(reset)
schedule.every().day.at("12:57").do(reset)
schedule.every().day.at("16:57").do(reset)
schedule.every().day.at("20:57").do(reset)

#자동매매 시작

KRW_bought_list = []
KRWsv_bought_list = []


# URL to
url = "https://coinmarketcap.com/ko/exchanges/upbit/"
ticker_list = get_ticker_list(url)

while True:
  try:
    schedule.run_pending()
    now = datetime.now()
    start_time = get_start_time("KRW-BTC")
    new_start_time = start_time + timedelta(days=1)
    start_time1 = start_time + timedelta(minutes=10)
    start_time2 = start_time1 + timedelta(hours=4)
    start_time3 = start_time2 + timedelta(hours=4)
    start_time4 = start_time3 + timedelta(hours=4)
    start_time5 = new_start_time - timedelta(hours=7,minutes=50)
    start_time6 = start_time5 + timedelta(hours=4)
    end_time1 = start_time1 + timedelta(hours=3,minutes=45)
    end_time2 = start_time2 + timedelta(hours=3,minutes=45)
    end_time3 = start_time3 + timedelta(hours=3,minutes=45)
    end_time4 = start_time4 + timedelta(hours=3,minutes=45)
    end_time5 = start_time5 + timedelta(hours=3,minutes=45)
    end_time6 = start_time6 + timedelta(hours=3,minutes=45)

    if start_time1<now<end_time1:
      ticker_list = get_ticker_list(url)
      ticker_list = ticker_list[:30]
      if 'KRW-BTT' in ticker_list:
        ticker_list.remove('KRW-BTT')
      for i in ticker_list:
        if len(KRW_bought_list) < 5:
          target_price = get_target_price(i,0.5)
          risk_price = get_risk_price(i,0.5)
          ma15 = get_ma15(i)
          current_price = get_current_price(i)
          if i.startswith('K'):
            if i in KRW_bought_list:
              if target_price*1.05 < current_price or risk_price > current_price:
                sell_all(i)
                KRWsv_bought_list.remove(i)
            if i not in KRW_bought_list:
              if target_price < current_price and ma15 < current_price:
                KRW_bought_list.append(i)
                KRWsv_bought_list.append(i)
                krw = get_balance('KRW')
                krw = krw/(6-len(KRW_bought_list))
                if krw > 5000:
                  upbit.buy_market_order(i,krw*0.9995)
          time.sleep(10)
    
    elif start_time2 < now < end_time2:
      ticker_list = get_ticker_list(url)
      ticker_list = ticker_list[:30]
      if 'KRW-BTT' in ticker_list:
        ticker_list.remove('KRW-BTT')
      for i in ticker_list:
        if len(KRW_bought_list) < 5:
          target_price = get_target_price(i,0.5)
          risk_price = get_risk_price(i,0.5)
          ma15 = get_ma15(i)
          current_price = get_current_price(i)
          if i.startswith('K'):
            if i in KRW_bought_list:
              if target_price*1.05 < current_price or risk_price > current_price:
                sell_all(i)
                KRWsv_bought_list.remove(i)
            if i not in KRW_bought_list:
              if target_price < current_price and ma15 < current_price:
                KRW_bought_list.append(i)
                KRWsv_bought_list.append(i)
                krw = get_balance('KRW')
                krw = krw/(6-len(KRW_bought_list))
                if krw > 5000:
                  upbit.buy_market_order(i,krw*0.9995)
          time.sleep(10)
    
    elif start_time3 < now < end_time3:
      ticker_list = get_ticker_list(url)
      ticker_list = ticker_list[:30]
      if 'KRW-BTT' in ticker_list:
        ticker_list.remove('KRW-BTT')
      for i in ticker_list:
        if len(KRW_bought_list) < 5:
          target_price = get_target_price(i,0.5)
          risk_price = get_risk_price(i,0.5)
          ma15 = get_ma15(i)
          current_price = get_current_price(i)
          if i.startswith('K'):
            if i in KRW_bought_list:
              if target_price*1.05 < current_price or risk_price > current_price:
                sell_all(i)
                KRWsv_bought_list.remove(i)
            if i not in KRW_bought_list:
              if target_price < current_price and ma15 < current_price:
                KRW_bought_list.append(i)
                KRWsv_bought_list.append(i)
                krw = get_balance('KRW')
                krw = krw/(6-len(KRW_bought_list))
                if krw > 5000:
                  upbit.buy_market_order(i,krw*0.9995)
          time.sleep(10)
    
    elif start_time4 < now < end_time4:
      ticker_list = get_ticker_list(url)
      ticker_list = ticker_list[:30]
      if 'KRW-BTT' in ticker_list:
        ticker_list.remove('KRW-BTT')
      for i in ticker_list:
        if len(KRW_bought_list) < 5:
          target_price = get_target_price(i,0.5)
          risk_price = get_risk_price(i,0.5)
          ma15 = get_ma15(i)
          current_price = get_current_price(i)
          if i.startswith('K'):
            if i in KRW_bought_list:
              if target_price*1.05 < current_price or risk_price > current_price:
                sell_all(i)
                KRWsv_bought_list.remove(i)
            if i not in KRW_bought_list:
              if target_price < current_price and ma15 < current_price:
                KRW_bought_list.append(i)
                KRWsv_bought_list.append(i)
                krw = get_balance('KRW')
                krw = krw/(6-len(KRW_bought_list))
                if krw > 5000:
                  upbit.buy_market_order(i,krw*0.9995)
          time.sleep(10)
    
    elif start_time5 < now < end_time5:
      ticker_list = get_ticker_list(url)
      ticker_list = ticker_list[:30]
      if 'KRW-BTT' in ticker_list:
        ticker_list.remove('KRW-BTT')
      for i in ticker_list:
        if len(KRW_bought_list) < 5:
          target_price = get_target_price(i,0.5)
          risk_price = get_risk_price(i,0.5)
          ma15 = get_ma15(i)
          current_price = get_current_price(i)
          if i.startswith('K'):
            if i in KRW_bought_list:
              if target_price*1.05 < current_price or risk_price > current_price:
                sell_all(i)
                KRWsv_bought_list.remove(i)
            if i not in KRW_bought_list:
              if target_price < current_price and ma15 < current_price:
                KRW_bought_list.append(i)
                KRWsv_bought_list.append(i)
                krw = get_balance('KRW')
                krw = krw/(6-len(KRW_bought_list))
                if krw > 5000:
                  upbit.buy_market_order(i,krw*0.9995)
          time.sleep(10)
    
    elif start_time6 < now < end_time6:
      ticker_list = get_ticker_list(url)
      ticker_list = ticker_list[:30]
      if 'KRW-BTT' in ticker_list:
        ticker_list.remove('KRW-BTT')
      for i in ticker_list:
        if len(KRW_bought_list) < 5:
          target_price = get_target_price(i,0.5)
          risk_price = get_risk_price(i,0.5)
          ma15 = get_ma15(i)
          current_price = get_current_price(i)
          if i.startswith('K'):
            if i in KRW_bought_list:
              if target_price*1.05 < current_price or risk_price > current_price:
                sell_all(i)
                KRWsv_bought_list.remove(i)
            if i not in KRW_bought_list:
              if target_price < current_price and ma15 < current_price:
                KRW_bought_list.append(i)
                KRWsv_bought_list.append(i)
                krw = get_balance('KRW')
                krw = krw/(6-len(KRW_bought_list))
                if krw > 5000:
                  upbit.buy_market_order(i,krw*0.9995)
          time.sleep(10)

    else:
      for i in KRWsv_bought_list:
        sell_all(i)
      KRW_bought_list = []
      KRWsv_bought_list = []

  except Exception as e:
    print(e)
    time.sleep(1)
