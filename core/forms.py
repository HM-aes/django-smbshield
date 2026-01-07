"""
Core Forms - User Registration and Authentication
"""
from datetime import timedelta

from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.utils import timezone

from .models import User

# Shadcn-style input classes
INPUT_CLASSES = 'w-full bg-zinc-950 border border-zinc-800 rounded-lg px-4 py-3 text-white placeholder-zinc-600 focus:outline-none focus:border-zinc-600 transition-colors'
SELECT_CLASSES = 'w-full bg-zinc-950 border border-zinc-800 rounded-lg px-4 py-3 text-white focus:outline-none focus:border-zinc-600 transition-colors'


class SignUpForm(UserCreationForm):
    """User registration form"""
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': INPUT_CLASSES,
            'placeholder': 'work@company.com'
        })
    )
    company_name = forms.CharField(
        max_length=200,
        required=False,
        widget=forms.TextInput(attrs={
            'class': INPUT_CLASSES,
            'placeholder': 'Your Company Ltd'
        })
    )
    job_title = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': INPUT_CLASSES,
            'placeholder': 'IT Manager'
        })
    )
    company_size = forms.ChoiceField(
        required=False,
        choices=[
            ('', 'Select company size'),
            ('1-10', '1-10 employees'),
            ('11-50', '11-50 employees'),
            ('51-200', '51-200 employees'),
            ('200+', '200+ employees'),
        ],
        widget=forms.Select(attrs={
            'class': SELECT_CLASSES
        })
    )
    
    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2', 'company_name', 'job_title', 'company_size')
        widgets = {
            'username': forms.TextInput(attrs={
                'class': INPUT_CLASSES,
                'placeholder': 'username'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['password1'].widget.attrs.update({
            'class': INPUT_CLASSES,
            'placeholder': '••••••••'
        })
        self.fields['password2'].widget.attrs.update({
            'class': INPUT_CLASSES,
            'placeholder': '••••••••'
        })
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.company_name = self.cleaned_data.get('company_name', '')
        user.job_title = self.cleaned_data.get('job_title', '')
        user.company_size = self.cleaned_data.get('company_size', '')

        # Set 30-day trial period for new users
        user.subscription_tier = User.SubscriptionTier.FREE
        user.subscription_expires = timezone.now() + timedelta(days=User.TRIAL_DURATION_DAYS)

        if commit:
            user.save()
        return user
