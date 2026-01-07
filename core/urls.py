"""
Core URL Configuration
"""
from django.urls import path
from .views import (
    HomeView, AboutView, signup_view, login_view, logout_view,
    FreeWeeklyView, PricingView, OWASPGuideView, SecurityToolkitView, GlossaryView,
    TrialExpiredView
)

app_name = 'core'

urlpatterns = [
    path('', HomeView.as_view(), name='home'),
    path('about/', AboutView.as_view(), name='about'),
    path('signup/', signup_view, name='signup'),
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),

    # New pages
    path('free-weekly/', FreeWeeklyView.as_view(), name='free_weekly'),
    path('pricing/', PricingView.as_view(), name='pricing'),
    path('trial-expired/', TrialExpiredView.as_view(), name='trial_expired'),

    # Resources
    path('resources/owasp-guide/', OWASPGuideView.as_view(), name='owasp_guide'),
    path('resources/security-toolkit/', SecurityToolkitView.as_view(), name='security_toolkit'),
    path('resources/glossary/', GlossaryView.as_view(), name='glossary'),
]
