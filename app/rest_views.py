import jieba
import numpy as np

from django.contrib import auth
from scipy.spatial.distance import cosine
from rest_framework.views import APIView
from app.db.mongo import MongoUser, MongoNews
from app.recommend.wordvec import WordVec

from rest_framework.response import Response

from app.stocks.get_stock_info import get_stock_info_list, get_stock_info

db_users = MongoUser()
db_news = MongoNews()

"""
提供一些主要的 API 接口
1. 登录、注册
2. 浏览个性化推荐的新闻，阅读新闻
3. 自定义自选股，查看、添加、删除
"""

class Login(APIView):
  """
    HTTP GET:
    :param username
    :param password
    """
  def __init__(self):
    self.authentication_classes = []
    self.permission_classes = []

  def get(self, request, format=None):
    username = request.GET.get('username', None)
    # 直接提供明文密码？
    password = request.GET.get('password', None)
    if username and password:
      res = db_users.check_user_password(username, password)
      user = auth.authenticate(request=request, username=username, password=password)
      auth.login(request, user)
      if res:
        return Response({'status': 1})
    return Response({'status': -1})

class Register(APIView):
  """
  HTTP GET:
  :param username
  :param password
  :param email
  """

  def __init__(self):
    self.authentication_classes = []
    self.permission_classes = []

  def get(self, request, format=None):
    username = request.GET.get('username', None)
    password = request.GET.get('password', None)
    email = request.GET.get('email', None)

    if username and password and email:
      if db_users.check_user_exist(username):
        # 重复的用户名
        return Response({'status': -3})
      elif db_users.check_email_exist(email):
        # 重复的邮件地址
        return Response({'status': -4})
      else:
        # 注册成功，数据库中增加用户
        new_user = {}
        new_user['username'] = username
        new_user['password'] = password
        new_user['email'] = email
        if db_users.insert_one_user(new_user):
          user = auth.authenticate(request=request, username=new_user['username'], password=new_user['password'])
          # pprint.pprint(new_user)
          auth.login(request, user)
          return Response({'status': 1})
        else:
          return Response({'status': -5})
    else:
      # 无效输入
      return Response({'status': -2})



        # form.save()

class GetRecommend(APIView):
  """
    HTTP GET:
    :param username
    """
  def __init__(self, dim=128):
    self.authentication_classes = []
    self.permission_classes = []
    self.word_vec = WordVec()
    self.dim = dim

  def _get_title_vec(self, title: str):
    item_matrix = []
    for token in jieba.cut(title, cut_all=False):
      token_vec = self.word_vec.getvec(token)
      if token_vec is not None:
        item_matrix.append(token_vec)
    item_array = np.array(item_matrix)
    return (np.mean(item_array, axis=0), np.max(item_array, axis=0))

  def get(self, request, format=None):
    print(request.GET)
    username = request.GET.get('username', None)
    user_embedding_matrix = []
    candidates = db_news.get_latest_news(top=100)
    for candidate in candidates:
      candidate['score'] = candidate['reads'] / 1000.0
    if username:
      user_read_list = db_users.get_user_recent_reads(username)
      if len(user_read_list) < 1:
        user_embedding_matrix.append([0.0] * self.dim)
      else:
        for read in user_read_list:
          user_embedding_matrix.append(self._get_title_vec(read)[0])
      user_embedding_array = np.array(user_embedding_matrix)
      user_em_mean = np.mean(user_embedding_array, axis=0)
      user_em_max = np.max(user_embedding_array, axis=0)
      user_em = np.concatenate((user_em_mean, user_em_max), axis=0)
      if len(user_read_list) > 1:
        for candidate in candidates:
          candidate_title = candidate['title']
          candidate_temp = self._get_title_vec(candidate_title)
          candidate_em = np.concatenate((candidate_temp[0], candidate_temp[1]), axis=0)
          candidate['score'] += 1.0 - cosine(user_em, candidate_em)

    data = sorted(candidates, key=lambda x: x['score'], reverse=True)
    return Response(data)

class AddUserReadNews(APIView):
  """
    HTTP GET:
    :param username
    :param news_id
    """
  def __init__(self):
    self.authentication_classes = []
    self.permission_classes = []

  def get(self, request, format=None):
    username = request.GET.get('username', None)
    # 从请求中得到阅读的新闻 id
    news_id = request.GET.get('newsid', None)
    if username and news_id:
      # 数据库中增加一次阅读量
      db_news.increase_reads(news_id)
      # 获取新闻标题
      title = db_news.get_news_title_by_id(news_id)
      if title:
        # 把新的新闻记录加到用户的历史记录中
        db_users.add_user_recent_reads_title(username, title)
        return Response({'status': 1})
    return Response({'status': -1})

class GetUserStocks(APIView):
  """
  HTTP GET:
  :param username
  """
  def __init__(self):
    self.authentication_classes = []
    self.permission_classes = []

  def get(self, request, format=None):
    username = request.GET.get('username', None)
    if username:
      stocks_db = db_users.get_user_stocks(username)
      if stocks_db:
        stocks_info_list = get_stock_info_list(stocks_db)
        return Response({'status': 1, 'stocklist': stocks_info_list})
    return Response({'status': -1, 'stocklist': []})


class AddUserStocks(APIView):
  """
  HTTP GET:
  :param username
  :param stock_id
  """
  def __init__(self):
    self.authentication_classes = []
    self.permission_classes = []

  def get(self, request, format=None):
    username = request.GET.get('username', None)
    stock_id = request.GET.get('stockid', None)
    if username and stock_id:
      print(username, stock_id)
      stock_entity = db_users.add_user_stock(username, stock_id)
      print(stock_entity)
      if stock_entity:
        return Response({'status': 1, 'stockentity': stock_entity})
    return Response({'status': -1})

class DelUserStocks(APIView):
  """
  HTTP GET:
  :param username
  :param stock_id
  """
  def __init__(self):
    self.authentication_classes = []
    self.permission_classes = []

  def get(self, request, format=None):
    username = request.GET.get('username', None)
    stock_id = request.GET.get('stockid', None)
    if username and stock_id:
      if db_users.delete_user_stock(username, stock_id) is not None:
        stock_entity = get_stock_info(stock_id)
        return Response({'status': 1, 'stockentity': stock_entity})
    return Response({'status': -1})


if __name__ == '__main__':
  gr = GetRecommend()
  gr.get(None)





