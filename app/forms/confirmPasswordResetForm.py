from django import forms
from django.conf import settings
from django.contrib.auth import password_validation
from django.utils.translation import ugettext, ugettext_lazy as _

# Using SetPasswordForm is better!
class ConfirmPasswordResetForm(forms.Form):
  """
    A form that lets a user change set their password without entering the old
    password
    Reference: https://github.com/django/django/blob/master/django/contrib/auth/forms.py
  """
  error_messages = {
    'password_mismatch': _("The two password fields didn't match."),
  }
  new_password1 = forms.CharField(
    label=_("New password"),
    widget=forms.PasswordInput(attrs={"class": "form-control"}),
    help_text='<ul class="text-small">'
              '<li>你的密码必须包含至少 8 个字符，且不能是纯数字。</li>'
              '<li>你的密码不能与其他个人信息太相似，也不能是简单常见密码。</li>'
              '</ul>'
    # widget=forms.PasswordInput,
    # strip=False,
    # help_text=password_validation.password_validators_help_text_html(),
  )
  new_password2 = forms.CharField(
    label=_("New password confirmation"),
    widget=forms.PasswordInput(attrs={"class": "form-control"}),
    help_text="为了校验，请输入与上面相同的密码。",
  )

  def __init__(self, user, *args, **kwargs):
    self.user = user
    super().__init__(*args, **kwargs)

  def clean_new_password2(self):
    print("clean pw2!")
    password1 = self.cleaned_data.get('new_password1')
    password2 = self.cleaned_data.get('new_password2')
    if password1 and password2:
      if password1 != password2:
        raise forms.ValidationError(
          self.error_messages['password_mismatch'],
          code='password_mismatch',
        )
    password_validation.validate_password(password2, self.user)
    return password2


