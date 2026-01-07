"""News Views"""
from django.views.generic import ListView, DetailView
from .models import NewsArticle


class NewsListView(ListView):
    model = NewsArticle
    template_name = 'pages/news/index.html'
    context_object_name = 'articles'
    paginate_by = 12
    
    def get_queryset(self):
        return NewsArticle.objects.filter(is_active=True).order_by('-published_at')


class NewsDetailView(DetailView):
    model = NewsArticle
    template_name = 'pages/news/detail.html'
    context_object_name = 'article'
    
    def get_object(self, queryset=None):
        obj = super().get_object(queryset)
        obj.views += 1
        obj.save(update_fields=['views'])
        return obj
