"""Education URLs"""
from django.urls import path
from . import views

app_name = 'education'

urlpatterns = [
    path('', views.LearningHomeView.as_view(), name='home'),
    path('module/<str:code>/', views.ModuleDetailView.as_view(), name='module'),
    path('lesson/<int:pk>/', views.LessonView.as_view(), name='lesson'),
    path('chat/', views.ProfessorChatPageView.as_view(), name='chat'),
    path('chat/api/', views.ProfessorChatAPIView.as_view(), name='chat_api'),
]

