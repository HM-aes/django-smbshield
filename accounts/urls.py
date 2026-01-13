"""
Accounts URL Configuration
Allauth URL patterns are included separately in main urls.py
"""
from django.urls import path

app_name = 'accounts'

urlpatterns = [
    # Custom account views can be added here
    # OAuth URLs are handled by allauth.urls in main urls.py
]
