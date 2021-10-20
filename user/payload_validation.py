from django import forms


class LoginPayload(forms.Form):
    email = forms.CharField()
    password = forms.CharField()

class RegisterPayload(forms.Form):
    email = forms.CharField()
    password = forms.CharField()
    username = forms.CharField()
    mobile = forms.CharField()
