"""
Education Models - Lessons, Modules, and Progress Tracking
"""
from django.db import models
from django.conf import settings


class OWASPModule(models.Model):
    """OWASP Top 10 Learning Modules"""
    
    # OWASP 2021 Categories
    code = models.CharField(max_length=20, unique=True)  # e.g., 'A01:2021'
    name = models.CharField(max_length=200)  # e.g., 'Injection'
    order = models.IntegerField(default=0)
    
    # Content
    description = models.TextField()
    icon = models.CharField(max_length=50, default='shield')  # Lucide icon name
    color = models.CharField(max_length=7, default='#EF4444')
    
    # Learning estimates
    estimated_hours = models.FloatField(default=2.0)
    difficulty_start = models.CharField(max_length=20, default='beginner')
    
    is_active = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'owasp_modules'
        ordering = ['order']
    
    def __str__(self):
        return f"{self.code} - {self.name}"


class Lesson(models.Model):
    """Individual lessons within modules"""
    
    class Difficulty(models.TextChoices):
        BEGINNER = 'beginner', 'Beginner'
        INTERMEDIATE = 'intermediate', 'Intermediate'
        ADVANCED = 'advanced', 'Advanced'
    
    module = models.ForeignKey(OWASPModule, on_delete=models.CASCADE, related_name='lessons')
    
    # Content
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200)
    order = models.IntegerField(default=0)
    difficulty = models.CharField(max_length=20, choices=Difficulty.choices)
    estimated_minutes = models.IntegerField(default=10)
    
    # AI-Generated or manually created
    is_ai_generated = models.BooleanField(default=True)
    
    # Lesson content (stored as JSON for flexibility)
    content = models.JSONField(default=dict)
    # Expected structure:
    # {
    #   "why_it_matters": "...",
    #   "what_it_is": "...",
    #   "real_world_example": "...",
    #   "how_to_protect": ["step1", "step2"],
    #   "quick_check_question": "...",
    #   "quick_check_answer": "...",
    #   "key_takeaway": "..."
    # }
    
    # Prerequisites
    prerequisites = models.ManyToManyField('self', symmetrical=False, blank=True)
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'lessons'
        ordering = ['module__order', 'order']
        unique_together = ['module', 'slug']
    
    def __str__(self):
        return f"{self.module.code}: {self.title}"


class UserProgress(models.Model):
    """Track user progress through lessons"""
    
    class Status(models.TextChoices):
        NOT_STARTED = 'not_started', 'Not Started'
        IN_PROGRESS = 'in_progress', 'In Progress'
        COMPLETED = 'completed', 'Completed'
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='lesson_progress'
    )
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE)
    
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.NOT_STARTED)
    
    # Progress tracking
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    time_spent_seconds = models.IntegerField(default=0)
    
    # Quick check results
    quick_check_passed = models.BooleanField(default=False)
    quick_check_attempts = models.IntegerField(default=0)
    
    # Notes (user can add notes while learning)
    notes = models.TextField(blank=True)
    
    class Meta:
        db_table = 'user_progress'
        unique_together = ['user', 'lesson']
    
    def __str__(self):
        return f"{self.user.username} - {self.lesson.title}: {self.status}"


class ChatHistory(models.Model):
    """Store Professor Shield chat history"""
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='professor_chats'
    )
    lesson = models.ForeignKey(Lesson, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Chat content
    user_message = models.TextField()
    assistant_response = models.TextField()
    
    # Metadata
    related_owasp = models.CharField(max_length=20, blank=True)
    confidence = models.FloatField(default=0.0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'chat_history'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.created_at}"


# Default OWASP modules to seed
DEFAULT_OWASP_MODULES = [
    {'code': 'A01:2021', 'name': 'Broken Access Control', 'order': 1, 'color': '#EF4444'},
    {'code': 'A02:2021', 'name': 'Cryptographic Failures', 'order': 2, 'color': '#F97316'},
    {'code': 'A03:2021', 'name': 'Injection', 'order': 3, 'color': '#F59E0B'},
    {'code': 'A04:2021', 'name': 'Insecure Design', 'order': 4, 'color': '#EAB308'},
    {'code': 'A05:2021', 'name': 'Security Misconfiguration', 'order': 5, 'color': '#84CC16'},
    {'code': 'A06:2021', 'name': 'Vulnerable Components', 'order': 6, 'color': '#22C55E'},
    {'code': 'A07:2021', 'name': 'Auth Failures', 'order': 7, 'color': '#14B8A6'},
    {'code': 'A08:2021', 'name': 'Data Integrity Failures', 'order': 8, 'color': '#06B6D4'},
    {'code': 'A09:2021', 'name': 'Logging Failures', 'order': 9, 'color': '#3B82F6'},
    {'code': 'A10:2021', 'name': 'SSRF', 'order': 10, 'color': '#8B5CF6'},
]
