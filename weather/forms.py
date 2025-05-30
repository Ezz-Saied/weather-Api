# weather/forms.py (update existing file)
from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

class CityForm(forms.Form):
    name = forms.CharField(
        label='',
        max_length=50,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter city name...'
        })
    )

class UserRegisterForm(UserCreationForm):
    email = forms.EmailField()
    
    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']
