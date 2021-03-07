# coding=utf-8
from __future__ import print_function, absolute_import, unicode_literals
import time
from vv_backtest.base import *
import matplotlib.pyplot as plt
from pylab import *
import pickle # 保存模型用
from collections import defaultdict
import numpy as np
import copy

# mpl.rcParams['font.sans-serif'] = ['SimHei']
# plt.ion()
# fig=plt.figure(1)

#action 0/1/2/3 不动/买开/卖开/平

def init(context):
    context.time_from = ''
    context.time_to = ''
    context.time_count = 0
    context.time_high = 0
    context.time_low = sys.maxsize

    account_id='e2310149-e322-11e9-a20c-00163e0a4100'
    context.symbol = 'RB9999'
    context.anaklines=[]

    context.before_state = []
    context.before_action = 0
    context.before_price = 0
    context.score = 0
    context.Q = defaultdict(lambda: [0, 0, 0, 0])

    curr_time=time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(time.time()))
    subscribe(symbols=context.symbol, frequency='tick')

def on_tick(context,tick):
    #自建15分钟K
    print(tick['created_at'], tick['price'])

    if context.time_from == '':  # 刚开始时
        context.time_from = tick['created_at']
        context.time_to = tick['created_at']
        context.time_high = tick['price']
        context.time_low = tick['price']
        return

    # 先处理K线
    timedelta = tick['created_at'] - context.time_to
    if timedelta.seconds >= 60:
        context.time_count = context.time_count + 1
        context.time_to = tick['created_at']

    if tick['price'] > context.time_high:
        context.time_high = tick['price']
    if tick["price"] < context.time_low:
        context.time_low = tick['price']

    bar = {}
    bar['bob'] = context.time_from
    bar['high'] = context.time_high
    bar['low'] = context.time_low
    update_latest_bar(bar)

    if context.time_count >= 15: #新建一根15M K
        bar['bob'] = context.time_to
        bar['high'] = tick['price']
        bar['low'] = tick['price']
        push_bar(bar)

        context.time_from = context.time_to
        context.time_count = 0
        context.time_high = 0
        context.time_low = sys.maxsize

    ############# 15 分钟线  处理结束
    start_qlearning(tick['price'])

def start_qlearning(now_price):
    now_state = get_state(now_price)
    before_state = context.before_state
    if len(now_state) == 0:
        return

    if len(before_state) == 0:
        context.before_state = now_state
        context.before_action = 0
        context.before_price = now_price
        return

    #开始qlearn
    lr, factor = 0.7, 0.95
    reward = get_reward(now_price)
    before_action = context.before_action

    context.Q[before_state][before_action] = (1 - lr) * context.Q[before_state][before_action] + lr * (reward + factor * max(context.Q[now_state]))
    context.score += reward

    a = get_max_action(now_state)
    implement_as_action(a, now_price)

    context.before_state = now_state
    context.before_action = a
    context.before_price = now_price


def push_bar(bar):
    if len(context.anaklines) > 50:
        del context.anaklines[0]
    context.anaklines.append(bar)  # 加入 只维护50个

def update_latest_bar(bar):
    if len(context.anaklines) == 0:
        context.anaklines.append(bar)
    else:
        context.anaklines[-1]['high'] = bar['high']
        context.anaklines[-1]['low'] = bar['low']

def get_state(now_price):
    #7个 k 线最高最低价
    useItemCount = 7
    retList = []
    maxPrice = 10000
    if len(context.anaklines) < useItemCount:
        return retList

    for i in range(useItemCount):
        nowItem = context.anaklines[i - useItemCount]
        retList.append(nowItem['high'] / maxPrice)
        retList.append(nowItem['low'] / maxPrice)

    retList.append(now_price / maxPrice)
    positions = context.account().positions(symbol=context.symbol, side=None)
    if positions:
        retList.append(1)
        retList.append(positions[0].side)
    else:
        retList.append(0)
        retList.append(0)

    return tuple(retList)

def get_reward(now_price):
    positions = context.account().positions(symbol=context.symbol, side=None)
    if positions:
        positionPrice = positions[0].price
        if positions[0].side == PositionSide_Long:  # 多单 = 1
            return (now_price - context.before_price) * 10
        else: # = 2
            return (context.before_price - now_price) * 10
    else:
        return -0.001

def get_max_action(now_state):
    a = np.argmax(context.Q[now_state])
    if now_state[-2] == 0:  # 没有仓位
        if a == 3:  # 平仓
            context.Q[now_state][a] = -1000000
            a = get_max_action(now_state)
    else: # 有仓位
        if a == 1 or a == 2: #1 买开 2 卖开
            context.Q[now_state][a] = -1000000
            a = get_max_action(now_state)
    return a

def implement_as_action(action, now_price):
    if action == 1: #买开
        data = order_volume(context.symbol, volume=1, side=OrderSide_Buy, order_type=OrderType_Market,
                            position_effect=PositionEffect_Open,
                            price=now_price,
                            order_duration=OrderDuration_Unknown, order_qualifier=OrderQualifier_Unknown)
    elif action == 2: #卖开
        data = order_volume(context.symbol, volume=1, side=OrderSide_Sell, order_type=OrderType_Market,
                            position_effect=PositionEffect_Open,
                            price=now_price,
                            order_duration=OrderDuration_Unknown, order_qualifier=OrderQualifier_Unknown)
    elif action == 3: #平
        ping_position()
def ping_position():
    positions = context.account().positions(symbol=context.symbol, side=None)
    if positions:  # 如果存在仓位
        order_cancel_all()
        positionPrice = positions[0].price
        if positions[0].side == PositionSide_Long:  # 多单
            order_target_percent(symbol=context.symbol, percent=0, order_type=OrderType_Market,
                                     position_side=PositionSide_Long)  # 平仓
            print("平完多单")
        else:  # 空单
            order_target_percent(symbol=context.symbol, percent=0, order_type=OrderType_Market,
                                 position_side=PositionSide_Short)  # 平仓
            print("平完空单")

if __name__ == '__main__':
    run(strategy_id='3dfcba6c-e03e-11e9-8ee1-00ff5e0b76d41',
        filename='qlearning_main.py',
        mode=MODE_BACKTEST,
        token='86b951b2035896a8c3813a328f8a575b504948be',
        backtest_start_time='2019-06-06 09:00:00',
        backtest_end_time='2019-10-24 16:00:00',
        backtest_adjust=ADJUST_PREV,
        backtest_initial_cash=500000000,
        backtest_commission_ratio=0.0001,
        backtest_slippage_ratio=0.0001)
