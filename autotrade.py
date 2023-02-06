import pyupbit
import requests
from bs4 import BeautifulSoup
from pytz import timezone
from datetime import datetime, timedelta
import numpy as np
import time
import schedule 

access = "gibkBxgdWxY0GC0yO2psvAIp4BBNHp2i6OUA4f4x"
secret = "skXnZ5OOjkh8nD1718xPWuurxpA2vEamc6jLMRzA"

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
    bought_list=[]
    return bought_list

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

bought_list = []

# Start time
start_time = get_start_time("KRW-BTC")
start_time1 = start_time.replace(hour=9, minute=15, second=0, microsecond=0)
end_time1 = start_time.replace(hour=13, minute=15, second=0, microsecond=0)

# Localize times to Korea Standard Time
KST = timezone('Asia/Seoul')
start_time1 = KST.localize(start_time1)
end_time1 = KST.localize(end_time1)

# Current time
now = datetime.now(timezone('Asia/Seoul'))

# List of bought tickers
bought_list = []

# URL to
url = "https://coinmarketcap.com/ko/exchanges/upbit/"
ticker_list = get_ticker_list(url)

while True:
  try:
    schedule.run_pending()
    now = datetime.now(timezone('Asia/Seoul'))
    start_time = get_start_time("KRW-BTC")
    new_start_time = start_time + timedelta(days=1)
    start_time1 = start_time.replace(hour=9, minute=10, second=0, microsecond=0)
    start_time2 = start_time.replace(hour=13,minute=10,second=0,microsecond=0)
    start_time3 = start_time.replace(hour=17,minute=10,second=0,microsecond=0)
    start_time4 = start_time.replace(hour=21,minute=10,second=0,microsecond=0)
    start_time5 = new_start_time.replace(hour=1,minute=10,second=0,microsecond=0)
    start_time6 = new_start_time.replace(hour=5,minute=10,second=0,microsecond=0)
    end_time1 = start_time.replace(hour=12, minute=55, second=0, microsecond=0)
    end_time2 = start_time.replace(hour=16, minute=55, second=0, microsecond=0)
    end_time3 = start_time.replace(hour=20, minute=55, second=0, microsecond=0)
    end_time4 = new_start_time.replace(hour=0, minute=55, second=0, microsecond=0)
    end_time5 = new_start_time.replace(hour=4, minute=55, second=0, microsecond=0)
    end_time6 = new_start_time.replace(hour=8, minute=55, second=0, microsecond=0)

    if start_time1<now<end_time1:
      ticker_list = get_ticker_list(url)
      if 'KRW-BTT' in ticker_list:
        ticker_list.remove('KRW-BTT')
      for i in ticker_list:
        if len(bought_list) < 5:
          target_price = get_target_price(i,0.5)
          risk_price = get_risk_price(i,0.5)
          ma15 = get_ma15(i)
          current_price = get_current_price(i)
          if current_price < risk_price:
            sell_all(i)
          if i not in bought_list:
            if target_price < current_price and ma15 < current_price:
              bought_list.append(i)
              krw = get_balance('KRW')
              krw = krw/(6-len(bought_list))
              if krw > 5000:
                upbit.buy_market_order(i,krw*0.9995)
          time.sleep(10)
    
    elif start_time2 < now < end_time2:
      ticker_list = get_ticker_list(url)
      if 'KRW-BTT' in ticker_list:
        ticker_list.remove('KRW-BTT')
      for i in ticker_list:
        if len(bought_list) < 5:
          target_price = get_target_price(i,0.5)
          risk_price = get_risk_price(i,0.5)
          ma15 = get_ma15(i)
          current_price = get_current_price(i)
          if current_price < risk_price:
            sell_all(i)
          if i not in bought_list:
            if target_price < current_price and ma15 < current_price:
              bought_list.append(i)
              krw = get_balance('KRW')
              krw = krw/(6-len(bought_list))
              if krw > 5000:
                upbit.buy_market_order(i,krw*0.9995)
          time.sleep(10)
    
    elif start_time3 < now < end_time3:
      ticker_list = get_ticker_list(url)
      if 'KRW-BTT' in ticker_list:
        ticker_list.remove('KRW-BTT')
      for i in ticker_list:
        if len(bought_list) < 5:
          target_price = get_target_price(i,0.5)
          risk_price = get_risk_price(i,0.5)
          ma15 = get_ma15(i)
          current_price = get_current_price(i)
          if current_price < risk_price:
            sell_all(i)
          if i not in bought_list:
            if target_price < current_price and ma15 < current_price:
              bought_list.append(i)
              krw = get_balance('KRW')
              krw = krw/(6-len(bought_list))
              if krw > 5000:
                upbit.buy_market_order(i,krw*0.9995)
          time.sleep(10)
    
    elif start_time4 < now < end_time4:
      ticker_list = get_ticker_list(url)
      if 'KRW-BTT' in ticker_list:
        ticker_list.remove('KRW-BTT')
      for i in ticker_list:
        if len(bought_list) < 5:
          target_price = get_target_price(i,0.5)
          risk_price = get_risk_price(i,0.5)
          ma15 = get_ma15(i)
          current_price = get_current_price(i)
          if current_price < risk_price:
            sell_all(i)
          if i not in bought_list:
            if target_price < current_price and ma15 < current_price:
              bought_list.append(i)
              krw = get_balance('KRW')
              krw = krw/(6-len(bought_list))
              if krw > 5000:
                upbit.buy_market_order(i,krw*0.9995)
          time.sleep(10)
    
    elif start_time5 < now < end_time5:
      ticker_list = get_ticker_list(url)
      if 'KRW-BTT' in ticker_list:
        ticker_list.remove('KRW-BTT')
      for i in ticker_list:
        if len(bought_list) < 5:
          target_price = get_target_price(i,0.5)
          risk_price = get_risk_price(i,0.5)
          ma15 = get_ma15(i)
          current_price = get_current_price(i)
          if current_price < risk_price:
            sell_all(i)
          if i not in bought_list:
            if target_price < current_price and ma15 < current_price:
              bought_list.append(i)
              krw = get_balance('KRW')
              krw = krw/(6-len(bought_list))
              if krw > 5000:
                upbit.buy_market_order(i,krw*0.9995)
          time.sleep(10)
    
    elif start_time6 < now < end_time6:
      ticker_list = get_ticker_list(url)
      if 'KRW-BTT' in ticker_list:
        ticker_list.remove('KRW-BTT')
      for i in ticker_list:
        if len(bought_list) < 5:
          target_price = get_target_price(i,0.5)
          risk_price = get_risk_price(i,0.5)
          ma15 = get_ma15(i)
          current_price = get_current_price(i)
          if current_price < risk_price:
            sell_all(i)
          if i not in bought_list:
            if target_price < current_price and ma15 < current_price:
              bought_list.append(i)
              krw = get_balance('KRW')
              krw = krw/(6-len(bought_list))
              if krw > 5000:
                upbit.buy_market_order(i,krw*0.9995)
          time.sleep(10)

    else:
      for i in bought_list:
        sell_all(i)
      bought_list = []

  except Exception as e:
    print(e)
    time.sleep(1)
