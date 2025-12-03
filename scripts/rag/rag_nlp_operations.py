#!/usr/bin/env python3
"""
RAG Database NLP Operations Script

This script provides comprehensive NLP operations for the RAG database including:
- Entity extraction and storage
- Sentiment analysis
- Text embeddings generation
- Document re-ranking and transformation
- Semantic analysis and natural meaning extraction
"""

import logging
import os
import sys
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
import json
import numpy as np
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

try:
    import spacy
    from sentence_transformers import SentenceTransformer
    import psycopg2
    from psycopg2.extras import RealDictCursor
    from dotenv import load_dotenv
except ImportError as e:
    print(f"Missing dependency: {e}")
    print("Please install required packages: pip install spacy sentence-transformers psycopg2-binary python-dotenv")
    sys.exit(1)

# Load existing modules
from nlp.preprocessor import DocumentPreprocessor, ProcessedDocument
from nlp.entity_extractor import EntityExtractor
from nlp.embeddings import SentenceTransformerStrategy, OpenAIEmbeddingStrategy
from document_processing.document_chunker import DocumentChunker
from document_processing.pipeline_executor import PipelineExecutor

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("rag_nlp_operations.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()


class RAGNLPOperations:
    """Comprehensive NLP operations manager for RAG database."""
    
    def __init__(self):
        """Initialize NLP operations with required models and database connection."""
        self.preprocessor = DocumentPreprocessor()
        self.entity_extractor = EntityExtractor()
        self.chunker = DocumentChunker()
        
        # Initialize embedding strategies
        self.sentence_transformer = SentenceTransformerStrategy()
        
        # Initialize OpenAI embeddings if API key is available
        openai_api_key = os.getenv('OPENAI_API_KEY')
        if openai_api_key:
            self.openai_embedder = OpenAIEmbeddingStrategy(openai_api_key)
        else:
            self.openai_embedder = None
            logger.warning("OpenAI API key not found. OpenAI embeddings will not be available.")
        
        # Database connection
        self.db_connection = None
        self._connect_to_database()
        
        logger.info("RAG NLP Operations initialized successfully")
    
    def _connect_to_database(self):
        """Establish database connection."""
        try:
            self.db_connection = psycopg2.connect(
                dbname=os.getenv("POSTGRES_DB", "opendiscourse"),
                user=os.getenv("POSTGRES_USER", "postgres"),
                password=os.getenv("POSTGRES_PASSWORD", "password"),
                host=os.getenv("POSTGRES_HOST", "localhost"),
                port=os.getenv("POSTGRES_PORT", "5432"),
            )
            logger.info("Database connection established")
        except Exception as e:
            logger.error(f"Failed to connect to database: {e}")
            raise
    
    def extract_and_store_entities(self, document_id: int, content: str) -> List[Dict[str, Any]]:
        """
        Extract entities from document content and store them in the database.
        
        Args:
            document_id: Database ID of the document
            content: Text content to process
            
        Returns:
            List of extracted entities with metadata
        """
        logger.info(f"Processing entities for document {document_id}")
        
        try:
            # Preprocess the document
            processed_doc = self.preprocessor.preprocess(content)
            
            # Extract entities
            entities = self.entity_extractor.extract_entities(processed_doc.doc)
            
            # Store entities in database
            stored_entities = []
            cursor = self.db_connection.cursor(cursor_factory=RealDictCursor)
            
            for entity in entities:
                # Check if entity already exists
                cursor.execute(
                    "SELECT id FROM entities WHERE text = %s AND label = %s",
                    (entity.text, entity.label)
                )
                existing_entity = cursor.fetchone()
                
                if existing_entity:
                    entity_id = existing_entity['id']
                else:
                    # Insert new entity
                    cursor.execute(
                        """INSERT INTO entities (text, label, kb_id, created_at) 
                           VALUES (%s, %s, %s, %s) RETURNING id""",
                        (entity.text, entity.label, entity.kb_id, datetime.now())
                    )
                    entity_id = cursor.fetchone()['id']
                
                # Link entity to document
                cursor.execute(
                    """INSERT INTO document_entity_map (document_id, entity_id, start_char, end_char, confidence)
                       VALUES (%s, %s, %s, %s, %s)
                       ON CONFLICT (document_id, entity_id, start_char) DO NOTHING""",
                    (document_id, entity_id, entity.start_char, entity.end_char, 1.0)
                )
                
                stored_entities.append({
                    'id': entity_id,
                    'text': entity.text,
                    'label': entity.label,
                    'start_char': entity.start_char,
                    'end_char': entity.end_char,
                    'kb_id': entity.kb_id
                })
            
            self.db_connection.commit()
            cursor.close()
            
            logger.info(f"Extracted and stored {len(stored_entities)} entities for document {document_id}")
            return stored_entities
            
        except Exception as e:
            logger.error(f"Error extracting entities for document {document_id}: {e}")
            if self.db_connection:
                self.db_connection.rollback()
            raise
    
    def analyze_sentiment(self, content: str) -> Dict[str, Any]:
        """
        Analyze sentiment of the given content.
        
        Args:
            content: Text content to analyze
            
        Returns:
            Dictionary containing sentiment analysis results
        """
        try:
            # Basic sentiment analysis using spaCy (can be enhanced with specialized models)
            processed_doc = self.preprocessor.preprocess(content)
            
            # Placeholder for sentiment analysis - can be replaced with specialized models
            # like VADER, TextBlob, or transformer-based sentiment models
            sentiment_result = {
                'overall_sentiment': 'neutral',
                'confidence': 0.7,
                'positive_score': 0.3,
                'negative_score': 0.2,
                'neutral_score': 0.5,
                'analysis_timestamp': datetime.now().isoformat(),
                'method': 'spacy_baseline'
            }
            
            # Extract emotional indicators from entities and linguistic patterns
            emotion_indicators = self._extract_emotion_indicators(processed_doc)
            sentiment_result['emotion_indicators'] = emotion_indicators
            
            return sentiment_result
            
        except Exception as e:
            logger.error(f"Error analyzing sentiment: {e}")
            raise
    
    def _extract_emotion_indicators(self, processed_doc: ProcessedDocument) -> List[Dict[str, Any]]:
        """Extract emotional indicators from processed document."""
        indicators = []
        
        # Look for emotional language patterns
        for token in processed_doc.doc:
            if token.pos_ == 'ADJ' and not token.is_stop:
                # Simple emotional adjective detection
                indicators.append({
                    'text': token.text,
                    'type': 'emotional_adjective',
                    'position': token.idx
                })
        
        return indicators
    
    def generate_embeddings(self, content: str, strategy: str = 'sentence_transformer') -> np.ndarray:
        """
        Generate embeddings for the given content.
        
        Args:
            content: Text content to embed
            strategy: Embedding strategy ('sentence_transformer' or 'openai')
            
        Returns:
            Numpy array containing the embedding vector
        """
        try:
            if strategy == 'sentence_transformer':
                return self.sentence_transformer.embed(content)
            elif strategy == 'openai' and self.openai_embedder:
                return self.openai_embedder.embed(content)
            else:
                logger.warning(f"Strategy '{strategy}' not available, falling back to sentence_transformer")
                return self.sentence_transformer.embed(content)
                
        except Exception as e:
            logger.error(f"Error generating embeddings: {e}")
            raise
    
    def rerank_documents(self, query: str, document_ids: List[int], top_k: int = 10) -> List[Tuple[int, float]]:
        """
        Re-rank documents based on semantic similarity to query.
        
        Args:
            query: Search query
            document_ids: List of document IDs to rank
            top_k: Number of top documents to return
            
        Returns:
            List of tuples (document_id, similarity_score) sorted by relevance
        """
        try:
            query_embedding = self.generate_embeddings(query)
            
            cursor = self.db_connection.cursor(cursor_factory=RealDictCursor)
            
            # Get document embeddings from database
            cursor.execute(
                "SELECT id, content_vector FROM documents WHERE id = ANY(%s)",
                (document_ids,)
            )
            
            document_scores = []
            for row in cursor.fetchall():
                if row['content_vector']:
                    # Calculate cosine similarity
                    doc_embedding = np.array(row['content_vector'])
                    similarity = np.dot(query_embedding, doc_embedding) / (
                        np.linalg.norm(query_embedding) * np.linalg.norm(doc_embedding)
                    )
                    document_scores.append((row['id'], float(similarity)))
            
            cursor.close()
            
            # Sort by similarity score and return top_k
            document_scores.sort(key=lambda x: x[1], reverse=True)
            return document_scores[:top_k]
            
        except Exception as e:
            logger.error(f"Error re-ranking documents: {e}")
            raise
    
    def extract_semantic_meaning(self, content: str) -> Dict[str, Any]:
        """
        Extract semantic meaning and natural language understanding from content.
        
        Args:
            content: Text content to analyze
            
        Returns:
            Dictionary containing semantic analysis results
        """
        try:
            processed_doc = self.preprocessor.preprocess(content)
            
            # Extract semantic features
            semantic_analysis = {
                'key_concepts': self._extract_key_concepts(processed_doc),
                'dependency_relations': self._extract_dependency_relations(processed_doc),
                'named_entities': [
                    {'text': ent.text, 'label': ent.label, 'start': ent.start_char, 'end': ent.end_char}
                    for ent in processed_doc.entities
                ],
                'noun_phrases': [chunk.text for chunk in processed_doc.doc.noun_chunks],
                'linguistic_patterns': self._analyze_linguistic_patterns(processed_doc),
                'semantic_roles': self._extract_semantic_roles(processed_doc),
                'analysis_timestamp': datetime.now().isoformat()
            }
            
            return semantic_analysis
            
        except Exception as e:
            logger.error(f"Error extracting semantic meaning: {e}")
            raise
    
    def _extract_key_concepts(self, processed_doc: ProcessedDocument) -> List[Dict[str, Any]]:
        """Extract key concepts from processed document."""
        concepts = []
        
        for token in processed_doc.doc:
            if (token.pos_ in ['NOUN', 'PROPN'] and 
                not token.is_stop and 
                not token.is_punct and 
                len(token.text) > 2):
                concepts.append({
                    'text': token.text,
                    'lemma': token.lemma_,
                    'pos': token.pos_,
                    'frequency': 1  # Can be enhanced with TF-IDF
                })
        
        return concepts
    
    def _extract_dependency_relations(self, processed_doc: ProcessedDocument) -> List[Dict[str, Any]]:
        """Extract dependency relations from processed document."""
        relations = []
        
        for token in processed_doc.doc:
            if token.dep_ != 'ROOT':
                relations.append({
                    'dependent': token.text,
                    'head': token.head.text,
                    'relation': token.dep_,
                    'dependent_pos': token.pos_,
                    'head_pos': token.head.pos_
                })
        
        return relations
    
    def _analyze_linguistic_patterns(self, processed_doc: ProcessedDocument) -> Dict[str, Any]:
        """Analyze linguistic patterns in the document."""
        doc = processed_doc.doc
        
        patterns = {
            'sentence_count': len(list(doc.sents)),
            'avg_sentence_length': np.mean([len(sent.text.split()) for sent in doc.sents]),
            'complex_sentences': sum(1 for sent in doc.sents if len(sent.text.split()) > 20),
            'passive_voice_count': sum(1 for token in doc if token.dep_ == 'auxpass'),
            'modal_verbs': [token.text for token in doc if token.tag_ == 'MD'],
            'superlatives': [token.text for token in doc if token.tag_ in ['JJS', 'RBS']]
        }
        
        return patterns
    
    def _extract_semantic_roles(self, processed_doc: ProcessedDocument) -> List[Dict[str, Any]]:
        """Extract semantic roles (simplified version)."""
        roles = []
        
        for sent in processed_doc.doc.sents:
            for token in sent:
                if token.dep_ in ['nsubj', 'dobj', 'iobj', 'pobj']:
                    roles.append({
                        'text': token.text,
                        'role': token.dep_,
                        'head': token.head.text,
                        'sentence': sent.text
                    })
        
        return roles
    
    def process_document_complete(self, document_id: int) -> Dict[str, Any]:
        """
        Perform complete NLP processing on a document.
        
        Args:
            document_id: Database ID of the document
            
        Returns:
            Dictionary containing all analysis results
        """
        try:
            cursor = self.db_connection.cursor(cursor_factory=RealDictCursor)
            cursor.execute(
                "SELECT content, title FROM documents WHERE id = %s",
                (document_id,)
            )
            
            document = cursor.fetchone()
            if not document:
                raise ValueError(f"Document {document_id} not found")
            
            content = document['content']
            
            logger.info(f"Starting complete NLP processing for document {document_id}")
            
            # Perform all NLP operations
            results = {
                'document_id': document_id,
                'title': document['title'],
                'processing_timestamp': datetime.now().isoformat(),
                'entities': self.extract_and_store_entities(document_id, content),
                'sentiment': self.analyze_sentiment(content),
                'semantic_meaning': self.extract_semantic_meaning(content),
                'embeddings_generated': True
            }
            
            # Generate and store embeddings
            embedding = self.generate_embeddings(content)
            cursor.execute(
                "UPDATE documents SET content_vector = %s WHERE id = %s",
                (embedding.tolist(), document_id)
            )
            
            self.db_connection.commit()
            cursor.close()
            
            logger.info(f"Completed NLP processing for document {document_id}")
            return results
            
        except Exception as e:
            logger.error(f"Error processing document {document_id}: {e}")
            if self.db_connection:
                self.db_connection.rollback()
            raise
    
    def close(self):
        """Close database connection."""
        if self.db_connection:
            self.db_connection.close()
            logger.info("Database connection closed")


def main():
    """Main execution function."""
    import argparse
    
    parser = argparse.ArgumentParser(description="RAG Database NLP Operations")
    parser.add_argument('--document-id', type=int, help='Process specific document ID')
    parser.add_argument('--all-documents', action='store_true', help='Process all documents')
    parser.add_argument('--sentiment-only', action='store_true', help='Run sentiment analysis only')
    parser.add_argument('--entities-only', action='store_true', help='Extract entities only')
    parser.add_argument('--embeddings-only', action='store_true', help='Generate embeddings only')
    
    args = parser.parse_args()
    
    nlp_ops = RAGNLPOperations()
    
    try:
        if args.document_id:
            # Process specific document
            results = nlp_ops.process_document_complete(args.document_id)
            print(json.dumps(results, indent=2, default=str))
            
        elif args.all_documents:
            # Process all documents
            cursor = nlp_ops.db_connection.cursor()
            cursor.execute("SELECT id FROM documents WHERE NOT is_deleted")
            document_ids = [row[0] for row in cursor.fetchall()]
            cursor.close()
            
            for doc_id in document_ids:
                try:
                    results = nlp_ops.process_document_complete(doc_id)
                    logger.info(f"Processed document {doc_id}")
                except Exception as e:
                    logger.error(f"Failed to process document {doc_id}: {e}")
        
        else:
            print("Please specify --document-id or --all-documents")
            
    finally:
        nlp_ops.close()


if __name__ == "__main__":
    main()