from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

'''
class LoginForm(forms.Form):
    username = forms.CharField(max_length=100)
    password = forms.CharField(widget=forms.PasswordInput())

'''


class LoginForm(forms.Form):
    username = forms.CharField(max_length=100)
    password = forms.CharField(widget=forms.PasswordInput())

    def clean_username(self):
        username = self.cleaned_data.get("username")
        dbuser = Dreamreal.objects.filter(name=username)

        if not dbuser:
            return "db doesn't has %s" % username
        return username




# class DreamrealForm(forms.Form):
#     website = forms.CharField(max_length=100)
#     username = forms.CharField(max_length=100)
#     phonenumber = forms.CharField(max_length=50)
#     mail = forms.CharField(max_length=100)


# class ProfileForm(forms.Form):
#     username = forms.CharField(max_length=100)
#     picture = forms.ImageField()


