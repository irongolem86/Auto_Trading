import time
import pyupbit
import datetime
import numpy as np
import requests

access = "sPlNdhKpz0UKC5mL1xRn6b04rPH5GAQuMp0iNlOf"
secret = "fxluWFXfEhgsnpwpz7eWweg9xvU4A9WXN0xOjSDk"
myToken = "xoxb-3046758207234-3032163309495-dovhhyCkZ3O4FcBcvJG5s8YD"

def post_message(token, channel, text):
    """슬랙 메시지 전송"""
    response = requests.post("https://slack.com/api/chat.postMessage",
    headers={"Authorization": "Bearer "+token},
    data={"channel": channel,"text": text}
    )

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
    """15일 이동 편균선 조회"""
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

def get_ror(k=0.5):
    """ k값에 따른 지난 일주일간 수익률 계산"""
    df = pyupbit.get_ohlcv("KRW-BTC", count=7)
    df['range'] = (df['high'] - df['low']) * k
    df['target'] = df['open'] + df['range'].shift(1)

    fee = 0.0005
    df['ror'] = np.where(df['high'] > df['target'],
                         df['close'] / df['target'] - fee,
                         1)

    ror = df['ror'].cumprod()[-2]
    return ror

def get_k():
    """ 지난 일주일 간 수익률을 비교하여 최적의 k값 계산"""
    max_k = 0.0
    max_ror = 0

    for k in np.arange(0.1, 1.0, 0.1):
        ror = get_ror(k)
        if max_ror < ror:
            max_ror = ror
            max_k = k

    return max_k

# 로그인
upbit = pyupbit.Upbit(access, secret)
print("autotrade start")

# 자동매매 시작
while True:
    try:
        now = datetime.datetime.now()
        start_time = get_start_time("KRW-BTC") #9:00
        end_time = start_time + datetime.timedelta(days=1) #9:00 + 1일

        # 9:00 < 현지 < #8:59:50
        if start_time < now < end_time - datetime.timedelta(seconds=10):
            target_price = get_target_price("KRW-BTC", get_k())
            ma15 = get_ma15("KRW-BTC")
            current_price = get_current_price("KRW-BTC")
            if target_price < current_price and ma15 < current_price:
                krw = get_balance("KRW")
                if krw > 5000:
                    buy_result = upbit.buy_market_order("KRW-BTC", krw*0.9995)
                    post_message(myToken, "#stock", "BTC buy : " + str(buy_result))
        else:
            btc = get_balance("BTC")
            if btc > 0.00008:
                sell_result = upbit.sell_market_order("KRW-BTC", btc*0.9995)
                post_message(myToken, "#stock", "BTC buy : " + str(sell_result))
        time.sleep(1)
    except Exception as e:
        print(e)
        post_message(myToken, "#stock", "BTC buy : " + str(e))
        time.sleep(1)