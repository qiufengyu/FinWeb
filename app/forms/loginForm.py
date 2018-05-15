from django import forms
from django.utils.translation import ugettext, ugettext_lazy as _


class LoginForm(forms.Form):
  """
  Login form
  """
  username = forms.CharField(
    required=True,
    label=_('用户名 / 电子邮件'),
    error_messages={'required': 'Please input username'},
    widget=forms.TextInput(attrs={"placeholder": _("username or email address"), "class": "form-control"}),
  )
  password = forms.CharField(
    required=True,
    label=_('password'),
    error_messages={'required': 'Please input password'},
    widget=forms.PasswordInput(attrs={"class": "form-control"}),
  )

  error_messages = {
    'invalid_login': _(
      "Please enter a correct username and password. Note that both "
      "fields may be case-sensitive."
    ),
    'inactive': _("This account is inactive."),
  }

  """
  To test some errors near the widgets
    def clean_username(self):
    username = self.cleaned_data.get('username')
    if username == 'test1':
      raise forms.ValidationError(
        "Invalid User",
        code='invalid_user',
      )

  def clean_password(self):
    pwd = self.cleaned_data.get('password')
    if pwd == '123':
      raise forms.ValidationError(
        "Invalid Pwd",
        code='invalid_pwd',
      )
  """

  def clean(self):
    if not self.is_valid():
      raise forms.ValidationError(self.error_messages['invalid_login'],
            code='invalid_login')
    else:
      super(LoginForm, self).clean()
      # return self.cleaned_data
