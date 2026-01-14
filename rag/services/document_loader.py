"""
Document Loader Service - Parse various document formats

Supports:
- PDF (.pdf)
- Word Documents (.docx)
- Markdown (.md)
- Plain Text (.txt)
"""

from pathlib import Path
from typing import Dict, Any, List, Optional
import logging

logger = logging.getLogger(__name__)


class DocumentLoader:
    """
    Load and parse various document formats.

    Extracts text content and metadata from documents
    for indexing into the RAG system.
    """

    SUPPORTED_EXTENSIONS = {'.pdf', '.docx', '.doc', '.md', '.markdown', '.txt'}

    def __init__(self):
        """Initialize the document loader."""
        logger.info("DocumentLoader initialized")

    def load(self, file_path: str) -> Dict[str, Any]:
        """
        Load and parse a document file.

        Args:
            file_path: Path to the document file

        Returns:
            Dict with keys:
                - text: Extracted text content
                - pages: List of page dicts (for PDFs)
                - metadata: Source metadata

        Raises:
            ValueError: If file type is not supported
        """
        path = Path(file_path)
        ext = path.suffix.lower()

        if ext not in self.SUPPORTED_EXTENSIONS:
            raise ValueError(
                f"Unsupported file type: {ext}. "
                f"Supported: {', '.join(self.SUPPORTED_EXTENSIONS)}"
            )

        logger.info(f"Loading document: {path.name}")

        if ext == '.pdf':
            return self._load_pdf(file_path)
        elif ext in {'.docx', '.doc'}:
            return self._load_docx(file_path)
        elif ext in {'.md', '.markdown'}:
            return self._load_markdown(file_path)
        elif ext == '.txt':
            return self._load_text(file_path)

    def _load_pdf(self, file_path: str) -> Dict[str, Any]:
        """Load and parse PDF file."""
        try:
            import pypdf
        except ImportError:
            raise ImportError(
                "pypdf is required for PDF support. "
                "Install with: pip install pypdf"
            )

        path = Path(file_path)
        pages = []

        with open(file_path, 'rb') as f:
            reader = pypdf.PdfReader(f)

            for i, page in enumerate(reader.pages):
                text = page.extract_text() or ''
                pages.append({
                    'text': text,
                    'page_number': i + 1
                })

        full_text = '\n\n'.join([p['text'] for p in pages])

        logger.info(f"Loaded PDF: {len(pages)} pages, {len(full_text)} chars")

        return {
            'text': full_text,
            'pages': pages,
            'metadata': {
                'source': path.name,
                'file_type': 'pdf',
                'page_count': len(pages)
            }
        }

    def _load_docx(self, file_path: str) -> Dict[str, Any]:
        """Load and parse Word document."""
        try:
            from docx import Document
        except ImportError:
            raise ImportError(
                "python-docx is required for Word document support. "
                "Install with: pip install python-docx"
            )

        path = Path(file_path)
        doc = Document(file_path)

        paragraphs = []
        for para in doc.paragraphs:
            if para.text.strip():
                paragraphs.append(para.text)

        full_text = '\n\n'.join(paragraphs)

        logger.info(f"Loaded DOCX: {len(paragraphs)} paragraphs, {len(full_text)} chars")

        return {
            'text': full_text,
            'metadata': {
                'source': path.name,
                'file_type': 'docx',
                'paragraph_count': len(paragraphs)
            }
        }

    def _load_markdown(self, file_path: str) -> Dict[str, Any]:
        """Load and parse Markdown file."""
        path = Path(file_path)

        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Extract title from first heading if present
        title = None
        lines = content.split('\n')
        for line in lines:
            if line.startswith('# '):
                title = line[2:].strip()
                break

        logger.info(f"Loaded Markdown: {len(content)} chars")

        return {
            'text': content,
            'metadata': {
                'source': path.name,
                'file_type': 'markdown',
                'title': title
            }
        }

    def _load_text(self, file_path: str) -> Dict[str, Any]:
        """Load plain text file."""
        path = Path(file_path)

        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        logger.info(f"Loaded text file: {len(content)} chars")

        return {
            'text': content,
            'metadata': {
                'source': path.name,
                'file_type': 'txt'
            }
        }

    def load_directory(
        self,
        directory: str,
        recursive: bool = True,
        category: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Load all supported documents from a directory.

        Args:
            directory: Path to the directory
            recursive: Whether to search subdirectories
            category: Optional category to add to metadata

        Returns:
            List of document dicts
        """
        path = Path(directory)
        documents = []

        if recursive:
            files = path.rglob('*')
        else:
            files = path.glob('*')

        for file_path in files:
            if file_path.is_file() and file_path.suffix.lower() in self.SUPPORTED_EXTENSIONS:
                try:
                    doc = self.load(str(file_path))
                    if category:
                        doc['metadata']['category'] = category
                    documents.append(doc)
                except Exception as e:
                    logger.error(f"Failed to load {file_path}: {str(e)}")

        logger.info(f"Loaded {len(documents)} documents from {directory}")
        return documents

    def is_supported(self, file_path: str) -> bool:
        """Check if a file type is supported."""
        ext = Path(file_path).suffix.lower()
        return ext in self.SUPPORTED_EXTENSIONS


# Global instance
document_loader = DocumentLoader()
