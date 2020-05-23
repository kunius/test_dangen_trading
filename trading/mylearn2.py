import sqlite3

conn = sqlite3.connect('D:\\sqlite\\' + 'log_time' + '.db')

c = conn.cursor()

conn.commit()