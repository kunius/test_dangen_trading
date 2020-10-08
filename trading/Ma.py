from vv_backtest.base import *
import sys

print("策略 -- 均线 -- 策略")

def init(context):
    # 读取传过来的变量
    # context.arg_ma_fast_n = int(sys.argv[1])
    # print("arg_ma_fast_n:"+sys.argv[1])
    # context.arg_ma_slow_n= int(sys.argv[2])
    # print("arg_ma_slow_n:"+sys.argv[2])
    # context.arg_lose_amount = int(sys.argv[3])
    # print("arg_lose_amount:"+sys.argv[3])
    # context.arg_win_amount = int(sys.argv[4])
    # print("arg_win_amount:"+sys.argv[4])
    # context.arg_is_plus = int(sys.argv[5])
    # print("arg_is_plus:"+sys.argv[5])

    #自定义变量
    context.arg_ma_fast_n = 11
    context.arg_ma_slow_n = 32
    context.arg_lose_amount = 35
    context.arg_win_amount = 45
    context.arg_is_plus = 2


    context.symbol = 'SHFE.rb2001'
    context.klines = []

    #订阅行情
    subscribe("RB9999",'tick')


def on_tick(context,tick):
    print(tick)

def on_bar(context,bar):
    my_bar = {'high': bar[0].high, 'low': bar[0].low,'price':bar[0].close, 'ma': (bar[0].high + bar[0].low) / 2, 'ma_fast': '', 'ma_slow': ''}
    context.klines.append(my_bar)
    if len(context.klines) > context.arg_ma_slow_n + 10: #只保留 慢线加10 的数量的k线
        context.klines.pop(0)

    if len(context.klines) < context.arg_ma_slow_n:
        return
    else:
        ma_fast_sum = 0
        for index in range(0,context.arg_ma_fast_n):
            ma_fast_sum += context.klines[~index]['ma']
        context.klines[-1]['ma_fast'] = ma_fast_sum/context.arg_ma_fast_n

        ma_slow_sum = 0
        for index in range(0,context.arg_ma_slow_n):
            ma_slow_sum +=context.klines[~index]['ma']
        context.klines[-1]['ma_slow'] = ma_slow_sum/context.arg_ma_slow_n
    #下面开始分析k线，是否需要建仓或者平仓

    if get_unfinished_orders():  # 如果有挂单则撤销掉
        order_cancel_all()

    now_positions = context.account().positions(symbol=context.symbol,side=None)
    if now_positions: # 如果当前有持仓，直接执行止损止盈
        if context.has_direction == 1:  # 多单
            if context.klines[-1]['price'] > context.has_price + context.arg_win_amount:
                print("多单止盈")
                order_target_percent(symbol=context.symbol,percent=0,position_side=PositionSide_Long,order_type=OrderType_Market)
            elif context.klines[-1]['price'] < context.has_price - context.arg_lose_amount:
                print("多单止损")
                order_target_percent(symbol=context.symbol,percent=0,position_side=PositionSide_Long,order_type=OrderType_Market)
        else:  #空单
            if context.klines[-1]['price'] < context.has_price - context.arg_win_amount:
                print("空单止盈")
                order_target_percent(symbol=context.symbol,percent=0,position_side=PositionSide_Short,order_type=OrderType_Market)
            elif context.klines[-1]['price'] > context.has_price + context.arg_lose_amount:
                print("空单止损")
                order_target_percent(symbol=context.symbol,percent=0,position_side=PositionSide_Short,order_type=OrderType_Market)
    else:  #当前没有持仓 计算是否需要建仓
        if context.klines[-1]['ma_fast'] >= context.klines[-1]['ma_slow'] and \
            context.klines[-2]['ma_fast'] < context.klines[-2]['ma_slow']:
            # 快线上穿慢线，建多单
            print("开始建多单")
            if context.arg_is_plus == 1:  #正向回测
                order_volume(symbol=context.symbol,volume=1,side=OrderSide_Buy,order_type=OrderType_Market,
                             position_effect=PositionEffect_Open)
                context.has_direction = 1
            else: # 反向回测
                order_volume(symbol=context.symbol,volume=1,side=OrderSide_Sell,order_type=OrderType_Market,
                             position_effect=PositionEffect_Open)
                context.has_direction = 2
            context.has_price = context.klines[-1]['price']
            print(context.has_price)
        elif context.klines[-1]['ma_fast'] <= context.klines[-1]['ma_slow'] and \
            context.klines[-2]['ma_fast'] > context.klines[-2]['ma_slow']:
            # 快线下穿慢线，建空单
            print("开始建空单")
            if context.arg_is_plus == 1:    #正向
                order_volume(symbol=context.symbol, volume=1, side=OrderSide_Sell, order_type=OrderType_Market,
                             position_effect=PositionEffect_Open)
                context.has_direction = 2
            else: #反向
                order_volume(symbol=context.symbol, volume=1, side=OrderSide_Buy, order_type=OrderType_Market,
                             position_effect=PositionEffect_Open)
                context.has_direction = 1
            context.has_price = context.klines[-1]['price']
            print(context.has_price)

if __name__ == "__main__":
    run(strategy_id='3dfcba6c-e03e-11e9-8ee1-00ff5e0b76d41',
        filename='Ma.py',
        mode=MODE_BACKTEST,
        token='86b951b2035896a8c3813a328f8a575b504948be',
        backtest_start_time='2017-06-06 09:00:00',
        backtest_end_time='2019-10-24 16:00:00',
        backtest_adjust=ADJUST_PREV,
        backtest_initial_cash=5000,
        backtest_commission_ratio=0.0001,
        backtest_slippage_ratio=0.0001)
