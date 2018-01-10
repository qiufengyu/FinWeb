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
from app.forms.userForm import UserForm
from app.forms.stockForm import StockForm

from app.forms.passwordResetForm import PasswordResetForm
from app.forms.passwordChangeForm import PasswordChangeForm
from app.forms.confirmPasswordResetForm import ConfirmPasswordResetForm
from app.db.mongo import MongoUser, MongoNews
from app.stocks.get_stock_info import get_stock_info, get_stock_info_list

db_users = MongoUser()
db_news = MongoNews()


def index(request):
  return render(request, 'index.html')


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
        return redirect('/')
      else:
        messages.error(request, _("请输入正确的用户和密码，注意它们它们都是区分大小写的。"))
    else:
      messages.error(request, _("请输入正确的用户和密码，注意它们它们都是区分大小写的。"))
  else:
    form = LoginForm()
  return render(request, 'registration/login.html', context={'form': form})


@login_required
def news(request):
  username = request.user.username
  news_list = db_news.get_latest_news(top=10)
  return render(request, 'news/news.html', context={'news_list': news_list})


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
                                                            'new_stock': new_stock['stock_name']})
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


"""
仅接受 POST 请求
"""
def add_read_news(request):
  pass


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
