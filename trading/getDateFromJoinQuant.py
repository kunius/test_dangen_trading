from jqdatasdk import *
import sqlite3
from datetime import datetime

auth('15555189680','189680')
is_auth = is_auth()
print(is_auth)

conn = sqlite3.connect('C:\\sqlite\\'+'RB9999'+'_1m'+'.db')
c = conn.cursor()
df = get_bars('RB9999.XSGE', 1000000000, unit='1m',fields=['date','open','high','low','close'],include_now=False,end_dt='2022-08-05')
for index, row in df.iterrows():
    c.execute("insert into main (bob,eob,high,low,open,close) values ('%s','%s','%d','%d','%d','%d')" % (row['date'].strftime("%Y-%m-%d %H:%M:%S"),row['date'].strftime("%Y-%m-%d %H:%M:%S"),
              row['high'],row['low'],row['open'],row['close']))

    # a = row['date'].strftime("%Y-%m-%d %H:%M:%S")
    # print(a)
conn.commit()

c.close()
conn.close()