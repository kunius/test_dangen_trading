import socket
import threading
import  time
import json
import sqlite3
import vv_backtest.base
import datetime


HOST = ''
PORT = 10888
connections = []
start_data = datetime.datetime.strptime('2017-01-01','%Y-%m-%d')
end_data = datetime.datetime.strptime('2018-01-01','%Y-%m-%d')

def server_connect():
    con = sqlite3.connect('C:\\sqlite\\' + 'RB9999' + 'tick' + '.db')
    cursor = con.cursor()
    datas = cursor.execute('select * from main')
    time.sleep(10)
    print("now start send tick")
    for data in datas:
        date_created_at = vv_backtest.base._getDatetime(data[1])
        if date_created_at < start_data or date_created_at > end_data:
            continue

        for con in connections:
            con[0].sendall(json.dumps(data).encode("utf-8"))
            print(str(con[1]) +" send: " + json.dumps(data))
        for con in connections:
            recv_data = con[0].recv(512)
            print(str(con[1]) + " recv: " + json.dumps(data))
    for con in connections:
        con[0].close()



if __name__ == "__main__":
    s = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
    s.bind((HOST,PORT))
    s.listen(5)
    t = threading.Thread(target=server_connect)
    t.start()
    while True:
        conn, addr = s.accept()
        print('Client\'s Address:', addr)
        connections.append((conn, addr[1]))

