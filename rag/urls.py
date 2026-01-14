"""
RAG URL Configuration
"""

from django.urls import path
from .views import (
    RAGQueryView,
    RAGFeedbackView,
    RAGHistoryView,
    DocumentListView,
    DocumentUploadView,
    KnowledgeBaseStatsView,
)

app_name = 'rag'

urlpatterns = [
    # Query endpoints
    path('query/', RAGQueryView.as_view(), name='query'),
    path('feedback/<int:query_id>/', RAGFeedbackView.as_view(), name='feedback'),
    path('history/', RAGHistoryView.as_view(), name='history'),

    # Document management (admin)
    path('documents/', DocumentListView.as_view(), name='document_list'),
    path('documents/upload/', DocumentUploadView.as_view(), name='document_upload'),

    # Stats
    path('stats/', KnowledgeBaseStatsView.as_view(), name='stats'),
]
