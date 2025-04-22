from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.forms.utils import ErrorList
from django.utils.safestring import mark_safe
from django import  forms
class CustomErrorList(ErrorList):
    def __str__(self):
        if not self:
            return ''
        return mark_safe(''.join([
            f'<div class="alert alert-danger" role="alert"> {e}</div>' for e in self]))

class CustomUserCreationForm(UserCreationForm):

    email = forms.EmailField( max_length= 256)

    def __init__(self, *args, **kwargs):
        super(CustomUserCreationForm, self).__init__ (*args, **kwargs)
        for fieldname in ['email' ,'username', 'password1',
        'password2']:
            self.fields[fieldname].help_text = None
            self.fields[fieldname].widget.attrs.update(
                {'class': 'form-control'}
            )