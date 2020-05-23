class MyObject(object):
    def __getitem__(self,name):
       return self.__getattribute__(name)
    def __setitem__(self, key, value):
        self.__setattr__(key,value)

class Tick(MyObject):
    pass

class Bar(MyObject):
    pass

class Position(MyObject):
    def __init__(self,time,symbol,volume,side,position_effect,price):
        self.time = time
        self.symbol = symbol
        self.volume = volume
        self.side = side
        self.position_effect = position_effect
        self.price = price

class Jiaoyidan(MyObject):
    def __init__(self,time,symbol,volume,side,position_effect,price,yingkui):
        self.time = time
        self.symbol = symbol
        self.volume = volume
        self.side = side
        self.position_effect = position_effect
        self.price = price
        self.yingkui = yingkui

class Weichengjiaodan(MyObject):
    def __init__(self,symbol,volume,side,order_type,position_effect,price,order_duration,order_qualifier):
        self.symbol = symbol
        self.volume = volume
        self.side = side
        self.order_type = order_type
        self.position_effect = position_effect
        self.price = price
        self.order_duration = order_duration
        self.order_qualifier = order_qualifier

class Account(MyObject):
    def __init__(self,cash):
        self.cash = cash
        self.current_cash = cash
        self.chicangs = []
        self.baozhengjin = 0
        self.keyongzijin = cash
        self.pingcangyingkui = 0
        self.chicangyingkui = 0
        self.shouxufei = 0
        self.jiaoyidans = []
        self.weichengjiaodans = []
    def positions(self,symbol, side=None):
        #目前只同时操作一种产品，直接返回就好了
        return self.chicangs
    def position(self,symbol, side):
        for index in range(0,len(self.positions)):
            if self.positions[index].symbol == symbol and self.positions[index].side == side:
                return self.positions[index]

class Context(MyObject):
    def __init__(self,cash):
        self.__account = Account(cash)
    def account(self, account_id=''):
        return self.__account
    def update_account(self):
        pass
