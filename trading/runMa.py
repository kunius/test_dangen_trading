import os
import datetime

max = 50
lose_amount_max = 50
win_amount_max = 50
for index_fast in range(5,max,3):
    for index_slow in range(index_fast+1,max,3):
        for lose_amount in range (10,lose_amount_max,5):
            for win_amount in range(10,win_amount_max,5):
                for plus in range(1,3):
                    os.system("python Ma.py"+" "+str(index_fast)+" "+str(index_slow)+" "+str(lose_amount)+" "+str(win_amount)
                              +" "+str(plus))

