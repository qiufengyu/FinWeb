from django.contrib.auth.models import User
from django.contrib.auth.hashers import make_password, check_password

from app.db.mongo import MongoUser, MongoNews


class MongoBackend(object):
  """
      Authenticate against the settings ADMIN_LOGIN and ADMIN_PASSWORD.

      Use the login name and a hash of the password. For example:

      ADMIN_LOGIN = 'admin'
      ADMIN_PASSWORD = 'pbkdf2_sha256$30000$Vo0VlMnkR4Bk$qEvtdyZRWTcOsCnI/oQ7fVOu1XAURIZYoOZ3iq8Dr4M='
  """
  db_user = MongoUser()

  def authenticate(self, request, username=None, password=None):
    # print(password)
    print("Authenticating username ", username)
    if username and password:
      # 用户名登录
      db_password = self.db_user.get_user_password(username)
      if db_password and check_password(password, db_password):
        # print(db_password, salt_password)
        # 刚注册的或是 sqlite 中未从 mongodb 更新的
        try:
          valid_user = User.objects.get(username=username)
        except User.DoesNotExist:
          print("Add user {} to SQLite".format(username))
          valid_user = User(username=username)
          valid_user.is_active = True
          valid_user.save()
        return valid_user
      # 邮箱登录
      db_password = self.db_user.get_user_password_by_email(username)
      if db_password and check_password(password, db_password):
        # print(db_password, salt_password)
        # 刚注册的或是 sqlite 中未从 mongodb 更新的
        try:
          username_by_email = self.db_user.check_email_exist(username)
          valid_user = User.objects.get(username=username_by_email['username'])
        except User.DoesNotExist:
          print("Add user {} to SQLite".format(username))
          valid_user = User(username=username)
          valid_user.is_active = True
          valid_user.save()
        return valid_user
    try:
      admin_user = User.objects.get(username=username)
      if admin_user.password:
        if check_password(password, encoded=admin_user.password):
          # print("OK")
          return admin_user
        else:
          return None
    except User.DoesNotExist:
      return None

  def get_user(self, user_id):
    try:
      return User.objects.get(pk=user_id)
    except User.DoesNotExist:
      return None
