from typing import List, Tuple, Optional
import spacy
import logging
from dataclasses import dataclass

@dataclass
class ChunkMetadata:
    """Metadata for a document chunk including context and references"""
    start_pos: int
    end_pos: int
    preceding_context: Optional[str] = None
    following_context: Optional[str] = None
    references: List[Tuple[str, int]] = None  # (reference_text, position)

class DocumentChunker:
    """Handles document chunking with semantic awareness and context preservation"""
    
    def __init__(self):
        self.nlp = spacy.load("en_core_web_sm")
        self.logger = logging.getLogger(__name__)
        
    def _get_semantic_boundaries(self, doc: str) -> List[int]:
        """Find semantic chunk boundaries using NLP"""
        try:
            # Process with spaCy
            processed_doc = self.nlp(doc)
            
            # Get sentence boundaries
            boundaries = [sent.start_char for sent in processed_doc.sents]
            boundaries.append(len(doc))  # Add document end
            
            return boundaries
            
        except Exception as e:
            self.logger.error(f"Error finding semantic boundaries: {str(e)}")
            # Fallback to simple newline splitting
            return [0] + [i for i, char in enumerate(doc) if char == '\n'] + [len(doc)]

    def _extract_references(self, chunk: str) -> List[Tuple[str, int]]:
        """Extract references and their positions from a chunk"""
        try:
            doc = self.nlp(chunk)
            references = []
            
            # Look for reference patterns (e.g., "[1]", "Figure 1", "Table 2")
            for match in processed_doc.matcher(doc):
                span = doc[match[1]:match[2]]
                references.append((span.text, span.start_char))
            
            return references
            
        except Exception as e:
            self.logger.error(f"Error extracting references: {str(e)}")
            return []

    def _get_context_window(self, doc: str, start: int, end: int, 
                          context_size: int = 100) -> Tuple[str, str]:
        """Extract preceding and following context for a chunk"""
        # Get preceding context
        preceding_start = max(0, start - context_size)
        preceding = doc[preceding_start:start].strip()
        
        # Get following context
        following_end = min(len(doc), end + context_size)
        following = doc[end:following_end].strip()
        
        return preceding, following

    def chunk_document(self, doc: str, chunk_size: int) -> List[str]:
        """Split document into semantic chunks while maintaining context"""
        try:
            if not doc or chunk_size <= 0:
                raise ValueError("Invalid document or chunk size")

            # Get semantic boundaries
            boundaries = self._get_semantic_boundaries(doc)
            
            chunks = []
            current_chunk = []
            current_size = 0
            chunk_start = 0
            
            for boundary in boundaries:
                # Get the next sentence
                sentence = doc[chunk_start:boundary].strip()
                sentence_size = len(sentence)
                
                # If adding this sentence exceeds chunk size, save current chunk
                if current_size + sentence_size > chunk_size and current_chunk:
                    # Join current chunk
                    chunk_text = " ".join(current_chunk)
                    chunks.append(chunk_text)
                    
                    # Start new chunk
                    current_chunk = [sentence]
                    current_size = sentence_size
                else:
                    # Add sentence to current chunk
                    current_chunk.append(sentence)
                    current_size += sentence_size
                
                chunk_start = boundary
            
            # Add remaining text as last chunk
            if current_chunk:
                chunks.append(" ".join(current_chunk))
            
            return chunks
            
        except Exception as e:
            self.logger.error(f"Error chunking document: {str(e)}")
            # Fallback to simple chunking
            return [doc[i:i+chunk_size] for i in range(0, len(doc), chunk_size)]

    def chunk_document_with_metadata(self, doc: str, chunk_size: int) -> List[Tuple[str, ChunkMetadata]]:
        """Split document into chunks and return with metadata"""
        try:
            chunks = []
            doc_chunks = self.chunk_document(doc, chunk_size)
            
            current_pos = 0
            for chunk in doc_chunks:
                chunk_start = doc.find(chunk, current_pos)
                chunk_end = chunk_start + len(chunk)
                
                # Get context windows
                preceding, following = self._get_context_window(doc, chunk_start, chunk_end)
                
                # Extract references
                references = self._extract_references(chunk)
                
                # Create metadata
                metadata = ChunkMetadata(
                    start_pos=chunk_start,
                    end_pos=chunk_end,
                    preceding_context=preceding,
                    following_context=following,
                    references=references
                )
                
                chunks.append((chunk, metadata))
                current_pos = chunk_end
            
            return chunks
            
        except Exception as e:
            self.logger.error(f"Error chunking document with metadata: {str(e)}")
            # Return simple chunks without metadata
            return [(chunk, ChunkMetadata(0, len(chunk))) for chunk in self.chunk_document(doc, chunk_size)]
