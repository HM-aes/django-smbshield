"""Dashboard URLs"""
from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    path('', views.DashboardHomeView.as_view(), name='home'),
    path('progress/', views.ProgressView.as_view(), name='progress'),
    path('settings/', views.SettingsView.as_view(), name='settings'),
]
