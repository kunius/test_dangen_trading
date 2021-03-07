import socket
import time
import json
import vv_backtest.utils

configPath = 'c:/main2.json'
tradeResultKey = 'trade_result'

vv_backtest.utils.writeInfoToJson(configPath, [tradeResultKey, "tade_count"], [[9,9,9,9,9,9,9,9], 000])
vv_backtest.utils.updateInfoToJson(configPath, "tade_count", 100)
vv_backtest.utils.updateInfoToJson(configPath, "tade_count", 2)