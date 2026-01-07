"""Education Views - Professor Shield Learning Area"""
import json
import os
from datetime import datetime

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.shortcuts import redirect
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import DetailView, TemplateView

from core.mixins import SubscriptionRequiredMixin

from .models import ChatHistory, Lesson, OWASPModule, UserProgress


class LearningHomeView(LoginRequiredMixin, TemplateView):
    template_name = 'pages/education/home.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['modules'] = OWASPModule.objects.filter(is_active=True)
        return context


class ModuleDetailView(LoginRequiredMixin, DetailView):
    model = OWASPModule
    template_name = 'pages/education/module.html'
    context_object_name = 'module'
    slug_field = 'code'
    slug_url_kwarg = 'code'

    def dispatch(self, request, *args, **kwargs):
        # Check module access before rendering
        self.object = self.get_object()
        user = request.user

        if user.is_authenticated and not user.can_access_module(self.object.code):
            messages.warning(
                request,
                f'Module {self.object.code} requires a Pro subscription. '
                'You have free access to modules A01 and A02.'
            )
            return redirect('core:pricing')

        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        # Check if user can access this module
        context['can_access'] = user.can_access_module(self.object.code)

        # Get lessons with progress
        lessons = self.object.lessons.filter(is_active=True)
        lessons_with_progress = []

        for lesson in lessons:
            progress = UserProgress.objects.filter(
                user=user, lesson=lesson
            ).first()

            lessons_with_progress.append({
                'lesson': lesson,
                'progress': progress
            })

        context['lessons_with_progress'] = lessons_with_progress
        return context


class LessonView(LoginRequiredMixin, DetailView):
    model = Lesson
    template_name = 'pages/education/lesson.html'
    context_object_name = 'lesson'

    def dispatch(self, request, *args, **kwargs):
        # Check module access before rendering lesson
        self.object = self.get_object()
        user = request.user
        module_code = self.object.module.code

        if user.is_authenticated and not user.can_access_module(module_code):
            messages.warning(
                request,
                f'This lesson requires a Pro subscription. '
                'Upgrade to access all OWASP modules.'
            )
            return redirect('core:pricing')

        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        # Get or create progress
        progress, created = UserProgress.objects.get_or_create(
            user=user,
            lesson=self.object,
            defaults={'status': 'in_progress'}
        )

        if created or progress.status == 'not_started':
            progress.status = 'in_progress'
            from django.utils import timezone
            progress.started_at = timezone.now()
            progress.save()

        context['progress'] = progress

        # Previous chat history for this lesson
        context['chat_history'] = ChatHistory.objects.filter(
            user=user,
            lesson=self.object
        ).order_by('created_at')[:10]

        return context


class ProfessorChatPageView(LoginRequiredMixin, TemplateView):
    """Professor Shield Chat Page - renders the chat UI"""
    template_name = 'pages/dashboard/chat.html'

    def dispatch(self, request, *args, **kwargs):
        """Check subscription before rendering"""
        if request.user.is_authenticated and not request.user.has_full_access:
            messages.warning(
                request,
                'Professor Shield AI requires a Pro subscription. '
                'Upgrade to chat with your AI security tutor.'
            )
            return redirect('core:pricing')
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Get recent chat history for this user
        context['chat_history'] = ChatHistory.objects.filter(
            user=self.request.user,
            lesson__isnull=True  # General chat, not lesson-specific
        ).order_by('-created_at')[:20]
        
        # OWASP modules for quick topic selection
        context['modules'] = OWASPModule.objects.filter(is_active=True)
        return context


@method_decorator(csrf_exempt, name='dispatch')
class ProfessorChatAPIView(LoginRequiredMixin, View):
    """Professor Shield Chat API - handles chat messages (async)"""

    async def post(self, request, *args, **kwargs):
        """Handle chat message - API endpoint for HTMX"""
        # Build user context
        user = await request.auser()
        
        # Check subscription access (Pro feature)
        if not user.has_full_access:
            return JsonResponse({
                'error': 'subscription_required',
                'message': 'Professor Shield AI requires a Pro subscription.',
                'upgrade_url': '/pricing/',
                'trial_expired': user.trial_expired,
            }, status=403)

        try:
            data = json.loads(request.body)
            message = data.get('message', '')
            lesson_id = data.get('lesson_id')

            if not message:
                return JsonResponse({'error': 'Message required'}, status=400)
            
            # Import agent
            from agents import ask_professor, UserContext
            
            user_context = UserContext(
                user_id=user.id,
                username=user.username,
                company_name=user.company_name or "",
                industry=user.industry or "",
                current_level=getattr(user, 'current_owasp_level', 1) or 1,
                knowledge_score=getattr(user, 'knowledge_score', 0.0) or 0.0,
            )
            
            # Get response from Professor Shield
            try:
                response = await ask_professor(message, user_context)
            except Exception as e:
                # Log the error (in a real app, use logging)
                print(f"AI Agent Error: {str(e)}")
                
                # Check for common error types
                error_msg = str(e).lower()
                if "quota" in error_msg or "429" in error_msg:
                    friendly_error = "Professor Shield is currently resting due to high demand (API quota exceeded). Please try again in a moment or switch to another provider."
                elif "balance" in error_msg or "402" in error_msg:
                    friendly_error = "The AI service credits are currently exhausted. Please check your API billing or balance."
                elif "api_key" in error_msg or "auth" in error_msg:
                    friendly_error = "There is an issue with the AI authentication. Please check the API configuration."
                else:
                    friendly_error = "Professor Shield encountered an unexpected issue. Our team has been notified. Please try again later."
                
                return JsonResponse({
                    'error': 'ai_error',
                    'message': friendly_error,
                    'technical_details': str(e) if user.is_staff else None
                }, status=503)
            
            # Save chat history
            lesson = None
            if lesson_id:
                lesson = await Lesson.objects.filter(id=lesson_id).afirst()
            
            await ChatHistory.objects.acreate(
                user=user,
                lesson=lesson,
                user_message=message,
                assistant_response=response.answer,
                related_owasp=response.related_owasp or '',
                confidence=response.confidence
            )
            
            return JsonResponse({
                'answer': response.answer,
                'related_owasp': response.related_owasp,
                'follow_up': response.follow_up_suggestion,
                'code_example': response.code_example,
            })
            
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)


# Keep legacy name for backward compatibility with URL
ProfessorChatView = ProfessorChatPageView
