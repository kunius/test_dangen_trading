import sqlite3
from gm.api import *

def init(context):
    subscribe("SHFE.rb2001",'60s')
    conn = sqlite3.connect('D:\\sqlite\\'+'SHFE.rb2001'+'60s'+'.db')
    context.conn =conn

def on_tick(context,tick):
    print(tick)

def on_bar(context,bar):
    conn = context.conn
    c = conn.cursor()
    c.execute("insert into main (bob,eob,high,low,open,close) values ('%s','%s','%d','%d','%d','%d')" % (bar[0].bob.strftime("%Y-%m-%d %H:%M:%S"),bar[0].eob.strftime("%Y-%m-%d %H:%M:%S"),
              bar[0].high,bar[0].low,bar[0].open,bar[0].close))
    conn.commit()

if __name__ == "__main__":
    run(strategy_id='3dfcba6c-e03e-11e9-8ee1-00ff5e0b76d41',
        filename='SavePrices.py',
        mode=MODE_BACKTEST,
        token='86b951b2035896a8c3813a328f8a575b504948be',
        backtest_start_time='2017-06-06 09:00:00',
        backtest_end_time='2019-10-24 16:00:00',
        backtest_adjust=ADJUST_PREV,
        backtest_initial_cash=5000,
        backtest_commission_ratio=0.0001,
        backtest_slippage_ratio=0.0001)
