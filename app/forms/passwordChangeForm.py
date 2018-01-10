from django import forms
from django.conf import settings
from django.contrib.auth import password_validation
from django.utils.translation import ugettext, ugettext_lazy as _

from .confirmPasswordResetForm import ConfirmPasswordResetForm
from ..db.mongo import MongoUser

mongo_user = MongoUser()

class PasswordChangeForm(ConfirmPasswordResetForm):
    """
    A form that lets a user change their password by entering their old
    password.
    """
    error_messages = dict(ConfirmPasswordResetForm.error_messages, **{
        'password_incorrect': _("Your old password was entered incorrectly. Please enter it again."),
    })
    old_password = forms.CharField(
        label=_("Old password"),
        strip=False,
        widget=forms.PasswordInput(attrs={'autofocus': True, "class": "form-control"}),
    )
    new_password1 = forms.CharField(label=_("Password"),
                                widget=forms.PasswordInput(attrs={"class": "form-control"}),
                                help_text='<ul class="text-small">'
                                          '<li>你的密码必须包含至少 8 个字符，且不能是纯数字。</li>'
                                          '<li>你的密码不能与其他个人信息太相似，也不能是简单常见密码。</li>'
                                          '</ul>')

    new_password2 = forms.CharField(label=_("Password confirmation"),
                                widget=forms.PasswordInput(attrs={"class": "form-control"}),
                                help_text="为了校验，请输入与上面相同的密码。")


    field_order = ['old_password', 'new_password1', 'new_password2']

    def clean_old_password(self):
        """
        Validate that the old_password field is correct.
        """
        old_password = self.cleaned_data["old_password"]
        if not mongo_user.check_user_password(self.user.username, old_password):
            raise forms.ValidationError(
                self.error_messages['password_incorrect'],
                code='password_incorrect',
            )
            return old_password
