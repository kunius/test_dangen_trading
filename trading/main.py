# coding=utf-8
from __future__ import print_function, absolute_import, unicode_literals
import time
from vv_backtest.base import *
import matplotlib.pyplot as plt
from pylab import *
import copy
import sys

print("原始 策略")

# mpl.rcParams['font.sans-serif'] = ['SimHei']
# plt.ion()
# fig=plt.figure(1)


def init(context):
    context.time_from = ''
    context.time_to = ''
    context.time_count = 0
    context.time_high = 0
    context.time_low = sys.maxsize

    context.find_index = 0

    account_id='e2310149-e322-11e9-a20c-00163e0a4100'
    context.symbol = 'SHFE.rb2001'
    context.anaklines=[]
    curr_time=time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(time.time()))
    subscribe(symbols=context.symbol, frequency='tick')
    # timeseries = history_n(symbol=context.symbol, frequency='900s', fields='high,low,bob',count=15,
    #                        end_time=curr_time)
    # analyze_klines(context,timeseries,True)

def analyze_klines(context,timeseries,history):
    for timeserie in timeseries:
        analyze_one_with_figure(context,timeserie,history)

def analyze_one_with_figure(context,oneline,history):
    # # 画图，观察数据分析是否正确
    # fig.canvas.manager.window.wm_geometry('+0+0')
    # plt.clf()
    # plt.plot(range(1,len(context.anaklines)+1),[context.anaklines[index]['useprice'] for index in range(0,len(context.anaklines))],alpha=0.2)
    # for index in range(0,len(context.anaklines)): # 写字
    #     status=context.anaklines[index]['status']
    #     if status == '上涨' or status=='上涨回调上行' or status=='下跌回调':
    #         color='r'
    #     elif status == '不定':
    #         color = 'y'
    #     else:
    #         color = 'g'
    #     plt.text(index+1,context.anaklines[index]['useprice'],context.anaklines[index]['status'],color=color)
    # # plt.show()
    # # 结束
    analyze_one(context, oneline, history)

def analyze_one(context,oneline,history):
    print(oneline['bob'])
    oneline['status'] = '不定'
    oneline['max'] = 0
    oneline['min'] = sys.maxsize
    oneline['amount'] = 0
    oneline['useprice']=(oneline['high']+oneline['low'])/2

    if len(context.anaklines)>50:
        del context.anaklines[0]
    context.anaklines.append(oneline)  # 加入 只维护50个

    if len(context.anaklines) < 8: # 数量少，不分析
        return
    else: # 核心处理 阶段
        temp8 = context.anaklines[-8:] # 取出最近的8条K
        find_index = 1
        for temp_index in range(-1,-9,-1): # 寻找最近的已经确定状态的K
            temp_status = temp8[temp_index]['status']
            if temp_status != '不定':
                find_index = temp_index
                break
        if find_index == 1: # 没有发现确定状态的K ， 确定上涨或是下跌趋势
            count_rise = count_fail = amount_rise = amount_fail = lastmidprice1 = lastmidprice2 =\
            maxvalue  = 0
            minvalue =sys.maxsize
            for temp_index in range(0,len(temp8)-1): # 分析 8 条K
                midprice1 = temp8[temp_index]['useprice']
                midprice2 = temp8[temp_index+1]['useprice']
                if temp_index == 6:
                    lastmidprice1 = midprice1
                    lastmidprice2 = midprice2
                if midprice2>midprice1:
                    count_rise = count_rise+1
                    amount_rise=amount_rise+(midprice2-midprice1)
                    if midprice2>maxvalue:
                        maxvalue=midprice2
                    if midprice1<minvalue:
                        minvalue = midprice1

                elif midprice2<midprice1:
                    count_fail = count_fail+1
                    amount_fail=amount_fail + (midprice1-midprice2)
                    if midprice2<minvalue:
                        minvalue=midprice2
                    if midprice1>maxvalue:
                        maxvalue=midprice1

            if count_rise-count_fail > 1 and amount_rise-amount_fail > 20 and (lastmidprice2>lastmidprice1): # 确定是上涨趋势
                for index in range(-8,0):  # 记录
                    context.anaklines[index]['status'] = '上涨'
                    context.anaklines[index]['max'] = maxvalue
                    context.anaklines[index]['min'] = minvalue
                    context.anaklines[index]['amount'] = amount_rise-amount_fail
            elif count_fail-count_rise > 1 and amount_fail-amount_rise > 20 and lastmidprice1>lastmidprice2: # 确定是下跌趋势
                for index in range(-8, 0):  # 记录
                    context.anaklines[index]['status'] = '下跌'
                    context.anaklines[index]['max'] = maxvalue
                    context.anaklines[index]['min'] = minvalue
                    context.anaklines[index]['amount'] = amount_fail-amount_rise
            else: # 不确定是什么趋势 不操作
                pass
        else: # 发现了确定状态的K，进一步分析
            last_status=context.anaklines[find_index]['status']
            if last_status=='上涨':
                newmidprice= context.anaklines[-1]['useprice']
                oldmidprice=context.anaklines[-2]['useprice']
                if newmidprice>=oldmidprice: # 还是 上涨趋势
                    context.anaklines[-1]['status']='上涨'
                    context.anaklines[-1]['max']=newmidprice
                    context.anaklines[-1]['min']=context.anaklines[-2]['min']
                    context.anaklines[-1]['amount']=context.anaklines[-2]['amount']+(newmidprice-oldmidprice)
                    for index in range(-2,~(len(context.anaklines)),-1):
                        if context.anaklines[index]['status']=='上涨':
                            context.anaklines[index]['max'] = newmidprice
                            context.anaklines[index]['amount'] = context.anaklines[-1]['amount']
                        else:
                            break
                elif context.anaklines[-1]['useprice'] > context.anaklines[find_index]['min']: # 上涨回调 趋势
                    context.anaklines[-1]['status']='上涨回调'
                    context.anaklines[-1]['max']=context.anaklines[-2]['max']
                    context.anaklines[-1]['min']=newmidprice
                    context.anaklines[-1]['amount']=abs(newmidprice-oldmidprice)
                else: # 上涨回调过度，重新开始
                    for index in range(-1,-9,-1):
                        context.anaklines[index]['status'] = '不定'
            elif last_status=='下跌':
                newmidprice=context.anaklines[-1]['useprice']
                oldmidprice=context.anaklines[-2]['useprice']
                if newmidprice<=oldmidprice: #还是 下跌趋势
                    context.anaklines[-1]['status']='下跌'
                    context.anaklines[-1]['max']=context.anaklines[-2]['max']
                    context.anaklines[-1]['min']=newmidprice
                    context.anaklines[-1]['amount']=context.anaklines[-2]['amount']+(oldmidprice-newmidprice)
                    for index in range(-2,~(len(context.anaklines)),-1):
                        if context.anaklines[index]['status']=='下跌':
                            context.anaklines[index]['min']=newmidprice
                            context.anaklines[index]['amount']=context.anaklines[-1]['amount']
                        else:
                            break
                elif context.anaklines[find_index]['max'] > context.anaklines[-1]['useprice']: # 下跌回调 趋势
                    context.anaklines[-1]['status']='下跌回调'
                    context.anaklines[-1]['max']=newmidprice
                    context.anaklines[-1]['min']=context.anaklines[-2]['min']
                    context.anaklines[-1]['amount']=newmidprice-oldmidprice
                else: # 回调过度，重新开始
                    for index in range(-1,-9,-1):
                        context.anaklines[index]['status'] = '不定'
            elif last_status=='上涨回调':
                newmidprice = context.anaklines[-1]['useprice']
                oldmidprice = context.anaklines[-2]['useprice']
                index_rise=0  # 寻找上一个上涨点
                for index in range(-2,~len(context.anaklines),-1):
                    if context.anaklines[index]['status']=='上涨':
                        index_rise=index
                        break
                if oldmidprice>=newmidprice: #继续下跌
                    if newmidprice>(context.anaklines[index_rise]['min']+context.anaklines[index_rise]['amount']/2): # 维持 上涨回调
                        context.anaklines[-1]['status']='上涨回调'
                        context.anaklines[-1]['max']=context.anaklines[-2]['max']
                        context.anaklines[-1]['min']=context.anaklines[-1]['useprice']
                        context.anaklines[-1]['amount']=context.anaklines[-2]['amount']+(oldmidprice-newmidprice)
                        for index in range(-2,~len(context.anaklines),-1):
                            if context.anaklines[index]['status']=='上涨回调':
                                context.anaklines[index]['min']=context.anaklines[-1]['min']
                                context.anaklines[index]['amount']=context.anaklines[-1]['amount']
                            else:
                                break
                    else: # 上涨回调 过度，，清空8K的状态
                        for index in range(-1,-9,-1):
                            context.anaklines[index]['status'] = '不定'
                else: # 开始  上涨 了
                    if newmidprice <= context.anaklines[index_rise]['max']: # 没有超过上涨最大值 ， 暂 确定 震荡
                        context.anaklines[-1]['status'] = '上涨回调上行'
                        context.anaklines[-1]['max'] = context.anaklines[-1]['useprice']
                        context.anaklines[-1]['min'] = context.anaklines[-2]['min']
                        context.anaklines[-1]['amount'] = context.anaklines[-1]['useprice']-context.anaklines[-2]['useprice']
                    else: # 超过最大值  ， 清空8K 状态
                        for index in range(-1, -9, -1):
                            context.anaklines[index]['status'] = '不定'
            elif last_status=='下跌回调':
                newmidprice = context.anaklines[-1]['useprice']
                oldmidprice = context.anaklines[-2]['useprice']
                index_fail = 0  # 寻找上一个下跌点
                for index in range(-2, ~len(context.anaklines), -1):
                    if context.anaklines[index]['status'] == '下跌':
                        index_fail = index
                        break
                if oldmidprice <= newmidprice:
                    if newmidprice < context.anaklines[index_fail]['max'] - context.anaklines[index_fail]['amount'] / 2:  # 维持 下跌回调
                        context.anaklines[-1]['status'] = '下跌回调'
                        context.anaklines[-1]['max'] = context.anaklines[-1]['useprice']
                        context.anaklines[-1]['min'] = context.anaklines[-2]['min']
                        context.anaklines[-1]['amount'] = context.anaklines[-2]['amount'] + (newmidprice - oldmidprice)
                        for index in range(-2, ~len(context.anaklines), -1):
                            if context.anaklines[index]['status'] == '下跌回调':
                                context.anaklines[index]['max'] = context.anaklines[-1]['max']
                                context.anaklines[index]['amount'] = context.anaklines[-1]['amount']
                            else:
                                break
                    else:  # 下跌回调 过度，，清空8K的状态
                        for index in range(-1, -9, -1):
                            context.anaklines[index]['status'] = '不定'
                else:
                    if newmidprice >= context.anaklines[index_fail]['min']: # 没有小于 下跌最小值，暂 定 震荡
                        context.anaklines[-1]['status'] = '下跌回调下行'
                        context.anaklines[-1]['max'] = context.anaklines[-2]['max']
                        context.anaklines[-1]['min'] = context.anaklines[-1]['useprice']
                        context.anaklines[-1]['amount'] = context.anaklines[-2]['useprice']-context.anaklines[-1]['useprice']
                    else: # 超过最小值  ， 清空8K 状态
                        for index in range(-1, -9, -1):
                            context.anaklines[index]['status'] = '不定'
            elif last_status == '上涨回调上行':
                #取上涨最高点 和 回调最低点
                find_index = 0
                for index in range(-1,~len(context.anaklines),-1):
                    if context.anaklines[index]['status'] == '上涨回调':
                        find_index=index
                        break
                if context.anaklines[find_index]['max']+6 >= context.anaklines[-1]['useprice'] \
                        and context.anaklines[find_index]['min']-6 <= context.anaklines[-1]['useprice']: # 继续上涨回调上行
                    context.anaklines[-1]['status'] = '上涨回调上行'
                    # 没有多单，就建仓
                    if not history:
                        print("判断是否可建多单")
                        positions=context.account().positions(symbol=context.symbol, side=None)
                        unfinished_orders = get_unfinished_orders()
                        if (not positions) and (not unfinished_orders):
                            data=order_volume(context.symbol, volume=1, side=OrderSide_Buy, order_type=OrderType_Limit, position_effect=PositionEffect_Open,
                                         price=round(context.anaklines[find_index]['min']),
                                         order_duration=OrderDuration_Unknown, order_qualifier=OrderQualifier_Unknown)
                            print(data)
                            context.find_index = copy.deepcopy(context.anaklines[find_index])
                else: # 结束上涨回调上行 ，清空，重新开始
                    for index in range(-1, -9, -1):
                        context.anaklines[index]['status'] = '不定'
            elif last_status == '下跌回调下行':
                #取最高点和最低点
                find_index = 0
                for index in range(-1,~len(context.anaklines),-1):
                    if context.anaklines[index]['status'] == '下跌回调':
                        find_index=index
                        break
                if context.anaklines[find_index]['max']+6 >= context.anaklines[-1]['useprice'] \
                    and context.anaklines[find_index]['min']-6 <= context.anaklines[-1]['useprice']: #继续 下跌回调下行
                    context.anaklines[-1]['status'] = '下跌回调下行' # 为了 没有建仓就建仓
                    # 没有空单，就建仓
                    if not history:
                        print("判断是否可建空单")
                        positions=context.account().positions(symbol=context.symbol, side=None)
                        if positions:
                            position = positions[0]
                            print(position.symbol)
                            print(position['symbol'])
                        unfinished_orders = get_unfinished_orders()
                        if (not positions) and (not unfinished_orders):
                            data=order_volume(context.symbol,volume=1,side=OrderSide_Sell,order_type=OrderType_Limit,position_effect=PositionEffect_Open,
                                         price=round(context.anaklines[find_index]['max']),
                                         order_duration=OrderDuration_Unknown,order_qualifier=OrderQualifier_Unknown)
                            print(data)
                            context.find_index = copy.deepcopy(context.anaklines[find_index])
                else: # 结束下跌回调下行
                    for index in range(-1, -9, -1):
                        context.anaklines[index]['status'] = '不定'
def on_tick(context,tick):
    #自建15分钟K
    print(tick['created_at'])

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

    if context.time_count >= 15: #放出一根K
        bar = {}
        bar['bob'] = context.time_from
        bar['high'] = context.time_high
        bar['low'] = context.time_low
        on_bar(context,bar)

        context.time_from = context.time_to
        context.time_count = 0
        context.time_high = 0
        context.time_low = sys.maxsize

    ############# 15 分钟线  处理结束

    # 开始处理 仓位  当find_index 不为0 时，说明建好仓了，可以处理仓位了 同步化变化
    if context.find_index != 0:
        positions = context.account().positions(symbol=context.symbol, side=None)
        unfinished_orders = get_unfinished_orders()
        price_max = context.find_index['max']
        price_min = context.find_index['min']
        status = context.find_index['status']
        if positions: # 如果存在仓位
            order_cancel_all()
            if status == '上涨回调': # 多单
                if (tick['price'] >= price_min+50) or (tick['price'] <= price_min-20): #止损止盈
                    order_target_percent(symbol=context.symbol, percent=0, order_type=OrderType_Market,
                                         position_side=PositionSide_Long)  #平仓
                    print("平 多单")
            else: # 空单
                if (tick['price'] >= price_max+20) or (tick['price'] <= price_max-50): #止损止盈
                    order_target_percent(symbol=context.symbol, percent=0, order_type=OrderType_Market,
                                         position_side=PositionSide_Short)  #平仓
                    print("平 空单")
        elif unfinished_orders: # 如果 存在未成交的挂单
            if status == '上涨回调': # 挂的多单
                if (tick['price'] >= price_max+6) or (tick['price'] <= price_min-6): # 未成交，取消挂单
                    order_cancel_all()
                    print("取消多单挂单")
            else:# 挂的空单
                if (tick['price'] >= price_max+6) or (tick['price'] <= price_min-6): #未成交，取消挂单
                    order_cancel_all()
                    print("取消多空单挂单")
        else: # 单子处理好了
            context.find_index = 0

def on_bar(context, bar):
    analyze_one_with_figure(context,bar,False)

def on_error(context, code, info):
    print(code)
    print(info)

if __name__ == '__main__':
    run(strategy_id='3dfcba6c-e03e-11e9-8ee1-00ff5e0b76d41',
        filename='main.py',
        mode=MODE_BACKTEST,
        token='86b951b2035896a8c3813a328f8a575b504948be',
        backtest_start_time='2019-06-06 09:00:00',
        backtest_end_time='2019-10-24 16:00:00',
        backtest_adjust=ADJUST_PREV,
        backtest_initial_cash=500000000,
        backtest_commission_ratio=0.0001,
        backtest_slippage_ratio=0.0001)
