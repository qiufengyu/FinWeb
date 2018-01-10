from django import forms
from django.utils.translation import ugettext, ugettext_lazy as _


class StockForm(forms.Form):
  """
  Stock form
  """
  stock_id = forms.CharField(
    required=True,
    label=_('Stock'),
    error_messages={'required': 'Please input stock id or stock name'},
    strip=True,
    widget=forms.TextInput(attrs={"style": "margin: 0.45rem auto", "class":"form-control",
                                  "placeholder": "请输入股票代码（sz/sh）或股票名称"}),
  )

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
      raise forms.ValidationError("Invalid input!", code='invalid')
    else:
      super(StockForm, self).clean()
      # return self.cleaned_data
