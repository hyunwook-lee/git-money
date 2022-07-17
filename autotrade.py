from re import search
from webbrowser import get
import pyupbit
from datetime import datetime,timedelta
import numpy as np
import time
import schedule 

access = "gibkBxgdWxY0GC0yO2psvAIp4BBNHp2i6OUA4f4x"
secret = "skXnZ5OOjkh8nD1718xPWuurxpA2vEamc6jLMRzA"

def get_target_price(ticker, k):
    """변동성 돌파 전략으로 매수 목표가 조회"""
    df = pyupbit.get_ohlcv(ticker, interval="minute240", count=2)
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

def get_start_time(ticker):
    """시작 시간 조회"""
    df = pyupbit.get_ohlcv(ticker, interval="day", count=1)
    start_time = df.index[0]
    return start_time

def sell_all(coin) :
    """전량매도"""
    balance = upbit.get_balance(coin)
    price = pyupbit.get_current_price(coin)
    if price * balance >= 5000 :
        print(upbit.sell_market_order(coin, balance))

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

while True:
    try:
        schedule.run_pending()
        now = datetime.now()
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

        if start_time1<now<end_time1 :
            a=pyupbit.get_tickers(fiat="KRW")
            for i in a:
                if len(bought_list) < 5:
                    new_now = datetime.now()
                    if new_now.hour == 12 and new_now.minute == 55:
                        break
                    target_price = get_target_price(i,0.5)
                    ma15 = get_ma15(i)
                    current_price = get_current_price(i)
                    if i not in bought_list:
                        if target_price < current_price and ma15 < current_price:
                            bought_list.append(i)
                            krw = get_balance('KRW')
                            krw = krw/(6-len(bought_list))
                            if krw > 5000:
                                upbit.buy_market_order(i,krw*0.9995)
            time.sleep(30)
        
        if start_time2<now<end_time2 :
            a=pyupbit.get_tickers(fiat="KRW")
            for i in a:
                if len(bought_list) < 5:
                    new_now = datetime.now()
                    if new_now.hour == 16 and new_now.minute == 55:
                        break
                    target_price = get_target_price(i,0.5)
                    ma15 = get_ma15(i)
                    current_price = get_current_price(i)
                    if i not in bought_list:
                        if target_price < current_price and ma15 < current_price:
                            bought_list.append(i)
                            krw = get_balance('KRW')
                            krw = krw/(6-len(bought_list))
                            if krw > 5000:
                                upbit.buy_market_order(i,krw*0.9995)
            time.sleep(30)
        
        if start_time3<now<end_time3 :
            a=pyupbit.get_tickers(fiat="KRW")
            for i in a:
                if len(bought_list) < 5:
                    new_now = datetime.now()
                    if new_now.hour == 20 and new_now.minute == 55:
                        break
                    target_price = get_target_price(i,0.5)
                    ma15 = get_ma15(i)
                    current_price = get_current_price(i)
                    if i not in bought_list:
                        if target_price < current_price and ma15 < current_price:
                            bought_list.append(i)
                            krw = get_balance('KRW')
                            krw = krw/(6-len(bought_list))
                            if krw > 5000:
                                upbit.buy_market_order(i,krw*0.9995)
            time.sleep(30)
        
        if start_time4<now<end_time4 :
            a=pyupbit.get_tickers(fiat="KRW")
            for i in a:
                if len(bought_list) < 5:
                    new_now = datetime.now()
                    if new_now.hour == 0 and new_now.minute == 55:
                        break
                    target_price = get_target_price(i,0.5)
                    ma15 = get_ma15(i)
                    current_price = get_current_price(i)
                    if i not in bought_list:
                        if target_price < current_price and ma15 < current_price:
                            bought_list.append(i)
                            krw = get_balance('KRW')
                            krw = krw/(6-len(bought_list))
                            if krw > 5000:
                                upbit.buy_market_order(i,krw*0.9995)
            time.sleep(30)
        
        if start_time5<now<end_time5 :
            a=pyupbit.get_tickers(fiat="KRW")
            for i in a:
                if len(bought_list) < 5:
                    new_now = datetime.now()
                    if new_now.hour == 4 and new_now.minute == 55:
                        break
                    target_price = get_target_price(i,0.5)
                    ma15 = get_ma15(i)
                    current_price = get_current_price(i)
                    if i not in bought_list:
                        if target_price < current_price and ma15 < current_price:
                            bought_list.append(i)
                            krw = get_balance('KRW')
                            krw = krw/(6-len(bought_list))
                            if krw > 5000:
                                upbit.buy_market_order(i,krw*0.9995)
            time.sleep(30)
        
        if start_time6<now<end_time6 :
            a=pyupbit.get_tickers(fiat="KRW")
            for i in a:
                if len(bought_list) < 5:
                    new_now = datetime.now()
                    if new_now.hour == 8 and new_now.minute == 55:
                        break
                    target_price = get_target_price(i,0.5)
                    ma15 = get_ma15(i)
                    current_price = get_current_price(i)
                    if i not in bought_list:
                        if target_price < current_price and ma15 < current_price:
                            bought_list.append(i)
                            krw = get_balance('KRW')
                            krw = krw/(6-len(bought_list))
                            if krw > 5000:
                                upbit.buy_market_order(i,krw*0.9995)
            time.sleep(30)

        if now.hour == 12 and now.minute == 56 :
            for i in bought_list:
                sell_all(i)
            bought_list = []

        if now.hour == 16 and now.minute == 56 :
            for i in bought_list:
                sell_all(i)
            bought_list = []
        
        if now.hour == 20 and now.minute == 56 :
            for i in bought_list:
                sell_all(i)
            bought_list = []
        
        if now.hour == 0 and now.minute == 56 :
            for i in bought_list:
                sell_all(i)
            bought_list = []
        
        if now.hour == 4 and now.minute == 56 :
            for i in bought_list:
                sell_all(i)
            bought_list = []
        
        if now.hour == 8 and now.minute == 56 :
            for i in bought_list:
                sell_all(i)
            bought_list = []

        time.sleep(2)         
    except Exception as e:
        print(e)
        time.sleep(1)