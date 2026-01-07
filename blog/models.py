"""
Blog Models - AI/LLM Security market analysis & opinions
"""
from django.db import models
from django.utils.text import slugify
from django.conf import settings


class BlogCategory(models.Model):
    """Blog post categories"""
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True)
    color = models.CharField(max_length=7, default='#3B82F6')  # Hex color
    
    class Meta:
        db_table = 'blog_categories'
        verbose_name_plural = 'Blog Categories'
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class BlogPost(models.Model):
    """Blog posts - your takes on AI/LLM security"""
    
    class Status(models.TextChoices):
        DRAFT = 'draft', 'Draft'
        REVIEW = 'review', 'In Review'
        PUBLISHED = 'published', 'Published'
    
    # Content
    title = models.CharField(max_length=300)
    slug = models.SlugField(unique=True, max_length=300)
    excerpt = models.TextField(max_length=500)
    content = models.TextField()  # Markdown content
    
    # Metadata
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='blog_posts'
    )
    category = models.ForeignKey(
        BlogCategory,
        on_delete=models.SET_NULL,
        null=True,
        related_name='posts'
    )
    tags = models.JSONField(default=list)
    
    # Related OWASP/Security topics
    owasp_categories = models.JSONField(default=list)
    related_llms = models.JSONField(default=list)  # e.g., ['Claude', 'GPT-4', 'Gemini']
    related_sectors = models.JSONField(default=list)  # e.g., ['Healthcare', 'Finance']
    
    # Publishing
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT)
    published_at = models.DateTimeField(null=True, blank=True)
    
    # SEO
    meta_title = models.CharField(max_length=70, blank=True)
    meta_description = models.CharField(max_length=160, blank=True)
    
    # Engagement
    views = models.IntegerField(default=0)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'blog_posts'
        ordering = ['-published_at']
        indexes = [
            models.Index(fields=['-published_at']),
            models.Index(fields=['status']),
            models.Index(fields=['slug']),
        ]
    
    def __str__(self):
        return self.title
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        if not self.meta_title:
            self.meta_title = self.title[:70]
        if not self.meta_description:
            self.meta_description = self.excerpt[:160]
        super().save(*args, **kwargs)


# Pre-populate categories for your content strategy
DEFAULT_CATEGORIES = [
    {'name': 'Market Analysis', 'slug': 'market-analysis', 'color': '#8B5CF6'},
    {'name': 'Sector Guide', 'slug': 'sector-guide', 'color': '#10B981'},
    {'name': 'Agent Reviews', 'slug': 'agent-reviews', 'color': '#F59E0B'},
    {'name': 'News Commentary', 'slug': 'news-commentary', 'color': '#EF4444'},
    {'name': 'OWASP Deep Dive', 'slug': 'owasp-deep-dive', 'color': '#3B82F6'},
    {'name': 'SMB Security Tips', 'slug': 'smb-security-tips', 'color': '#06B6D4'},
]
