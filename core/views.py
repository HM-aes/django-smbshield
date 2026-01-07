"""
Core Views - Homepage, About, Auth
"""
from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.views.generic import TemplateView
from django.contrib import messages

from news.models import NewsArticle, DailyBriefing
from .models import SiteSettings


class HomeView(TemplateView):
    template_name = 'pages/home.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get latest news for homepage
        context['latest_news'] = NewsArticle.objects.order_by('-published_at')[:3]

        # Get breaking news if any
        context['breaking_news'] = NewsArticle.objects.filter(
            is_breaking=True
        ).first()
        
        # Get site settings
        settings = SiteSettings.get_settings()
        if settings.show_alert_banner:
            context['alert_banner'] = {
                'text': settings.alert_banner_text,
                'type': settings.alert_banner_type
            }
        
        return context


class AboutView(TemplateView):
    template_name = 'pages/about.html'


class FreeWeeklyView(TemplateView):
    template_name = 'pages/free_weekly.html'


class PricingView(TemplateView):
    template_name = 'pages/pricing.html'


class OWASPGuideView(TemplateView):
    template_name = 'pages/owasp_guide.html'


class SecurityToolkitView(TemplateView):
    template_name = 'pages/security_toolkit.html'


class GlossaryView(TemplateView):
    template_name = 'pages/glossary.html'


class TrialExpiredView(TemplateView):
    template_name = 'pages/trial_expired.html'


def signup_view(request):
    if request.method == 'POST':
        # Handle signup
        from .forms import SignUpForm
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Welcome to SMBShield! Your free trial has started.')
            return redirect('dashboard:home')
    else:
        from .forms import SignUpForm
        form = SignUpForm()
    
    return render(request, 'pages/signup.html', {'form': form})


def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            next_url = request.GET.get('next', 'dashboard:home')
            return redirect(next_url)
        else:
            messages.error(request, 'Invalid credentials')
    
    return render(request, 'pages/login.html')


def logout_view(request):
    logout(request)
    messages.info(request, 'You have been logged out.')
    return redirect('core:home')
