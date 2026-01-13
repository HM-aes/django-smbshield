"""
Custom Allauth Adapters for SMBShield
Handles trial setup for OAuth signups and email configuration
"""
from allauth.account.adapter import DefaultAccountAdapter
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter


class CustomAccountAdapter(DefaultAccountAdapter):
    """
    Custom adapter for standard account operations.
    Customizes email verification and redirect behavior.
    """
    
    def get_login_redirect_url(self, request):
        """Redirect to dashboard after login"""
        return '/dashboard/'
    
    def get_signup_redirect_url(self, request):
        """Redirect to dashboard after signup"""
        return '/dashboard/'


class CustomSocialAccountAdapter(DefaultSocialAccountAdapter):
    """
    Custom adapter for social/OAuth account operations.
    Ensures trial is properly set up for OAuth signups.
    """
    
    def pre_social_login(self, request, sociallogin):
        """
        Called before social login completes.
        Can be used to associate existing accounts.
        """
        pass
    
    def save_user(self, request, sociallogin, form=None):
        """
        Save user from OAuth signup and initialize trial.
        """
        user = super().save_user(request, sociallogin, form)
        
        # Ensure user starts with free trial tier
        # (This is already the default in our User model, but explicit is good)
        from core.models import User
        if user.subscription_tier == User.SubscriptionTier.FREE:
            # User is on free trial - trial_ends_at is calculated automatically
            pass
        
        return user
    
    def get_login_redirect_url(self, request):
        """Redirect to dashboard after OAuth login"""
        return '/dashboard/'
