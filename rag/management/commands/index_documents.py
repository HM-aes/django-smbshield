"""
Management command to index documents into Qdrant vector database

Usage:
    python manage.py index_documents                    # Index pending documents
    python manage.py index_documents --source ./docs/   # Index from directory
    python manage.py index_documents --clear            # Clear and re-index all
    python manage.py index_documents --category owasp   # Set category for indexed docs
"""

from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from pathlib import Path
import logging

from rag.models import Document
from rag.services import embedder_service, ChunkerService, get_vector_store_service
from rag.services.document_loader import document_loader

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Index documents into Qdrant vector database'

    def add_arguments(self, parser):
        parser.add_argument(
            '--source',
            type=str,
            help='Path to directory containing documents to index'
        )
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing vectors before indexing'
        )
        parser.add_argument(
            '--category',
            type=str,
            default='general',
            help='Category for indexed documents (default: general)'
        )
        parser.add_argument(
            '--chunk-size',
            type=int,
            default=512,
            help='Chunk size in tokens (default: 512)'
        )
        parser.add_argument(
            '--chunk-overlap',
            type=int,
            default=50,
            help='Chunk overlap in tokens (default: 50)'
        )
        parser.add_argument(
            '--pending-only',
            action='store_true',
            help='Only process documents with pending status from database'
        )

    def handle(self, *args, **options):
        source_dir = options['source']
        clear_first = options['clear']
        category = options['category']
        chunk_size = options['chunk_size']
        chunk_overlap = options['chunk_overlap']
        pending_only = options['pending_only']

        # Initialize services
        self.stdout.write('Initializing RAG services...')

        chunker = ChunkerService(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap
        )

        vector_store = get_vector_store_service(
            embedder_dim=embedder_service.get_embedding_dimension()
        )

        if clear_first:
            self.stdout.write(self.style.WARNING('Clearing existing vectors...'))
            vector_store.clear_collection()
            self.stdout.write(self.style.SUCCESS('Vectors cleared'))

        # Determine what to index
        if source_dir:
            # Index from directory
            self._index_from_directory(
                source_dir, category, chunker, vector_store
            )
        elif pending_only:
            # Index pending documents from database
            self._index_pending_documents(chunker, vector_store)
        else:
            # Default: index all pending documents
            self._index_pending_documents(chunker, vector_store)

        # Report stats
        total_vectors = vector_store.count()
        self.stdout.write(
            self.style.SUCCESS(f'\nTotal vectors in knowledge base: {total_vectors}')
        )

    def _index_from_directory(
        self,
        directory: str,
        category: str,
        chunker: ChunkerService,
        vector_store
    ):
        """Index documents from a directory."""
        source_path = Path(directory)

        if not source_path.exists():
            raise CommandError(f'Directory not found: {directory}')

        if not source_path.is_dir():
            raise CommandError(f'Not a directory: {directory}')

        # Load documents
        self.stdout.write(f'Loading documents from: {directory}')
        documents = document_loader.load_directory(
            directory,
            recursive=True,
            category=category
        )

        if not documents:
            self.stdout.write(self.style.WARNING('No supported documents found'))
            return

        self.stdout.write(f'Found {len(documents)} documents')

        # Process each document
        total_chunks = 0
        for doc in documents:
            source_name = doc['metadata'].get('source', 'unknown')
            self.stdout.write(f'  Processing: {source_name}')

            # Chunk the document
            chunks = chunker.chunk_text(doc['text'], doc['metadata'])

            if not chunks:
                self.stdout.write(self.style.WARNING(f'    No chunks created'))
                continue

            # Generate embeddings
            chunk_texts = [c.text for c in chunks]
            embeddings = embedder_service.encode_documents(
                chunk_texts,
                show_progress=False
            )

            # Prepare payloads
            payloads = [
                {
                    'text': c.text,
                    'source': c.metadata.get('source'),
                    'page': c.metadata.get('page_number'),
                    'section': c.metadata.get('section', ''),
                    'category': c.metadata.get('category', category),
                    'chunk_index': c.chunk_id,
                    'total_chunks': c.metadata.get('total_chunks')
                }
                for c in chunks
            ]

            # Insert into vector store
            vector_store.insert(embeddings, payloads)

            total_chunks += len(chunks)
            self.stdout.write(f'    Created {len(chunks)} chunks')

        self.stdout.write(
            self.style.SUCCESS(f'\nIndexed {len(documents)} documents, {total_chunks} chunks')
        )

    def _index_pending_documents(self, chunker: ChunkerService, vector_store):
        """Index pending documents from the database."""
        pending_docs = Document.objects.filter(status='pending')
        count = pending_docs.count()

        if count == 0:
            self.stdout.write('No pending documents to index')
            return

        self.stdout.write(f'Processing {count} pending documents...')

        indexed_count = 0
        failed_count = 0

        for doc in pending_docs:
            self.stdout.write(f'  Processing: {doc.title}')

            # Update status
            doc.status = 'processing'
            doc.save()

            try:
                # Load the document
                file_path = doc.file.path
                doc_data = document_loader.load(file_path)

                # Add metadata
                doc_data['metadata']['category'] = doc.category
                doc_data['metadata']['document_id'] = doc.id

                # Chunk the document
                chunks = chunker.chunk_text(doc_data['text'], doc_data['metadata'])

                if not chunks:
                    doc.status = 'failed'
                    doc.error_message = 'No chunks created'
                    doc.save()
                    failed_count += 1
                    continue

                # Generate embeddings
                chunk_texts = [c.text for c in chunks]
                embeddings = embedder_service.encode_documents(
                    chunk_texts,
                    show_progress=False
                )

                # Prepare payloads
                payloads = [
                    {
                        'text': c.text,
                        'source': doc.title,
                        'page': c.metadata.get('page_number'),
                        'section': c.metadata.get('section', ''),
                        'category': doc.category,
                        'document_id': doc.id,
                        'chunk_index': c.chunk_id
                    }
                    for c in chunks
                ]

                # Insert into vector store
                vector_store.insert(embeddings, payloads)

                # Update document status
                doc.status = 'indexed'
                doc.chunk_count = len(chunks)
                doc.indexed_at = timezone.now()
                doc.error_message = ''
                doc.save()

                indexed_count += 1
                self.stdout.write(f'    Created {len(chunks)} chunks')

            except Exception as e:
                doc.status = 'failed'
                doc.error_message = str(e)
                doc.save()
                failed_count += 1
                self.stdout.write(
                    self.style.ERROR(f'    Failed: {str(e)}')
                )

        self.stdout.write(
            self.style.SUCCESS(
                f'\nIndexed: {indexed_count}, Failed: {failed_count}'
            )
        )
