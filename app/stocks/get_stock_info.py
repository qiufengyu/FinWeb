"""
其他数据接口
查看日K线图：
http://image.sinajs.cn/newchart/daily/n/sh601006.gif
分时线的查询：
http://image.sinajs.cn/newchart/min/n/sh000001.gif
日K线查询：
http://image.sinajs.cn/newchart/daily/n/sh000001.gif
周K线查询：
http://image.sinajs.cn/newchart/weekly/n/sh000001.gif
月K线查询：
http://image.sinajs.cn/newchart/monthly/n/sh000001.gif
"""
import urllib.request

SINA_JS_STOCK_REQUEST = 'http://hq.sinajs.cn/list='

def get_stock_info(stock_code):
  req = urllib.request.Request(url=SINA_JS_STOCK_REQUEST + stock_code)
  response = urllib.request.urlopen(req)
  data = response.read().decode("gbk").split(',')
  current = float(data[3])
  previous_close = float(data[2])
  delta = float(data[3]) - float(data[2])
  if previous_close > 0:
    percent = 100.0 * delta / previous_close
  else:
    percent = 0.0
  start_index = data[0].index('"') + 1
  name = data[0][start_index:]
  stock_info = {}
  stock_info['id'] = stock_code
  stock_info['name'] = name
  stock_info['current'] = "{:.2f}".format(current)
  stock_info['delta'] = "{:+.2f}".format(delta)
  stock_info['percent'] = "{:+.2f}".format(percent)
  if delta > 0.0:
    stock_info['color'] = 'red'
    stock_info['current'] = stock_info['current'] + ' ▲'
  elif delta < 0.0:
    stock_info['color'] = 'green'
    stock_info['current'] = stock_info['current'] + ' ▼'
  else:
    stock_info['color'] = 'black'
  return stock_info

def get_stock_info_list(stock_code_list):
  stock_code_all = ','.join(stock_code_list)
  req = urllib.request.Request(url=SINA_JS_STOCK_REQUEST + stock_code_all)
  response = urllib.request.urlopen(req)
  data_list = response.read().decode("gbk").split('\n')
  stock_info_list = []
  for i in range(len(data_list)-1):
    print(data_list[i])
    data = data_list[i].split(',')
    current = float(data[3])
    previous_close = float(data[2])
    delta = float(data[3]) - float(data[2])
    if previous_close > 0:
      percent = 100.0 * delta / previous_close
    else:
      percent = 0.0
    start_index = data[0].index('"') + 1
    name = data[0][start_index:]
    stock_info = {}
    stock_info['id'] = stock_code_list[i]
    stock_info['name'] = name
    stock_info['current'] = "{:.2f}".format(current)
    stock_info['delta'] = "{:+.2f}".format(delta)
    stock_info['percent'] = "{:+.2f}".format(percent)
    if delta > 0.0:
      stock_info['color'] = 'red'
      stock_info['current'] = stock_info['current'] + ' ▲'
    elif delta < 0.0:
      stock_info['color'] = 'green'
      stock_info['current'] = stock_info['current'] + ' ▼'
    else:
      stock_info['color'] = 'black'
    stock_info_list.append(stock_info)
  print(stock_info_list)
  return stock_info_list