import importlib
import datetime
from vv_backtest.storage import *
from vv_backtest.enum import *
import sqlite3
import threading
from pylab import *

#变量区
MODE_BACKTEST = 0
ADJUST_PREV = 0
mainpy=''
context = ''
threads=[]
tick=Tick()
cash_history = []
cash_day = {}
count_ping = 0
count_win = 0
is_thread_stop = False

is_cash_day = True   #是否画资金曲线
is_cash_trade = False  #是否画交易曲线
is_save_figure = False
is_record = False   # 是否记录参数和回测结果
start_data = datetime.datetime.strptime('2018-01-01','%Y-%m-%d')
end_data = datetime.datetime.strptime('2018-12-08','%Y-%m-%d')


class myThread (threading.Thread):
    def __init__(self,symbol,frequency):
        threading.Thread.__init__(self)
        self.symbol = symbol
        self.frequency = frequency
    def run(self): #具体回测位置
        # 备用变量
        global cash_day
        global tick

        #con=sqlite3.connect('C:\\sqlite\\'+self.symbol+self.frequency+'.db')
        con=sqlite3.connect('C:\\sqlite\\'+'RB9999'+self.frequency+'.db')
        cursor = con.cursor()
        data = cursor.execute('select * from main')
        if self.frequency == 'tick': # 分时数据
            for row in data:
                if is_thread_stop: #是否要停止回测
                    break

                tick['symbol'] = self.symbol
                date_created_at = _getDatetime(row[1])
                if date_created_at < start_data or date_created_at > end_data:
                    continue
                if hasattr(tick,'created_at'):
                    if tick['created_at'].date() != date_created_at.date():
                        cash_day[tick['created_at'].strftime("%Y-%m-%d")] = context.account().current_cash
                tick['created_at'] = date_created_at
                # tick['high'] = row[2]
                # tick['low'] = row[3]
                # tick['open'] = row[4]
                # tick['price'] = row[5]
                tick['price'] = row[4]
                mainpy.on_tick(context,tick)
                tick['price'] = row[3]
                mainpy.on_tick(context,tick)
                tick['price'] = row[2]
                mainpy.on_tick(context,tick)
                tick['price'] = row[5]
                mainpy.on_tick(context,tick)
                _computer_account(context,tick)

        elif self.frequency == '60s':  # 60s 数据
            for row in data:
                if is_thread_stop:  # 是否要停止回测
                    break

                tick['symbol'] = self.symbol
                bob = datetime.datetime.strptime(row[1],'%Y-%m-%d %H:%M:%S')
                eob = datetime.datetime.strptime(row[2],'%Y-%m-%d %H:%M:%S')

                if hasattr(tick,'created_at'):
                    if tick['created_at'].date() != bob.date():
                        cash_day[tick['created_at'].strftime("%Y-%m-%d")] = context.account().current_cash
                tick['created_at'] = bob
                tick['eob'] = eob
                tick['high'] = row[3]
                tick['low'] = row[4]
                tick['price'] = row[6]
                tick['close'] = row[6]

                bar = []
                bar.append(tick)
                mainpy.on_bar(context,bar)
                _computer_account(context, tick)
        else:# 其他 K 线
            pass
        plt.close()
def run(strategy_id='3dfcba6c-e03e-11e9-8ee1-00ff5e0b76d41',
    filename='main2.py',
    mode=MODE_BACKTEST,
    token='86b951b2035896a8c3813a328f8a575b504948be',
    backtest_start_time='2018-06-06 09:00:00',
    backtest_end_time='2019-10-24 16:00:00',
    backtest_adjust=ADJUST_PREV,
    backtest_initial_cash=5000,
    backtest_commission_ratio=0.0001,
    backtest_slippage_ratio=0.0001):

    global context #初始化context
    context = Context(backtest_initial_cash)
    global mainpy #拿到模块用于回调
    mainpy=importlib.import_module(filename[0:-3])
    # 先执行 init 函数
    mainpy.init(context)
    #开始回测
    for thread in threads:
        thread.daemon = True
        thread.start()
    for thread in threads:
        thread.join()
    global count_win
    global count_ping
    print("总交易数："+str(count_ping))
    print("赢数："+str(count_win))

    #按交易画资金图
    if is_cash_trade:
        plt.ioff()
        plt.figure(9)
        plt.scatter(range(1, len(cash_history) + 1), cash_history, color='r', marker='+')
        plt.show()

    #按天画资金图
    if is_cash_day:
        plt.ioff()
        plt.figure(9)
        x=[]
        for key in cash_day.keys():
            x.append(datetime.datetime.strptime(key,"%Y-%m-%d"))

        #plt.xticks(_getListFromList(10,x),cash_day.keys(), color='blue', rotation=30)  # 此处locs参数与X值数组相同
        plt.xticks(_getListFromList(10,x),_getListFromList(10,list(cash_day.keys())), color='blue', rotation=90)  # 此处locs参数与X值数组相同
        plt.plot(x,list(cash_day.values()),color='r',marker='+')
        plt.show()

#订阅函数
def subscribe(symbols, frequency):
    threads.append(myThread(symbols,frequency))

#取消仓位
def order_cancel_all():
    for index in range(0,len(context.account().weichengjiaodans)):
        del context.account().weichengjiaodans[index]

#建平仓函数
def order_target_percent(symbol, percent=0, order_type=OrderType_Market,
                                         position_side=PositionSide_Long):
    if percent == 0: # 只使用了这一点
        for index in range(0,len(context.account().chicangs)):
            position = context.account().chicangs[index]
            if position.side == position_side and position.symbol == symbol: #满足条件，开始平仓
                if position_side == PositionSide_Long:
                    side = PositionSide_Short
                else:
                    side =PositionSide_Long
                order_volume(symbol=position.symbol,volume=position.volume,side=side,order_type=OrderType_Market,position_effect=PositionEffect_Close)
                cash_history.append(context.account().current_cash)

#建仓函数
def order_volume(symbol, volume, side, order_type, position_effect,
                 price=0, order_duration=OrderDuration_Unknown, order_qualifier=OrderQualifier_Unknown, account=''):
    global is_thread_stop
    # 先检查是否符合建仓条件
    if position_effect == PositionEffect_Open: #开始建仓
        if context.account().keyongzijin >= cash_deposit[symbol]*volume: #可用资金大于需要占用的保证金
            # 开始建仓
            context.account().weichengjiaodans.append(Weichengjiaodan(symbol=symbol, volume=volume, side=side, order_type=order_type,position_effect=position_effect,
                                price=price, order_duration=order_duration, order_qualifier=order_qualifier))
            _computer_account(context, tick)
        else:
            print("可用资金不足。。。是不是亏大了。。。。停止回测。。。。。")
            is_thread_stop = True

    elif position_effect == PositionEffect_Close:  #开始平仓  上面的平仓函数已经过滤了，这里就直接建仓了
        #开始建仓
        context.account().weichengjiaodans.append(Weichengjiaodan(symbol=symbol,volume=volume,side=side,order_type=order_type,position_effect=position_effect,
                                                                  price=price,order_duration=order_duration,order_qualifier=order_qualifier))
        _computer_account(context,tick)

#计算账户情况
def _computer_account(context,tick):
    global is_thread_stop
    global count_ping
    global count_win
    #先看未成交单
    for index in range(0,len(context.account().weichengjiaodans)):
        weichengjiao = context.account().weichengjiaodans[index]
        if tick['symbol'] == weichengjiao.symbol:
            if weichengjiao.order_type == OrderType_Limit: #限价交易
                if weichengjiao.position_effect == PositionEffect_Open:#开仓
                    if weichengjiao.side == OrderSide_Buy: #买入
                        #限价 买入 开仓
                        if tick['price'] <= weichengjiao.price - spread[tick['symbol']]: #价格合适
                            if context.account().keyongzijin >= cash_deposit[tick['symbol']]*weichengjiao.volume: # 钱也够
                                #全部成交
                                del context.account().weichengjiaodans[index]
                                context.account().chicangs.append(Position(time=tick['created_at'],symbol=tick['symbol'],volume=weichengjiao.volume,side=weichengjiao.side
                                                                            ,position_effect=weichengjiao.position_effect,price=weichengjiao.price))
                                context.account().jiaoyidans.append(Jiaoyidan(time=tick['created_at'],symbol=tick['symbol'],volume=weichengjiao.volume,side=weichengjiao.side
                                                                              ,position_effect=weichengjiao.position_effect,price=weichengjiao.price,yingkui=0))
                                context.account().baozhengjin = context.account().baozhengjin + cash_deposit[tick['symbol']]*weichengjiao.volume
                            else: # 现在每次只买一手，暂不考虑多手的问题
                                pass

                        else: # 价格不合适，不能成交
                            pass
                    else:#空单 限价 开仓
                        if tick['price'] >= weichengjiao.price + spread[tick['symbol']]: #价格合适
                            if context.account().keyongzijin >= cash_deposit[tick['symbol']]*weichengjiao.volume: #钱也够
                                #全部成交
                                del context.account().weichengjiaodans[index]
                                context.account().chicangs.append(Position(time=tick['created_at'],symbol=tick['symbol'],volume=weichengjiao.volume,side=weichengjiao.side
                                                                            ,position_effect=weichengjiao.position_effect,price=weichengjiao.price))
                                context.account().jiaoyidans.append(Jiaoyidan(time=tick['created_at'],symbol=tick['symbol'],volume=weichengjiao.volume,side=weichengjiao.side
                                                                              ,position_effect=weichengjiao.position_effect,price=weichengjiao.price,yingkui=0))
                                context.account().baozhengjin = context.account().baozhengjin + cash_deposit[tick['symbol']] * weichengjiao.volume
                            else:#现在只买一手，暂不考虑多手的问题
                                pass
                        else: #价格不合适
                            pass
                else: #平仓
                    if weichengjiao.side == OrderSide_Buy: #买入 平仓 限价
                        if tick['price'] <= weichengjiao.price - spread[tick['symbol']]: #价格合适
                            #寻找对应的单子，然后卖掉
                            find_index = -1
                            for index1 in range(0,len(context.account().chicangs)):
                                position = context.account().chicangs[index1]
                                if position.symbol == tick['symbol'] and position.side == OrderSide_Sell:
                                    find_index = index1

                            if find_index != -1: # 仓位中存在对应的需要平仓的单子，开始平仓
                                if context.account().chicangs[find_index].volume == weichengjiao.volume: #数量一致直接平仓
                                    yingkui = (context.account().chicangs[find_index].price - weichengjiao.pirce)*weichengjiao.volume*spread_yingkui[tick['symbol']]
                                    context.account().jiaoyidans.append(Jiaoyidan(time=tick['created_at'], symbol=tick['symbol'],
                                                  volume=weichengjiao.volume, side=weichengjiao.side
                                                  , position_effect=weichengjiao.position_effect,
                                                  price=weichengjiao.price, yingkui=yingkui))
                                    context.account().pingcangyingkui = context.account().pingcangyingkui + yingkui
                                    context.account().baozhengjin = context.account().baozhengjin - cash_deposit[tick['symbol']]*weichengjiao.volume
                                    context.account().shouxufei = context.account().shouxufei + service_charge[tick['symbol']]*2
                                    del context.account().weichengjiaodans[index]
                                    del context.account().chicangs[find_index]
                                    #统计
                                    count_ping = count_ping+1
                                    if yingkui>0:
                                        count_win=count_win+1

                                else: #数量不一致，，现在只操作一手持仓，暂时不用考虑这块
                                    pass
                        else: #价格不合适，直接过
                            pass
                    else: # 卖出 平仓 限价
                        if tick['price'] >= weichengjiao.price + spread[tick['symbol']]: #价格合适
                            # 寻找对应的单子，然后卖掉
                            find_index = -1
                            for index1 in range(0, len(context.account().chicangs)):
                                position = context.account().chicangs[index1]
                                if position.symbol == tick['symbol'] and position.side == OrderSide_Buy:
                                    find_index = index1
                            if find_index != -1: # 仓位中存在对应的需要平仓的单子，开始平仓
                                if context.account().chicangs[find_index].volume == weichengjiao.volume: #数量一致直接平仓
                                    yingkui = (weichengjiao.pirce-context.account().chicangs[find_index].price)*weichengjiao.volume*spread_yingkui[tick['symbol']]
                                    context.account().jiaoyidans.append(Jiaoyidan(time=tick['created_at'], symbol=tick['symbol'],
                                                  volume=weichengjiao.volume, side=weichengjiao.side
                                                  , position_effect=weichengjiao.position_effect,
                                                  price=weichengjiao.price, yingkui=yingkui))
                                    context.account().pingcangyingkui = context.account().pingcangyingkui + yingkui
                                    context.account().baozhengjin = context.account().baozhengjin - cash_deposit[tick['symbol']]*weichengjiao.volume
                                    context.account().shouxufei = context.account().shouxufei + service_charge[tick['symbol']]*2
                                    del context.account().weichengjiaodans[index]
                                    del context.account().chicangs[find_index]
                                    #统计
                                    count_ping = count_ping+1
                                    if yingkui>0:
                                        count_win=count_win+1
                                else: #数量不一致，，现在只操作一手持仓，暂时不用考虑这块
                                    pass
                        else: #价格不合适 ，直接过
                            pass
            elif weichengjiao.order_type == OrderType_Market: ##########################          市价交易
                if weichengjiao.position_effect == PositionEffect_Open:#开仓
                    if weichengjiao.side == OrderSide_Buy: #买入
                        #市价 买入 开仓
                        if context.account().keyongzijin >= cash_deposit[tick['symbol']]*weichengjiao.volume: # 钱够
                            #全部成交
                            del context.account().weichengjiaodans[index]
                            context.account().chicangs.append(Position(time=tick['created_at'],symbol=tick['symbol'],volume=weichengjiao.volume,side=weichengjiao.side
                                                                        ,position_effect=weichengjiao.position_effect,price=tick['price']+spread[tick['symbol']]))
                            context.account().jiaoyidans.append(Jiaoyidan(time=tick['created_at'],symbol=tick['symbol'],volume=weichengjiao.volume,side=weichengjiao.side
                                                                          ,position_effect=weichengjiao.position_effect,price=tick['price']+spread[tick['symbol']],yingkui=0))
                            context.account().baozhengjin = context.account().baozhengjin + cash_deposit[tick['symbol']]*weichengjiao.volume
                        else: # 现在每次只买一手，暂不考虑多手的问题
                            pass
                    else:#空单 市价 开仓
                        if context.account().keyongzijin >= cash_deposit[tick['symbol']]*weichengjiao.volume: #钱也够
                            #全部成交
                            del context.account().weichengjiaodans[index]
                            context.account().chicangs.append(Position(time=tick['created_at'],symbol=tick['symbol'],volume=weichengjiao.volume,side=weichengjiao.side
                                                                        ,position_effect=weichengjiao.position_effect,price=tick['price']-spread[tick['symbol']]))
                            context.account().jiaoyidans.append(Jiaoyidan(time=tick['created_at'],symbol=tick['symbol'],volume=weichengjiao.volume,side=weichengjiao.side
                                                                          ,position_effect=weichengjiao.position_effect,price=tick['price']-spread[tick['symbol']],yingkui=0))
                            context.account().baozhengjin = context.account().baozhengjin + cash_deposit[tick['symbol']] * weichengjiao.volume
                        else:#现在只买一手，暂不考虑多手的问题
                            pass

                else: #平仓
                    if weichengjiao.side == OrderSide_Buy: #买入 平仓 市价
                        #寻找对应的单子，然后卖掉
                        find_index = -1
                        for index1 in range(0,len(context.account().chicangs)):
                            position = context.account().chicangs[index1]
                            if position.symbol == tick['symbol'] and position.side == OrderSide_Sell:
                                find_index = index1

                        if find_index != -1: # 仓位中存在对应的需要平仓的单子，开始平仓
                            if context.account().chicangs[find_index].volume == weichengjiao.volume: #数量一致直接平仓
                                yingkui = (context.account().chicangs[find_index].price - (tick['price']+spread[tick['symbol']]))*weichengjiao.volume*spread_yingkui[tick['symbol']]
                                context.account().jiaoyidans.append(Jiaoyidan(time=tick['created_at'], symbol=tick['symbol'],
                                              volume=weichengjiao.volume, side=weichengjiao.side
                                              , position_effect=weichengjiao.position_effect,
                                              price=tick['price']+spread[tick['symbol']], yingkui=yingkui))
                                context.account().pingcangyingkui = context.account().pingcangyingkui + yingkui
                                context.account().baozhengjin = context.account().baozhengjin - cash_deposit[tick['symbol']]*weichengjiao.volume
                                context.account().shouxufei = context.account().shouxufei + service_charge[tick['symbol']]*2
                                del context.account().weichengjiaodans[index]
                                del context.account().chicangs[find_index]
                                # 统计
                                count_ping = count_ping + 1
                                if yingkui > 0:
                                    count_win = count_win + 1
                            else: #数量不一致，，现在只操作一手持仓，暂时不用考虑这块
                                pass
                    else: # 卖出 平仓 市价
                        # 寻找对应的单子，然后卖掉
                        find_index = -1
                        for index1 in range(0, len(context.account().chicangs)):
                            position = context.account().chicangs[index1]
                            if position.symbol == tick['symbol'] and position.side == OrderSide_Buy:
                                find_index = index1
                        if find_index != -1: # 仓位中存在对应的需要平仓的单子，开始平仓
                            if context.account().chicangs[find_index].volume == weichengjiao.volume: #数量一致直接平仓
                                chengjiaojia = tick['price']-spread[tick['symbol']]
                                yingkui = (chengjiaojia-context.account().chicangs[find_index].price)*weichengjiao.volume*spread_yingkui[tick['symbol']]
                                context.account().jiaoyidans.append(Jiaoyidan(time=tick['created_at'], symbol=tick['symbol'],
                                              volume=weichengjiao.volume, side=weichengjiao.side
                                              , position_effect=weichengjiao.position_effect,
                                              price=chengjiaojia, yingkui=yingkui))
                                context.account().pingcangyingkui = context.account().pingcangyingkui + yingkui
                                context.account().baozhengjin = context.account().baozhengjin - cash_deposit[tick['symbol']]*weichengjiao.volume
                                context.account().shouxufei = context.account().shouxufei + service_charge[tick['symbol']]*2
                                del context.account().weichengjiaodans[index]
                                del context.account().chicangs[find_index]
                                # 统计
                                count_ping = count_ping + 1
                                if yingkui > 0:
                                    count_win = count_win + 1
                            else: #数量不一致，，现在只操作一手持仓，暂时不用考虑这块
                                pass
            else: #其他交易类型，暂时不支持
                pass
    #看持仓
    context.account().chicangyingkui = 0
    for index_p in range(0,len(context.account().chicangs)): # 持仓
        position = context.account().chicangs[index_p]
        if position.side== OrderSide_Buy: # 买入--多单
            fudongyingkui = (tick['price'] - position.price)*position.volume*spread_yingkui[tick['symbol']]
            context.account().chicangyingkui =context.account().chicangyingkui + fudongyingkui
        else: # 卖出--空单
            fudongyingkui = (position.price - tick['price'])*position.volume*spread_yingkui[tick['symbol']]
            context.account().chicangyingkui = context.account().chicangyingkui + fudongyingkui
    #计算账户情况
    context.account().current_cash = context.account().cash + context.account().pingcangyingkui + context.account().chicangyingkui \
                                     -context.account().shouxufei
    context.account().keyongzijin = context.account().current_cash - context.account().baozhengjin

def _getDatetime(str):
    index_g1 = -1
    index_g2 = -1
    index_m1 = -1
    index_m2 = -1
    index_d1 = -1
    index_j1 = -1
    for index in range(0, len(str)):
        if str[index] == '-':
            if index_g1 == -1:
                index_g1 = index
            elif index_g2 == -1:
                index_g2 = index
        elif str[index] == ':':
            if index_m1 == -1:
                index_m1 = index
            elif index_m2 == -1:
                index_m2 = index
        elif str[index] == '.':
            if index_d1 == -1:
                index_d1 = index
        elif str[index] == '+':
            if index_j1 == -1:
                index_j1 = index
    year = str[0:index_g1]
    month = str[index_g1 + 1:index_g2]
    day = str[index_g2 + 1:index_g2 + 3]
    hour = str[index_m1 - 2:index_m1]
    minute = str[index_m1 + 1:index_m2]
    second = str[index_m2 + 1:index_m2 + 3]
    if index_d1 != -1:
        millisecond = str[index_d1 + 1:index_j1]
        return datetime.datetime(year=int(year), month=int(month), day=int(day), hour=int(hour), minute=int(minute),
                            second=int(second), microsecond=int(millisecond))
    else:
        return datetime.datetime(year=int(year), month=int(month), day=int(day), hour=int(hour), minute=int(minute),
                            second=int(second))

def _getListFromList(num,list):
    relist=[]
    for index in range(0,len(list)):
        if index == 0 or index%num== 0 or index == len(list)-1:
            relist.append(list[index])
    return relist


#获取未成交单情况
def get_unfinished_orders():
    return context.account().weichengjiaodans
















