import pyupbit
import requests
from bs4 import BeautifulSoup
from pytz import timezone
from datetime import datetime, timedelta
import numpy as np
import time
import schedule
import logging

# 로그 설정
logging.basicConfig(filename='trading_bot.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

access = "UeYK9fTGpD01T1oC3Dm4kJSNxq2lS6jbuy6NETxV"
secret = "ARaqQQFOx82OERax8bLyPy5ccxXG91aOggjYzrxu"

# 특정 ticker의 최적 k 값 계산
def get_ror(k=0.5, ticker="KRW-BTC"):
    df = pyupbit.get_ohlcv(ticker, count=7)
    df['range'] = (df['high'] - df['low']) * k
    df['target'] = df['open'] + df['range'].shift(1)
    
    df['ror'] = np.where(df['high'] > df['target'],
                         df['close'] / df['target'],
                         1)

    ror = df['ror'].cumprod()[-2]
    return ror

def get_optimal_k(ticker):
    best_k = 0.1
    best_ror = 0
    for k in np.arange(0.1, 1.0, 0.1):
        ror = get_ror(k, ticker)
        if ror > best_ror:
            best_ror = ror
            best_k = k
    return best_k

# 목표 가격 및 리스크 가격 계산
def get_target_price(ticker, k):
    df = pyupbit.get_ohlcv(ticker, interval="day", count=2)
    return df.iloc[-2]['close'] + (df.iloc[-2]['high'] - df.iloc[-2]['low']) * k

def get_risk_price(ticker, k):
    df = pyupbit.get_ohlcv(ticker, interval="day", count=2)
    return (df.iloc[-2]['close'] + df.iloc[-2]['low']) * 0.5

# 15일 이동 평균 + RSI 지표 추가
def get_ma15(ticker):
    df = pyupbit.get_ohlcv(ticker, interval="day", count=15)
    return df['close'].rolling(15).mean().iloc[-1]

def get_rsi(ticker, period=14):
    df = pyupbit.get_ohlcv(ticker, interval="day", count=period+1)
    delta = df['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs)).iloc[-1]

def get_balance(ticker):
    balances = upbit.get_balances()
    for b in balances:
        if b['currency'] == ticker:
            return float(b['balance']) if b['balance'] is not None else 0
    return 0

# 비율 매도 전략 적용
def sell_partial():
    for coin in KRW_bought_list[:]:
        balance = upbit.get_balance(coin)
        price = pyupbit.get_current_price(coin)
        if price * balance >= 5000:
            sell_amount = balance * 0.5  # 50% 매도
            upbit.sell_market_order(coin, sell_amount)
            if coin not in KRW_sold_list:
                KRW_sold_list.append(coin)

# 최종 전량 매도
def sell_all():
    for coin in KRW_bought_list[:]:
        balance = upbit.get_balance(coin)
        if balance > 0:
            upbit.sell_market_order(coin, balance)
            KRW_sold_list.append(coin)
            KRW_bought_list.remove(coin)

# 현재가 가져오기
def get_current_price(ticker):
    return pyupbit.get_orderbook(ticker=ticker)["orderbook_units"][0]["ask_price"]

# 트레일링 스탑 손절가 계산
def get_trailing_stop(target_price, current_price, trailing_stop_rate=0.95):
    return max(target_price * trailing_stop_rate, current_price * trailing_stop_rate)

# 거래소 티커 목록 가져오기 (최적화)
def get_ticker_list():
    url = "https://coinmarketcap.com/ko/exchanges/upbit/"
    try:
        res = requests.get(url)
        res.raise_for_status()
    except requests.exceptions.RequestException as e:
        logging.error(f"URL 가져오기 오류: {e}")
        return []
    bs = BeautifulSoup(res.text, 'html.parser')
    ticker_list = [x.text.strip().replace('/', '-') for x in bs.select("tbody td div a")]
    return [x.split('-')[1] + '-' + x.split('-')[0] for x in ticker_list if x.strip()]

# 로그인
upbit = pyupbit.Upbit(access, secret)
logging.info("Auto trade started")

# 자동 매매 시작
KRW_bought_list = []
KRW_sold_list = []

# 매도 스케줄 설정 (08:40 50% 매도, 08:55 전량 매도)
schedule.every().day.at("08:40").do(sell_partial)
schedule.every().day.at("08:55").do(sell_all)

# 매도, 매수 리스트 초기화 (09:00 기준)
schedule.every().day.at("09:00").do(lambda: (KRW_bought_list.clear(), KRW_sold_list.clear()))

while True:
    try:
        schedule.run_pending()
        now = datetime.now()
        ticker_list = get_ticker_list()[:30]
        if 'KRW-BTT' in ticker_list:
            ticker_list.remove('KRW-BTT')
        
        # 09:00~08:40 사이에만 매수 진행 (08:40~09:00 제외)
        if now.hour >= 9 or now.hour < 8:
            for i in ticker_list:
                if len(KRW_bought_list) < 5 and i not in KRW_sold_list:
                    k = get_optimal_k(i)
                    target_price = get_target_price(i, k)
                    risk_price = get_risk_price(i, k)
                    ma15 = get_ma15(i)
                    rsi = get_rsi(i)
                    current_price = get_current_price(i)
                    trailing_stop = get_trailing_stop(target_price, current_price)
                    
                    if i.startswith('K'):
                        if i in KRW_bought_list:
                            if trailing_stop > current_price or risk_price > current_price:
                                upbit.sell_market_order(i, get_balance(i))
                                KRW_sold_list.append(i)
                                KRW_bought_list.remove(i)
                        elif target_price < current_price and ma15 < current_price and rsi < 70:
                            KRW_bought_list.append(i)
                            krw = get_balance('KRW') / (6 - len(KRW_bought_list))
                            if krw > 5000:
                                upbit.buy_market_order(i, krw * 0.9995)
                time.sleep(10)

    except Exception as e:
        logging.error(f"오류 발생: {e}")
        time.sleep(1)
