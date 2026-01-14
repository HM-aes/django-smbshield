"""
RAG Admin Interface - Document management and query analytics
"""

from django.contrib import admin
from django.utils.html import format_html
from .models import Document, RAGQuery, RAGCitation


class RAGCitationInline(admin.TabularInline):
    """Inline display of citations for a query."""
    model = RAGCitation
    extra = 0
    readonly_fields = ['source', 'page', 'section', 'chunk_id']
    can_delete = False


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    """Admin interface for document management."""

    list_display = [
        'title',
        'file_type',
        'category',
        'status_badge',
        'chunk_count',
        'uploaded_by',
        'created_at',
        'indexed_at'
    ]
    list_filter = ['status', 'file_type', 'category', 'created_at']
    search_fields = ['title', 'description']
    readonly_fields = ['chunk_count', 'indexed_at', 'error_message', 'created_at', 'updated_at']
    date_hierarchy = 'created_at'

    fieldsets = (
        ('Document Info', {
            'fields': ('title', 'description', 'file', 'file_type', 'category')
        }),
        ('Processing Status', {
            'fields': ('status', 'chunk_count', 'error_message', 'indexed_at')
        }),
        ('Metadata', {
            'fields': ('uploaded_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    actions = ['mark_pending', 'reindex_documents']

    def status_badge(self, obj):
        """Display status as colored badge."""
        colors = {
            'pending': '#f59e0b',     # amber
            'processing': '#3b82f6',  # blue
            'indexed': '#22c55e',     # green
            'failed': '#ef4444',      # red
        }
        color = colors.get(obj.status, '#6b7280')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; '
            'border-radius: 4px; font-size: 11px;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_badge.short_description = 'Status'

    @admin.action(description='Mark selected as pending')
    def mark_pending(self, request, queryset):
        count = queryset.update(status='pending', error_message='')
        self.message_user(request, f'Marked {count} documents as pending.')

    @admin.action(description='Queue for re-indexing')
    def reindex_documents(self, request, queryset):
        count = queryset.update(status='pending', error_message='')
        self.message_user(
            request,
            f'Queued {count} documents for re-indexing. '
            f'Run: python manage.py index_documents'
        )


@admin.register(RAGQuery)
class RAGQueryAdmin(admin.ModelAdmin):
    """Admin interface for query analytics."""

    list_display = [
        'id',
        'user',
        'question_preview',
        'confidence_badge',
        'was_helpful_icon',
        'response_time_ms',
        'created_at'
    ]
    list_filter = ['was_helpful', 'created_at', 'confidence']
    search_fields = ['question', 'answer', 'user__username', 'user__email']
    readonly_fields = [
        'user', 'question', 'answer', 'confidence',
        'search_results_count', 'response_time_ms', 'created_at'
    ]
    date_hierarchy = 'created_at'
    inlines = [RAGCitationInline]

    fieldsets = (
        ('Query', {
            'fields': ('user', 'question')
        }),
        ('Response', {
            'fields': ('answer', 'confidence', 'search_results_count', 'response_time_ms')
        }),
        ('Feedback', {
            'fields': ('was_helpful', 'user_feedback')
        }),
        ('Metadata', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )

    def question_preview(self, obj):
        """Show truncated question."""
        return obj.question[:60] + '...' if len(obj.question) > 60 else obj.question
    question_preview.short_description = 'Question'

    def confidence_badge(self, obj):
        """Display confidence as colored badge."""
        if obj.confidence >= 0.8:
            color = '#22c55e'  # green
        elif obj.confidence >= 0.5:
            color = '#f59e0b'  # amber
        else:
            color = '#ef4444'  # red

        return format_html(
            '<span style="background-color: {}; color: white; padding: 2px 6px; '
            'border-radius: 3px; font-size: 11px;">{:.0%}</span>',
            color,
            obj.confidence
        )
    confidence_badge.short_description = 'Confidence'

    def was_helpful_icon(self, obj):
        """Display helpfulness as icon."""
        if obj.was_helpful is None:
            return format_html('<span style="color: #9ca3af;">—</span>')
        elif obj.was_helpful:
            return format_html('<span style="color: #22c55e;">✓</span>')
        else:
            return format_html('<span style="color: #ef4444;">✗</span>')
    was_helpful_icon.short_description = 'Helpful'


@admin.register(RAGCitation)
class RAGCitationAdmin(admin.ModelAdmin):
    """Admin interface for citations (read-only)."""

    list_display = ['id', 'query', 'source', 'page', 'section']
    list_filter = ['source']
    search_fields = ['source', 'section', 'query__question']
    readonly_fields = ['query', 'source', 'page', 'section', 'chunk_id']

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False
