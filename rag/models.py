"""
RAG Models - Database models for document management and query tracking
"""

from django.db import models
from django.conf import settings


class Document(models.Model):
    """
    Uploaded documents for the knowledge base.

    Stores document metadata and tracks indexing status.
    """

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('indexed', 'Indexed'),
        ('failed', 'Failed'),
    ]

    FILE_TYPE_CHOICES = [
        ('pdf', 'PDF'),
        ('docx', 'Word Document'),
        ('md', 'Markdown'),
        ('txt', 'Plain Text'),
    ]

    CATEGORY_CHOICES = [
        ('owasp', 'OWASP'),
        ('general', 'General Security'),
        ('smb_specific', 'SMB-Specific'),
        ('compliance', 'Compliance'),
        ('best_practices', 'Best Practices'),
        ('threat_intel', 'Threat Intelligence'),
        ('vendor', 'Vendor Documentation'),
    ]

    # Basic info
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    file = models.FileField(upload_to='rag_documents/')
    file_type = models.CharField(max_length=20, choices=FILE_TYPE_CHOICES)
    category = models.CharField(
        max_length=50,
        choices=CATEGORY_CHOICES,
        default='general'
    )

    # Processing status
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )
    chunk_count = models.IntegerField(default=0)
    error_message = models.TextField(blank=True)

    # Metadata
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='uploaded_documents'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    indexed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Document'
        verbose_name_plural = 'Documents'

    def __str__(self):
        return f"{self.title} ({self.get_status_display()})"

    @property
    def is_indexed(self) -> bool:
        return self.status == 'indexed'


class RAGQuery(models.Model):
    """
    Log all RAG queries for analytics and feedback.
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='rag_queries'
    )
    question = models.TextField()
    answer = models.TextField()
    confidence = models.FloatField()
    search_results_count = models.IntegerField(default=0)
    response_time_ms = models.IntegerField(null=True, blank=True)

    # User feedback
    was_helpful = models.BooleanField(null=True, blank=True)
    user_feedback = models.TextField(blank=True)

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'RAG Query'
        verbose_name_plural = 'RAG Queries'

    def __str__(self):
        return f"Query by {self.user.username}: {self.question[:50]}..."


class RAGCitation(models.Model):
    """
    Store citations for each query.
    """

    query = models.ForeignKey(
        RAGQuery,
        on_delete=models.CASCADE,
        related_name='citations'
    )
    source = models.CharField(max_length=255)
    page = models.IntegerField(null=True, blank=True)
    section = models.CharField(max_length=255, blank=True)
    chunk_id = models.CharField(max_length=255, blank=True)

    class Meta:
        verbose_name = 'RAG Citation'
        verbose_name_plural = 'RAG Citations'

    def __str__(self):
        parts = [self.source]
        if self.page:
            parts.append(f"Page {self.page}")
        return ", ".join(parts)
