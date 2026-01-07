"""
Assessment Models - Quizzes, Questions, and Results
"""
from django.db import models
from django.conf import settings


class Quiz(models.Model):
    """Quiz container"""
    
    class Difficulty(models.TextChoices):
        BEGINNER = 'beginner', 'Beginner'
        INTERMEDIATE = 'intermediate', 'Intermediate'
        ADVANCED = 'advanced', 'Advanced'
        MIXED = 'mixed', 'Mixed'
    
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    
    # Targeting
    owasp_categories = models.JSONField(default=list)
    difficulty = models.CharField(max_length=20, choices=Difficulty.choices)
    
    # Settings
    time_limit_minutes = models.IntegerField(default=15)
    passing_percentage = models.IntegerField(default=70)
    shuffle_questions = models.BooleanField(default=True)
    show_answers_after = models.BooleanField(default=True)
    
    # AI Generation
    is_ai_generated = models.BooleanField(default=True)
    generation_prompt = models.TextField(blank=True)  # Store prompt for regeneration
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'quizzes'
        verbose_name_plural = 'Quizzes'
    
    def __str__(self):
        return self.title
    
    @property
    def total_points(self):
        return sum(q.points for q in self.questions.all())


class Question(models.Model):
    """Individual quiz question"""
    
    class QuestionType(models.TextChoices):
        MULTIPLE_CHOICE = 'multiple_choice', 'Multiple Choice'
        TRUE_FALSE = 'true_false', 'True/False'
        SCENARIO = 'scenario', 'Scenario Based'
        FILL_BLANK = 'fill_blank', 'Fill in the Blank'
    
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name='questions')
    
    question_type = models.CharField(max_length=20, choices=QuestionType.choices)
    question_text = models.TextField()
    owasp_category = models.CharField(max_length=50, blank=True)
    
    # Options (for multiple choice)
    options = models.JSONField(default=list)  # ["Option A", "Option B", "Option C", "Option D"]
    correct_answer = models.CharField(max_length=500)  # Index for MC, text for others
    
    # Explanations
    explanation = models.TextField()
    wrong_answer_explanations = models.JSONField(default=dict)  # {"A": "Why A is wrong", ...}
    
    # Metadata
    points = models.IntegerField(default=10)
    time_limit_seconds = models.IntegerField(default=60)
    hint = models.TextField(blank=True)
    order = models.IntegerField(default=0)
    
    class Meta:
        db_table = 'questions'
        ordering = ['order']
    
    def __str__(self):
        return f"{self.quiz.title} - Q{self.order}"


class QuizAttempt(models.Model):
    """User's quiz attempt"""
    
    class Status(models.TextChoices):
        IN_PROGRESS = 'in_progress', 'In Progress'
        COMPLETED = 'completed', 'Completed'
        TIMED_OUT = 'timed_out', 'Timed Out'
        ABANDONED = 'abandoned', 'Abandoned'
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='quiz_attempts'
    )
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE)
    
    # Status
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.IN_PROGRESS)
    
    # Results
    score = models.IntegerField(default=0)
    max_score = models.IntegerField(default=0)
    percentage = models.FloatField(default=0.0)
    passed = models.BooleanField(default=False)
    
    # Breakdown
    correct_count = models.IntegerField(default=0)
    wrong_count = models.IntegerField(default=0)
    skipped_count = models.IntegerField(default=0)
    
    # Timing
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    time_taken_seconds = models.IntegerField(default=0)
    
    class Meta:
        db_table = 'quiz_attempts'
        ordering = ['-started_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.quiz.title} ({self.percentage}%)"


class QuestionAnswer(models.Model):
    """Individual question answer within an attempt"""
    attempt = models.ForeignKey(QuizAttempt, on_delete=models.CASCADE, related_name='answers')
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    
    user_answer = models.CharField(max_length=500, blank=True)
    is_correct = models.BooleanField(default=False)
    points_earned = models.IntegerField(default=0)
    
    # Timing
    time_spent_seconds = models.IntegerField(default=0)
    answered_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'question_answers'
        unique_together = ['attempt', 'question']
    
    def __str__(self):
        status = "✓" if self.is_correct else "✗"
        return f"{status} {self.question}"


class KnowledgeGap(models.Model):
    """Identified knowledge gaps from quiz analysis"""
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='knowledge_gaps'
    )
    
    owasp_category = models.CharField(max_length=50)
    description = models.TextField()
    severity = models.CharField(max_length=20, default='moderate')  # minor, moderate, significant
    
    # Recommendations
    recommended_lessons = models.JSONField(default=list)
    practice_questions_needed = models.IntegerField(default=3)
    
    # Tracking
    identified_at = models.DateTimeField(auto_now_add=True)
    addressed = models.BooleanField(default=False)
    addressed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'knowledge_gaps'
        ordering = ['-identified_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.owasp_category}: {self.severity}"
