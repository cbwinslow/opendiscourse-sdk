#!/usr/bin/env python3
"""
Government Data Ingestion Script for OpenDiscourse

This script fetches documents from govinfo.gov API and processes them
for the OpenDiscourse political document analysis platform.
"""

import os
import sys
import asyncio
import aiohttp
import json
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any
import logging
from dataclasses import dataclass
import spacy
from transformers import pipeline, AutoTokenizer, AutoModel
import torch
import numpy as np
from supabase import create_client, Client
import psycopg2
from psycopg2.extras import RealDictCursor

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class Document:
    """Document data structure"""
    id: str
    title: str
    content: str
    source: str
    document_type: str
    metadata: Dict[str, Any]
    url: str
    published_date: datetime

@dataclass
class Entity:
    """Entity data structure"""
    name: str
    entity_type: str
    confidence: float
    start_pos: int
    end_pos: int
    metadata: Dict[str, Any]

class GovInfoIngestor:
    """Handles document ingestion from govinfo.gov API"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv('GOVINFO_API_KEY')
        self.base_url = "https://api.govinfo.gov"
        self.session: Optional[aiohttp.ClientSession] = None
        
        # Initialize NLP components
        self.nlp = spacy.load("en_core_web_sm")
        self.tokenizer = AutoTokenizer.from_pretrained("sentence-transformers/all-mpnet-base-v2")
        self.model = AutoModel.from_pretrained("sentence-transformers/all-mpnet-base-v2")
        
        # Initialize Supabase client
        supabase_url = os.getenv('SUPABASE_URL', 'http://localhost:54321')
        supabase_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
        self.supabase: Client = create_client(supabase_url, supabase_key)
        
        # Initialize PostgreSQL connection
        self.pg_conn = psycopg2.connect(
            host=os.getenv('POSTGRES_HOST', 'localhost'),
            port=os.getenv('POSTGRES_PORT', '54322'),
            database=os.getenv('POSTGRES_DB', 'postgres'),
            user=os.getenv('POSTGRES_USER', 'postgres'),
            password=os.getenv('POSTGRES_PASSWORD', 'postgres')
        )

    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()
        if self.pg_conn:
            self.pg_conn.close()

    async def fetch_collection_documents(
        self, 
        collection: str, 
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Fetch documents from a specific govinfo collection"""
        
        if not start_date:
            start_date = datetime.now() - timedelta(days=30)
        if not end_date:
            end_date = datetime.now()
            
        params = {
            'collection': collection,
            'publishedDate': f"{start_date.strftime('%Y-%m-%d')}|{end_date.strftime('%Y-%m-%d')}",
            'pageSize': min(limit, 1000),
            'api_key': self.api_key
        }
        
        url = f"{self.base_url}/collections/{collection}/2024-01-01"
        
        logger.info(f"Fetching documents from {collection} between {start_date} and {end_date}")
        
        try:
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get('packages', [])
                else:
                    logger.error(f"API request failed with status {response.status}")
                    return []
        except Exception as e:
            logger.error(f"Error fetching documents: {str(e)}")
            return []

    async def fetch_document_content(self, package_id: str) -> Optional[str]:
        """Fetch full text content of a document"""
        
        # Try different content formats
        content_types = ['xml', 'txt', 'pdf']
        
        for content_type in content_types:
            url = f"{self.base_url}/packages/{package_id}/{content_type}"
            params = {'api_key': self.api_key} if self.api_key else {}
            
            try:
                async with self.session.get(url, params=params) as response:
                    if response.status == 200:
                        if content_type == 'xml':
                            content = await response.text()
                            return self.extract_text_from_xml(content)
                        elif content_type == 'txt':
                            return await response.text()
                        elif content_type == 'pdf':
                            # For PDF, we would need additional processing
                            logger.info(f"PDF content found for {package_id}, skipping for now")
                            continue
            except Exception as e:
                logger.warning(f"Failed to fetch {content_type} for {package_id}: {str(e)}")
                continue
        
        return None

    def extract_text_from_xml(self, xml_content: str) -> str:
        """Extract readable text from XML content"""
        try:
            root = ET.fromstring(xml_content)
            text_parts = []
            
            # Extract text from various XML elements
            for elem in root.iter():
                if elem.text and elem.text.strip():
                    text_parts.append(elem.text.strip())
            
            return ' '.join(text_parts)
        except ET.ParseError as e:
            logger.error(f"XML parsing error: {str(e)}")
            return xml_content  # Return raw content if parsing fails

    def extract_entities(self, text: str) -> List[Entity]:
        """Extract named entities from text using spaCy"""
        doc = self.nlp(text)
        entities = []
        
        for ent in doc.ents:
            entity = Entity(
                name=ent.text,
                entity_type=ent.label_,
                confidence=1.0,  # spaCy doesn't provide confidence scores
                start_pos=ent.start_char,
                end_pos=ent.end_char,
                metadata={
                    'description': spacy.explain(ent.label_),
                    'lemma': ent.lemma_
                }
            )
            entities.append(entity)
        
        return entities

    def generate_embeddings(self, text: str) -> np.ndarray:
        """Generate embeddings for document text"""
        # Tokenize and encode
        encoded = self.tokenizer(
            text, 
            truncation=True, 
            padding=True, 
            max_length=512, 
            return_tensors='pt'
        )
        
        # Generate embeddings
        with torch.no_grad():
            outputs = self.model(**encoded)
            embeddings = outputs.last_hidden_state.mean(dim=1)
        
        return embeddings.numpy().flatten()

    async def process_document(self, doc_data: Dict[str, Any]) -> Optional[Document]:
        """Process a single document from govinfo API"""
        
        package_id = doc_data.get('packageId')
        if not package_id:
            return None
        
        logger.info(f"Processing document: {package_id}")
        
        # Fetch full content
        content = await self.fetch_document_content(package_id)
        if not content:
            logger.warning(f"No content found for {package_id}")
            return None
        
        # Create document object
        document = Document(
            id=package_id,
            title=doc_data.get('title', 'Untitled'),
            content=content,
            source='govinfo.gov',
            document_type=doc_data.get('docClass', 'unknown'),
            metadata={
                'collection': doc_data.get('collectionCode'),
                'congress': doc_data.get('congress'),
                'session': doc_data.get('session'),
                'chamber': doc_data.get('chamber'),
                'categories': doc_data.get('category', []),
                'gov_id': package_id
            },
            url=doc_data.get('packageLink', ''),
            published_date=datetime.fromisoformat(
                doc_data.get('dateIssued', datetime.now().isoformat())
            )
        )
        
        return document

    async def store_document(self, document: Document) -> bool:
        """Store document in Supabase and PostgreSQL"""
        try:
            # Extract entities
            entities = self.extract_entities(document.content)
            
            # Generate embeddings
            embeddings = self.generate_embeddings(document.content)
            
            # Store in Supabase
            doc_data = {
                'id': document.id,
                'title': document.title,
                'content': document.content,
                'source': document.source,
                'document_type': document.document_type,
                'metadata': document.metadata,
                'url': document.url,
                'published_date': document.published_date.isoformat(),
                'created_at': datetime.now().isoformat(),
                'processed': True,
                'embedding': embeddings.tolist()
            }
            
            result = self.supabase.table('documents').upsert(doc_data).execute()
            
            # Store entities
            for entity in entities:
                entity_data = {
                    'document_id': document.id,
                    'name': entity.name,
                    'entity_type': entity.entity_type,
                    'confidence': entity.confidence,
                    'start_pos': entity.start_pos,
                    'end_pos': entity.end_pos,
                    'metadata': entity.metadata,
                    'created_at': datetime.now().isoformat()
                }
                
                self.supabase.table('entities').insert(entity_data).execute()
            
            logger.info(f"Successfully stored document {document.id} with {len(entities)} entities")
            return True
            
        except Exception as e:
            logger.error(f"Error storing document {document.id}: {str(e)}")
            return False

    async def ingest_collection(
        self, 
        collection: str, 
        days_back: int = 30,
        max_documents: int = 100
    ) -> Dict[str, int]:
        """Ingest documents from a specific collection"""
        
        start_date = datetime.now() - timedelta(days=days_back)
        end_date = datetime.now()
        
        logger.info(f"Starting ingestion for collection: {collection}")
        
        # Fetch document list
        doc_list = await self.fetch_collection_documents(
            collection, start_date, end_date, max_documents
        )
        
        stats = {
            'fetched': len(doc_list),
            'processed': 0,
            'stored': 0,
            'errors': 0
        }
        
        # Process each document
        for doc_data in doc_list[:max_documents]:
            try:
                document = await self.process_document(doc_data)
                if document:
                    stats['processed'] += 1
                    if await self.store_document(document):
                        stats['stored'] += 1
                    else:
                        stats['errors'] += 1
                else:
                    stats['errors'] += 1
                    
            except Exception as e:
                logger.error(f"Error processing document: {str(e)}")
                stats['errors'] += 1
        
        logger.info(f"Ingestion complete for {collection}: {stats}")
        return stats

async def main():
    """Main ingestion function"""
    
    # Collections to ingest
    collections = [
        'BILLS',      # Congressional Bills
        'CREC',       # Congressional Record
        'FR',         # Federal Register
        'CFR',        # Code of Federal Regulations
        'GOVPUB',     # Government Publications
    ]
    
    # Check environment variables
    required_env_vars = ['SUPABASE_URL', 'SUPABASE_SERVICE_ROLE_KEY']
    missing_vars = [var for var in required_env_vars if not os.getenv(var)]
    
    if missing_vars:
        logger.error(f"Missing required environment variables: {missing_vars}")
        sys.exit(1)
    
    # Initialize ingester
    async with GovInfoIngestor() as ingestor:
        overall_stats = {}
        
        for collection in collections:
            try:
                stats = await ingestor.ingest_collection(
                    collection, 
                    days_back=7,  # Last week
                    max_documents=50  # Limit for demo
                )
                overall_stats[collection] = stats
                
                # Add delay between collections to be nice to the API
                await asyncio.sleep(2)
                
            except Exception as e:
                logger.error(f"Failed to ingest collection {collection}: {str(e)}")
                overall_stats[collection] = {'error': str(e)}
        
        # Print summary
        print("\n" + "="*50)
        print("INGESTION SUMMARY")
        print("="*50)
        for collection, stats in overall_stats.items():
            print(f"{collection}: {stats}")
        print("="*50)

if __name__ == "__main__":
    asyncio.run(main())