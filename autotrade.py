import pyupbit
import requests
from pytz import timezone
from datetime import datetime, timedelta
import numpy as np
import time
import schedule
import logging
import concurrent.futures

# 로그 설정
logging.basicConfig(filename='trading_bot.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

access = "UeYK9fTGpD01T1oC3Dm4kJSNxq2lS6jbuy6NETxV"
secret = "ARaqQQFOx82OERax8bLyPy5ccxXG91aOggjYzrxu"

# 시가총액 상위 30개 코인 고정 리스트
ticker_list = [
    "KRW-ETH", "KRW-XRP", "KRW-SOL", "KRW-DOGE", "KRW-ADA", "KRW-TRX", "KRW-LINK", "KRW-HBAR", "KRW-XLM",
    "KRW-AVAX", "KRW-SUI", "KRW-DOT", "KRW-BCH", "KRW-UNI", "KRW-NEAR", "KRW-APT", "KRW-ONDO", "KRW-AAVE",
    "KRW-ETC", "KRW-TRUMP", "KRW-MNT", "KRW-VET", "KRW-POL", "KRW-ALGO", "KRW-CRO", "KRW-RENDER", "KRW-ATOM", "KRW-ARB"
]

# 특정 ticker의 최적 k 값 계산
# ✅ 특정 기간 동안 최적의 k 값 찾기 (기존 코드 최적화)
def get_best_k_for_days(ticker, days):
    df = pyupbit.get_ohlcv(ticker, count=days)
    if df is None or len(df) < days:
        return 0  # 데이터 부족 시 0 반환

    best_k = 0.1
    best_ror = 0
    for k in np.arange(0.05, 1.0, 0.05):  # 0.05 단위로 탐색
        df['range'] = (df['high'] - df['low']) * k
        df['target'] = df['open'] + df['range'].shift(1)
        df['ror'] = np.where(df['high'] > df['target'],
                             df['close'] / df['target'],
                             1)
        ror = df['ror'].cumprod().iloc[-2]  # 마지막 날 수익률
        if ror > best_ror:
            best_ror = ror
            best_k = k
    return best_k

# ✅ 최적 K 값을 병렬 처리 (멀티스레딩 사용)
def get_optimal_k_parallel(ticker_list):
    global k_cache  # 캐시 사용

    def calculate_k(ticker):
        k_7 = get_best_k_for_days(ticker, 7)
        k_14 = get_best_k_for_days(ticker, 14)
        k_30 = get_best_k_for_days(ticker, 30)
        optimal_k = round((k_7 * 0.5 + k_14 * 0.3 + k_30 * 0.2), 2)
        return ticker, optimal_k

    with concurrent.futures.ThreadPoolExecutor() as executor:
        results = executor.map(calculate_k, ticker_list)

    # 결과를 캐시에 저장
    for ticker, optimal_k in results:
        k_cache[ticker] = optimal_k

# ✅ K 값 미리 계산 후 사용
def get_k_value(ticker):
    return k_cache.get(ticker, 0.5)  # 캐시에 없으면 기본값 0.5 사용
    
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

def reset_daily_data():
    global buy_prices
    global k_cache
    buy_prices.clear()  # 딕셔너리 초기화
    k_cache.clear()
    
# 로그인
upbit = pyupbit.Upbit(access, secret)
logging.info("Auto trade started")

# 자동 매매 시작
KRW_bought_list = []
KRW_sold_list = []
buy_prices = {}
k_cache = {}
get_optimal_k_parallel(ticker_list)

# 일정 시간마다 매도 실행
schedule.every().day.at("08:57").do(lambda: (KRW_bought_list.clear(), KRW_sold_list.clear()))
schedule.every().day.at("08:55").do(reset_daily_data)

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
                        
                    k = get_k_value(i)
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
                
        if (now.hour == 9 and now.minute >= 55) or (now.hour == 10 and now.minute == 0):
            get_optimal_k_parallel(ticker_list)
        
        else:
            for i in KRW_bought_list:
                sell_coin(i)
                time.sleep(1)
                
            KRW_bought_list = []
            KRW_sold_list = []
            buy_prices = {}
            k_cache = {}
            
            time.sleep(3)

    except Exception as e:
        logging.error(f"오류 발생: {e}")
        time.sleep(1)
