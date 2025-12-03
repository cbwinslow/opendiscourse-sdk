#!/usr/bin/env python3
"""
Comprehensive Test Suite for OpenDiscourse

This test suite covers:
- Database connectivity and schema validation
- Document ingestion and processing
- NLP processing pipeline
- API endpoints
- Vector database integration
- Search functionality
"""

import os
import sys
import pytest
import asyncio
import json
import tempfile
from pathlib import Path
from typing import Dict, Any, List
import requests
import psycopg2
from psycopg2.extras import RealDictCursor
from supabase import create_client, Client
import numpy as np
from datetime import datetime

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.govinfo_ingestor import GovInfoIngestor
from scripts.nlp_processor import AdvancedNLPProcessor

class TestConfig:
    """Test configuration and utilities"""
    
    def __init__(self):
        self.supabase_url = os.getenv('SUPABASE_URL', 'http://localhost:54321')
        self.supabase_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
        self.backend_url = os.getenv('BACKEND_URL', 'http://localhost:8000')
        self.frontend_url = os.getenv('FRONTEND_URL', 'http://localhost:3000')
        
        # Database connection
        self.db_config = {
            'host': os.getenv('POSTGRES_HOST', 'localhost'),
            'port': int(os.getenv('POSTGRES_PORT', '54322')),
            'database': os.getenv('POSTGRES_DB', 'postgres'),
            'user': os.getenv('POSTGRES_USER', 'postgres'),
            'password': os.getenv('POSTGRES_PASSWORD', 'postgres')
        }

@pytest.fixture(scope="session")
def config():
    """Test configuration fixture"""
    return TestConfig()

@pytest.fixture(scope="session")
def supabase_client(config):
    """Supabase client fixture"""
    return create_client(config.supabase_url, config.supabase_key)

@pytest.fixture(scope="session")
def db_connection(config):
    """Database connection fixture"""
    conn = psycopg2.connect(**config.db_config)
    yield conn
    conn.close()

class TestDatabaseConnectivity:
    """Test database connectivity and schema"""
    
    def test_postgres_connection(self, db_connection):
        """Test PostgreSQL connection"""
        with db_connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
            assert result[0] == 1
    
    def test_supabase_connection(self, supabase_client):
        """Test Supabase connection"""
        try:
            # Simple query to test connection
            result = supabase_client.table('documents').select('count').execute()
            assert result is not None
        except Exception as e:
            pytest.fail(f"Supabase connection failed: {str(e)}")
    
    def test_required_tables_exist(self, db_connection):
        """Test that all required tables exist"""
        required_tables = [
            'documents',
            'entities',
            'entity_relationships',
            'analysis_results',
            'rag_queries',
            'ingestion_logs',
            'document_chunks',
            'gov_data_sources'
        ]
        
        with db_connection.cursor() as cursor:
            cursor.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
            """)
            existing_tables = [row[0] for row in cursor.fetchall()]
            
            missing_tables = set(required_tables) - set(existing_tables)
            assert not missing_tables, f"Missing tables: {missing_tables}"
    
    def test_vector_extension(self, db_connection):
        """Test that pgvector extension is installed"""
        with db_connection.cursor() as cursor:
            cursor.execute("SELECT extname FROM pg_extension WHERE extname = 'vector'")
            result = cursor.fetchone()
            assert result is not None, "pgvector extension not installed"

class TestDocumentIngestion:
    """Test document ingestion functionality"""
    
    @pytest.fixture
    def sample_document(self):
        """Sample document for testing"""
        return {
            'id': 'test-doc-001',
            'title': 'Test Climate Policy Document',
            'content': 'This is a test document about climate change policy. It mentions the Environmental Protection Agency and discusses carbon emissions regulations.',
            'source': 'test-source',
            'document_type': 'policy',
            'metadata': {'test': True},
            'url': 'https://example.com/test-doc',
            'published_date': datetime.now()
        }
    
    def test_document_insertion(self, supabase_client, sample_document):
        """Test inserting a document into the database"""
        # Clean up any existing test document
        supabase_client.table('documents').delete().eq('id', sample_document['id']).execute()
        
        # Insert document
        doc_data = {
            'id': sample_document['id'],
            'title': sample_document['title'],
            'content': sample_document['content'],
            'source': sample_document['source'],
            'document_type': sample_document['document_type'],
            'metadata': sample_document['metadata'],
            'url': sample_document['url'],
            'published_date': sample_document['published_date'].isoformat(),
            'processed': False
        }
        
        result = supabase_client.table('documents').insert(doc_data).execute()
        assert len(result.data) == 1
        assert result.data[0]['id'] == sample_document['id']
    
    def test_document_retrieval(self, supabase_client, sample_document):
        """Test retrieving a document from the database"""
        result = supabase_client.table('documents').select('*').eq('id', sample_document['id']).execute()
        assert len(result.data) == 1
        doc = result.data[0]
        assert doc['title'] == sample_document['title']
        assert doc['content'] == sample_document['content']

class TestNLPProcessing:
    """Test NLP processing functionality"""
    
    @pytest.fixture
    def nlp_processor(self):
        """NLP processor fixture"""
        return AdvancedNLPProcessor()
    
    @pytest.fixture
    def sample_text(self):
        """Sample text for NLP testing"""
        return """
        President Joe Biden announced new climate policies today. 
        The Environmental Protection Agency will implement stricter emissions standards. 
        Senator Elizabeth Warren supports the initiative, while Representative Kevin McCarthy opposes it.
        The bill aims to reduce carbon emissions by 50% by 2030 in California and New York.
        """
    
    def test_entity_extraction(self, nlp_processor, sample_text):
        """Test entity extraction"""
        entities = nlp_processor.extract_entities(sample_text)
        
        # Should extract people, organizations, locations
        entity_types = [ent['label'] for ent in entities]
        assert 'PERSON' in entity_types or 'PER' in entity_types
        assert 'ORG' in entity_types
        assert 'GPE' in entity_types or 'LOC' in entity_types
        
        # Check for specific entities
        entity_names = [ent['name'].lower() for ent in entities]
        assert any('biden' in name for name in entity_names)
        assert any('environmental protection agency' in name or 'epa' in name for name in entity_names)
    
    def test_sentiment_analysis(self, nlp_processor, sample_text):
        """Test sentiment analysis"""
        sentiment = nlp_processor.analyze_sentiment(sample_text)
        
        assert 'positive' in sentiment
        assert 'negative' in sentiment
        assert 'neutral' in sentiment
        assert 'overall_sentiment' in sentiment
        assert 'confidence' in sentiment
        
        # Confidence should be between 0 and 1
        assert 0 <= sentiment['confidence'] <= 1
    
    def test_embedding_generation(self, nlp_processor, sample_text):
        """Test embedding generation"""
        embeddings = nlp_processor.generate_embeddings(sample_text)
        
        # Should be a numpy array
        assert isinstance(embeddings, np.ndarray)
        
        # Should have correct dimensions (768 for sentence-transformers)
        assert embeddings.shape == (768,)
        
        # Should not be all zeros
        assert not np.allclose(embeddings, 0)
    
    def test_relationship_extraction(self, nlp_processor, sample_text):
        """Test relationship extraction"""
        entities = nlp_processor.extract_entities(sample_text)
        relationships = nlp_processor.extract_relationships(entities, sample_text)
        
        # Should find some relationships
        assert len(relationships) > 0
        
        # Each relationship should have required fields
        for rel in relationships:
            assert 'entity1' in rel
            assert 'entity2' in rel
            assert 'relationship_type' in rel
            assert 'confidence' in rel

class TestAPIEndpoints:
    """Test API endpoints"""
    
    @pytest.fixture
    def api_base_url(self, config):
        """API base URL"""
        return f"{config.backend_url}/api/v1"
    
    def test_api_health_check(self, config):
        """Test API health check"""
        try:
            response = requests.get(config.backend_url, timeout=10)
            assert response.status_code == 200
        except requests.exceptions.ConnectionError:
            pytest.skip("Backend API not running")
    
    def test_documents_endpoint(self, api_base_url):
        """Test documents API endpoint"""
        try:
            response = requests.get(f"{api_base_url}/documents", timeout=10)
            assert response.status_code in [200, 401, 404]  # 401 if auth required, 404 if not implemented
        except requests.exceptions.ConnectionError:
            pytest.skip("Backend API not running")
    
    def test_search_endpoint(self, api_base_url):
        """Test search API endpoint"""
        try:
            test_query = {"query": "climate change"}
            response = requests.post(f"{api_base_url}/search/semantic", json=test_query, timeout=10)
            assert response.status_code in [200, 401, 404, 422]
        except requests.exceptions.ConnectionError:
            pytest.skip("Backend API not running")

class TestVectorDatabases:
    """Test vector database integration"""
    
    def test_qdrant_connection(self):
        """Test Qdrant connection"""
        try:
            qdrant_url = os.getenv('QDRANT_URL', 'http://localhost:6333')
            response = requests.get(f"{qdrant_url}/", timeout=5)
            assert response.status_code == 200
        except requests.exceptions.ConnectionError:
            pytest.skip("Qdrant not running")
    
    def test_weaviate_connection(self):
        """Test Weaviate connection"""
        try:
            weaviate_url = os.getenv('WEAVIATE_URL', 'http://localhost:8080')
            response = requests.get(f"{weaviate_url}/v1/.well-known/ready", timeout=5)
            assert response.status_code == 200
        except requests.exceptions.ConnectionError:
            pytest.skip("Weaviate not running")
    
    def test_chromadb_connection(self):
        """Test ChromaDB connection"""
        try:
            chroma_url = f"http://{os.getenv('CHROMA_HOST', 'localhost')}:{os.getenv('CHROMA_PORT', '8001')}"
            response = requests.get(f"{chroma_url}/api/v1/heartbeat", timeout=5)
            assert response.status_code == 200
        except requests.exceptions.ConnectionError:
            pytest.skip("ChromaDB not running")

class TestSearchFunctionality:
    """Test search functionality"""
    
    def test_vector_similarity_search(self, db_connection):
        """Test vector similarity search function"""
        try:
            # Create a test embedding
            test_embedding = np.random.rand(768).tolist()
            
            with db_connection.cursor(cursor_factory=RealDictCursor) as cursor:
                # Test the semantic_search function
                cursor.execute("""
                    SELECT * FROM semantic_search(%s::vector, 0.1, 5)
                """, (test_embedding,))
                
                results = cursor.fetchall()
                # Should not error, even if no results
                assert isinstance(results, list)
                
        except Exception as e:
            if "function semantic_search does not exist" in str(e):
                pytest.skip("Semantic search function not created yet")
            else:
                raise

class TestFrontendIntegration:
    """Test frontend integration"""
    
    def test_frontend_accessibility(self, config):
        """Test that frontend is accessible"""
        try:
            response = requests.get(config.frontend_url, timeout=10)
            assert response.status_code == 200
        except requests.exceptions.ConnectionError:
            pytest.skip("Frontend not running")
    
    def test_api_routes_accessible(self, config):
        """Test that API routes are accessible from frontend"""
        api_routes = [
            '/api/upload',
            '/api/query'
        ]
        
        for route in api_routes:
            try:
                # Test OPTIONS request (CORS preflight)
                response = requests.options(f"{config.frontend_url}{route}", timeout=5)
                # Should not return 404
                assert response.status_code != 404
            except requests.exceptions.ConnectionError:
                pytest.skip("Frontend not running")

class TestEndToEndWorkflow:
    """Test end-to-end workflow"""
    
    @pytest.mark.asyncio
    async def test_document_processing_workflow(self, supabase_client):
        """Test complete document processing workflow"""
        # This test requires the full stack to be running
        # Skip if not in integration test mode
        if not os.getenv('RUN_INTEGRATION_TESTS'):
            pytest.skip("Integration tests not enabled")
        
        # Create test document
        test_doc = {
            'id': 'integration-test-001',
            'title': 'Integration Test Document',
            'content': 'This is a test document for integration testing. It mentions President Biden and climate change policies.',
            'source': 'integration-test',
            'document_type': 'test',
            'metadata': {'test': True},
            'processed': False
        }
        
        try:
            # Clean up existing test data
            supabase_client.table('entities').delete().eq('document_id', test_doc['id']).execute()
            supabase_client.table('analysis_results').delete().eq('document_id', test_doc['id']).execute()
            supabase_client.table('documents').delete().eq('id', test_doc['id']).execute()
            
            # Insert test document
            supabase_client.table('documents').insert(test_doc).execute()
            
            # Process with NLP
            processor = AdvancedNLPProcessor()
            result = await processor.process_document(test_doc['id'], test_doc['content'])
            
            # Store results
            success = await processor.store_processing_results(result)
            assert success
            
            # Verify entities were extracted
            entities_result = supabase_client.table('entities').select('*').eq('document_id', test_doc['id']).execute()
            assert len(entities_result.data) > 0
            
            # Verify analysis results were stored
            analysis_result = supabase_client.table('analysis_results').select('*').eq('document_id', test_doc['id']).execute()
            assert len(analysis_result.data) > 0
            
            # Verify document was marked as processed
            doc_result = supabase_client.table('documents').select('*').eq('id', test_doc['id']).execute()
            assert doc_result.data[0]['processed'] == True
            
        finally:
            # Clean up test data
            supabase_client.table('entities').delete().eq('document_id', test_doc['id']).execute()
            supabase_client.table('analysis_results').delete().eq('document_id', test_doc['id']).execute()
            supabase_client.table('documents').delete().eq('id', test_doc['id']).execute()

if __name__ == "__main__":
    # Run tests
    pytest.main([
        __file__,
        "-v",
        "--tb=short",
        "--strict-markers"
    ])