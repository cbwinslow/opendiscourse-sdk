#!/usr/bin/env python3
"""
Lightweight RAG Script Integration

This script provides a lightweight integration layer that works with existing
dependencies and gradually adds NLP capabilities as dependencies become available.
"""

import logging
import os
import sys
import json
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

class LightweightRAGOperations:
    """Lightweight RAG operations that work with minimal dependencies."""
    
    def __init__(self):
        """Initialize with available dependencies."""
        self.available_features = self._check_available_features()
        logger.info(f"Initialized with features: {list(self.available_features.keys())}")
    
    def _check_available_features(self) -> Dict[str, bool]:
        """Check which features are available based on installed dependencies."""
        features = {}
        
        # Check database connectivity
        try:
            import psycopg2
            features['database'] = True
        except ImportError:
            features['database'] = False
            logger.warning("Database features disabled - psycopg2 not available")
        
        # Check NLP capabilities
        try:
            import spacy
            features['spacy_nlp'] = True
        except ImportError:
            features['spacy_nlp'] = False
            logger.warning("spaCy NLP features disabled - spacy not available")
        
        # Check embeddings
        try:
            from sentence_transformers import SentenceTransformer
            features['embeddings'] = True
        except ImportError:
            features['embeddings'] = False
            logger.warning("Embedding features disabled - sentence-transformers not available")
        
        # Check advanced analytics
        try:
            import numpy as np
            features['analytics'] = True
        except ImportError:
            features['analytics'] = False
            logger.warning("Analytics features disabled - numpy not available")
        
        return features
    
    def analyze_document_basic(self, content: str, document_id: str = None) -> Dict[str, Any]:
        """Basic document analysis using simple text processing."""
        try:
            # Basic text statistics
            words = content.split()
            sentences = content.split('.')
            
            analysis = {
                'document_id': document_id,
                'analysis_timestamp': datetime.now().isoformat(),
                'basic_stats': {
                    'character_count': len(content),
                    'word_count': len(words),
                    'sentence_count': len(sentences),
                    'avg_word_length': sum(len(word) for word in words) / len(words) if words else 0,
                    'avg_sentence_length': len(words) / len(sentences) if sentences else 0
                },
                'content_preview': content[:200] + '...' if len(content) > 200 else content
            }
            
            # Add advanced analysis if dependencies available
            if self.available_features.get('spacy_nlp'):
                analysis['nlp_analysis'] = self._analyze_with_spacy(content)
            
            if self.available_features.get('analytics'):
                analysis['advanced_metrics'] = self._calculate_advanced_metrics(content)
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error in basic document analysis: {e}")
            return {
                'document_id': document_id,
                'error': str(e),
                'analysis_timestamp': datetime.now().isoformat()
            }
    
    def _analyze_with_spacy(self, content: str) -> Dict[str, Any]:
        """Analyze content using spaCy if available."""
        try:
            import spacy
            nlp = spacy.load("en_core_web_sm")
            
            doc = nlp(content)
            
            return {
                'entities': [
                    {
                        'text': ent.text,
                        'label': ent.label_,
                        'start': ent.start_char,
                        'end': ent.end_char
                    }
                    for ent in doc.ents
                ],
                'noun_phrases': [chunk.text for chunk in doc.noun_chunks],
                'pos_tags': [(token.text, token.pos_) for token in doc if not token.is_space][:20]  # Limit output
            }
        except Exception as e:
            logger.warning(f"spaCy analysis failed: {e}")
            return {'error': str(e)}
    
    def _calculate_advanced_metrics(self, content: str) -> Dict[str, Any]:
        """Calculate advanced metrics using numpy if available."""
        try:
            import numpy as np
            
            # Basic readability metrics
            words = content.split()
            sentences = content.split('.')
            
            word_lengths = [len(word) for word in words]
            sentence_lengths = [len(sentence.split()) for sentence in sentences if sentence.strip()]
            
            return {
                'readability_metrics': {
                    'avg_word_length': float(np.mean(word_lengths)) if word_lengths else 0,
                    'std_word_length': float(np.std(word_lengths)) if word_lengths else 0,
                    'avg_sentence_length': float(np.mean(sentence_lengths)) if sentence_lengths else 0,
                    'std_sentence_length': float(np.std(sentence_lengths)) if sentence_lengths else 0
                },
                'complexity_score': self._calculate_complexity_score(words, sentences)
            }
        except Exception as e:
            logger.warning(f"Advanced metrics calculation failed: {e}")
            return {'error': str(e)}
    
    def _calculate_complexity_score(self, words: List[str], sentences: List[str]) -> float:
        """Calculate a simple complexity score."""
        if not words or not sentences:
            return 0.0
        
        # Simple complexity based on word length and sentence length
        avg_word_length = sum(len(word) for word in words) / len(words)
        avg_sentence_length = len(words) / len(sentences)
        
        # Normalize to 0-1 scale
        complexity = min(1.0, (avg_word_length / 10 + avg_sentence_length / 50) / 2)
        return round(complexity, 3)
    
    def extract_basic_entities(self, content: str) -> List[Dict[str, Any]]:
        """Extract basic entities using simple pattern matching."""
        import re
        
        entities = []
        
        # Simple patterns for common entity types
        patterns = {
            'EMAIL': r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
            'URL': r'https?://[^\s]+',
            'PHONE': r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b',
            'DATE': r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b',
            'CAPITALIZED': r'\b[A-Z][a-z]+(?:\s[A-Z][a-z]+)*\b'  # Potential proper nouns
        }
        
        for entity_type, pattern in patterns.items():
            matches = re.finditer(pattern, content)
            for match in matches:
                entities.append({
                    'text': match.group(),
                    'type': entity_type,
                    'start': match.start(),
                    'end': match.end(),
                    'confidence': 0.8 if entity_type != 'CAPITALIZED' else 0.5
                })
        
        return entities
    
    def validate_document_data(self, document_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate document data structure."""
        validation_result = {
            'is_valid': True,
            'issues': [],
            'validation_timestamp': datetime.now().isoformat()
        }
        
        # Check required fields
        required_fields = ['content', 'title']
        for field in required_fields:
            if not document_data.get(field):
                validation_result['issues'].append(f"Missing required field: {field}")
                validation_result['is_valid'] = False
        
        # Check content length
        content = document_data.get('content', '')
        if len(content) < 10:
            validation_result['issues'].append("Content is too short (minimum 10 characters)")
            validation_result['is_valid'] = False
        elif len(content) > 1000000:
            validation_result['issues'].append("Content is too long (maximum 1,000,000 characters)")
            validation_result['is_valid'] = False
        
        # Check title length
        title = document_data.get('title', '')
        if len(title) > 500:
            validation_result['issues'].append("Title is too long (maximum 500 characters)")
            validation_result['is_valid'] = False
        
        return validation_result
    
    def generate_basic_report(self, documents: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate a basic report from document data."""
        if not documents:
            return {
                'report_timestamp': datetime.now().isoformat(),
                'total_documents': 0,
                'error': 'No documents provided'
            }
        
        # Calculate basic statistics
        total_docs = len(documents)
        total_content_length = sum(len(doc.get('content', '')) for doc in documents)
        avg_content_length = total_content_length / total_docs if total_docs > 0 else 0
        
        # Source type distribution
        source_types = {}
        for doc in documents:
            source_type = doc.get('source_type', 'unknown')
            source_types[source_type] = source_types.get(source_type, 0) + 1
        
        # Recent documents (last 7 days)
        recent_threshold = datetime.now().timestamp() - (7 * 24 * 3600)
        recent_docs = 0
        for doc in documents:
            created_at = doc.get('created_at')
            if created_at:
                try:
                    if isinstance(created_at, str):
                        doc_time = datetime.fromisoformat(created_at.replace('Z', '+00:00')).timestamp()
                    else:
                        doc_time = created_at.timestamp()
                    
                    if doc_time > recent_threshold:
                        recent_docs += 1
                except:
                    pass
        
        return {
            'report_timestamp': datetime.now().isoformat(),
            'total_documents': total_docs,
            'total_content_length': total_content_length,
            'avg_content_length': round(avg_content_length, 2),
            'recent_documents_7_days': recent_docs,
            'source_type_distribution': source_types,
            'features_available': self.available_features
        }
    
    def process_document_complete(self, document_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process a document with all available features."""
        document_id = document_data.get('id', 'unknown')
        content = document_data.get('content', '')
        
        logger.info(f"Processing document {document_id}")
        
        result = {
            'document_id': document_id,
            'processing_timestamp': datetime.now().isoformat(),
            'validation': self.validate_document_data(document_data),
            'analysis': self.analyze_document_basic(content, document_id),
            'basic_entities': self.extract_basic_entities(content),
            'features_used': self.available_features
        }
        
        return result


def main():
    """Main execution function."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Lightweight RAG Operations")
    parser.add_argument('--analyze-text', type=str, help='Analyze given text')
    parser.add_argument('--extract-entities', type=str, help='Extract entities from text')
    parser.add_argument('--validate-json', type=str, help='Validate document from JSON file')
    parser.add_argument('--test-features', action='store_true', help='Test available features')
    
    args = parser.parse_args()
    
    rag_ops = LightweightRAGOperations()
    
    if args.test_features:
        print("Available Features:")
        print(json.dumps(rag_ops.available_features, indent=2))
    
    elif args.analyze_text:
        result = rag_ops.analyze_document_basic(args.analyze_text)
        print("Analysis Result:")
        print(json.dumps(result, indent=2, default=str))
    
    elif args.extract_entities:
        entities = rag_ops.extract_basic_entities(args.extract_entities)
        print("Extracted Entities:")
        print(json.dumps(entities, indent=2))
    
    elif args.validate_json:
        try:
            with open(args.validate_json, 'r') as f:
                doc_data = json.load(f)
            
            validation = rag_ops.validate_document_data(doc_data)
            print("Validation Result:")
            print(json.dumps(validation, indent=2))
        except Exception as e:
            print(f"Error reading JSON file: {e}")
    
    else:
        print("Please specify an operation. Use --help for available options.")


if __name__ == "__main__":
    main()