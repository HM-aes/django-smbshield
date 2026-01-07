"""Assessment Views - Quiz taking and results"""
from django.views.generic import TemplateView, DetailView, View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect, get_object_or_404
from django.http import JsonResponse
from django.utils import timezone
import json

from .models import Quiz, Question, QuizAttempt, QuestionAnswer


class AssessmentHomeView(LoginRequiredMixin, TemplateView):
    template_name = 'pages/assessment/home.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        # Available quizzes
        context['quizzes'] = Quiz.objects.filter(is_active=True)
        
        # Recent attempts
        context['recent_attempts'] = QuizAttempt.objects.filter(
            user=user
        ).order_by('-started_at')[:10]
        
        # Stats
        attempts = QuizAttempt.objects.filter(user=user, status='completed')
        context['total_attempts'] = attempts.count()
        context['average_score'] = sum(a.percentage for a in attempts) / attempts.count() if attempts.count() > 0 else 0
        context['best_score'] = max((a.percentage for a in attempts), default=0)
        
        return context


class QuizView(LoginRequiredMixin, DetailView):
    model = Quiz
    template_name = 'pages/assessment/quiz.html'
    context_object_name = 'quiz'


class StartQuizView(LoginRequiredMixin, View):
    """Start a new quiz attempt"""
    
    def post(self, request, pk):
        quiz = get_object_or_404(Quiz, pk=pk)
        
        # Create new attempt
        attempt = QuizAttempt.objects.create(
            user=request.user,
            quiz=quiz,
            max_score=quiz.total_points,
            status='in_progress'
        )
        
        return redirect('assessment:take_quiz', attempt_id=attempt.id)


class TakeQuizView(LoginRequiredMixin, TemplateView):
    template_name = 'pages/assessment/take_quiz.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        attempt_id = self.kwargs.get('attempt_id')
        attempt = get_object_or_404(QuizAttempt, id=attempt_id, user=self.request.user)
        
        context['attempt'] = attempt
        context['questions'] = attempt.quiz.questions.all()
        context['time_remaining'] = attempt.quiz.time_limit_minutes * 60  # seconds
        
        return context


class SubmitQuizView(LoginRequiredMixin, View):
    """Submit quiz answers"""
    
    def post(self, request, pk):
        attempt = get_object_or_404(QuizAttempt, pk=pk, user=request.user)
        
        if attempt.status != 'in_progress':
            return JsonResponse({'error': 'Quiz already submitted'}, status=400)
        
        try:
            data = json.loads(request.body)
            answers = data.get('answers', {})  # {question_id: answer}
            
            correct_count = 0
            total_points = 0
            
            for question_id, user_answer in answers.items():
                question = Question.objects.get(id=question_id)
                is_correct = str(user_answer).strip().lower() == str(question.correct_answer).strip().lower()
                
                points = question.points if is_correct else 0
                total_points += points
                
                if is_correct:
                    correct_count += 1
                
                QuestionAnswer.objects.create(
                    attempt=attempt,
                    question=question,
                    user_answer=user_answer,
                    is_correct=is_correct,
                    points_earned=points
                )
            
            # Update attempt
            attempt.score = total_points
            attempt.correct_count = correct_count
            attempt.wrong_count = len(answers) - correct_count
            attempt.skipped_count = attempt.quiz.questions.count() - len(answers)
            attempt.percentage = (total_points / attempt.max_score * 100) if attempt.max_score > 0 else 0
            attempt.passed = attempt.percentage >= attempt.quiz.passing_percentage
            attempt.status = 'completed'
            attempt.completed_at = timezone.now()
            attempt.time_taken_seconds = int((attempt.completed_at - attempt.started_at).total_seconds())
            attempt.save()
            
            # Update user stats
            user = request.user
            user.total_quizzes_passed += 1 if attempt.passed else 0
            user.last_quiz_at = timezone.now()
            user.save()
            
            return JsonResponse({
                'success': True,
                'result_url': f'/assess/result/{attempt.id}/'
            })
            
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)


class QuizResultView(LoginRequiredMixin, DetailView):
    model = QuizAttempt
    template_name = 'pages/assessment/result.html'
    context_object_name = 'attempt'
    
    def get_queryset(self):
        return QuizAttempt.objects.filter(user=self.request.user)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['answers'] = self.object.answers.select_related('question').all()
        return context
