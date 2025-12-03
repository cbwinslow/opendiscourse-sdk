#!/usr/bin/env python3
"""
NLP Processing Pipeline for OpenDiscourse

This script handles advanced NLP processing including:
- Entity extraction and classification
- Sentiment analysis
- Topic modeling
- Relationship extraction
- Content summarization
"""

import os
import sys
import logging
from typing import Dict, List, Any, Tuple, Optional
from dataclasses import dataclass
import spacy
from spacy import displacy
import pandas as pd
import numpy as np
from transformers import (
    AutoTokenizer, AutoModel, AutoModelForSequenceClassification,
    pipeline, AutoModelForTokenClassification
)
import torch
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.decomposition import LatentDirichletAllocation
from sklearn.cluster import KMeans
import networkx as nx
from supabase import create_client, Client
import asyncio
import json
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class ProcessingResult:
    """Results from NLP processing"""
    document_id: str
    entities: List[Dict[str, Any]]
    sentiment: Dict[str, float]
    topics: List[Dict[str, Any]]
    summary: str
    relationships: List[Dict[str, Any]]
    embeddings: np.ndarray
    metadata: Dict[str, Any]

class AdvancedNLPProcessor:
    """Advanced NLP processing for political documents"""
    
    def __init__(self):
        logger.info("Initializing NLP processor...")
        
        # Load spaCy model with extensions
        self.nlp = spacy.load("en_core_web_sm")
        
        # Load transformers models
        self.tokenizer = AutoTokenizer.from_pretrained("sentence-transformers/all-mpnet-base-v2")
        self.embedding_model = AutoModel.from_pretrained("sentence-transformers/all-mpnet-base-v2")
        
        # Sentiment analysis
        self.sentiment_analyzer = pipeline(
            "sentiment-analysis",
            model="cardiffnlp/twitter-roberta-base-sentiment-latest",
            return_all_scores=True
        )
        
        # Named Entity Recognition for political entities
        self.political_ner = pipeline(
            "ner",
            model="dbmdz/bert-large-cased-finetuned-conll03-english",
            aggregation_strategy="simple"
        )
        
        # Summarization
        self.summarizer = pipeline(
            "summarization",
            model="facebook/bart-large-cnn",
            max_length=150,
            min_length=50
        )
        
        # Initialize topic modeling components
        self.tfidf_vectorizer = TfidfVectorizer(
            max_features=1000,
            stop_words='english',
            ngram_range=(1, 2)
        )
        self.lda_model = LatentDirichletAllocation(
            n_components=10,
            random_state=42
        )
        
        # Initialize Supabase client
        supabase_url = os.getenv('SUPABASE_URL', 'http://localhost:54321')
        supabase_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
        self.supabase: Client = create_client(supabase_url, supabase_key)
        
        logger.info("NLP processor initialized successfully")

    def extract_entities(self, text: str) -> List[Dict[str, Any]]:
        """Extract and classify entities using multiple models"""
        entities = []
        
        # spaCy NER
        doc = self.nlp(text)
        for ent in doc.ents:
            entity = {
                'name': ent.text,
                'label': ent.label_,
                'description': spacy.explain(ent.label_),
                'start': ent.start_char,
                'end': ent.end_char,
                'confidence': 1.0,  # spaCy doesn't provide confidence
                'source': 'spacy'
            }
            entities.append(entity)
        
        # Political NER using transformers
        try:
            political_entities = self.political_ner(text)
            for ent in political_entities:
                entity = {
                    'name': ent['word'],
                    'label': ent['entity_group'],
                    'description': f"Political entity: {ent['entity_group']}",
                    'start': ent['start'],
                    'end': ent['end'],
                    'confidence': ent['score'],
                    'source': 'transformers'
                }
                entities.append(entity)
        except Exception as e:
            logger.warning(f"Political NER failed: {str(e)}")
        
        # Deduplicate entities
        unique_entities = []
        seen_entities = set()
        
        for entity in entities:
            entity_key = (entity['name'].lower(), entity['label'])
            if entity_key not in seen_entities:
                seen_entities.add(entity_key)
                unique_entities.append(entity)
        
        return unique_entities

    def analyze_sentiment(self, text: str) -> Dict[str, float]:
        """Perform detailed sentiment analysis"""
        try:
            # Split text into chunks for better analysis
            chunks = [text[i:i+500] for i in range(0, len(text), 500)]
            
            sentiments = []
            for chunk in chunks[:10]:  # Limit to avoid rate limits
                result = self.sentiment_analyzer(chunk)
                sentiments.extend(result)
            
            # Aggregate results
            label_scores = {'positive': [], 'negative': [], 'neutral': []}
            
            for sentiment_batch in sentiments:
                for sentiment in sentiment_batch:
                    label = sentiment['label'].lower()
                    if 'pos' in label:
                        label_scores['positive'].append(sentiment['score'])
                    elif 'neg' in label:
                        label_scores['negative'].append(sentiment['score'])
                    else:
                        label_scores['neutral'].append(sentiment['score'])
            
            # Calculate averages
            result = {}
            for label, scores in label_scores.items():
                result[label] = np.mean(scores) if scores else 0.0
            
            # Determine overall sentiment
            max_sentiment = max(result.keys(), key=lambda k: result[k])
            result['overall_sentiment'] = max_sentiment
            result['confidence'] = result[max_sentiment]
            
            return result
            
        except Exception as e:
            logger.error(f"Sentiment analysis failed: {str(e)}")
            return {
                'positive': 0.0,
                'negative': 0.0,
                'neutral': 1.0,
                'overall_sentiment': 'neutral',
                'confidence': 0.0
            }

    def extract_topics(self, documents: List[str]) -> List[Dict[str, Any]]:
        """Extract topics using LDA topic modeling"""
        try:
            if len(documents) < 2:
                return []
            
            # Vectorize documents
            tfidf_matrix = self.tfidf_vectorizer.fit_transform(documents)
            
            # Fit LDA model
            lda_result = self.lda_model.fit_transform(tfidf_matrix)
            
            # Extract topics
            feature_names = self.tfidf_vectorizer.get_feature_names_out()
            topics = []
            
            for topic_idx, topic in enumerate(self.lda_model.components_):
                top_words_idx = topic.argsort()[-10:][::-1]
                top_words = [feature_names[i] for i in top_words_idx]
                topic_weights = [topic[i] for i in top_words_idx]
                
                topics.append({
                    'id': topic_idx,
                    'words': top_words,
                    'weights': topic_weights.tolist(),
                    'coherence': float(np.mean(topic_weights))
                })
            
            return topics
            
        except Exception as e:
            logger.error(f"Topic modeling failed: {str(e)}")
            return []

    def extract_relationships(self, entities: List[Dict[str, Any]], text: str) -> List[Dict[str, Any]]:
        """Extract relationships between entities"""
        relationships = []
        
        try:
            doc = self.nlp(text)
            
            # Create entity map
            entity_map = {}
            for ent in entities:
                entity_map[ent['name'].lower()] = ent
            
            # Find entity co-occurrences and dependencies
            for sent in doc.sents:
                sent_entities = []
                for token in sent:
                    if token.text.lower() in entity_map:
                        sent_entities.append(entity_map[token.text.lower()])
                
                # Create relationships for entities in the same sentence
                for i, ent1 in enumerate(sent_entities):
                    for ent2 in sent_entities[i+1:]:
                        # Determine relationship type based on context
                        relationship_type = self.determine_relationship_type(ent1, ent2, sent.text)
                        
                        relationship = {
                            'entity1': ent1['name'],
                            'entity2': ent2['name'],
                            'relationship_type': relationship_type,
                            'context': sent.text,
                            'confidence': 0.8  # Basic confidence score
                        }
                        relationships.append(relationship)
            
            return relationships
            
        except Exception as e:
            logger.error(f"Relationship extraction failed: {str(e)}")
            return []

    def determine_relationship_type(self, ent1: Dict, ent2: Dict, context: str) -> str:
        """Determine the type of relationship between two entities"""
        
        # Simple rule-based relationship classification
        context_lower = context.lower()
        
        # Political relationships
        if 'vote' in context_lower or 'support' in context_lower:
            return 'political_support'
        elif 'oppose' in context_lower or 'against' in context_lower:
            return 'political_opposition'
        elif 'meet' in context_lower or 'discuss' in context_lower:
            return 'meeting'
        elif 'member' in context_lower or 'committee' in context_lower:
            return 'membership'
        elif 'represent' in context_lower:
            return 'representation'
        else:
            return 'co_occurrence'

    def generate_embeddings(self, text: str) -> np.ndarray:
        """Generate dense embeddings for text"""
        try:
            # Tokenize
            encoded = self.tokenizer(
                text,
                truncation=True,
                padding=True,
                max_length=512,
                return_tensors='pt'
            )
            
            # Generate embeddings
            with torch.no_grad():
                outputs = self.embedding_model(**encoded)
                embeddings = outputs.last_hidden_state.mean(dim=1)
            
            return embeddings.numpy().flatten()
            
        except Exception as e:
            logger.error(f"Embedding generation failed: {str(e)}")
            return np.zeros(768)  # Return zero vector as fallback

    def summarize_text(self, text: str) -> str:
        """Generate a summary of the text"""
        try:
            # Limit text length for summarization
            max_length = 1024
            if len(text) > max_length:
                text = text[:max_length]
            
            # Generate summary
            summary = self.summarizer(text, max_length=150, min_length=50, do_sample=False)
            return summary[0]['summary_text']
            
        except Exception as e:
            logger.error(f"Summarization failed: {str(e)}")
            return text[:200] + "..." if len(text) > 200 else text

    async def process_document(self, document_id: str, text: str) -> ProcessingResult:
        """Process a single document with full NLP pipeline"""
        logger.info(f"Processing document: {document_id}")
        
        try:
            # Extract entities
            entities = self.extract_entities(text)
            
            # Analyze sentiment
            sentiment = self.analyze_sentiment(text)
            
            # Extract relationships
            relationships = self.extract_relationships(entities, text)
            
            # Generate summary
            summary = self.summarize_text(text)
            
            # Generate embeddings
            embeddings = self.generate_embeddings(text)
            
            # For topic modeling, we'd need multiple documents
            # This would typically be done in batch processing
            topics = []
            
            # Create processing result
            result = ProcessingResult(
                document_id=document_id,
                entities=entities,
                sentiment=sentiment,
                topics=topics,
                summary=summary,
                relationships=relationships,
                embeddings=embeddings,
                metadata={
                    'processing_date': datetime.now().isoformat(),
                    'entity_count': len(entities),
                    'relationship_count': len(relationships),
                    'text_length': len(text)
                }
            )
            
            logger.info(f"Processed document {document_id}: {len(entities)} entities, {len(relationships)} relationships")
            return result
            
        except Exception as e:
            logger.error(f"Error processing document {document_id}: {str(e)}")
            raise

    async def store_processing_results(self, result: ProcessingResult) -> bool:
        """Store processing results in the database"""
        try:
            # Store entities
            for entity in result.entities:
                entity_data = {
                    'document_id': result.document_id,
                    'name': entity['name'],
                    'entity_type': entity['label'],
                    'confidence': entity['confidence'],
                    'start_pos': entity['start'],
                    'end_pos': entity['end'],
                    'metadata': {
                        'description': entity['description'],
                        'source': entity['source']
                    }
                }
                
                self.supabase.table('entities').insert(entity_data).execute()
            
            # Store sentiment analysis
            sentiment_data = {
                'document_id': result.document_id,
                'analysis_type': 'sentiment',
                'result': result.sentiment,
                'confidence': result.sentiment['confidence']
            }
            
            self.supabase.table('analysis_results').insert(sentiment_data).execute()
            
            # Store relationships
            for relationship in result.relationships:
                rel_data = {
                    'document_id': result.document_id,
                    'analysis_type': 'relationship',
                    'result': relationship,
                    'confidence': relationship['confidence']
                }
                
                self.supabase.table('analysis_results').insert(rel_data).execute()
            
            # Update document with embeddings and summary
            doc_update = {
                'embedding': result.embeddings.tolist(),
                'metadata': result.metadata,
                'processed': True
            }
            
            self.supabase.table('documents').update(doc_update).eq('id', result.document_id).execute()
            
            logger.info(f"Successfully stored processing results for document {result.document_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error storing processing results: {str(e)}")
            return False

    async def process_all_unprocessed_documents(self) -> Dict[str, int]:
        """Process all unprocessed documents in the database"""
        logger.info("Starting batch processing of unprocessed documents")
        
        # Fetch unprocessed documents
        response = self.supabase.table('documents').select('id, content').eq('processed', False).execute()
        documents = response.data
        
        stats = {
            'processed': 0,
            'errors': 0,
            'total': len(documents)
        }
        
        for doc in documents:
            try:
                result = await self.process_document(doc['id'], doc['content'])
                if await self.store_processing_results(result):
                    stats['processed'] += 1
                else:
                    stats['errors'] += 1
                    
            except Exception as e:
                logger.error(f"Error processing document {doc['id']}: {str(e)}")
                stats['errors'] += 1
        
        logger.info(f"Batch processing complete: {stats}")
        return stats

async def main():
    """Main processing function"""
    
    # Check environment variables
    required_env_vars = ['SUPABASE_URL', 'SUPABASE_SERVICE_ROLE_KEY']
    missing_vars = [var for var in required_env_vars if not os.getenv(var)]
    
    if missing_vars:
        logger.error(f"Missing required environment variables: {missing_vars}")
        sys.exit(1)
    
    # Initialize processor
    processor = AdvancedNLPProcessor()
    
    # Process all unprocessed documents
    stats = await processor.process_all_unprocessed_documents()
    
    print("\n" + "="*50)
    print("NLP PROCESSING SUMMARY")
    print("="*50)
    print(f"Total documents: {stats['total']}")
    print(f"Successfully processed: {stats['processed']}")
    print(f"Errors: {stats['errors']}")
    print("="*50)

if __name__ == "__main__":
    asyncio.run(main())