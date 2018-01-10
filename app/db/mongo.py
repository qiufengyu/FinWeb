import pymongo
import datetime

from django.conf import settings
from django.contrib.auth.hashers import make_password, check_password

# 9hv-7Ub-whD-77P
class MongoUser(object):
  def __init__(self):
    self.client = pymongo.MongoClient(settings.MONGO_HOST, settings.MONGO_PORT)
    self.db = self.client[settings.MONGO_DBNAME]
    self.db_users = self.db.users
    self.stockstable = self.db[settings.MONGO_COLLECTION_EAST_MONEY_STOCK_LIST]
    self.db_users.ensure_index('username', unique=True)
    self.db_users.ensure_index('email', unique=True)

  def __del__(self):
    self.client.close()

  def check_user_exist(self, username):
    return self.db_users.find_one({'username': username})

  def check_user_password(self, username, password):
    db_password = self.get_user_password(username)
    if db_password:
      return check_password(password=password, encoded=db_password)
    return None

  def check_email_exist(self, email):
    return self.db_users.find_one({'email': email})

  def salt_password(self, password):
    return make_password(password, salt=None)  # hashlib.md5(password.encode('utf-8') + self.salt).hexdigest()

  def insert_one_user(self, user):
    new_user = dict(user).copy()
    if new_user['username'] and new_user['password']:
      new_user['recent_reads_title'] = []
      new_user['recent_reads_url'] = []
      new_user['tags'] = []
      new_user['stocks'] = []
      salted_password = self.salt_password(
        new_user['password'])  # hashlib.md5(new_user['user_password'].encode('utf-8') + self.salt).hexdigest()
      new_user['password'] = salted_password
      return self.db_users.insert_one(dict(new_user))
    else:
      return None

  def get_user_password(self, username):
    if self.check_user_exist(username):
      return self.db_users.find_one({'username': username})['password']
    else:
      return None

  def get_user_password_by_email(self, email):
    if self.check_email_exist(email):
      return self.db_users.find_one({'email': email})['password']
    else:
      return None

  def update_user_password(self, username, new_password):
    if self.check_user_exist(username):
      new_hash_password = make_password(new_password, salt=None)
      return self.db_users.find_one_and_update({'username': username},
                                               {'$set': {'password': new_hash_password}})
    else:
      return None

  def get_user_stocks(self, username):
    if self.check_user_exist(username):
      stocks_dict_list = self.db_users.find_one({'username': username})['stocks']
      sorted_stocks_dict_list = sorted(stocks_dict_list, key=lambda x: x['datetime'])
      stocks_list = []
      for y in sorted_stocks_dict_list:
        stocks_list.append(y['stock_id'])
      return stocks_list
    else:
      return None

  def delete_user_stock(self, username, stock_id):
    user_entity = self.check_user_exist(username)
    if user_entity:
      user_stocks = user_entity['stocks']
      for stock_del in user_stocks:
        if stock_id == stock_del['stock_id']:
          user_stocks.remove(stock_del)
      print("in mongo.py", user_stocks)
      # 写回数据库
      return self.db_users.find_one_and_update({'username': username},
                                               {'$set': {'stocks': user_stocks}})
    return None

  def get_user_email(self, username):
    user_entity = self.check_user_exist(username)
    if user_entity:
      return self.db_users.find_one({'username': username})['email']
    else:
      return None

  def add_user_stock(self, username, stock_id):
    user_stocks = None
    stock_entity = None
    print("Try adding stock", stock_id)
    if stock_id.startswith('sz') or stock_id.startswith('sh'):
      stock_entity = self.stockstable.find_one({'stock_id': stock_id})
      if stock_entity:
        user_entity = self.check_user_exist(username)
        if user_entity:
          user_stocks = user_entity['stocks']
          this_stock = {}
          this_stock['stock_id'] = stock_id
          this_stock['datetime'] = datetime.datetime.now()
          user_stocks.append(this_stock)
    else:
      stock_entity = self.stockstable.find_one({'stock_name': stock_id})
      if stock_entity:
        user_entity = self.check_user_exist(username)
        if user_entity:
          user_stocks = user_entity['stocks']
          this_stock = {}
          this_stock['stock_id'] = stock_entity['stock_id']
          this_stock['datetime'] = datetime.datetime.now()
          user_stocks.append(this_stock)
    if user_stocks:
      # 去重
      stock_id_set = set()
      for stock in user_stocks:
        if stock['stock_id'] not in stock_id_set:
          stock_id_set.add(stock['stock_id'])
        else:
          user_stocks.remove(stock)
      self.db_users.find_one_and_update({'username': username},
                                        {'$set': {'stocks': user_stocks}})
      return stock_entity
    return None


class MongoNews(object):
  def __init__(self):
    self.client = pymongo.MongoClient(settings.MONGO_HOST, settings.MONGO_PORT)
    self.db = self.client[settings.MONGO_DBNAME]
    self.db_candidate = self.db.candidate

  def get_latest_news(self, top=10):
    """
    :return: 最新的十条新闻，不论用户喜好，仅做测试时用。
    或者在主页显示，为了节省数据传输的开销，先不传输具体的内容
    """
    news_cursor = self.db_candidate.find().sort('pb_time', pymongo.DESCENDING)
    ret_news = []
    i = 0
    for news in news_cursor:
      if i > top:
        break
      news_item = {}
      news_item['id'] = news['_id']
      news_item['title'] = news['title']
      news_item['pb_time'] = news['pb_time']
      news_item['source'] = news['source']
      if 'author' in news and news['author']:
        news_item['author'] = news['author']
      else:
        news_item['author'] = ''
      news_item['url'] = news['url']
      if 'summary' in news:
        news_item['summary'] = news['summary']
      else:
        contents = news['para_content_text_and_images']
        for c in contents:
          if 'http' in c or len(c) < 25:
            continue
          else:
            news_item['summary'] = c
            break
      c2 = news_item['summary']
      if len(c2) > 120:
        news_item['summary'] = c2[:115] + '......'
      ret_news.append(news_item)
      i = i + 1
    return ret_news