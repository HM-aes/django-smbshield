"""
RAG API Views - Async endpoints for RAG queries and document management

Follows the same patterns as agents/views.py:
- Async class-based views
- Subscription checks for pro features
- JSON responses
"""

import json
import time
from django.http import JsonResponse
from django.views import View
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.mixins import LoginRequiredMixin
from django.utils import timezone

from .models import RAGQuery, RAGCitation, Document
from .services import rag_retriever


@method_decorator(csrf_exempt, name='dispatch')
class RAGQueryView(LoginRequiredMixin, View):
    """
    RAG query endpoint - Pro feature

    POST /api/rag/query/
    Body: {"question": "What is SQL injection?"}

    Returns: {"answer": "...", "citations": [...], "confidence": 0.85, ...}
    """

    async def post(self, request):
        # Check subscription access
        if not request.user.has_full_access:
            return JsonResponse({
                'error': 'subscription_required',
                'message': 'Knowledge Base Q&A requires a Pro subscription.',
                'upgrade_url': '/pricing/',
            }, status=403)

        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)

        question = data.get('question', '').strip()
        if not question:
            return JsonResponse({'error': 'Question is required'}, status=400)

        if len(question) > 1000:
            return JsonResponse({'error': 'Question too long (max 1000 chars)'}, status=400)

        # Optional filters
        category = data.get('category')
        filter_conditions = {}
        if category:
            filter_conditions['category'] = category

        # Execute RAG query
        start_time = time.time()

        try:
            result = await rag_retriever.query_async(
                question=question,
                user_id=str(request.user.id),
                filter_conditions=filter_conditions if filter_conditions else None
            )
        except Exception as e:
            return JsonResponse({
                'error': 'Query failed',
                'message': str(e)
            }, status=500)

        response_time_ms = int((time.time() - start_time) * 1000)

        # Save query to database for analytics
        try:
            rag_query = await RAGQuery.objects.acreate(
                user=request.user,
                question=question,
                answer=result.get('answer', ''),
                confidence=result.get('confidence', 0.0),
                search_results_count=result.get('search_results_count', 0),
                response_time_ms=response_time_ms
            )

            # Save citations
            for citation in result.get('citations', []):
                await RAGCitation.objects.acreate(
                    query=rag_query,
                    source=citation.get('source', ''),
                    page=citation.get('page'),
                    section=citation.get('section', '')
                )
        except Exception as e:
            # Don't fail the request if saving fails
            pass

        return JsonResponse({
            **result,
            'query_id': rag_query.id if 'rag_query' in locals() else None,
            'response_time_ms': response_time_ms
        })


@method_decorator(csrf_exempt, name='dispatch')
class RAGFeedbackView(LoginRequiredMixin, View):
    """
    Submit feedback for a RAG query

    POST /api/rag/feedback/<query_id>/
    Body: {"was_helpful": true, "feedback": "optional text"}
    """

    async def post(self, request, query_id):
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)

        try:
            query = await RAGQuery.objects.aget(id=query_id, user=request.user)
        except RAGQuery.DoesNotExist:
            return JsonResponse({'error': 'Query not found'}, status=404)

        query.was_helpful = data.get('was_helpful')
        query.user_feedback = data.get('feedback', '')
        await query.asave()

        return JsonResponse({'status': 'success', 'message': 'Feedback saved'})


class RAGHistoryView(LoginRequiredMixin, View):
    """
    Get user's RAG query history

    GET /api/rag/history/
    Query params: ?limit=20&offset=0
    """

    async def get(self, request):
        limit = min(int(request.GET.get('limit', 20)), 100)
        offset = int(request.GET.get('offset', 0))

        queries = []
        async for query in RAGQuery.objects.filter(
            user=request.user
        ).order_by('-created_at')[offset:offset + limit]:
            citations = []
            async for citation in query.citations.all():
                citations.append({
                    'source': citation.source,
                    'page': citation.page,
                    'section': citation.section
                })

            queries.append({
                'id': query.id,
                'question': query.question,
                'answer': query.answer[:200] + '...' if len(query.answer) > 200 else query.answer,
                'confidence': query.confidence,
                'was_helpful': query.was_helpful,
                'created_at': query.created_at.isoformat(),
                'citations': citations
            })

        return JsonResponse({
            'queries': queries,
            'count': len(queries),
            'offset': offset,
            'limit': limit
        })


class DocumentListView(LoginRequiredMixin, View):
    """
    List documents in the knowledge base (staff only)

    GET /api/rag/documents/
    """

    async def get(self, request):
        if not request.user.is_staff:
            return JsonResponse({'error': 'Admin access required'}, status=403)

        documents = []
        async for doc in Document.objects.all().order_by('-created_at')[:50]:
            documents.append({
                'id': doc.id,
                'title': doc.title,
                'file_type': doc.file_type,
                'category': doc.category,
                'status': doc.status,
                'chunk_count': doc.chunk_count,
                'created_at': doc.created_at.isoformat(),
                'indexed_at': doc.indexed_at.isoformat() if doc.indexed_at else None
            })

        return JsonResponse({'documents': documents, 'count': len(documents)})


@method_decorator(csrf_exempt, name='dispatch')
class DocumentUploadView(LoginRequiredMixin, View):
    """
    Upload a document for indexing (staff only)

    POST /api/rag/documents/upload/
    """

    async def post(self, request):
        if not request.user.is_staff:
            return JsonResponse({'error': 'Admin access required'}, status=403)

        if 'file' not in request.FILES:
            return JsonResponse({'error': 'No file provided'}, status=400)

        uploaded_file = request.FILES['file']
        title = request.POST.get('title', uploaded_file.name)
        category = request.POST.get('category', 'general')

        # Determine file type
        ext = uploaded_file.name.split('.')[-1].lower()
        file_type_map = {
            'pdf': 'pdf',
            'docx': 'docx',
            'doc': 'docx',
            'md': 'md',
            'markdown': 'md',
            'txt': 'txt'
        }
        file_type = file_type_map.get(ext)

        if not file_type:
            return JsonResponse({
                'error': f'Unsupported file type: {ext}'
            }, status=400)

        # Create document record
        document = await Document.objects.acreate(
            title=title,
            file=uploaded_file,
            file_type=file_type,
            category=category,
            status='pending',
            uploaded_by=request.user
        )

        return JsonResponse({
            'status': 'success',
            'message': 'Document uploaded. Run index_documents to process.',
            'document_id': document.id
        })


class KnowledgeBaseStatsView(LoginRequiredMixin, View):
    """
    Get knowledge base statistics

    GET /api/rag/stats/
    """

    async def get(self, request):
        from .services import rag_retriever

        try:
            vector_count = rag_retriever.vector_store.count()
        except Exception:
            vector_count = 0

        doc_count = await Document.objects.filter(status='indexed').acount()
        query_count = await RAGQuery.objects.acount()
        helpful_count = await RAGQuery.objects.filter(was_helpful=True).acount()

        return JsonResponse({
            'vector_count': vector_count,
            'document_count': doc_count,
            'query_count': query_count,
            'helpful_queries': helpful_count,
            'helpfulness_rate': helpful_count / query_count if query_count > 0 else 0
        })
