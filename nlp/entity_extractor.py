from typing import List, Optional, Dict
import spacy
from spacy.tokens import Doc
from .preprocessor import Entity

class EntityExtractor:
    def __init__(self, kb_mapping: Optional[Dict[str, str]] = None):
        """
        Initialize the entity extractor.
        
        Args:
            kb_mapping: Optional dictionary mapping entity text to knowledge base IDs
        """
        self.kb_mapping = kb_mapping or {}
        
    def extract_entities(self, doc: spacy.tokens.Doc) -> List[Entity]:
        """
        Extract and classify named entities from a spaCy Doc.
        
        Args:
            doc: A spaCy Doc object
            
        Returns:
            List of extracted entities with their classifications
        """
        entities = []
        
        # Extract named entities
        for ent in doc.ents:
            # Get knowledge base ID if available
            kb_id = self._get_kb_id(ent.text)
            
            # Create entity with linking information
            entity = Entity(
                text=ent.text,
                label=ent.label_,
                start_char=ent.start_char,
                end_char=ent.end_char,
                kb_id=kb_id
            )
            entities.append(entity)
            
        return entities
    
    def _get_kb_id(self, entity_text: str) -> Optional[str]:
        """Look up knowledge base ID for an entity."""
        return self.kb_mapping.get(entity_text.lower())
    
    def add_kb_mapping(self, entity_text: str, kb_id: str) -> None:
        """Add or update a knowledge base mapping."""
        self.kb_mapping[entity_text.lower()] = kb_id
