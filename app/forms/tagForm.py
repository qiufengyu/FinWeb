from django import forms
from django.utils.translation import ugettext, ugettext_lazy as _


class TagForm(forms.Form):
  """
  Stock form
  """
  tag_name = forms.CharField(
    required=True,
    label=_('Tag'),
    error_messages={'required': 'Please input tag name'},
    strip=True,
    widget=forms.TextInput(attrs={"style": "margin: 0.45rem auto", "class":"form-control",
                                  "placeholder": "请输入想要添加的标签"}),
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
      super(TagForm, self).clean()
      # return self.cleaned_data
