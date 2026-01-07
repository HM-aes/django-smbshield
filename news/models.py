"""
News Models - Stores analyzed news articles
"""
from django.db import models
from django.utils import timezone


class NewsSource(models.Model):
    """RSS/API news sources"""
    name = models.CharField(max_length=100)
    url = models.URLField()
    feed_type = models.CharField(max_length=20, default='rss')  # rss, api, scrape
    is_active = models.BooleanField(default=True)
    last_fetched = models.DateTimeField(null=True, blank=True)
    reliability_score = models.FloatField(default=0.8)  # 0-1
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'news_sources'
    
    def __str__(self):
        return self.name


class NewsArticle(models.Model):
    """Analyzed news articles"""
    
    class Urgency(models.TextChoices):
        LOW = 'low', 'Low'
        MEDIUM = 'medium', 'Medium'
        HIGH = 'high', 'High'
        CRITICAL = 'critical', 'Critical'
    
    # Source
    source = models.ForeignKey(NewsSource, on_delete=models.CASCADE, null=True)
    original_url = models.URLField(unique=True)
    original_title = models.CharField(max_length=500)
    original_content = models.TextField()
    
    # AI-Generated Summary
    title = models.CharField(max_length=300)
    summary = models.TextField()
    urgency = models.CharField(max_length=20, choices=Urgency.choices, default=Urgency.LOW)
    
    # Categorization
    owasp_categories = models.JSONField(default=list)  # List of OWASP category strings
    affected_industries = models.JSONField(default=list)
    tags = models.JSONField(default=list)
    
    # Action items
    action_required = models.BooleanField(default=False)
    action_items = models.JSONField(default=list)
    
    # Metadata
    published_at = models.DateTimeField()
    analyzed_at = models.DateTimeField(auto_now_add=True)
    
    # Display
    is_featured = models.BooleanField(default=False)
    is_breaking = models.BooleanField(default=False)
    views = models.IntegerField(default=0)
    
    class Meta:
        db_table = 'news_articles'
        ordering = ['-published_at']
        indexes = [
            models.Index(fields=['-published_at']),
            models.Index(fields=['urgency']),
            models.Index(fields=['is_breaking']),
        ]
    
    def __str__(self):
        return self.title


class DailyBriefing(models.Model):
    """Daily news briefings for homepage"""
    date = models.DateField(unique=True)
    
    # AI-Generated content
    headline = models.CharField(max_length=200)
    summary = models.TextField()
    threat_level = models.CharField(max_length=20, default='low')
    
    # Related articles
    top_story = models.ForeignKey(
        NewsArticle, 
        on_delete=models.SET_NULL, 
        null=True,
        related_name='top_story_briefings'
    )
    breaking_alerts = models.ManyToManyField(
        NewsArticle, 
        related_name='breaking_briefings',
        blank=True
    )
    other_news = models.ManyToManyField(
        NewsArticle,
        related_name='other_briefings',
        blank=True
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'daily_briefings'
        ordering = ['-date']
    
    def __str__(self):
        return f"Briefing for {self.date}"
