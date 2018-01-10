from django import forms
from django.utils.translation import ugettext, ugettext_lazy as _


class PasswordResetForm(forms.Form):
  error_messages = {
    'invalid_email': _("The email is invalid."),
  }

  email = forms.EmailField(label=_("Email"), required=True, max_length=254,
                           widget=forms.EmailInput(attrs={"placeholder": "name@example.com", "class": "form-control"}))

  def clean_email(self):
    email = self.cleaned_data.get("email")
    if '@' not in email:
      raise forms.ValidationError(
        self.error_messages['invalid_email'],
        code='invalid_email',
      )
    return email
