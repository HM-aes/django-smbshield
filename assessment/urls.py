"""Assessment URLs"""
from django.urls import path
from . import views

app_name = 'assessment'

urlpatterns = [
    path('', views.AssessmentHomeView.as_view(), name='home'),
    path('quiz/<int:pk>/', views.QuizView.as_view(), name='quiz'),
    path('quiz/<int:pk>/start/', views.StartQuizView.as_view(), name='start_quiz'),
    path('quiz/<int:pk>/submit/', views.SubmitQuizView.as_view(), name='submit_quiz'),
    path('result/<int:pk>/', views.QuizResultView.as_view(), name='result'),
]
