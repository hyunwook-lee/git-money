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
def get_ror(k, ticker, days=7):
    """ 특정 기간 동안의 수익률을 계산하는 함수 """
    df = pyupbit.get_ohlcv(ticker, count=days)
    if df is None or len(df) < days:
        return 0  # 데이터가 부족하면 0 반환

    df['range'] = (df['high'] - df['low']) * k
    df['target'] = df['open'] + df['range'].shift(1)

    df['ror'] = np.where(df['high'] > df['target'],
                         df['close'] / df['target'],
                         1)

    return df['ror'].cumprod().iloc[-2]  # 마지막 날의 누적 수익률 반환

def get_best_k_for_days(ticker, days):
    """ 특정 기간(days)에 대한 최적의 k 값 찾기 """
    best_k = 0.1
    best_ror = 0
    for k in np.arange(0.05, 1.0, 0.05):  # 0.05 단위로 더 세밀하게 탐색
        ror = get_ror(k, ticker, days)
        if ror > best_ror:
            best_ror = ror
            best_k = k
    return best_k

def get_optimal_k(ticker):
    """ 최근 7일, 14일, 30일 데이터를 활용하여 최적 k 값 도출 """
    k_7 = get_best_k_for_days(ticker, 7)
    k_14 = get_best_k_for_days(ticker, 14)
    k_30 = get_best_k_for_days(ticker, 30)

    # 평균을 내서 최종 k 값 결정 (최근 7일에 가중치를 더 줄 수도 있음)
    optimal_k = (k_7 * 0.5 + k_14 * 0.3 + k_30 * 0.2)
    
    return round(optimal_k, 2)  # 소수점 2자리까지 반올림
# API 오류 방지를 위한 안전한 가격 조회 함수
def get_current_price(ticker):
    """현재가 조회"""
    return pyupbit.get_orderbook(ticker=ticker)["orderbook_units"][0]["ask_price"]

# 목표 가격 및 리스크 가격 계산
def get_target_price(ticker, k):
    df = pyupbit.get_ohlcv(ticker, interval="day", count=2)
    return df.iloc[-2]['close'] + (df.iloc[-2]['high'] - df.iloc[-2]['low']) * k if df is not None else None

def get_risk_price(ticker, buy_price):
    return buy_price * 0.975 if buy_price else None  # 손절가 = 매수가 * 0.975 (-3.5%)

def get_profit_price(ticker, buy_price):
    return buy_price * 1.10 if buy_price else None  # 익절가 = 매수가 * 1.10 (+10%)

# 15일 이동 평균 + RSI 지표 추가
def get_ma15(ticker):
    df = pyupbit.get_ohlcv(ticker, interval="day", count=15)
    return df['close'].rolling(15).mean().iloc[-1] if df is not None else None

def get_rsi(ticker, period=14):
    df = pyupbit.get_ohlcv(ticker, interval="day", count=period+1)
    if df is not None:
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(period).mean()
        rs = gain / loss
        return 100 - (100 / (1 + rs)).iloc[-1]
    return None

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

# 매도 함수
def sell_coin(coin, percent=1.0):
    asset = coin.split('-')[1]  # 'KRW-XXX' -> 'XXX'
    balance = get_balance(asset)
    price = get_current_price(coin)

    if balance is None or price is None:
        logging.error(f"{coin} 매도 실패! 잔고 또는 현재가 조회 오류")
        return

    balance = round(balance, 8)
    sell_amount = balance * percent
    sell_value = sell_amount * price

    if sell_value < 5000:
        logging.info(f"{coin} 매도 불가! 최소 주문 금액 부족 (보유 금액: {sell_value}원)")
        return

    order_result = upbit.sell_market_order(coin, sell_amount*0.9995)
    if order_result:
        logging.info(f"{coin} 매도 결과: {order_result}")
    else:
        logging.error(f"{coin} 매도 실패! API 응답 없음")

    time.sleep(0.5)


# 로그인
upbit = pyupbit.Upbit(access, secret)
logging.info("Auto trade started")

# 자동 매매 시작
KRW_bought_list = []
KRW_sold_list = []
buy_prices = {}

# 일정 시간마다 매도 실행
schedule.every().day.at("09:55").do(lambda: (KRW_bought_list.clear(), KRW_sold_list.clear()))

while True:
    try:
        schedule.run_pending()
        now = datetime.now()

        # ✅ 10시에서 다음날 8시반 까지 매수
        if now.hour >= 10 or now.hour < 8 or (now.hour == 8 and now.minute < 30):
            for i in ticker_list:
                current_price = get_current_price(i)
                if current_price is None:
                    continue

                # ✅ 손절 체크
                if i in KRW_bought_list:
                    buy_price = buy_prices.get(i, None)
                    risk_price = get_risk_price(i, buy_price)

                    if risk_price is not None and current_price < risk_price:
                        logging.info(f"{i} 손절 매도! 현재가 {current_price} < 손절가 {risk_price}")
                        sell_coin(i)
                        KRW_sold_list.append(i)
                        KRW_bought_list.remove(i)
                        
                    elif profit_price is not None and current_price > profit_price:
                        logging.info(f"{i} 익절 매도! 현재가 {current_price} > 익절가 {profit_price}")
                        sell_coin(i)
                        KRW_sold_list.append(i)
                        KRW_bought_list.remove(i)

                # ✅ 매수 로직
                if len(KRW_bought_list) < 5 and i not in KRW_sold_list and i not in KRW_bought_list:
                    if get_balance(i.split('-')[1]) > 0:  # 이미 보유 중이면 매수하지 않음
                        continue
                        
                    k = get_optimal_k(i)
                    target_price = get_target_price(i, k)
                    ma15 = get_ma15(i)
                    rsi = get_rsi(i)

                    if target_price is None or ma15 is None or rsi is None:
                        continue  # 데이터 부족하면 건너뜀

                    if target_price < current_price and ma15 < current_price and 30 < rsi < 70:
                        KRW_bought_list.append(i)
                        krw = get_balance('KRW') / (6 - len(KRW_bought_list))

                        if krw > 5000:
                            upbit.buy_market_order(i, krw * 0.9995)
                            buy_prices[i] = current_price
                            logging.info(f"{i} 매수 실행! 매수가: {current_price}, 투자 금액: {krw}")
                
                time.sleep(3)
        
        else:
            for i in KRW_bought_list:
                sell_coin(i)

            KRW_bought_list = []
            KRW_sold_list = []
            
            time.sleep(3)

    except Exception as e:
        logging.error(f"오류 발생: {e}")
        time.sleep(1)
