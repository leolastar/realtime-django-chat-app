from django import forms
from django.contrib.auth import authenticate
from .models import User
from django.contrib.auth.forms import UserCreationForm 
from django.core.exceptions import ValidationError
import logging

logger = logging.getLogger(__name__)
    
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
        
        user = super().save(commit=False)
        user.username = self.cleaned_data["email"]
        user.set_password(self.cleaned_data["password1"])
        if commit:
            user.save()
            logger.info("SignUpForm user saved", user)
        return user


