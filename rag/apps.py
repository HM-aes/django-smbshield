from django.apps import AppConfig


class RagConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'rag'
    verbose_name = 'RAG Knowledge Base'

    def ready(self):
        """Initialize app when Django starts."""
        # Import signals if needed
        pass
