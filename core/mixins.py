"""
Access Control Mixins for Subscription-based Features
"""
import asyncio
from functools import wraps

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.shortcuts import redirect


class SubscriptionRequiredMixin(LoginRequiredMixin):
    """
    Mixin that requires user to have full access (trial or Pro).
    Redirects to upgrade page if access denied.
    """

    subscription_redirect_url = 'core:pricing'
    subscription_message = 'This feature requires a Pro subscription.'

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return super().dispatch(request, *args, **kwargs)

        if not request.user.has_full_access:
            messages.warning(request, self.subscription_message)
            return redirect(self.subscription_redirect_url)

        return super().dispatch(request, *args, **kwargs)


class ModuleAccessMixin(LoginRequiredMixin):
    """
    Mixin for OWASP module access control.
    Checks if user can access the specific module based on module code.
    """

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return super().dispatch(request, *args, **kwargs)

        # Get module code from URL kwargs
        module_code = kwargs.get('code', '')

        if not request.user.can_access_module(module_code):
            messages.warning(
                request,
                f'Module {module_code} requires a Pro subscription. '
                'Upgrade to access all OWASP Top 10 modules.'
            )
            return redirect('core:pricing')

        return super().dispatch(request, *args, **kwargs)


# Decorator versions for function-based views
def subscription_required(view_func):
    """Decorator version of SubscriptionRequiredMixin for function-based views"""

    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('core:login')
        if not request.user.has_full_access:
            messages.warning(request, 'This feature requires a Pro subscription.')
            return redirect('core:pricing')
        return view_func(request, *args, **kwargs)

    return wrapper


def subscription_required_json(view_func):
    """
    Decorator for API views that returns JSON error for non-subscribers.
    Works with both sync and async views.
    """

    @wraps(view_func)
    async def async_wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({'error': 'Authentication required'}, status=401)
        if not request.user.has_full_access:
            return JsonResponse({
                'error': 'subscription_required',
                'upgrade_url': '/pricing/',
                'message': 'This feature requires a Pro subscription.',
                'trial_expired': request.user.trial_expired,
            }, status=403)
        return await view_func(request, *args, **kwargs)

    @wraps(view_func)
    def sync_wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({'error': 'Authentication required'}, status=401)
        if not request.user.has_full_access:
            return JsonResponse({
                'error': 'subscription_required',
                'upgrade_url': '/pricing/',
                'message': 'This feature requires a Pro subscription.',
                'trial_expired': request.user.trial_expired,
            }, status=403)
        return view_func(request, *args, **kwargs)

    # Return appropriate wrapper based on whether view is async
    if asyncio.iscoroutinefunction(view_func):
        return async_wrapper
    return sync_wrapper
