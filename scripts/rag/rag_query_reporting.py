#!/usr/bin/env python3
"""
RAG Database Query and Reporting Script

This script provides comprehensive query and reporting capabilities for the RAG database including:
- Semantic search and document retrieval
- Entity-based queries and analytics
- Content analysis and insights
- Performance reporting
- Export and data visualization
- Custom report generation
"""

import logging
import os
import sys
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
import json
from datetime import datetime, timedelta
import csv
from collections import defaultdict, Counter

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
        logging.FileHandler("rag_query_reporting.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()


class RAGQueryReporter:
    """Comprehensive query and reporting system for RAG database."""
    
    def __init__(self):
        """Initialize query reporter with database connection."""
        self.db_connection = None
        self._connect_to_database()
        logger.info("RAG Query Reporter initialized successfully")
    
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
    
    def semantic_search(self, query: str, limit: int = 10, threshold: float = 0.7) -> List[Dict[str, Any]]:
        """
        Perform semantic search using embeddings.
        
        Args:
            query: Search query text
            limit: Maximum number of results to return
            threshold: Minimum similarity threshold
            
        Returns:
            List of matching documents with similarity scores
        """
        logger.info(f"Performing semantic search for: '{query}'")
        
        # For this implementation, we'll use a placeholder query embedding
        # In a real implementation, this would use the same embedding model as the documents
        
        cursor = self.db_connection.cursor(cursor_factory=RealDictCursor)
        
        # Fallback to text search if no embeddings available
        cursor.execute("""
            SELECT d.id, d.title, d.content, d.source_url, d.source_type, d.created_at,
                   ts_rank(to_tsvector('english', d.content), plainto_tsquery('english', %s)) as text_rank
            FROM documents d
            WHERE NOT d.is_deleted
            AND to_tsvector('english', d.content) @@ plainto_tsquery('english', %s)
            ORDER BY text_rank DESC
            LIMIT %s
        """, (query, query, limit))
        
        results = []
        for row in cursor.fetchall():
            results.append({
                'document_id': row['id'],
                'title': row['title'],
                'content_preview': row['content'][:500] + '...' if len(row['content']) > 500 else row['content'],
                'source_url': row['source_url'],
                'source_type': row['source_type'],
                'created_at': row['created_at'].isoformat() if row['created_at'] else None,
                'similarity_score': float(row['text_rank']) if row['text_rank'] else 0.0,
                'search_method': 'text_search'
            })
        
        cursor.close()
        logger.info(f"Found {len(results)} documents matching query")
        return results
    
    def entity_search(self, entity_text: str = None, entity_type: str = None, 
                     limit: int = 50) -> List[Dict[str, Any]]:
        """
        Search for entities and related documents.
        
        Args:
            entity_text: Specific entity text to search for
            entity_type: Entity type/label to filter by
            limit: Maximum number of results
            
        Returns:
            List of entities with related document information
        """
        logger.info(f"Searching entities: text='{entity_text}', type='{entity_type}'")
        
        cursor = self.db_connection.cursor(cursor_factory=RealDictCursor)
        
        # Build query based on parameters
        where_conditions = []
        params = []
        
        if entity_text:
            where_conditions.append("e.text ILIKE %s")
            params.append(f"%{entity_text}%")
        
        if entity_type:
            where_conditions.append("e.label = %s")
            params.append(entity_type)
        
        where_clause = " AND ".join(where_conditions) if where_conditions else "TRUE"
        params.append(limit)
        
        cursor.execute(f"""
            SELECT e.id, e.text, e.label, e.kb_id, e.created_at,
                   COUNT(dem.document_id) as document_count,
                   ARRAY_AGG(DISTINCT d.title) FILTER (WHERE d.title IS NOT NULL) as related_documents
            FROM entities e
            LEFT JOIN document_entity_map dem ON e.id = dem.entity_id
            LEFT JOIN documents d ON dem.document_id = d.id AND NOT d.is_deleted
            WHERE {where_clause}
            GROUP BY e.id, e.text, e.label, e.kb_id, e.created_at
            ORDER BY document_count DESC, e.text
            LIMIT %s
        """, params)
        
        results = []
        for row in cursor.fetchall():
            results.append({
                'entity_id': row['id'],
                'text': row['text'],
                'label': row['label'],
                'kb_id': row['kb_id'],
                'created_at': row['created_at'].isoformat() if row['created_at'] else None,
                'document_count': row['document_count'],
                'related_documents': row['related_documents'][:5] if row['related_documents'] else []  # Limit to first 5
            })
        
        cursor.close()
        logger.info(f"Found {len(results)} entities matching criteria")
        return results
    
    def get_document_analytics(self, document_id: int = None) -> Dict[str, Any]:
        """
        Get analytics for specific document or all documents.
        
        Args:
            document_id: Specific document ID (optional)
            
        Returns:
            Dictionary containing document analytics
        """
        cursor = self.db_connection.cursor(cursor_factory=RealDictCursor)
        
        if document_id:
            logger.info(f"Getting analytics for document {document_id}")
            
            # Get document details
            cursor.execute("""
                SELECT d.id, d.title, d.content, d.source_type, d.source_url, d.created_at,
                       LENGTH(d.content) as content_length,
                       ARRAY_LENGTH(STRING_TO_ARRAY(d.content, ' '), 1) as word_count
                FROM documents d
                WHERE d.id = %s AND NOT d.is_deleted
            """, (document_id,))
            
            document = cursor.fetchone()
            if not document:
                raise ValueError(f"Document {document_id} not found")
            
            # Get related entities
            cursor.execute("""
                SELECT e.text, e.label, COUNT(*) as mention_count
                FROM entities e
                JOIN document_entity_map dem ON e.id = dem.entity_id
                WHERE dem.document_id = %s
                GROUP BY e.id, e.text, e.label
                ORDER BY mention_count DESC
            """, (document_id,))
            
            entities = cursor.fetchall()
            
            analytics = {
                'document_id': document['id'],
                'title': document['title'],
                'content_length': document['content_length'],
                'word_count': document['word_count'],
                'source_type': document['source_type'],
                'source_url': document['source_url'],
                'created_at': document['created_at'].isoformat() if document['created_at'] else None,
                'entity_count': len(entities),
                'entities': [dict(e) for e in entities],
                'estimated_reading_time': round((document['word_count'] or 0) / 200, 1)  # 200 WPM average
            }
            
        else:
            logger.info("Getting analytics for all documents")
            
            # Get overall statistics
            cursor.execute("""
                SELECT 
                    COUNT(*) as total_documents,
                    AVG(LENGTH(content)) as avg_content_length,
                    SUM(LENGTH(content)) as total_content_length,
                    COUNT(content_vector) as documents_with_embeddings
                FROM documents
                WHERE NOT is_deleted
            """)
            
            stats = cursor.fetchone()
            
            # Get source type distribution
            cursor.execute("""
                SELECT source_type, COUNT(*) as count
                FROM documents
                WHERE NOT is_deleted
                GROUP BY source_type
                ORDER BY count DESC
            """)
            
            source_distribution = cursor.fetchall()
            
            # Get entity statistics
            cursor.execute("""
                SELECT 
                    COUNT(*) as total_entities,
                    COUNT(DISTINCT label) as unique_entity_types,
                    COUNT(DISTINCT text) as unique_entities
                FROM entities
            """)
            
            entity_stats = cursor.fetchone()
            
            analytics = {
                'total_documents': stats['total_documents'],
                'avg_content_length': float(stats['avg_content_length']) if stats['avg_content_length'] else 0,
                'total_content_length': stats['total_content_length'],
                'documents_with_embeddings': stats['documents_with_embeddings'],
                'embedding_coverage': (stats['documents_with_embeddings'] / stats['total_documents']) if stats['total_documents'] > 0 else 0,
                'source_distribution': [dict(s) for s in source_distribution],
                'entity_statistics': dict(entity_stats)
            }
        
        cursor.close()
        return analytics
    
    def generate_content_insights(self, days_back: int = 30) -> Dict[str, Any]:
        """
        Generate content insights for the specified time period.
        
        Args:
            days_back: Number of days to look back for analysis
            
        Returns:
            Dictionary containing content insights
        """
        logger.info(f"Generating content insights for last {days_back} days")
        
        cursor = self.db_connection.cursor(cursor_factory=RealDictCursor)
        cutoff_date = datetime.now() - timedelta(days=days_back)
        
        # Get document creation trends
        cursor.execute("""
            SELECT DATE(created_at) as date, COUNT(*) as documents_created
            FROM documents
            WHERE created_at >= %s AND NOT is_deleted
            GROUP BY DATE(created_at)
            ORDER BY date
        """, (cutoff_date,))
        
        creation_trends = cursor.fetchall()
        
        # Get most common entity types
        cursor.execute("""
            SELECT e.label, COUNT(*) as count
            FROM entities e
            JOIN document_entity_map dem ON e.id = dem.entity_id
            JOIN documents d ON dem.document_id = d.id
            WHERE d.created_at >= %s AND NOT d.is_deleted
            GROUP BY e.label
            ORDER BY count DESC
            LIMIT 10
        """, (cutoff_date,))
        
        top_entity_types = cursor.fetchall()
        
        # Get most mentioned entities
        cursor.execute("""
            SELECT e.text, e.label, COUNT(*) as mention_count
            FROM entities e
            JOIN document_entity_map dem ON e.id = dem.entity_id
            JOIN documents d ON dem.document_id = d.id
            WHERE d.created_at >= %s AND NOT d.is_deleted
            GROUP BY e.id, e.text, e.label
            ORDER BY mention_count DESC
            LIMIT 20
        """, (cutoff_date,))
        
        top_entities = cursor.fetchall()
        
        # Get content length distribution
        cursor.execute("""
            SELECT 
                CASE 
                    WHEN LENGTH(content) < 1000 THEN 'Short (<1K)'
                    WHEN LENGTH(content) < 5000 THEN 'Medium (1K-5K)'
                    WHEN LENGTH(content) < 10000 THEN 'Long (5K-10K)'
                    ELSE 'Very Long (>10K)'
                END as length_category,
                COUNT(*) as count
            FROM documents
            WHERE created_at >= %s AND NOT is_deleted
            GROUP BY length_category
            ORDER BY count DESC
        """, (cutoff_date,))
        
        length_distribution = cursor.fetchall()
        
        insights = {
            'analysis_period': {
                'days_back': days_back,
                'start_date': cutoff_date.isoformat(),
                'end_date': datetime.now().isoformat()
            },
            'creation_trends': [dict(c) for c in creation_trends],
            'top_entity_types': [dict(e) for e in top_entity_types],
            'top_entities': [dict(e) for e in top_entities],
            'content_length_distribution': [dict(l) for l in length_distribution],
            'insights_generated_at': datetime.now().isoformat()
        }
        
        cursor.close()
        return insights
    
    def generate_performance_report(self) -> Dict[str, Any]:
        """
        Generate database performance and usage report.
        
        Returns:
            Dictionary containing performance metrics
        """
        logger.info("Generating performance report")
        
        cursor = self.db_connection.cursor(cursor_factory=RealDictCursor)
        
        # Get table sizes
        cursor.execute("""
            SELECT 
                schemaname,
                tablename,
                attname,
                n_distinct,
                correlation
            FROM pg_stats 
            WHERE schemaname = 'public' 
            AND tablename IN ('documents', 'entities', 'document_entity_map')
        """)
        
        table_stats = cursor.fetchall()
        
        # Get index usage
        cursor.execute("""
            SELECT 
                t.tablename,
                indexname,
                idx_tup_read,
                idx_tup_fetch,
                idx_scan
            FROM pg_stat_user_indexes i
            JOIN pg_stat_user_tables t ON i.relid = t.relid
            WHERE t.schemaname = 'public'
        """)
        
        index_usage = cursor.fetchall()
        
        # Get database size information
        cursor.execute("""
            SELECT 
                pg_size_pretty(pg_database_size(current_database())) as database_size,
                pg_size_pretty(pg_total_relation_size('documents')) as documents_table_size,
                pg_size_pretty(pg_total_relation_size('entities')) as entities_table_size
        """)
        
        size_info = cursor.fetchone()
        
        # Get recent query performance (if pg_stat_statements is available)
        try:
            cursor.execute("""
                SELECT query, calls, total_time, mean_time, rows
                FROM pg_stat_statements 
                WHERE query LIKE '%documents%' OR query LIKE '%entities%'
                ORDER BY total_time DESC
                LIMIT 10
            """)
            query_stats = cursor.fetchall()
        except:
            query_stats = []
        
        report = {
            'report_generated_at': datetime.now().isoformat(),
            'database_size_info': dict(size_info) if size_info else {},
            'table_statistics': [dict(s) for s in table_stats],
            'index_usage': [dict(i) for i in index_usage],
            'query_performance': [dict(q) for q in query_stats],
            'recommendations': self._generate_performance_recommendations(table_stats, index_usage)
        }
        
        cursor.close()
        return report
    
    def export_data(self, export_format: str = 'json', output_file: str = None, 
                   query: str = None) -> str:
        """
        Export data from the database.
        
        Args:
            export_format: Format for export ('json', 'csv')
            output_file: Output file path (optional)
            query: Custom SQL query (optional)
            
        Returns:
            Path to the exported file
        """
        if not output_file:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_file = f"rag_export_{timestamp}.{export_format}"
        
        logger.info(f"Exporting data to {output_file} in {export_format} format")
        
        cursor = self.db_connection.cursor(cursor_factory=RealDictCursor)
        
        if query:
            cursor.execute(query)
        else:
            # Default export query
            cursor.execute("""
                SELECT d.id, d.title, d.content, d.source_type, d.source_url, d.created_at,
                       STRING_AGG(e.text, '; ') as entities,
                       STRING_AGG(e.label, '; ') as entity_types
                FROM documents d
                LEFT JOIN document_entity_map dem ON d.id = dem.document_id
                LEFT JOIN entities e ON dem.entity_id = e.id
                WHERE NOT d.is_deleted
                GROUP BY d.id, d.title, d.content, d.source_type, d.source_url, d.created_at
                ORDER BY d.created_at DESC
            """)
        
        data = cursor.fetchall()
        
        if export_format.lower() == 'json':
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump([dict(row) for row in data], f, indent=2, default=str)
        
        elif export_format.lower() == 'csv':
            if data:
                with open(output_file, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.DictWriter(f, fieldnames=data[0].keys())
                    writer.writeheader()
                    for row in data:
                        writer.writerow(row)
        
        cursor.close()
        logger.info(f"Exported {len(data)} records to {output_file}")
        return output_file
    
    def create_custom_report(self, report_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a custom report based on configuration.
        
        Args:
            report_config: Configuration dictionary specifying report parameters
            
        Returns:
            Generated report data
        """
        logger.info("Creating custom report")
        
        report = {
            'report_name': report_config.get('name', 'Custom Report'),
            'generated_at': datetime.now().isoformat(),
            'config': report_config,
            'sections': {}
        }
        
        cursor = self.db_connection.cursor(cursor_factory=RealDictCursor)
        
        # Process each section in the report config
        for section_name, section_config in report_config.get('sections', {}).items():
            if section_config['type'] == 'query':
                cursor.execute(section_config['sql'], section_config.get('params', []))
                report['sections'][section_name] = [dict(row) for row in cursor.fetchall()]
            
            elif section_config['type'] == 'analytics':
                if section_config['analytics_type'] == 'document_stats':
                    report['sections'][section_name] = self.get_document_analytics()
                elif section_config['analytics_type'] == 'content_insights':
                    days_back = section_config.get('days_back', 30)
                    report['sections'][section_name] = self.generate_content_insights(days_back)
            
            elif section_config['type'] == 'search':
                search_results = self.semantic_search(
                    section_config['query'],
                    limit=section_config.get('limit', 10)
                )
                report['sections'][section_name] = search_results
        
        cursor.close()
        return report
    
    def _generate_performance_recommendations(self, table_stats: List[Dict], 
                                           index_usage: List[Dict]) -> List[str]:
        """Generate performance optimization recommendations."""
        recommendations = []
        
        # Check for unused indexes
        for index in index_usage:
            if index['idx_scan'] == 0:
                recommendations.append(f"Consider dropping unused index: {index['indexname']}")
        
        # Check for tables without proper indexing
        table_names = {stat['tablename'] for stat in table_stats}
        indexed_tables = {index['tablename'] for index in index_usage}
        
        for table in table_names:
            if table not in indexed_tables:
                recommendations.append(f"Consider adding indexes to table: {table}")
        
        # General recommendations
        recommendations.extend([
            "Run VACUUM ANALYZE regularly to update table statistics",
            "Monitor query performance and add indexes for slow queries",
            "Consider partitioning large tables for better performance"
        ])
        
        return recommendations
    
    def close(self):
        """Close database connection."""
        if self.db_connection:
            self.db_connection.close()
            logger.info("Database connection closed")


def main():
    """Main execution function."""
    import argparse
    
    parser = argparse.ArgumentParser(description="RAG Database Query and Reporting")
    parser.add_argument('--search', type=str, help='Perform semantic search')
    parser.add_argument('--entity-search', type=str, help='Search for entities')
    parser.add_argument('--entity-type', type=str, help='Filter entities by type')
    parser.add_argument('--document-analytics', type=int, help='Get analytics for specific document ID')
    parser.add_argument('--content-insights', type=int, default=30, help='Generate content insights (days back)')
    parser.add_argument('--performance-report', action='store_true', help='Generate performance report')
    parser.add_argument('--export', type=str, choices=['json', 'csv'], help='Export data format')
    parser.add_argument('--output', type=str, help='Output file path')
    parser.add_argument('--query', type=str, help='Custom SQL query for export')
    parser.add_argument('--limit', type=int, default=10, help='Limit number of results')
    
    args = parser.parse_args()
    
    reporter = RAGQueryReporter()
    
    try:
        if args.search:
            # Perform semantic search
            results = reporter.semantic_search(args.search, limit=args.limit)
            print("Search Results:")
            print(json.dumps(results, indent=2, default=str))
        
        elif args.entity_search:
            # Search entities
            results = reporter.entity_search(
                entity_text=args.entity_search,
                entity_type=args.entity_type,
                limit=args.limit
            )
            print("Entity Search Results:")
            print(json.dumps(results, indent=2, default=str))
        
        elif args.document_analytics is not None:
            # Get document analytics
            analytics = reporter.get_document_analytics(args.document_analytics)
            print("Document Analytics:")
            print(json.dumps(analytics, indent=2, default=str))
        
        elif args.content_insights:
            # Generate content insights
            insights = reporter.generate_content_insights(args.content_insights)
            print("Content Insights:")
            print(json.dumps(insights, indent=2, default=str))
        
        elif args.performance_report:
            # Generate performance report
            report = reporter.generate_performance_report()
            print("Performance Report:")
            print(json.dumps(report, indent=2, default=str))
        
        elif args.export:
            # Export data
            output_file = reporter.export_data(
                export_format=args.export,
                output_file=args.output,
                query=args.query
            )
            print(f"Data exported to: {output_file}")
        
        else:
            print("Please specify an operation. Use --help for available options.")
    
    finally:
        reporter.close()


if __name__ == "__main__":
    main()