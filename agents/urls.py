"""
Agent API URL Configuration
"""
from django.urls import path
from .views import (
    ProfessorShieldView,
    LessonGeneratorView,
    QuizGeneratorView,
    NewsAnalysisView,
)

app_name = 'agents'

urlpatterns = [
    # Professor Shield
    path('professor/ask/', ProfessorShieldView.as_view(), name='professor_ask'),
    path('professor/lesson/', LessonGeneratorView.as_view(), name='professor_lesson'),
    
    # Assessment Bot
    path('assessment/quiz/', QuizGeneratorView.as_view(), name='generate_quiz'),
    
    # News Agent
    path('news/analyze/', NewsAnalysisView.as_view(), name='analyze_news'),
]
