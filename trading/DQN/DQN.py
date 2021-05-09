# coding=utf-8
from __future__ import print_function, absolute_import, unicode_literals
import time
from vv_backtest.base import *
import pickle # 保存模型用
from collections import defaultdict
import numpy as np
import copy
import sys
from collections import deque
import random
import gym
import numpy as np
from tensorflow.keras import models, layers, optimizers

#action 0/1 不动/买开

class DQN(object):
    def __init__(self):
        self.step = 0
        self.update_freq = 200  # 模型更新频率
        self.replay_size = 2000  # 训练集大小
        self.replay_queue = deque(maxlen=self.replay_size)
        self.model = self.create_model()
        self.target_model = self.create_model()

    def create_model(self):
        """创建一个隐藏层为100的神经网络"""
        STATE_DIM, ACTION_DIM = 14, 2  # 2 action
        model = models.Sequential([
            layers.Dense(100, input_dim=STATE_DIM, activation='relu'),
            layers.Dense(ACTION_DIM, activation="linear")
        ])
        model.compile(loss='mean_squared_error',
                      optimizer=optimizers.Adam(0.001))
        return model

    def act(self, s, epsilon=0.1):
        """预测动作"""
        # 刚开始时，加一点随机成分，产生更多的状态
        if np.random.uniform() < epsilon - self.step * 0.0002:
            return np.random.choice([0, 1])
        return np.argmax(self.model.predict(np.array([s]))[0])

    def save_model(self, file_path='dqn.h5'):
        self.model.save(file_path)

    def remember(self, s, a, next_s, reward):
        self.replay_queue.append((s, a, next_s, reward))

    def train(self, batch_size=64, lr=1, factor=0.95):
        if len(self.replay_queue) < self.replay_size:
            return
        self.step += 1
        # 每 update_freq 步，将 model 的权重赋值给 target_model
        if self.step % self.update_freq == 0:
            self.target_model.set_weights(self.model.get_weights())

        replay_batch = random.sample(self.replay_queue, batch_size)
        s_batch = np.array([replay[0] for replay in replay_batch])
        next_s_batch = np.array([replay[2] for replay in replay_batch])

        Q = self.model.predict(s_batch)
        Q_next = self.target_model.predict(next_s_batch)

        # 使用公式更新训练集中的Q值
        for i, replay in enumerate(replay_batch):
            _, a, _, reward = replay
            Q[i][a] = (1 - lr) * Q[i][a] + lr * (reward + factor * np.amax(Q_next[i]))

        # 传入网络进行训练
        self.model.fit(s_batch, Q, verbose=0)

def init(context):
    context.time_from = ''
    context.time_to = ''
    context.time_count = 0
    context.time_high = 0
    context.time_low = sys.maxsize
    context.still_count = 0

    account_id='e2310149-e322-11e9-a20c-00163e0a4100'
    context.symbol = 'RB9999'
    context.anaklines=[]

    context.before_state = []
    context.before_action = 0
    context.before_price = 0
    context.score = 0
    context.learn_count = 0
    context.has_ping = False
    context.DQN = DQN()

    curr_time=time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(time.time()))
    subscribe(symbols=context.symbol, frequency='tick')

def on_tick(context,tick):
    #自建15分钟K
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

        ############# 新建之前进行learning，忽略最新波动，只保留15M 线
        if should_learning():
            start_qlearning(tick['price'])

        bar['bob'] = context.time_to
        bar['high'] = tick['price']
        bar['low'] = tick['price']
        push_bar(bar)

        context.time_from = context.time_to
        context.time_count = 0
        context.time_high = 0
        context.time_low = sys.maxsize

    if should_ping_cang(tick['price']):
        ping_position()
        context.has_ping = True

def start_qlearning(now_price):
    context.learn_count = context.learn_count + 1

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
    reward = get_reward(now_price)
    before_action = context.before_action
    if before_action != 0: # 买买手续费点差
        reward = reward - 40 - 20

    context.DQN.remember(before_state, before_action, now_state, reward)
    context.DQN.train()
    context.score += reward

    a = context.DQN.act(now_state)
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

def find_highest(kLineList):
    highest = 0
    for anakline in kLineList:
        if anakline['low'] > highest:
            highest = anakline['low']
        if anakline['high'] > highest:
            highest = anakline['high']
    return highest

def get_state(now_price):
    #7个 k 线最高最低价
    useItemCount = 7
    retList = []
    if len(context.anaklines) < useItemCount:
        return retList

    maxPrice = find_highest(context.anaklines[-useItemCount:])

    for i in range(useItemCount):
        nowItem = context.anaklines[i - useItemCount]
        retList.append(maxPrice - nowItem['high'])
        retList.append(maxPrice - nowItem['low'])
    return retList

def get_reward(now_price):
    if context.has_ping:
        if context.account().jiaoyidans:
            yingkui = context.account().jiaoyidans[-1].yingkui
            context.has_ping = False
            return yingkui
    else:
        return 0

def get_reward2(now_price):
    positions = context.account().positions(symbol=context.symbol, side=None)
    if context.before_action == 3:
        return context.account().jiaoyidans[-1].yingkui
    else:
        return 0

def implement_as_action(action, now_price):
    if action == 1: #买开
        data = order_volume(context.symbol, volume=1, side=OrderSide_Buy, order_type=OrderType_Market,
                            position_effect=PositionEffect_Open,
                            price=now_price,
                            order_duration=OrderDuration_Unknown, order_qualifier=OrderQualifier_Unknown)
        print("%s 买开" % (context.time_to))

def ping_position():
    positions = context.account().positions(symbol=context.symbol, side=None)
    if positions:  # 如果存在仓位
        order_cancel_all()
        positionPrice = positions[0].price
        if positions[0].side == PositionSide_Long:  # 多单
            order_target_percent(symbol=context.symbol, percent=0, order_type=OrderType_Market,
                                     position_side=PositionSide_Long)  # 平仓
            print("%s 平完多单" % (context.time_to))
        else:  # 空单
            order_target_percent(symbol=context.symbol, percent=0, order_type=OrderType_Market,
                                 position_side=PositionSide_Short)  # 平仓
            print("%s 平完空单" % (context.time_to))

def should_ping_cang(now_price):
    ying = 40
    kui = 40
    positions = context.account().positions(symbol=context.symbol, side=None)
    if positions:
        positionPrice = positions[0].price
        if now_price - positionPrice > ying or positionPrice - now_price > kui:
            return True
    return False

def should_learning():
    positions = context.account().positions(symbol=context.symbol, side=None)
    if positions:
        return False
    return True

if __name__ == '__main__':
    run(strategy_id='3dfcba6c-e03e-11e9-8ee1-00ff5e0b76d41',
        filename='DQN.py',
        mode=MODE_BACKTEST,
        token='86b951b2035896a8c3813a328f8a575b504948be',
        backtest_start_time='2019-06-06 09:00:00',
        backtest_end_time='2019-10-24 16:00:00',
        backtest_adjust=ADJUST_PREV,
        backtest_initial_cash=1000000,
        backtest_commission_ratio=0.0001,
        backtest_slippage_ratio=0.0001)

def save_info(cash_history, count_ping, count_win):
    with open('DQN-result.txt', 'a') as f:
        if (len(cash_history) > 0):
            writh_str = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S') + " 总交易数: " + str(
                count_ping) + " 总赢数：" + str(count_win) + " 最后剩余：" + str(cash_history[-1]) \
                        + " shouxufei: " + str(context.account().shouxufei) + " score:" + str(context.score) + '\r'
            f.write(writh_str)

def save_model(count):
    if count % 100 == 0:
        context.DQN.save_model()