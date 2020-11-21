import socket
import time
import json

HOST = 'localhost'
PORT = 10888
s = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
s.connect((HOST,PORT))
data = 'get'
print("222222222222")
while True:
   data = s.recv(512)
   if not data:
      print("server closed when recv")
      break

   mylist = json.loads(data.decode("utf-8"))
   print('Receve from server:\n', mylist)
   s.sendall("yes".encode("utf-8"))

s.close()