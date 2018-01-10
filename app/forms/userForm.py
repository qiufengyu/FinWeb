from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from django.utils.translation import ugettext, ugettext_lazy as _


class UserForm(UserCreationForm):
  """
  A form that creates a user, with no privileges, from the given username and
  password.
  """
  error_messages = {
    'password_mismatch': _("The two password fields didn't match."),
    'invalid_email': _("The email is invalid."),
  }

  username = forms.CharField(label=_("username"), required=True,
                             error_messages={'required': 'Please input username'},
                             widget=forms.TextInput(attrs={"placeholder": "username", "class": "form-control"}),
                             help_text=_("Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only.")
                             )

  email = forms.EmailField(label=_("email address"), required=True,
                           widget=forms.EmailInput(attrs={"placeholder": "name@example.com", "class": "form-control"}),
                           help_text=_("必填。是找回密码的唯一依据。"))

  password1 = forms.CharField(label=_("Password"),
                              widget=forms.PasswordInput(attrs={"class": "form-control"}),
                              help_text='<ul class="text-small">'
                                        '<li>你的密码必须包含至少 8 个字符，且不能是纯数字。</li>'
                                        '<li>你的密码不能与其他个人信息太相似，也不能是简单常见密码。</li>'                                                                 
                                        '</ul>')

  password2 = forms.CharField(label=_("Password confirmation"),
                              widget=forms.PasswordInput(attrs={"class": "form-control"}),
                              help_text="为了校验，请输入与上面相同的密码。")

  field_order = ['username', 'email', 'password1', 'password2']
  # def clean(self):
  # 	# print("clean !")
  # 	username = self.cleaned_data.get('username')
  # 	client = pymongo.MongoClient(settings.MONGO_HOST, settings.MONGO_PORT)
  # 	db = client[settings.MONGO_DBNAME]
  # 	db_users = db.users
  # 	if db_users.find_one({'user_name': username}):
  # 		self.add_error('username', self.error_messages['duplicate_user'])
  # 		return None
  # 	return self.cleaned_data


  def clean_password2(self):
    # print('clean password')
    password1 = self.cleaned_data.get("password1")
    password2 = self.cleaned_data.get("password2")
    if password1 and password2 and password1 != password2:
      raise forms.ValidationError(
        self.error_messages['password_mismatch'],
        code='password_mismatch',
      )
    return password2

  def clean_email(self):
    email = self.cleaned_data.get("email")
    if '@' not in email:
      raise forms.ValidationError(
        self.error_messages['invalid_email'],
        code='invalid_email',
      )
    return email

  def save(self, commit=True):
    user = super(UserForm, self).save(commit=False)
    user.set_password(self.cleaned_data["password1"])
    if commit:
      user.save()
    return user
