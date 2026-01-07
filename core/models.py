"""
Core Models - User, Subscription, Settings
"""
from datetime import timedelta

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone


class User(AbstractUser):
    """Custom User Model for SMBShield"""

    # Trial and access constants
    TRIAL_DURATION_DAYS = 30
    FREE_OWASP_MODULES = ['A01', 'A02']  # First 2 modules always free

    class SubscriptionTier(models.TextChoices):
        FREE = 'free', 'Free Trial'
        PRO = 'pro', 'Professional (€99/month)'
        ENTERPRISE = 'enterprise', 'Enterprise'
    
    # Profile
    company_name = models.CharField(max_length=200, blank=True)
    job_title = models.CharField(max_length=100, blank=True)
    company_size = models.CharField(max_length=50, blank=True)  # 1-10, 11-50, 51-200, 200+
    industry = models.CharField(max_length=100, blank=True)
    
    # Subscription
    subscription_tier = models.CharField(
        max_length=20,
        choices=SubscriptionTier.choices,
        default=SubscriptionTier.FREE
    )
    stripe_customer_id = models.CharField(max_length=100, blank=True)
    subscription_active = models.BooleanField(default=False)
    subscription_expires = models.DateTimeField(null=True, blank=True)
    
    # Learning Progress
    current_owasp_level = models.IntegerField(default=1)  # 1-10 modules
    total_lessons_completed = models.IntegerField(default=0)
    total_quizzes_passed = models.IntegerField(default=0)
    knowledge_score = models.FloatField(default=0.0)  # 0-100
    
    # Engagement
    last_lesson_at = models.DateTimeField(null=True, blank=True)
    last_quiz_at = models.DateTimeField(null=True, blank=True)
    streak_days = models.IntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'users'
    
    def __str__(self):
        return f"{self.email} ({self.company_name or 'No Company'})"
    
    @property
    def is_pro(self):
        return self.subscription_tier in [self.SubscriptionTier.PRO, self.SubscriptionTier.ENTERPRISE]
    
    @property
    def display_name(self):
        return self.get_full_name() or self.username

    # Trial tracking properties
    @property
    def trial_ends_at(self):
        """Trial ends 30 days after signup, or at subscription_expires if set"""
        if self.is_pro:
            return None  # Pro users don't have trial
        if self.subscription_expires:
            return self.subscription_expires
        return self.created_at + timedelta(days=self.TRIAL_DURATION_DAYS)

    @property
    def is_in_trial(self):
        """True if user is in active trial period (not a paid subscriber)"""
        if self.is_pro or self.subscription_active:
            return False
        return timezone.now() < self.trial_ends_at

    @property
    def trial_days_remaining(self):
        """Days left in trial, 0 if expired or is pro"""
        if not self.is_in_trial:
            return 0
        delta = self.trial_ends_at - timezone.now()
        return max(0, delta.days)

    @property
    def trial_expired(self):
        """True if trial has expired and user is not a paying subscriber"""
        if self.is_pro or self.subscription_active:
            return False
        return timezone.now() >= self.trial_ends_at

    @property
    def has_full_access(self):
        """True if user has access to all Pro features (trial or paid)"""
        return self.is_pro or self.is_in_trial

    def can_access_module(self, module_code):
        """Check if user can access a specific OWASP module"""
        if self.has_full_access:
            return True
        # Free tier: only first 2 modules (check if code starts with A01 or A02)
        return any(module_code.startswith(prefix) for prefix in self.FREE_OWASP_MODULES)


class SiteSettings(models.Model):
    """Global site settings (singleton)"""
    site_name = models.CharField(max_length=100, default='SMBShield')
    tagline = models.CharField(max_length=200, default='Cybersecurity Education for European SMBs')
    contact_email = models.EmailField(default='hello@smbshield.eu')
    
    # Feature flags
    news_agent_enabled = models.BooleanField(default=True)
    professor_shield_enabled = models.BooleanField(default=True)
    assessment_bot_enabled = models.BooleanField(default=True)
    
    # Alert banner
    show_alert_banner = models.BooleanField(default=False)
    alert_banner_text = models.TextField(blank=True)
    alert_banner_type = models.CharField(max_length=20, default='info')  # info, warning, danger
    
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Site Settings'
        verbose_name_plural = 'Site Settings'
    
    def save(self, *args, **kwargs):
        self.pk = 1  # Singleton pattern
        super().save(*args, **kwargs)
    
    @classmethod
    def get_settings(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj
