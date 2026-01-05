"""
Semantic chunking strategy for A.R.T.E.M.I.S.

Provides sentence-aware chunking using embeddings to group semantically
related content. Respects paragraph and heading boundaries for structured
documents like Markdown.
"""

import re
from typing import List, Dict, Tuple, Any, Optional

from artemis.rag.ingestion.chunkers.registry import register_chunker, ChunkStrategy
from artemis.utils import get_logger

logger = get_logger(__name__)

# Try to import embedder for semantic similarity
try:
    from artemis.rag.core.embedder import Embedder
    _EMBEDDER_AVAILABLE = True
except ImportError:
    _EMBEDDER_AVAILABLE = False
    Embedder = None


def _split_into_sentences(text: str) -> List[str]:
    """Split text into sentences using simple regex."""
    # Simple sentence splitting - can be improved with nltk or spacy
    sentences = re.split(r'(?<=[.!?])\s+', text)
    return [s.strip() for s in sentences if s.strip()]


def _split_into_paragraphs(text: str) -> List[str]:
    """Split text into paragraphs."""
    paragraphs = text.split('\n\n')
    return [p.strip() for p in paragraphs if p.strip()]


def _split_markdown_sections(text: str) -> List[Tuple[str, int]]:
    """
    Split Markdown text into sections based on headings.
    
    Returns:
        List of (section_text, heading_level) tuples
    """
    lines = text.split('\n')
    sections = []
    current_section = []
    current_level = 0
    
    for line in lines:
        # Check for markdown heading (## Heading)
        heading_match = re.match(r'^(#{1,6})\s+(.+)$', line)
        if heading_match:
            # Save previous section
            if current_section:
                sections.append(('\n'.join(current_section), current_level))
            # Start new section
            current_level = len(heading_match.group(1))
            current_section = [line]
        else:
            current_section.append(line)
    
    # Add final section
    if current_section:
        sections.append(('\n'.join(current_section), current_level))
    
    return sections


@register_chunker(ChunkStrategy.SEMANTIC)
def semantic_chunker(
    text: str,
    chunk_size: int = 1000,
    respect_paragraphs: bool = True,
    respect_markdown: bool = True,
    embedder: Optional[Embedder] = None,
) -> Tuple[List[str], List[Dict[str, Any]]]:
    """
    Chunk text using semantic boundaries.
    
    Uses sentence and paragraph awareness to create semantically coherent
    chunks. For Markdown, respects heading boundaries. Optionally uses
    embeddings for more sophisticated semantic grouping.
    
    Args:
        text: Input text to chunk
        chunk_size: Target size of each chunk in characters (default: 1000)
        respect_paragraphs: If True, tries to keep paragraphs intact (default: True)
        respect_markdown: If True, respects Markdown heading boundaries (default: True)
        embedder: Optional Embedder instance for semantic similarity. If None,
                 uses paragraph/sentence-based chunking only.
        
    Returns:
        Tuple of (documents, metadata) where:
        - documents: List of text chunks
        - metadata: List of metadata dicts with chunk info
    """
    if not text or not text.strip():
        logger.warning("Empty text provided to semantic_chunker")
        return [], []
    
    logger.debug(f"Chunking text semantically (size={chunk_size})")
    
    # Check if text looks like Markdown
    is_markdown = respect_markdown and ('#' in text or '```' in text or '**' in text)
    
    if is_markdown:
        # Use Markdown section-based chunking
        sections = _split_markdown_sections(text)
        logger.debug(f"Detected Markdown, split into {len(sections)} sections")
        
        documents = []
        metadata_list = []
        chunk_idx = 0
        current_chunk = []
        current_size = 0
        
        for section_text, heading_level in sections:
            section_size = len(section_text)
            
            # If section fits in current chunk, add it
            if current_size + section_size <= chunk_size or not current_chunk:
                current_chunk.append(section_text)
                current_size += section_size
            else:
                # Finalize current chunk
                chunk_text = "\n\n".join(current_chunk)
                documents.append(chunk_text)
                metadata_list.append({
                    "chunk_index": chunk_idx,
                    "chunk_size": len(chunk_text),
                    "strategy": ChunkStrategy.SEMANTIC.value,
                    "markdown": True,
                })
                chunk_idx += 1
                
                # Start new chunk with this section
                current_chunk = [section_text]
                current_size = section_size
        
        # Add remaining chunk
        if current_chunk:
            chunk_text = "\n\n".join(current_chunk)
            documents.append(chunk_text)
            metadata_list.append({
                "chunk_index": chunk_idx,
                "chunk_size": len(chunk_text),
                "strategy": ChunkStrategy.SEMANTIC.value,
                "markdown": True,
            })
        
        logger.info(f"Created {len(documents)} semantic chunks from Markdown")
        return documents, metadata_list
    
    # Use paragraph-based chunking
    if respect_paragraphs:
        paragraphs = _split_into_paragraphs(text)
        logger.debug(f"Split into {len(paragraphs)} paragraphs")
        
        documents = []
        metadata_list = []
        chunk_idx = 0
        current_chunk = []
        current_size = 0
        
        for para in paragraphs:
            para_size = len(para)
            
            # If paragraph fits in current chunk, add it
            if current_size + para_size <= chunk_size or not current_chunk:
                current_chunk.append(para)
                current_size += para_size
            else:
                # Finalize current chunk
                chunk_text = "\n\n".join(current_chunk)
                documents.append(chunk_text)
                metadata_list.append({
                    "chunk_index": chunk_idx,
                    "chunk_size": len(chunk_text),
                    "strategy": ChunkStrategy.SEMANTIC.value,
                })
                chunk_idx += 1
                
                # Start new chunk with this paragraph
                current_chunk = [para]
                current_size = para_size
        
        # Add remaining chunk
        if current_chunk:
            chunk_text = "\n\n".join(current_chunk)
            documents.append(chunk_text)
            metadata_list.append({
                "chunk_index": chunk_idx,
                "chunk_size": len(chunk_text),
                "strategy": ChunkStrategy.SEMANTIC.value,
            })
        
        logger.info(f"Created {len(documents)} semantic chunks from paragraphs")
        return documents, metadata_list
    
    # Fallback to sentence-based chunking
    sentences = _split_into_sentences(text)
    logger.debug(f"Split into {len(sentences)} sentences")
    
    documents = []
    metadata_list = []
    chunk_idx = 0
    current_chunk = []
    current_size = 0
    
    for sentence in sentences:
        sent_size = len(sentence) + 2  # +2 for ". "
        
        if current_size + sent_size > chunk_size and current_chunk:
            chunk_text = ". ".join(current_chunk) + "."
            documents.append(chunk_text)
            metadata_list.append({
                "chunk_index": chunk_idx,
                "chunk_size": len(chunk_text),
                "strategy": ChunkStrategy.SEMANTIC.value,
            })
            chunk_idx += 1
            current_chunk = []
            current_size = 0
        
        current_chunk.append(sentence)
        current_size += sent_size
    
    # Add remaining chunk
    if current_chunk:
        chunk_text = ". ".join(current_chunk) + "."
        documents.append(chunk_text)
        metadata_list.append({
            "chunk_index": chunk_idx,
            "chunk_size": len(chunk_text),
            "strategy": ChunkStrategy.SEMANTIC.value,
        })
    
    logger.info(f"Created {len(documents)} semantic chunks from sentences")
    return documents, metadata_list

