from dataclasses import dataclass
from typing import List, Optional
import spacy
from spacy.tokens import Doc

@dataclass
class Entity:
    text: str
    label: str
    start_char: int
    end_char: int
    kb_id: Optional[str] = None

@dataclass
class ProcessedDocument:
    text: str
    clean_text: str
    entities: List[Entity]
    doc: Doc

class DocumentPreprocessor:
    def __init__(self):
        self.nlp = spacy.load("en_core_web_lg")
        
    def preprocess(self, text: str) -> ProcessedDocument:
        # Clean text by removing extra whitespace and normalizing quotes
        clean_text = self._clean_text(text)
        
        # Process with spaCy pipeline
        doc = self.nlp(clean_text)
        
        # Extract entities
        entities = self._extract_entities(doc)
        
        return ProcessedDocument(
            text=text,
            clean_text=clean_text,
            entities=entities,
            doc=doc
        )
        
    def _clean_text(self, text: str) -> str:
        # Remove extra whitespace
        text = " ".join(text.split())
        
        # Normalize quotes
        text = text.replace('"', '"').replace('"', '"')
        text = text.replace("'", "'").replace("'", "'")
        
        return text
        
    def _extract_entities(self, doc: Doc) -> List[Entity]:
        entities = []
        
        for ent in doc.ents:
            entity = Entity(
                text=ent.text,
                label=ent.label_,
                start_char=ent.start_char,
                end_char=ent.end_char
            )
            entities.append(entity)
            
        return entities
