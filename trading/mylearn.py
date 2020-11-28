import socket
import time
import json


def readInfoFromJson(key):
   with open('./info.json', 'r', encoding='utf8')as fp:
      json_data = json.load(fp)
      return json_data[key]

def writeInfoToJson(keys, values):
   with open('./info.json', 'w', encoding='utf8')as fp:
      json_data = {}
      for i in range(0, len(keys)):
         json_data[keys[i]] = values[i]
      json.dump(json_data, fp, ensure_ascii=False)

def updateInfoToJson(key, value):
   with open('./info.json', 'r+', encoding='utf8')as fp:
      json_data = json.load(fp)
      dataList = json_data[key]
      if type(dataList) is list:
         dataList.pop(0)
         dataList.append(value)
         json_data[key] = dataList
      else:
         json_data[key] = value
      fp.seek(0)
      json.dump(json_data, fp, ensure_ascii=False)
#writeInfoToJson(["computer","result"], [2,4])
a=updateInfoToJson('computer',8)
print(a)