from typing import Optional, Dict, Any
from dataclasses import dataclass
import logging
from transformers import AutoTokenizer, AutoModel
import torch
import spacy

@dataclass
class ProcessedDocument:
    """Data class representing a processed document with metadata and embeddings"""
    id: str
    content: str
    embeddings: torch.Tensor
    entities: Dict[str, Any]
    metadata: Dict[str, Any]
    language: str
    error: Optional[str] = None

class DocumentIngestor:
    """Handles document ingestion pipeline including preprocessing, entity extraction, and embedding generation"""
    
    def __init__(self):
        # Initialize NLP components
        self.nlp = spacy.load("en_core_web_sm")
        self.tokenizer = AutoTokenizer.from_pretrained("sentence-transformers/all-mpnet-base-v2")
        self.model = AutoModel.from_pretrained("sentence-transformers/all-mpnet-base-v2")
        self.logger = logging.getLogger(__name__)

    def preprocess_document(self, content: str) -> str:
        """Clean and normalize document content"""
        try:
            # Basic cleaning
            content = content.strip()
            
            # Use spaCy for basic text preprocessing
            doc = self.nlp(content)
            
            # Normalize whitespace and join sentences
            processed_text = " ".join([sent.text.strip() for sent in doc.sents])
            
            return processed_text
            
        except Exception as e:
            self.logger.error(f"Error in document preprocessing: {str(e)}")
            raise

    def extract_entities(self, content: str) -> Dict[str, Any]:
        """Extract named entities and key information from document"""
        try:
            doc = self.nlp(content)
            
            entities = {
                "organizations": [],
                "persons": [],
                "locations": [],
                "dates": [],
                "misc": []
            }
            
            # Extract entities by type
            for ent in doc.ents:
                if ent.label_ in ["ORG"]:
                    entities["organizations"].append(ent.text)
                elif ent.label_ in ["PERSON"]:
                    entities["persons"].append(ent.text)
                elif ent.label_ in ["GPE", "LOC"]:
                    entities["locations"].append(ent.text)
                elif ent.label_ in ["DATE"]:
                    entities["dates"].append(ent.text)
                else:
                    entities["misc"].append((ent.text, ent.label_))
            
            # Deduplicate lists
            for key in entities:
                entities[key] = list(set(entities[key]))
                
            return entities
            
        except Exception as e:
            self.logger.error(f"Error in entity extraction: {str(e)}")
            raise

    def generate_embeddings(self, content: str) -> torch.Tensor:
        """Generate document embeddings using transformer model"""
        try:
            # Tokenize and generate embeddings
            inputs = self.tokenizer(content, return_tensors="pt", 
                                  truncation=True, max_length=512,
                                  padding=True)
            
            with torch.no_grad():
                outputs = self.model(**inputs)
                # Use mean pooling of last hidden state
                embeddings = torch.mean(outputs.last_hidden_state, dim=1)
            
            return embeddings
            
        except Exception as e:
            self.logger.error(f"Error generating embeddings: {str(e)}")
            raise

    def detect_language(self, content: str) -> str:
        """Detect document language"""
        try:
            doc = self.nlp(content[:1000])  # Use first 1000 chars for efficiency
            return doc.lang_
        except Exception as e:
            self.logger.error(f"Error detecting language: {str(e)}")
            return "unknown"

    def ingest(self, document: 'Document') -> ProcessedDocument:
        """Main ingestion pipeline combining all processing steps"""
        try:
            # Initialize result
            processed = ProcessedDocument(
                id=document.id,
                content="",
                embeddings=None,
                entities={},
                metadata={},
                language=""
            )
            
            # Step 1: Preprocess document
            self.logger.info(f"Preprocessing document {document.id}")
            processed.content = self.preprocess_document(document.content)
            
            # Step 2: Detect language
            processed.language = self.detect_language(processed.content)
            
            # Step 3: Extract entities
            self.logger.info(f"Extracting entities from document {document.id}")
            processed.entities = self.extract_entities(processed.content)
            
            # Step 4: Generate embeddings
            self.logger.info(f"Generating embeddings for document {document.id}")
            processed.embeddings = self.generate_embeddings(processed.content)
            
            # Step 5: Add metadata
            processed.metadata = {
                "original_length": len(document.content),
                "processed_length": len(processed.content),
                "num_entities": sum(len(v) for v in processed.entities.values()),
                "embedding_dim": processed.embeddings.shape[-1]
            }
            
            return processed
            
        except Exception as e:
            self.logger.error(f"Error processing document {document.id}: {str(e)}")
            # Return partial results with error
            return ProcessedDocument(
                id=document.id,
                content=document.content,
                embeddings=None,
                entities={},
                metadata={},
                language="unknown",
                error=str(e)
            )
