#!/usr/bin/env python3
"""
RAG Database Data Management Script

This script provides comprehensive data management operations for the RAG database including:
- Data validation and cleaning
- Database migration utilities
- Data quality assessment
- Duplicate detection and removal
- Schema validation and updates
- Performance optimization
"""

import logging
import os
import sys
from typing import List, Dict, Any, Optional, Tuple, Set
from pathlib import Path
import json
import re
from datetime import datetime, timedelta
import hashlib

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

try:
    import psycopg2
    from psycopg2.extras import RealDictCursor
    from dotenv import load_dotenv
    import numpy as np
except ImportError as e:
    print(f"Missing dependency: {e}")
    print("Please install required packages: pip install psycopg2-binary python-dotenv numpy")
    sys.exit(1)

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("rag_data_management.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()


class RAGDataManager:
    """Comprehensive data management for RAG database."""
    
    def __init__(self):
        """Initialize data manager with database connection."""
        self.db_connection = None
        self._connect_to_database()
        self.validation_rules = self._load_validation_rules()
        logger.info("RAG Data Manager initialized successfully")
    
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
    
    def _load_validation_rules(self) -> Dict[str, Any]:
        """Load data validation rules."""
        return {
            'documents': {
                'required_fields': ['content', 'title'],
                'min_content_length': 10,
                'max_content_length': 1000000,
                'allowed_source_types': ['web', 'api', 'file', 'scraper'],
                'title_max_length': 500
            },
            'entities': {
                'required_fields': ['text', 'label'],
                'min_text_length': 1,
                'max_text_length': 200,
                'allowed_labels': [
                    'PERSON', 'ORG', 'GPE', 'LOC', 'PRODUCT', 'EVENT',
                    'WORK_OF_ART', 'LAW', 'LANGUAGE', 'DATE', 'TIME',
                    'PERCENT', 'MONEY', 'QUANTITY', 'ORDINAL', 'CARDINAL'
                ]
            },
            'embeddings': {
                'required_dimensions': [384, 512, 768, 1024, 1536],  # Common embedding dimensions
                'vector_norm_tolerance': 0.1
            }
        }
    
    def validate_documents(self) -> Dict[str, Any]:
        """
        Validate all documents in the database.
        
        Returns:
            Dictionary containing validation results
        """
        logger.info("Starting document validation")
        
        cursor = self.db_connection.cursor(cursor_factory=RealDictCursor)
        cursor.execute("SELECT * FROM documents")
        documents = cursor.fetchall()
        
        validation_results = {
            'total_documents': len(documents),
            'valid_documents': 0,
            'invalid_documents': 0,
            'issues': [],
            'validation_timestamp': datetime.now().isoformat()
        }
        
        rules = self.validation_rules['documents']
        
        for doc in documents:
            doc_issues = []
            
            # Check required fields
            for field in rules['required_fields']:
                if not doc.get(field) or doc[field].strip() == '':
                    doc_issues.append(f"Missing or empty required field: {field}")
            
            # Validate content length
            if doc.get('content'):
                content_length = len(doc['content'])
                if content_length < rules['min_content_length']:
                    doc_issues.append(f"Content too short: {content_length} characters")
                elif content_length > rules['max_content_length']:
                    doc_issues.append(f"Content too long: {content_length} characters")
            
            # Validate title length
            if doc.get('title') and len(doc['title']) > rules['title_max_length']:
                doc_issues.append(f"Title too long: {len(doc['title'])} characters")
            
            # Validate source type
            if doc.get('source_type') and doc['source_type'] not in rules['allowed_source_types']:
                doc_issues.append(f"Invalid source type: {doc['source_type']}")
            
            # Check for malformed URLs
            if doc.get('source_url'):
                if not self._is_valid_url(doc['source_url']):
                    doc_issues.append(f"Malformed URL: {doc['source_url']}")
            
            # Check for suspicious content patterns
            if doc.get('content'):
                if self._has_suspicious_patterns(doc['content']):
                    doc_issues.append("Content contains suspicious patterns")
            
            if doc_issues:
                validation_results['invalid_documents'] += 1
                validation_results['issues'].append({
                    'document_id': doc['id'],
                    'title': doc.get('title', 'No title'),
                    'issues': doc_issues
                })
            else:
                validation_results['valid_documents'] += 1
        
        cursor.close()
        logger.info(f"Document validation completed. Valid: {validation_results['valid_documents']}, "
                   f"Invalid: {validation_results['invalid_documents']}")
        
        return validation_results
    
    def validate_entities(self) -> Dict[str, Any]:
        """
        Validate all entities in the database.
        
        Returns:
            Dictionary containing validation results
        """
        logger.info("Starting entity validation")
        
        cursor = self.db_connection.cursor(cursor_factory=RealDictCursor)
        cursor.execute("SELECT * FROM entities")
        entities = cursor.fetchall()
        
        validation_results = {
            'total_entities': len(entities),
            'valid_entities': 0,
            'invalid_entities': 0,
            'issues': [],
            'validation_timestamp': datetime.now().isoformat()
        }
        
        rules = self.validation_rules['entities']
        
        for entity in entities:
            entity_issues = []
            
            # Check required fields
            for field in rules['required_fields']:
                if not entity.get(field) or entity[field].strip() == '':
                    entity_issues.append(f"Missing or empty required field: {field}")
            
            # Validate text length
            if entity.get('text'):
                text_length = len(entity['text'])
                if text_length < rules['min_text_length']:
                    entity_issues.append(f"Text too short: {text_length} characters")
                elif text_length > rules['max_text_length']:
                    entity_issues.append(f"Text too long: {text_length} characters")
            
            # Validate label
            if entity.get('label') and entity['label'] not in rules['allowed_labels']:
                entity_issues.append(f"Invalid label: {entity['label']}")
            
            # Check for malformed text
            if entity.get('text'):
                if not self._is_valid_entity_text(entity['text']):
                    entity_issues.append("Entity text contains invalid characters")
            
            if entity_issues:
                validation_results['invalid_entities'] += 1
                validation_results['issues'].append({
                    'entity_id': entity['id'],
                    'text': entity.get('text', 'No text'),
                    'label': entity.get('label', 'No label'),
                    'issues': entity_issues
                })
            else:
                validation_results['valid_entities'] += 1
        
        cursor.close()
        logger.info(f"Entity validation completed. Valid: {validation_results['valid_entities']}, "
                   f"Invalid: {validation_results['invalid_entities']}")
        
        return validation_results
    
    def validate_embeddings(self) -> Dict[str, Any]:
        """
        Validate embeddings in the database.
        
        Returns:
            Dictionary containing validation results
        """
        logger.info("Starting embedding validation")
        
        cursor = self.db_connection.cursor(cursor_factory=RealDictCursor)
        cursor.execute("SELECT id, content_vector FROM documents WHERE content_vector IS NOT NULL")
        documents_with_embeddings = cursor.fetchall()
        
        validation_results = {
            'total_embeddings': len(documents_with_embeddings),
            'valid_embeddings': 0,
            'invalid_embeddings': 0,
            'issues': [],
            'validation_timestamp': datetime.now().isoformat()
        }
        
        rules = self.validation_rules['embeddings']
        
        for doc in documents_with_embeddings:
            embedding_issues = []
            
            try:
                embedding = np.array(doc['content_vector'])
                
                # Check dimension
                if embedding.shape[0] not in rules['required_dimensions']:
                    embedding_issues.append(f"Invalid embedding dimension: {embedding.shape[0]}")
                
                # Check for NaN or infinite values
                if np.any(np.isnan(embedding)) or np.any(np.isinf(embedding)):
                    embedding_issues.append("Embedding contains NaN or infinite values")
                
                # Check vector norm (should be close to 1 for normalized embeddings)
                norm = np.linalg.norm(embedding)
                if abs(norm - 1.0) > rules['vector_norm_tolerance']:
                    embedding_issues.append(f"Embedding not normalized, norm: {norm}")
                
                # Check for zero vectors
                if np.allclose(embedding, 0):
                    embedding_issues.append("Embedding is zero vector")
                
            except Exception as e:
                embedding_issues.append(f"Error processing embedding: {str(e)}")
            
            if embedding_issues:
                validation_results['invalid_embeddings'] += 1
                validation_results['issues'].append({
                    'document_id': doc['id'],
                    'issues': embedding_issues
                })
            else:
                validation_results['valid_embeddings'] += 1
        
        cursor.close()
        logger.info(f"Embedding validation completed. Valid: {validation_results['valid_embeddings']}, "
                   f"Invalid: {validation_results['invalid_embeddings']}")
        
        return validation_results
    
    def detect_duplicates(self, similarity_threshold: float = 0.95) -> Dict[str, Any]:
        """
        Detect duplicate documents based on content similarity.
        
        Args:
            similarity_threshold: Threshold for considering documents as duplicates
            
        Returns:
            Dictionary containing duplicate detection results
        """
        logger.info("Starting duplicate detection")
        
        cursor = self.db_connection.cursor(cursor_factory=RealDictCursor)
        cursor.execute("""
            SELECT id, title, content, 
                   md5(content) as content_hash,
                   content_vector
            FROM documents 
            WHERE NOT is_deleted
        """)
        documents = cursor.fetchall()
        
        duplicates = {
            'exact_duplicates': [],
            'similar_documents': [],
            'hash_duplicates': [],
            'detection_timestamp': datetime.now().isoformat()
        }
        
        # Group by content hash for exact duplicates
        hash_groups = {}
        for doc in documents:
            content_hash = doc['content_hash']
            if content_hash not in hash_groups:
                hash_groups[content_hash] = []
            hash_groups[content_hash].append(doc)
        
        # Find hash-based duplicates
        for content_hash, docs in hash_groups.items():
            if len(docs) > 1:
                duplicates['hash_duplicates'].append({
                    'content_hash': content_hash,
                    'documents': [{'id': d['id'], 'title': d['title']} for d in docs],
                    'count': len(docs)
                })
        
        # Find similar documents using embeddings
        docs_with_embeddings = [d for d in documents if d['content_vector']]
        
        for i, doc1 in enumerate(docs_with_embeddings):
            for doc2 in docs_with_embeddings[i+1:]:
                if doc1['id'] != doc2['id']:
                    try:
                        embedding1 = np.array(doc1['content_vector'])
                        embedding2 = np.array(doc2['content_vector'])
                        
                        # Calculate cosine similarity
                        similarity = np.dot(embedding1, embedding2) / (
                            np.linalg.norm(embedding1) * np.linalg.norm(embedding2)
                        )
                        
                        if similarity >= similarity_threshold:
                            duplicates['similar_documents'].append({
                                'document1': {'id': doc1['id'], 'title': doc1['title']},
                                'document2': {'id': doc2['id'], 'title': doc2['title']},
                                'similarity': float(similarity)
                            })
                    except Exception as e:
                        logger.warning(f"Error calculating similarity between docs {doc1['id']} and {doc2['id']}: {e}")
        
        cursor.close()
        logger.info(f"Duplicate detection completed. Hash duplicates: {len(duplicates['hash_duplicates'])}, "
                   f"Similar documents: {len(duplicates['similar_documents'])}")
        
        return duplicates
    
    def clean_data(self, dry_run: bool = True) -> Dict[str, Any]:
        """
        Clean and normalize data in the database.
        
        Args:
            dry_run: If True, only report what would be cleaned without making changes
            
        Returns:
            Dictionary containing cleaning results
        """
        logger.info(f"Starting data cleaning (dry_run={dry_run})")
        
        cleaning_results = {
            'operations_performed': [],
            'items_cleaned': 0,
            'cleaning_timestamp': datetime.now().isoformat(),
            'dry_run': dry_run
        }
        
        cursor = self.db_connection.cursor(cursor_factory=RealDictCursor)
        
        # Clean document content
        cursor.execute("SELECT id, content, title FROM documents WHERE NOT is_deleted")
        documents = cursor.fetchall()
        
        for doc in documents:
            cleaned_content = self._clean_text(doc['content'])
            cleaned_title = self._clean_text(doc['title']) if doc['title'] else None
            
            if cleaned_content != doc['content'] or cleaned_title != doc['title']:
                if not dry_run:
                    cursor.execute(
                        "UPDATE documents SET content = %s, title = %s WHERE id = %s",
                        (cleaned_content, cleaned_title, doc['id'])
                    )
                
                cleaning_results['operations_performed'].append({
                    'type': 'document_cleaning',
                    'document_id': doc['id'],
                    'changes': {
                        'content_changed': cleaned_content != doc['content'],
                        'title_changed': cleaned_title != doc['title']
                    }
                })
                cleaning_results['items_cleaned'] += 1
        
        # Clean entity text
        cursor.execute("SELECT id, text FROM entities")
        entities = cursor.fetchall()
        
        for entity in entities:
            cleaned_text = self._clean_entity_text(entity['text'])
            
            if cleaned_text != entity['text']:
                if not dry_run:
                    cursor.execute(
                        "UPDATE entities SET text = %s WHERE id = %s",
                        (cleaned_text, entity['id'])
                    )
                
                cleaning_results['operations_performed'].append({
                    'type': 'entity_cleaning',
                    'entity_id': entity['id'],
                    'original_text': entity['text'],
                    'cleaned_text': cleaned_text
                })
                cleaning_results['items_cleaned'] += 1
        
        if not dry_run:
            self.db_connection.commit()
        
        cursor.close()
        logger.info(f"Data cleaning completed. Items cleaned: {cleaning_results['items_cleaned']}")
        
        return cleaning_results
    
    def migrate_schema(self, target_version: str) -> Dict[str, Any]:
        """
        Migrate database schema to target version.
        
        Args:
            target_version: Target schema version
            
        Returns:
            Dictionary containing migration results
        """
        logger.info(f"Starting schema migration to version {target_version}")
        
        migration_results = {
            'target_version': target_version,
            'migration_timestamp': datetime.now().isoformat(),
            'operations_performed': [],
            'success': False
        }
        
        cursor = self.db_connection.cursor()
        
        try:
            # Get current schema version
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS schema_version (
                    version VARCHAR(50) PRIMARY KEY,
                    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            cursor.execute("SELECT version FROM schema_version ORDER BY applied_at DESC LIMIT 1")
            current_version = cursor.fetchone()
            current_version = current_version[0] if current_version else "0.0.0"
            
            logger.info(f"Current schema version: {current_version}")
            
            # Apply migrations based on target version
            if target_version == "1.1.0" and current_version < "1.1.0":
                self._apply_migration_1_1_0(cursor, migration_results)
            
            if target_version == "1.2.0" and current_version < "1.2.0":
                self._apply_migration_1_2_0(cursor, migration_results)
            
            # Update schema version
            cursor.execute(
                "INSERT INTO schema_version (version) VALUES (%s) ON CONFLICT (version) DO NOTHING",
                (target_version,)
            )
            
            self.db_connection.commit()
            migration_results['success'] = True
            
        except Exception as e:
            self.db_connection.rollback()
            migration_results['error'] = str(e)
            logger.error(f"Schema migration failed: {e}")
            raise
        
        finally:
            cursor.close()
        
        logger.info(f"Schema migration completed successfully")
        return migration_results
    
    def _apply_migration_1_1_0(self, cursor, migration_results):
        """Apply migration to version 1.1.0 - Add indexing and performance improvements."""
        
        # Add vector index for faster similarity searches
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_documents_content_vector 
            ON documents USING ivfflat (content_vector vector_cosine_ops) 
            WITH (lists = 100)
        """)
        migration_results['operations_performed'].append("Added vector index for documents")
        
        # Add full-text search index
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_documents_content_fts 
            ON documents USING gin(to_tsvector('english', content))
        """)
        migration_results['operations_performed'].append("Added full-text search index")
        
        # Add entity performance indexes
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_entities_text ON entities(text)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_entities_label ON entities(label)")
        migration_results['operations_performed'].append("Added entity indexes")
    
    def _apply_migration_1_2_0(self, cursor, migration_results):
        """Apply migration to version 1.2.0 - Add analytics and metadata tables."""
        
        # Add document analytics table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS document_analytics (
                id SERIAL PRIMARY KEY,
                document_id INTEGER REFERENCES documents(id),
                sentiment_score FLOAT,
                complexity_score FLOAT,
                readability_score FLOAT,
                topic_keywords TEXT[],
                analysis_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        migration_results['operations_performed'].append("Added document analytics table")
        
        # Add processing metadata table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS processing_metadata (
                id SERIAL PRIMARY KEY,
                document_id INTEGER REFERENCES documents(id),
                processing_stage VARCHAR(50),
                started_at TIMESTAMP,
                completed_at TIMESTAMP,
                status VARCHAR(20),
                error_message TEXT,
                metadata JSONB
            )
        """)
        migration_results['operations_performed'].append("Added processing metadata table")
    
    def generate_quality_report(self) -> Dict[str, Any]:
        """
        Generate comprehensive data quality report.
        
        Returns:
            Dictionary containing quality metrics and recommendations
        """
        logger.info("Generating data quality report")
        
        report = {
            'generation_timestamp': datetime.now().isoformat(),
            'validation_results': {},
            'duplicate_analysis': {},
            'statistics': {},
            'recommendations': []
        }
        
        # Run validations
        report['validation_results']['documents'] = self.validate_documents()
        report['validation_results']['entities'] = self.validate_entities()
        report['validation_results']['embeddings'] = self.validate_embeddings()
        
        # Run duplicate detection
        report['duplicate_analysis'] = self.detect_duplicates()
        
        # Generate statistics
        report['statistics'] = self._generate_statistics()
        
        # Generate recommendations
        report['recommendations'] = self._generate_recommendations(report)
        
        logger.info("Data quality report generated successfully")
        return report
    
    def _generate_statistics(self) -> Dict[str, Any]:
        """Generate database statistics."""
        cursor = self.db_connection.cursor(cursor_factory=RealDictCursor)
        
        stats = {}
        
        # Document statistics
        cursor.execute("SELECT COUNT(*) as total, COUNT(content_vector) as with_embeddings FROM documents WHERE NOT is_deleted")
        doc_stats = cursor.fetchone()
        stats['documents'] = {
            'total': doc_stats['total'],
            'with_embeddings': doc_stats['with_embeddings'],
            'embedding_coverage': doc_stats['with_embeddings'] / doc_stats['total'] if doc_stats['total'] > 0 else 0
        }
        
        # Entity statistics
        cursor.execute("SELECT COUNT(*) as total, COUNT(DISTINCT label) as unique_labels FROM entities")
        entity_stats = cursor.fetchone()
        stats['entities'] = {
            'total': entity_stats['total'],
            'unique_labels': entity_stats['unique_labels']
        }
        
        # Get most common entity types
        cursor.execute("SELECT label, COUNT(*) as count FROM entities GROUP BY label ORDER BY count DESC LIMIT 10")
        stats['entities']['top_labels'] = [{'label': row['label'], 'count': row['count']} for row in cursor.fetchall()]
        
        cursor.close()
        return stats
    
    def _generate_recommendations(self, report: Dict[str, Any]) -> List[str]:
        """Generate recommendations based on quality report."""
        recommendations = []
        
        # Document recommendations
        doc_validation = report['validation_results']['documents']
        if doc_validation['invalid_documents'] > 0:
            recommendations.append(f"Fix {doc_validation['invalid_documents']} invalid documents")
        
        # Embedding recommendations
        embedding_coverage = report['statistics']['documents']['embedding_coverage']
        if embedding_coverage < 0.9:
            recommendations.append(f"Generate embeddings for remaining documents (current coverage: {embedding_coverage:.1%})")
        
        # Duplicate recommendations
        if report['duplicate_analysis']['hash_duplicates']:
            recommendations.append(f"Remove {len(report['duplicate_analysis']['hash_duplicates'])} sets of duplicate documents")
        
        # Performance recommendations
        recommendations.append("Consider running VACUUM ANALYZE on database tables")
        recommendations.append("Monitor query performance and add indexes as needed")
        
        return recommendations
    
    def _clean_text(self, text: str) -> str:
        """Clean and normalize text content."""
        if not text:
            return text
        
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove non-printable characters
        text = ''.join(char for char in text if char.isprintable() or char.isspace())
        
        # Normalize quotes
        text = text.replace('"', '"').replace('"', '"')
        text = text.replace(''', "'").replace(''', "'")
        
        # Strip leading/trailing whitespace
        text = text.strip()
        
        return text
    
    def _clean_entity_text(self, text: str) -> str:
        """Clean entity text."""
        if not text:
            return text
        
        # Remove leading/trailing whitespace
        text = text.strip()
        
        # Remove non-alphanumeric characters except spaces, hyphens, and apostrophes
        text = re.sub(r'[^\w\s\-\']', '', text)
        
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)
        
        return text
    
    def _is_valid_url(self, url: str) -> bool:
        """Check if URL is valid format."""
        url_pattern = re.compile(
            r'^https?://'  # http:// or https://
            r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain...
            r'localhost|'  # localhost...
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
            r'(?::\d+)?'  # optional port
            r'(?:/?|[/?]\S+)$', re.IGNORECASE)
        return url_pattern.match(url) is not None
    
    def _has_suspicious_patterns(self, content: str) -> bool:
        """Check for suspicious patterns in content."""
        suspicious_patterns = [
            r'<script.*?</script>',  # Script tags
            r'javascript:',  # JavaScript URLs
            r'data:image/',  # Data URLs
            r'eval\s*\(',  # eval() calls
            r'onclick\s*=',  # onclick handlers
        ]
        
        for pattern in suspicious_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                return True
        
        return False
    
    def _is_valid_entity_text(self, text: str) -> bool:
        """Check if entity text is valid."""
        if not text or len(text.strip()) == 0:
            return False
        
        # Check for control characters
        if any(ord(char) < 32 and char not in '\t\n\r' for char in text):
            return False
        
        return True
    
    def close(self):
        """Close database connection."""
        if self.db_connection:
            self.db_connection.close()
            logger.info("Database connection closed")


def main():
    """Main execution function."""
    import argparse
    
    parser = argparse.ArgumentParser(description="RAG Database Data Management")
    parser.add_argument('--validate', action='store_true', help='Run validation on all data')
    parser.add_argument('--detect-duplicates', action='store_true', help='Detect duplicate documents')
    parser.add_argument('--clean', action='store_true', help='Clean and normalize data')
    parser.add_argument('--migrate', type=str, help='Migrate schema to specified version')
    parser.add_argument('--quality-report', action='store_true', help='Generate comprehensive quality report')
    parser.add_argument('--dry-run', action='store_true', help='Perform dry run (no actual changes)')
    
    args = parser.parse_args()
    
    data_manager = RAGDataManager()
    
    try:
        if args.validate:
            # Run all validations
            doc_results = data_manager.validate_documents()
            entity_results = data_manager.validate_entities()
            embedding_results = data_manager.validate_embeddings()
            
            print("Document Validation Results:")
            print(json.dumps(doc_results, indent=2))
            print("\nEntity Validation Results:")
            print(json.dumps(entity_results, indent=2))
            print("\nEmbedding Validation Results:")
            print(json.dumps(embedding_results, indent=2))
        
        elif args.detect_duplicates:
            # Detect duplicates
            duplicate_results = data_manager.detect_duplicates()
            print("Duplicate Detection Results:")
            print(json.dumps(duplicate_results, indent=2, default=str))
        
        elif args.clean:
            # Clean data
            cleaning_results = data_manager.clean_data(dry_run=args.dry_run)
            print("Data Cleaning Results:")
            print(json.dumps(cleaning_results, indent=2))
        
        elif args.migrate:
            # Migrate schema
            migration_results = data_manager.migrate_schema(args.migrate)
            print("Migration Results:")
            print(json.dumps(migration_results, indent=2))
        
        elif args.quality_report:
            # Generate quality report
            quality_report = data_manager.generate_quality_report()
            print("Data Quality Report:")
            print(json.dumps(quality_report, indent=2, default=str))
        
        else:
            print("Please specify an operation: --validate, --detect-duplicates, --clean, --migrate, or --quality-report")
    
    finally:
        data_manager.close()


if __name__ == "__main__":
    main()