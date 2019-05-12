from pprint import pprint

import jieba
import numpy as np
from scipy.spatial.distance import cosine
from collections import defaultdict
from operator import itemgetter

from django.conf import settings
from django.contrib import auth
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.tokens import default_token_generator
from django.http import HttpResponseServerError, HttpResponse
from django.http import JsonResponse

from django.core.mail import send_mail
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.template import loader

from django.utils.translation import ugettext, ugettext_lazy as _

from django.contrib.auth.models import User
from django.contrib.auth.forms import PasswordChangeForm
from django.shortcuts import render, redirect

from app.forms.loginForm import LoginForm
from app.forms.tagForm import TagForm
from app.forms.userForm import UserForm
from app.forms.stockForm import StockForm

from app.forms.passwordResetForm import PasswordResetForm
from app.forms.passwordChangeForm import PasswordChangeForm
from app.forms.confirmPasswordResetForm import ConfirmPasswordResetForm
from app.db.mongo import MongoUser, MongoNews
from app.recommend.wordvec import WordVec
from app.stocks.get_stock_info import get_stock_info, get_stock_info_list

db_users = MongoUser()
db_news = MongoNews()
word_vec = WordVec()

def index(request):
  news_list = db_news.get_latest_news(top=15)
  return render(request, 'index.html', context={'news_list': news_list})

def login(request):
  if request.method == 'POST':
    form = LoginForm(request.POST)
    if form.is_valid():
      username = request.POST['username']
      password = request.POST['password']
      user = auth.authenticate(request=request, username=username, password=password)
      if user and user.is_active:
        auth.login(request, user)
        print("Login ok")
        # calculate user profile
        uem = get_user_profile(username)
        db_users.update_user_em(username, uem)
        return redirect('/')
      else:
        messages.error(request, _("请输入正确的用户和密码，注意它们它们都是区分大小写的。"))
    else:
      messages.error(request, _("请输入正确的用户和密码，注意它们它们都是区分大小写的。"))
  else:
    form = LoginForm()
  return render(request, 'registration/login.html', context={'form': form})

# 管理个性化标签
@login_required
def tagsview(request):
  username = request.user.username
  form = TagForm()
  tags_list = []
  if request.method == 'POST':
    new_tag = db_users.add_user_tag(username=username, tag_name=request.POST['tag_name'])
    tags_db = db_users.get_user_tags(username)
    if new_tag and tags_db:
      return render(request, 'user/usertag.html', context={'tags': tags_db, 'form': form,
                                                            'new_tag': new_tag})
    elif tags_db:
      return render(request, 'user/usertag.html', context={'tags': tags_db, 'form': form,
                                                            'new_tag_error': '添加失败，请输入合法且不重复的标签！'})
  else:
    tags_db = db_users.get_user_tags(username)
    if tags_db:
      return render(request, 'user/usertag.html', context={'tags': tags_db, 'form': form})
  return render(request, 'user/usertag.html', context={"tags": tags_list, 'form': form})

@login_required
def tagsadd(request):
  username = request.user.username
  if request.method == 'POST':
    if request.POST['tag_name'] and username:
      tag_entity = db_users.add_user_tag(username, request.POST['tag_name'])
      if tag_entity:
        return JsonResponse({"info": 0})
  return HttpResponseServerError("添加错误，请检查您的输入！", content_type="text/plain")

@login_required
def tagsdel(request):
  username = request.user.username
  if request.method == 'POST':
    if request.POST['tag_name'] and username:
      tag_name = db_users.delete_user_tag(username, request.POST['tag_name'])
      if tag_name:
        return JsonResponse({"info": 0, "name": tag_name})
  return HttpResponseServerError('删除错误！', content_type="text/plain")

# 管理用户的好友
@login_required
def friendsview(request):
  friends = []
  username = str(request.user)
  if username:
    user_entity = db_users.check_user_exist(username)
    if user_entity:
      friend_list = user_entity["friends"]
      for x in friend_list:
        friend = {}
        friend["username"] = x
        recent_like_id, recent_like_title = db_users.get_user_recent_like_one(x)
        if recent_like_title and recent_like_id:
          friend["recentid"] = recent_like_id
          friend["recenttitle"] = recent_like_title
        friends.append(friend)
  return render(request, 'user/userfriend.html', context={"friends": friends})

def friendsadd(request):
  if request.method == 'POST':
    username = str(request.user)
    friendname = request.POST.get('friendname', None)
    if username and friendname:
      res = db_users.add_user_friend(username=username, friend=friendname)
      if res == 1:
        return JsonResponse({"info": 1})
      else:
        return JsonResponse({"info": 0})
  return HttpResponseServerError('数据库错误！', content_type="text/plain")

def friendsdelete(request):
  if request.method == 'POST':
    username = str(request.user)
    friendname = request.POST.get('fname', None)
    if username and friendname:
      res = db_users.del_user_friend(username=username, friend=friendname)
      if res == 1:
        return JsonResponse({"info": 1})
      else:
        return JsonResponse({"info": 0})
  return HttpResponseServerError('数据库错误！', content_type="text/plain")

# 管理用户的收藏
@login_required
def newslike(request):
  like_content = []
  username = str(request.user)
  if username:
    user_entity = db_users.check_user_exist(username)
    if user_entity:
      like_list = user_entity["likes_title"]
      like_list_objid = user_entity["likes_objid"]
      for (x, y) in zip(like_list, like_list_objid):
        item = {}
        item["title"] = x
        item["objid"] = y
        like_content.append(item)
  return render(request, 'user/userlike.html', context={"likecontext": like_content})

# 查看一个用户的收藏
@login_required
def userview(request, username=None):
  like_content = []
  target_user = "查无此人，"
  if username:
    target_user += str(username)
    user_entity = db_users.check_user_exist(username)
    if user_entity:
      exists = 1
      target_user = username
      like_list = user_entity["likes_title"]
      like_list_objid = user_entity["likes_objid"]
      for (x, y) in zip(like_list, like_list_objid):
        item = {}
        item["title"] = x
        item["objid"] = y
        like_content.append(item)
      return render(request, 'user/user.html',
                      context={"likecontext": like_content, "targetuser": target_user, "exists": exists})
  return render(request, 'user/user.html', context={"likecontext": like_content, "targetuser": target_user})

# 仅接受 POST 请求
def add_read_news(request):
  if request.method == 'POST':
    read_id = request.POST.get('news_id', None)
    news_item = None
    if read_id:
      db_news.increase_reads(read_id)
      news_item = db_news.get_news_by_id(read_id)
    if news_item and request.user:
      username = request.user
      uu = str(username)
      # print(username, url, title)
      db_users.add_user_recent_reads(username=uu, news=news_item)
      return JsonResponse({"info": "OK"})
    return HttpResponseServerError('数据库错误！', content_type="text/plain")

def _get_title_vec(title: str):
  item_matrix = []
  for token in jieba.cut(title, cut_all=False):
    token_vec = word_vec.getvec(token)
    if token_vec is not None:
      item_matrix.append(token_vec)
  item_array = np.array(item_matrix)
  return (np.mean(item_array, axis=0), np.max(item_array, axis=0))

def get_user_profile(username):
  user_entity = db_users.check_user_exist(username)
  user_read_list = user_entity['recent_reads_title']
  user_embedding_matrix = []
  if len(user_read_list) < 1:
    user_embedding_matrix.append([0.0] * settings.WORD_VEC_DIM)
  else:
    for read in user_read_list:
      user_embedding_matrix.append(_get_title_vec(read)[0])
  user_embedding_array = np.array(user_embedding_matrix)
  user_em_mean = np.mean(user_embedding_array, axis=0)
  user_em_max = np.max(user_embedding_array, axis=0)
  user_em = np.concatenate((user_em_mean, user_em_max), axis=0)
  return user_em

# 推荐算法实现
@login_required
def news(request):
  username = str(request.user)
  print(username)
  user_embedding_matrix = []
  candidates = db_news.get_latest_news(top=150)
  for candidate in candidates:
    candidate['score'] = candidate['reads'] / 10000.0
  if username:
    user_entity = db_users.check_user_exist(username)
    user_read_list = user_entity['recent_reads_title']
    user_read_url_set = set(user_entity['recent_reads_url'])
    user_friends = user_entity["friends"]
    user_keywords = user_entity["tags"] # 字典结构
    user_friends_likes_objid = []
    for friend in user_friends:
      friend_entity = db_users.check_user_exist(friend)
      user_friends_likes_objid += friend_entity["likes_objid"]
    if len(user_read_list) < 1:
      user_embedding_matrix.append([0.0] * settings.WORD_VEC_DIM)
    else:
      for read in user_read_list:
        user_embedding_matrix.append(_get_title_vec(read)[0])
    user_embedding_array = np.array(user_embedding_matrix)
    user_em_mean = np.mean(user_embedding_array, axis=0)
    user_em_max = np.max(user_embedding_array, axis=0)
    user_em = np.concatenate((user_em_mean, user_em_max), axis=0)
    db_users.update_user_em(username, user_em)
    filtered_candidates = []
    for candidate in candidates:
      if candidate['url'] not in user_read_url_set:
        candidate_title = candidate['title']
        candidate_temp = _get_title_vec(candidate_title)
        candidate_em = np.concatenate((candidate_temp[0], candidate_temp[1]), axis=0)
        candidate['score'] += 1.0 - cosine(user_em, candidate_em)
        # 如果是好友收藏，上调 0.1
        if candidate['id'] in user_friends_likes_objid:
          candidate['score'] += 0.1
        # 如果含有用户关键字，上调 0.1
        keywords_tune = 0.0
        for kw in user_keywords:
          if kw['name'] in candidate['title']:
            keywords_tune = 0.02
        candidate['score'] += keywords_tune
        filtered_candidates.append(candidate)
  data = sorted(filtered_candidates, key=lambda x: x['score'], reverse=True)
  return render(request, 'news/news.html', context={'news_list': data})

def newsid(request, objid=None):
  # 首先需要增加用户的阅读历史记录
  username = str(request.user)
  if objid:
    print(username, ": ", objid)
    news = db_news.get_news_by_id(objid)
    # 同时为其阅读量增加 1
    db_news.increase_reads(objid)
    if "likedby" in news and len(news["likedby"]) > 0:
      news_toshow = []
      raw_likedby = defaultdict(float)
      current_user_em = get_user_profile(username)
      for friend in news["likedby"]:
        friend_em = get_user_profile(friend)
        raw_likedby[friend] = cosine(current_user_em, friend_em)
      for fr in sorted(raw_likedby.items(), key=itemgetter(1)):
        news_toshow.append(fr[0])
      news["likedby"] = news_toshow[-10:]
      print(news_toshow)
    if news:
      db_users.add_user_recent_reads(username, news)
      return render(request, "news/newsid.html", context={"news": news})
  return render(request, "news/newsid.html", context={"errorMsg": 1})

@login_required
def newslikeupdate(request):
  if request.method == 'POST':
    # 首先需要增加用户的收藏记录
    username = str(request.user)
    print(request.POST)
    objid = request.POST.get('news_id', None)
    if objid:
      print(username, "likes:", objid)
      news = db_news.get_news_by_id(objid)
      if news:
        # 用户更新收藏
        res = db_users.user_likes_add(username, news)
        if res == 1:
          # 此时发生收藏，新闻中记录
          db_news.add_liked(objid, username)
          return JsonResponse({"info": 1})
        else:
          return JsonResponse({"info": 0})
    return HttpResponseServerError("数据库添加错误", content_type="text/plain")

@login_required
def newslikedelete(request):
  if request.method == 'POST':
    username = str(request.user)
    print(request.POST)
    objid = request.POST.get('news_id', None)
    if objid:
      print(username, "dislikes:", objid)
      news = db_news.get_news_by_id(objid)
      if news:
        # 用户方面删除记录
        res1 = db_users.user_likes_delete(username, news)
        if res1 == 1:
          # 新闻方面删除
          db_news.del_liked(objid, username)
          return JsonResponse({"info": 1})
        else:
          return JsonResponse({"info": 0})
    return HttpResponseServerError("数据库删除错误", content_type="text/plain")


@login_required
def stocks(request):
  """
  用自定义的 Form 删除刚添加的自选股会出错，
  只能重定向至原来的页面，但是没有添加成功的提示信息
  """
  username = request.user.username
  form = StockForm()
  stocks_info_list = []
  if request.method == 'POST':
    new_stock = db_users.add_user_stock(username=username, stock_id=request.POST['stock_id'])
    stocks_db = db_users.get_user_stocks(username)
    # print('in views.py', stocks)
    if new_stock and stocks_db:
      stocks_info_list = get_stock_info_list(stocks_db)
      return render(request, 'stocks/stocks.html', context={'stocks': stocks_info_list, 'form': form,
                                                            'new_stock': new_stock['name']})
    elif stocks_db:
      stocks_info_list = get_stock_info_list(stocks_db)
      return render(request, 'stocks/stocks.html', context={'stocks': stocks_info_list, 'form': form,
                                                            'new_stock_error': '添加失败，请输入正确的股票代码或股票名称！'})
  else:
    stocks_db = db_users.get_user_stocks(username)
    # print('in views.py', stocks)
    if stocks_db:
      stocks_info_list = get_stock_info_list(stocks_db)
  return render(request, 'stocks/stocks.html', context={'stocks': stocks_info_list, 'form': form})


@login_required
def stocks_add(request):
  username = request.user.username
  if request.method == 'POST':
    if request.POST['stock_id'] and username:
      stock_entity = db_users.add_user_stock(username, request.POST['stock_id'])
      if stock_entity:
        stock_info = get_stock_info(stock_entity['stock_id'])
        return JsonResponse(stock_info)
  return HttpResponseServerError("添加错误，请检查您的股票代码或者股票名称！", content_type="text/plain")


@login_required
def stocks_del(request):
  username = request.user.username
  if request.method == 'POST':
    if request.POST['stock_id'] and username:
      if db_users.delete_user_stock(username, request.POST['stock_id']) is not None:
        stock_info = get_stock_info(request.POST['stock_id'])
        return JsonResponse(stock_info)
  return HttpResponseServerError('删除错误！', content_type="text/plain")


@login_required
def logout(request):
  # type(request.user): django.utils.functional.SimpleLazyObjectdb.sqlite3
  # print(type(request.user.username)) -> str
  auth.logout(request)
  return redirect('/')

def register(request):
  if request.method == 'POST':
    form = UserForm(request.POST)
    if form.is_valid():
      new_user = dict()
      new_user['username'] = request.POST['username']
      new_user['password'] = request.POST['password1']
      new_user['email'] = request.POST['email']
      if db_users.check_user_exist(new_user['username']):
        print("User exists!")
        messages.error(request, "This username already exists!")
        return render(request, 'registration/register.html', context={'form': form})
      elif db_users.check_email_exist(new_user['email']):
        print("User email exists!")
        messages.error(request, "This email already exists!")
        return render(request, 'registration/register.html', context={'form': form})
      else:
        # 注册成功，数据库中增加用户
        if db_users.insert_one_user(new_user):
          user = auth.authenticate(request=request, username=new_user['username'], password=new_user['password'])
          # pprint.pprint(new_user)
          auth.login(request, user)
          return redirect('/')
        else:
          messages.error(request, "Invalid input for username or password")
          # form.save()
  else:
    form = UserForm()
  return render(request, 'registration/register.html', context={'form': form})


@login_required
def change_password(request):
  user = User.objects.get(username=request.user.username)
  if request.method == 'POST':
    form = PasswordChangeForm(user, request.POST)
    # print(request.POST)
    # 此处使用自定义的验证方式：
    # 1. 旧密码是正确的
    # 2. 两个新密码是一致的
    if request.POST['new_password1'] == request.POST['new_password2']:
      username = request.user.username
      user = auth.authenticate(request=request, username=username, password=request.POST['old_password'])
      if user:
        # if form.is_valid():
        db_users.update_user_password(username=username, new_password=request.POST['new_password1'])
        auth.logout(request)
        return render(request, 'registration/password_change_done.html')
      # else:
        # messages.error(request, _("Your old password was entered incorrectly. Please enter it again."))
    # else:
      # messages.error(request, _("The two password fields didn't match."))
  else:
    form = PasswordChangeForm(user=user)
  return render(request, 'registration/password_change_form.html', context={'form': form})


def password_reset(request):
  if request.method == 'POST':
    form = PasswordResetForm(request.POST)
    to_email = request.POST['email']
    if to_email:
      user_in_db = db_users.check_email_exist(to_email)
      print(user_in_db)
      if user_in_db:
        # 发送邮件
        # pprint.pprint(user_in_db)
        username = user_in_db['username']
        try:
          model_user = User.objects.get(username=username)
        except User.DoesNotExist:
          print("Add user {} to SQLite".format(username))
          model_user = User(username=username)
          model_user.is_active = True
          model_user.save()
        # print(model_user.pk)
        ctx = {'email': to_email,
               'domain': request.META['HTTP_HOST'],
               'site_name': 'FinNews',
               # For Django 2.0 and Python 3.6.3
               # before we do not need to decode into utf-8
               'uid': urlsafe_base64_encode(force_bytes(model_user.pk)).decode('utf-8'),
               'user': model_user,
               'token': default_token_generator.make_token(model_user),
               'protocol': 'http',
               }
        subject_template_name = 'registration/password_reset_subject.html'
        # copied from django/contrib/admin/templates/registration/password_reset_subject.txt to templates directory
        email_template_name = 'registration/password_reset_email.html'
        # copied from django/contrib/admin/templates/registration/password_reset_email.html to templates directory
        subject = loader.render_to_string(subject_template_name, ctx)
        # Email subject *must not* contain newlines
        subject = ''.join(subject.splitlines())
        email = loader.render_to_string(email_template_name, ctx)
        send_mail(subject, email, settings.EMAIL_HOST_USER, [to_email], fail_silently=False)
        return render(request, 'registration/password_reset_done.html', context={'email': to_email})
      else:
        messages.error(request, _("The email is not registered!"))
        # print("No user!")
  else:
    form = PasswordResetForm()
  return render(request, 'registration/password_reset_form.html', context={'form': form})


def password_reset_done(request):
  return redirect('/')

def password_reset_confirm(request, uidb64=None, token=None, *arg, **kwargs):
  assert uidb64 is not None and token is not None
  try:
    uid = urlsafe_base64_decode(uidb64)
    valid_user = User.objects.get(pk=uid)
  except (TypeError, ValueError, OverflowError, User.DoesNotExist):
    valid_user = None
  # print(type(valid_user))
  if request.method == 'POST':
    form = ConfirmPasswordResetForm(valid_user, request.POST)
    if valid_user is not None and default_token_generator.check_token(valid_user, token):
      if form.is_valid():
        new_password = request.POST['new_password2']
        username = valid_user.get_username()
        if db_users.check_user_exist(username=username):
          db_users.update_user_password(username=username, new_password=new_password)
          return render(request, 'registration/password_reset_complete.html')
      else:
        print(form.errors)
        render(request, 'registration/password_reset_confirm.html', context={'form': form})
    else:
      messages.error(request, _('The reset password link is no longer valid.'))
  else:
    form = ConfirmPasswordResetForm(valid_user)
  return render(request, 'registration/password_reset_confirm.html', context={'form': form})


def password_reset_complete(request):
  return redirect('/')


def check_email_exist(request):
  if request.method == 'POST':
    if request.POST['email']:
      ret_val = {}
      if db_users.check_email_exist(request.POST['email']):
        ret_val['exist'] = 1
      else:
        ret_val['exist'] = -1
      return JsonResponse(ret_val)
  return HttpResponseServerError('数据库检查错误！', content_type="text/plain")


def check_username_exist(request):
  if request.method == 'POST':
    if request.POST['username']:
      ret_val = {}
      if db_users.check_user_exist(request.POST['username']):
        ret_val['exist'] = 1
      else:
        ret_val['exist'] = -1
      return JsonResponse(ret_val)
  return HttpResponseServerError('数据库检查错误！', content_type="text/plain")

"""
一些废弃的做法
"""

def reserve(request):
  return HttpResponseServerError('未定义方法', content_type="text/plain")
# @login_required
# def stocks2(request):
#   """
#   添加、删除方式使用 js + ajax
#   """
#   username = request.user.username
#   stocks_db = db_users.get_user_stocks(username)
#   stocks_info_list = []
#   if stocks_db:
#     stocks_info_list = get_stock_info_list(stocks_db)
#     # for stock in stocks_db:
#       # stocks_info_list.append(get_stock_info(stock))
#   return render(request, 'stocks/stocks2.html', context={'stocks': stocks_info_list})

# @login_required
# def stocks2_del(request):
#   username = request.user.username
#   if request.method == 'POST':
#     if request.POST['stock_id'] and username:
#       if db_users.delete_user_stock(username, request.POST['stock_id']) is not None:
#         stock_info = get_stock_info(request.POST['stock_id'])
#         return JsonResponse(stock_info)
#   return HttpResponseServerError('删除错误！', content_type="text/plain")
