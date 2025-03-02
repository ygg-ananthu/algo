from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User

class SignupForm(forms.ModelForm):
    virtual_balance = forms.DecimalField(
        max_digits=10, decimal_places=2, required=True)
    client_id = forms.CharField(max_length=100, required=True)
    client_secret = forms.CharField(max_length=100, required=True)
    password = forms.CharField(widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ['username', 'password', 'virtual_balance', 
                  'client_id', 'client_secret']

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password'])
        if commit:
            user.save()
        return user
