import numpy as np
import pymongo
import datetime

from bson import ObjectId
from django.conf import settings
from django.contrib.auth.hashers import make_password, check_password

# 9hv-7Ub-whD-77P
from app.stocks.get_stock_info import get_stock_info


class MongoUser(object):
  def __init__(self):
    self.client = pymongo.MongoClient(settings.MONGO_HOST, settings.MONGO_PORT)
    self.db = self.client[settings.MONGO_DBNAME]
    self.db_users = self.db.users
    self.stockstable = self.db[settings.MONGO_COLLECTION_EAST_MONEY_STOCK_LIST]
    self.db_users.ensure_index('username', unique=True)
    self.db_users.ensure_index('email', unique=True)

  def __del__(self):
    pass
    # self.client.close()

  def check_user_exist(self, username: str):
    return self.db_users.find_one({'username': username})

  def check_user_password(self, username: str, password: str) -> bool:
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
      new_user['recent_reads_objid'] = []
      new_user['likes_title'] = []
      new_user['likes_url'] = []
      new_user['likes_objid'] = []
      new_user['friends'] = []
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
      user = self.db_users.find_one({'username': username})
      stocks_dict_list = []
      if 'stocks' in user:
        stocks_dict_list = user['stocks']
      sorted_stocks_dict_list = sorted(stocks_dict_list, key=lambda x: x['datetime'])
      stocks_list = []
      for y in sorted_stocks_dict_list:
        stocks_list.append(y['stock_id'])
      return stocks_list
    else:
      return None

  def get_user_recent_reads(self, username):
    recent_reads = []
    if self.check_user_exist(username):
      user = self.db_users.find_one({'username': username})
      if 'recent_reads_title' in user:
        recent_reads = user['recent_reads_title']
    return recent_reads

  def get_user_recent_reads_url(self, username):
    recent_reads = []
    if self.check_user_exist(username):
      user = self.db_users.find_one({'username': username})
      if 'recent_reads_url' in user:
        recent_reads = user['recent_reads_url']
    return recent_reads

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

  def get_user_em(self, username):
    user_entity = self.check_user_exist(username)
    if user_entity:
      ue = self.db_users.find_one({'username': username})
      if "profile" in ue:
        return np.array(ue["profile"])
    return None

  def update_user_em(self, username, em):
    user_entity = self.check_user_exist(username)
    em_list = em.tolist()
    if user_entity:
      self.db_users.find_one_and_update({'username': username},
                                        {'$set': {'profile': em_list}})
    else:
      return None

  def add_user_stock(self, username, stock_id):
    user_stocks = None
    stock_entity = None
    real_id = stock_id
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
          this_stock['stock_id'] = str(stock_entity['stock_id'])
          real_id = this_stock['stock_id']
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
    if stock_entity:
      return get_stock_info(real_id)
    return None

  def add_user_tag(self, username, tag_name):
    user_tags = None
    # print("Try adding tag", tag_name)
    user_entity = self.check_user_exist(username)
    if user_entity:
      user_tags = user_entity["tags"]
      this_tag = {}
      this_tag["name"] = tag_name
      this_tag["datetime"] = datetime.datetime.now()
      user_tags.append(this_tag)
    if user_tags:
      tags_id_set = set()
      for tag in user_tags:
        if tag["name"] not in tags_id_set:
          tags_id_set.add(tag["name"])
        else:
          user_tags.remove(tag)
      self.db_users.find_one_and_update({'username': username},
                                        {'$set': {'tags': user_tags}})
      return tag_name
    return None

  def get_user_tags(self, username):
    if self.check_user_exist(username):
      user = self.db_users.find_one({'username': username})
      if 'tags' in user:
        tags_dict_list = user['tags']
        sorted_tags_dict_list = sorted(tags_dict_list, key=lambda x: x['datetime'])
        tags_list = []
        idx = 0
        for x in sorted_tags_dict_list:
          idx += 1
          this_tag = {}
          this_tag['name'] = x['name']
          this_tag['id'] = idx
          tags_list.append(this_tag)
        return tags_list
    else:
      return None

  def delete_user_tag(self, username, tag_name):
    user_entity = self.check_user_exist(username)
    if user_entity:
      user_tags = user_entity['tags']
      if tag_name in user_tags:
        del user_tags[tag_name]
      # 写回数据库
      self.db_users.find_one_and_update({'username': username},
                                               {'$set': {'tags': user_tags}})
      return tag_name
    return None

  def user_likes_add(self, username, news):
    user_entity = self.check_user_exist(username)
    if user_entity:
      # print(user_entity)
      user_likes_title = user_entity['likes_title']
      user_likes_url = user_entity['likes_url']
      user_likes_objid = user_entity['likes_objid']
      if news['id'] in user_likes_objid:
        # 如果已经收藏，点击取消
        user_likes_title.remove(news['title'])
        user_likes_url.remove(news['url'])
        user_likes_objid.remove(news['id'])
        self.db_users.find_one_and_update({'username': username},
                                          {'$set': {'likes_title': user_likes_title,
                                                    'likes_url': user_likes_url,
                                                    'likes_objid': user_likes_objid } } )
        return -1
      else:
        user_likes_title.append(news['title'])
        user_likes_url.append(news['url'])
        user_likes_objid.append(news['id'])
        self.db_users.find_one_and_update({'username': username},
                                          {'$set': {'likes_title': user_likes_title,
                                                    'likes_url': user_likes_url,
                                                    'likes_objid': user_likes_objid}})
        return 1
    return -2

  def user_likes_delete(self, username, news):
    user_entity = self.check_user_exist(username)
    if user_entity:
      # print(user_entity)
      user_likes_title = user_entity['likes_title']
      user_likes_url = user_entity['likes_url']
      user_likes_objid = user_entity['likes_objid']
      if news["id"] in user_likes_objid:
        # 如果已经收藏，点击取消
        user_likes_title.remove(news['title'])
        user_likes_url.remove(news['url'])
        user_likes_objid.remove(news['id'])
        self.db_users.find_one_and_update({'username': username},
                                          {'$set': {'likes_title': user_likes_title,
                                                    'likes_url': user_likes_url,
                                                    'likes_objid': user_likes_objid}})
        return 1
      else:
        return -1
    return -2

  def add_user_friend(self, username, friend):
    user_entity = self.check_user_exist(username)
    friend_entity = self.check_user_exist(friend)
    if user_entity and friend_entity:
      # print(user_entity)
      user_friends = user_entity['friends']
      if friend in user_friends:
        return -1
      else:
        user_friends.append(friend)
        self.db_users.find_one_and_update({'username': username},
                                          {'$set': {'friends': user_friends}})
        return 1
    return -1

  def del_user_friend(self, username, friend):
    user_entity = self.check_user_exist(username)
    friend_entity = self.check_user_exist(friend)
    if user_entity and friend_entity:
      # print(user_entity)
      user_friends = user_entity['friends']
      if friend in user_friends:
        user_friends.remove(friend)
        self.db_users.find_one_and_update({'username': username},
                                          {'$set': {'friends': user_friends}})
        return 1
      else:
        return -1
    return -1

  def add_user_recent_reads(self, username, news):
    user_entity = self.check_user_exist(username)
    if user_entity:
      print(user_entity)
      recent_reads_objid = user_entity['recent_reads_objid']
      recent_reads_title = user_entity['recent_reads_title']
      recent_reads_url = user_entity['recent_reads_url']
      if news['id'] in recent_reads_objid:
        return
      if len(recent_reads_objid) < 50:
        recent_reads_objid.append(news['id'])
        recent_reads_title.append(news['title'])
        recent_reads_url.append(news['url'])
      else:
        recent_reads_objid = [news['id']] + recent_reads_objid[:-1]
        recent_reads_title = [news['title']] + recent_reads_title[:-1]
        recent_reads_url = [news['url']] + recent_reads_url[:-1]
      self.db_users.find_one_and_update({'username': username},
                                        {'$set': {'recent_reads_url': recent_reads_url,
                                                  'recent_reads_title': recent_reads_title,
                                                  'recent_reads_objid': recent_reads_objid}})

  def get_user_recent_like_one(self, username):
    print(username)
    recent_like_id = None
    recent_like_title = None
    if self.check_user_exist(username):
      user = self.db_users.find_one({'username': username})
      if 'likes_objid' in user:
        likes_objid = user['likes_objid']
        recent_like_id = likes_objid[-1] if len(likes_objid) > 0 else None
      if 'likes_title' in user:
        likes_title = user['likes_title']
        recent_like_title = likes_title[-1] if len(likes_title) > 0 else None
    return recent_like_id, recent_like_title


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
    news_cursor = self.db_candidate.find().sort([
      ('reads', pymongo.DESCENDING),
      ('pb_time', pymongo.DESCENDING) ])
    ret_news = []
    i = 0
    for news in news_cursor:
      if i > top:
        break
      news_item = {}
      news_item['id'] = str(news['_id'])
      news_item['title'] = news['title']
      news_item['pb_time'] = news['pb_time']
      news_item['source'] = news['source']
      news_item['reads'] = int(news['reads'])
      news_item['paras'] = news['para_content_text_and_images']
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
          if '//' in c or len(c) < 25:
            continue
          else:
            news_item['summary'] = c
            break
      c2 = news_item['summary'] if 'summary' in news_item else ''
      if len(c2) > 120:
        news_item['summary'] = c2[:115] + '......'
      ret_news.append(news_item)
      i = i + 1
    return ret_news

  def get_news_by_id(self, id: str):
    res = self.db_candidate.find_one({"_id": ObjectId(id)})
    # print(res)
    if res:
      res['id'] = str(res['_id'])
      return res
    else:
      return None

  def increase_reads(self, id: str):
    res = self.db_candidate.find_one({"_id": ObjectId(id)})
    if res:
      self.db_candidate.find_one_and_update({'_id': ObjectId(id)},
                          {'$inc': {'reads': 1}})

  def add_liked(self, newsid=None, username=None):
    if newsid and username:
      old = self.db_candidate.find_one({'_id': ObjectId(newsid)})
      likedby = [username]
      if "likedby" in old:
        if username not in old["likedby"]:
          likedby = likedby + old["likedby"]
      self.db_candidate.find_one_and_update({'_id': ObjectId(newsid)},
                                            {'$set': {'likedby': likedby}})

  def del_liked(self, newsid=None, username=None):
    if newsid and username:
      old = self.db_candidate.find_one({'_id': ObjectId(newsid)})
      if "likedby" in old:
        old_likedby = old["likedby"]
        if username in old_likedby:
          likedby = old_likedby.remove(username)
          self.db_candidate.find_one_and_update({'_id': ObjectId(newsid)},
                                            {'$set': {'likedby': likedby}})





