from django import forms
from django.contrib.auth import authenticate
from .models import User
from django.contrib.auth.forms import UserCreationForm 
from django.core.exceptions import ValidationError

class SignUpForm(UserCreationForm):

    class Meta:
        model = User
        fields = ("first_name", "last_name", "email", "password1", "password2")

    def clean_email(self):
        email = self.cleaned_data.get("email")
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("Email already registered.")
        return email

    def save(self, commit=True):
        print("self.cleaned_data", self.cleaned_data)
        print("self.cleaned_data['password1']", self.cleaned_data['password1'])
        
        user = super().save(commit=False)
        user.username = self.cleaned_data["email"]
        user.set_password(self.cleaned_data["password1"])
        print("user", user)
        print("user.password", user.password)
        if commit:
            user.save()
        return user

# class LoginForm(forms.Form):
#     email = forms.EmailField()
#     print("LoginForm email", email)
#     password = forms.CharField(widget=forms.PasswordInput)
#     print("LoginForm password", password)
#     def clean(self):
#         email = self.cleaned_data["email"]
#         print("LoginForm clean email", email)
#         password = self.cleaned_data["password"]
#         print("LoginForm clean password", password)
#         print("LoginForm clean self.cleaned_data", self.cleaned_data)
#         return self.cleaned_data

