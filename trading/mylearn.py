import datetime
with open('q-learning-result.txt', 'a') as f:
    str = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S') + " : " + str(1) + " " + str(2) + " " + \
          str(3) + '\r'
    f.write(str)