"""
Agent API Views - Async endpoints for AI interactions
"""
from django.http import JsonResponse
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.contrib.auth.mixins import LoginRequiredMixin
import json
import asyncio

from . import (
    UserContext,
    OWASPCategory,
    DifficultyLevel,
    ask_professor,
    generate_lesson,
    generate_quiz,
    evaluate_quiz_answer,
    analyze_article,
    generate_daily_briefing,
)


def get_user_context(user) -> UserContext:
    """Build UserContext from Django user"""
    return UserContext(
        user_id=user.id,
        username=user.username,
        company_name=user.company_name,
        industry=user.industry,
        current_level=user.current_owasp_level,
        knowledge_score=user.knowledge_score,
        completed_topics=[]  # Would load from progress tracking
    )


@method_decorator(csrf_exempt, name='dispatch')
class ProfessorShieldView(LoginRequiredMixin, View):
    """Professor Shield Q&A endpoint - Pro feature"""

    async def post(self, request):
        # Check subscription access (Pro feature)
        if not request.user.has_full_access:
            return JsonResponse({
                'error': 'subscription_required',
                'message': 'Professor Shield AI requires a Pro subscription.',
                'upgrade_url': '/pricing/',
                'trial_expired': request.user.trial_expired,
            }, status=403)

        try:
            data = json.loads(request.body)
            question = data.get('question', '')

            if not question:
                return JsonResponse({'error': 'Question required'}, status=400)

            user_context = get_user_context(request.user)
            response = await ask_professor(question, user_context)

            return JsonResponse({
                'answer': response.answer,
                'confidence': response.confidence,
                'related_owasp': response.related_owasp.value if response.related_owasp else None,
                'follow_up': response.follow_up_suggestion,
                'code_example': response.code_example,
            })

        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)


@method_decorator(csrf_exempt, name='dispatch')
class LessonGeneratorView(LoginRequiredMixin, View):
    """Generate lesson content - Pro feature"""

    async def post(self, request):
        # Check subscription access (Pro feature)
        if not request.user.has_full_access:
            return JsonResponse({
                'error': 'subscription_required',
                'message': 'AI Lesson Generator requires a Pro subscription.',
                'upgrade_url': '/pricing/',
                'trial_expired': request.user.trial_expired,
            }, status=403)

        try:
            data = json.loads(request.body)
            category = data.get('category', 'A01:2021 - Injection')
            difficulty = data.get('difficulty', 'beginner')

            owasp_cat = OWASPCategory(category)
            diff_level = DifficultyLevel(difficulty)
            user_context = get_user_context(request.user)

            lesson = await generate_lesson(owasp_cat, diff_level, user_context)

            return JsonResponse({
                'title': lesson.title,
                'category': lesson.owasp_category.value,
                'difficulty': lesson.difficulty.value,
                'estimated_minutes': lesson.estimated_minutes,
                'why_it_matters': lesson.why_it_matters,
                'what_it_is': lesson.what_it_is,
                'real_world_example': lesson.real_world_example,
                'how_to_protect': lesson.how_to_protect,
                'quick_check': {
                    'question': lesson.quick_check_question,
                    'answer': lesson.quick_check_answer,
                },
                'key_takeaway': lesson.key_takeaway,
            })

        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)


@method_decorator(csrf_exempt, name='dispatch')
class QuizGeneratorView(LoginRequiredMixin, View):
    """Generate quiz - Pro feature"""

    async def post(self, request):
        # Check subscription access (Pro feature)
        if not request.user.has_full_access:
            return JsonResponse({
                'error': 'subscription_required',
                'message': 'Quiz Generator requires a Pro subscription.',
                'upgrade_url': '/pricing/',
                'trial_expired': request.user.trial_expired,
            }, status=403)

        try:
            data = json.loads(request.body)
            categories = data.get('categories', ['A01:2021 - Injection'])
            difficulty = data.get('difficulty', 'beginner')
            num_questions = data.get('num_questions', 5)

            owasp_cats = [OWASPCategory(c) for c in categories]
            diff_level = DifficultyLevel(difficulty)
            user_context = get_user_context(request.user)

            quiz = await generate_quiz(
                owasp_cats,
                diff_level,
                num_questions,
                user_context
            )

            return JsonResponse({
                'id': quiz.id,
                'title': quiz.title,
                'description': quiz.description,
                'questions': [
                    {
                        'id': q.id,
                        'type': q.question_type.value,
                        'question': q.question,
                        'options': q.options,
                        'points': q.points,
                        'time_limit': q.time_limit_seconds,
                        'hint': q.hint,
                    }
                    for q in quiz.questions
                ],
                'total_points': quiz.total_points,
                'passing_score': quiz.passing_score,
                'time_limit_minutes': quiz.time_limit_minutes,
            })

        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)


@method_decorator(csrf_exempt, name='dispatch')
class NewsAnalysisView(View):
    """Analyze news article (public endpoint for news page)"""
    
    async def post(self, request):
        try:
            data = json.loads(request.body)
            content = data.get('content', '')
            source_url = data.get('source_url', '')
            
            if not content:
                return JsonResponse({'error': 'Content required'}, status=400)
            
            summary = await analyze_article(content, source_url)
            
            return JsonResponse({
                'title': summary.title,
                'summary': summary.summary,
                'urgency': summary.urgency.value,
                'owasp_categories': [c.value for c in summary.owasp_categories],
                'action_required': summary.action_required,
                'action_items': summary.action_items,
                'affected_industries': summary.affected_industries,
            })
            
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
