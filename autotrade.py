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

# 시가총액 상위 30개 코인 고정 리스트
ticker_list = [
    "KRW-ETH", "KRW-XRP", "KRW-SOL", "KRW-DOGE", "KRW-ADA", "KRW-TRX", "KRW-LINK", "KRW-HBAR", "KRW-XLM",
    "KRW-AVAX", "KRW-SHIB", "KRW-SUI", "KRW-DOT", "KRW-BCH", "KRW-UNI", "KRW-NEAR", "KRW-APT", "KRW-ONDO", "KRW-AAVE",
    "KRW-ETC", "KRW-TRUMP", "KRW-MNT", "KRW-VET", "KRW-POL", "KRW-ALGO", "KRW-CRO", "KRW-RENDER", "KRW-ATOM", "KRW-ARB"
]

# 특정 ticker의 최적 k 값 계산
def get_ror(k=0.5, ticker="KRW-BTC"):
    df = pyupbit.get_ohlcv(ticker, count=7)
    df['range'] = (df['high'] - df['low']) * k
    df['target'] = df['open'] + df['range'].shift(1)
    
    df['ror'] = np.where(df['high'] > df['target'],
                         df['close'] / df['target'],
                         1)

    ror = df['ror'].cumprod().iloc[-2]
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

def get_risk_price(ticker, buy_price):
    return buy_price * 0.96  # 손절가 = 매수가 * 0.96 (-4%)

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

def sell_partial():
    for coin in KRW_bought_list[:]:
        balance = upbit.get_balance(coin)
        price = pyupbit.get_current_price(coin)
        if price * balance >= 5000:
            upbit.sell_market_order(coin, balance * 0.5)  # 50% 매도

def sell_all():
    for coin in KRW_bought_list[:]:
        balance = upbit.get_balance(coin)
        price = pyupbit.get_current_price(coin)
        if price * balance >= 5000:
            upbit.sell_market_order(coin, balance)  # 남은 수량 전량 매도
            KRW_sold_list.append(coin)
            KRW_bought_list.remove(coin)

# 현재가 가져오기
def get_current_price(ticker):
    return pyupbit.get_orderbook(ticker=ticker)["orderbook_units"][0]["ask_price"]

# 로그인
upbit = pyupbit.Upbit(access, secret)
logging.info("Auto trade started")

# 자동 매매 시작
KRW_bought_list = []
KRW_sold_list = []

# 08:40~08:55 동안 반복적으로 매도 실행
schedule.every().day.at("08:40").do(lambda: schedule.every(5).minutes.until("08:55").do(sell_partial))
schedule.every().day.at("08:55").do(sell_all)

# 매도, 매수 리스트 초기화 (09:00 기준)
schedule.every().day.at("09:00").do(lambda: (KRW_bought_list.clear(), KRW_sold_list.clear()))

buy_prices = {}

while True:
    try:
        schedule.run_pending()
        now = datetime.now()
        
        # 09:00~08:30 사이에만 매수 진행 (08:30~09:00 제외)
        if now.hour >= 9 or (now.hour == 8 and now.minute < 30):
            for i in ticker_list:
                if len(KRW_bought_list) < 5 and i not in KRW_sold_list:
                    k = get_optimal_k(i)
                    target_price = get_target_price(i, k)
                    current_price = get_current_price(i)
                    ma15 = get_ma15(i)
                    rsi = get_rsi(i)
                    
                    if i in KRW_bought_list:
                        risk_price = get_risk_price(i, buy_prices[i])  # 손절가 설정
                        if current_price < risk_price:
                            upbit.sell_market_order(i, get_balance(i) * 0.5)  # 비율 매도 전략
                            if get_balance(i) * 0.5 < 5000:
                                KRW_sold_list.append(i)
                                KRW_bought_list.remove(i)
                    
                    elif target_price < current_price and ma15 < current_price and rsi < 70:
                        KRW_bought_list.append(i)
                        krw = get_balance('KRW') / (6 - len(KRW_bought_list))
                        if krw > 5000:
                            upbit.buy_market_order(i, krw * 0.9995)
                            buy_prices[i] = current_price  # 매수가 기록
                time.sleep(10)

    except Exception as e:
        logging.error(f"오류 발생: {e}")
        time.sleep(1)
