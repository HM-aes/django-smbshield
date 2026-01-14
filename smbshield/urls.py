"""
SMBShield URL Configuration
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # Authentication (OAuth, password reset)
    path('accounts/', include('allauth.urls')),
    
    # Public pages
    path('', include('core.urls')),
    path('news/', include('news.urls')),
    path('blog/', include('blog.urls')),
    
    # Members only (dashboard)
    path('dashboard/', include('dashboard.urls')),
    path('learn/', include('education.urls')),
    path('assess/', include('assessment.urls')),
    
    # API endpoints for agents
    path('api/agents/', include('agents.urls')),

    # RAG knowledge base API
    path('api/rag/', include('rag.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
