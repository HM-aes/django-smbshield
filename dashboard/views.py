"""Dashboard Views - Members only area"""
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.shortcuts import redirect

from education.models import UserProgress, OWASPModule
from assessment.models import QuizAttempt, KnowledgeGap
from news.models import NewsArticle


class DashboardHomeView(LoginRequiredMixin, TemplateView):
    template_name = 'pages/dashboard/home.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        # Progress stats
        context['total_lessons'] = UserProgress.objects.filter(
            user=user, status='completed'
        ).count()
        
        context['total_quizzes'] = QuizAttempt.objects.filter(
            user=user, status='completed'
        ).count()
        
        context['knowledge_score'] = user.knowledge_score
        context['streak_days'] = user.streak_days
        
        # OWASP Modules progress
        context['modules'] = OWASPModule.objects.all()
        
        # Recent quiz results
        context['recent_quizzes'] = QuizAttempt.objects.filter(
            user=user
        ).order_by('-completed_at')[:5]
        
        # Knowledge gaps
        context['knowledge_gaps'] = KnowledgeGap.objects.filter(
            user=user, addressed=False
        )[:3]
        
        # Latest threat intel
        context['latest_threats'] = NewsArticle.objects.filter(
            urgency__in=['high', 'critical']
        ).order_by('-published_at')[:5]
        
        # Latest news for news cards
        context['latest_news'] = NewsArticle.objects.order_by('-published_at')[:4]
        
        return context


class ProgressView(LoginRequiredMixin, TemplateView):
    template_name = 'pages/dashboard/progress.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        # Detailed progress by module
        modules = OWASPModule.objects.all()
        progress_data = []
        
        for module in modules:
            total_lessons = module.lessons.count()
            completed = UserProgress.objects.filter(
                user=user,
                lesson__module=module,
                status='completed'
            ).count()
            
            progress_data.append({
                'module': module,
                'total': total_lessons,
                'completed': completed,
                'percentage': (completed / total_lessons * 100) if total_lessons > 0 else 0
            })
        
        context['progress_data'] = progress_data
        
        # Quiz performance over time
        context['quiz_history'] = QuizAttempt.objects.filter(
            user=user
        ).order_by('-started_at')[:20]
        
        return context


class SettingsView(LoginRequiredMixin, TemplateView):
    template_name = 'pages/dashboard/settings.html'

    def post(self, request, *args, **kwargs):
        user = request.user
        updated = False

        # Profile fields
        if 'email' in request.POST:
            email = request.POST.get('email', '').strip()
            first_name = request.POST.get('first_name', '').strip()
            last_name = request.POST.get('last_name', '').strip()

            if email and email != user.email:
                user.email = email
                updated = True
            if first_name != user.first_name:
                user.first_name = first_name
                updated = True
            if last_name != user.last_name:
                user.last_name = last_name
                updated = True

        # Company fields
        if 'company_name' in request.POST:
            company_name = request.POST.get('company_name', '').strip()
            job_title = request.POST.get('job_title', '').strip()
            company_size = request.POST.get('company_size', '').strip()
            industry = request.POST.get('industry', '').strip()

            if company_name != user.company_name:
                user.company_name = company_name
                updated = True
            if job_title != user.job_title:
                user.job_title = job_title
                updated = True
            if company_size != user.company_size:
                user.company_size = company_size
                updated = True
            if industry != user.industry:
                user.industry = industry
                updated = True

        if updated:
            user.save()
            messages.success(request, 'Settings saved successfully.')
        else:
            messages.info(request, 'No changes detected.')

        return redirect('dashboard:settings')
