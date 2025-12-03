import spacy
# import lexnlp.extract.en.entities.organization  # Example import for LexNLP

# Load a spaCy model (you might need to download one, e.g., 'en_core_web_sm')
try:
    nlp = spacy.load("en_core_web_sm")
except OSError:
    print("Downloading spaCy model 'en_core_web_sm'...")
    from spacy.cli import download
    download("en_core_web_sm")
    nlp = spacy.load("en_core_web_sm")

# If using a legal model like Blackstone, load it here instead
# try:
#     nlp_legal = spacy.load("en_blackstone_model")
# except OSError:
#     print("Downloading spaCy model 'en_blackstone_model'...")
#     # You would need to find the correct way to download/install the Blackstone model
#     # download("en_blackstone_model") # This might not work directly
#     nlp_legal = spacy.load("en_blackstone_model")


def extract_entities(text: str) -> list[dict]:
    """
    Extract entities from text using spaCy (and potentially LexNLP).
    """
    doc = nlp(text) # Use the loaded spaCy model

    entities = []
    for ent in doc.ents:
        # Create a dictionary for each entity
        entity_data = {
            "text": ent.text,
            "type": ent.label_, # Use spaCy's entity label as the type
            "metadata": {
                "start_char": ent.start_char,
                "end_char": ent.end_char,
                # Add more metadata as needed, e.g., confidence score if available
            },
            # We might generate entity_id here or in the ingestion function
            # "entity_id": str(uuid.uuid4()) # Example of generating a UUID
        }
        entities.append(entity_data)

    # TODO: Integrate LexNLP or other libraries for additional entity types if needed

    return entities


def extract_declarations(text: str, entities: list) -> list[dict]:
    """
    Extract declarations from text and link them to entities.
    """
    # Placeholder implementation
    declarations = []
    # This is a simplified placeholder. Real implementation needs logic
    # to identify statements and link them to entities.
    # For demonstration, let's just create a dummy declaration
    if entities:
        declarations.append({
            "text": text[:100] + "...", # Example: first 100 chars as a dummy declaration
            "madeByEntity": [entities[0]["entity_id"]] if "entity_id" in entities[0] else [], # Link to the first entity if exists
            "affectsEntity": [] # Placeholder
        })
    return declarations
import spacy
# import lexnlp.extract.en.entities.organization  # Example import for LexNLP

# Load a spaCy model (you might need to download one, e.g., 'en_core_web_sm')
try:
    nlp = spacy.load("en_core_web_sm")
except OSError:
    print("Downloading spaCy model 'en_core_web_sm'...")
    from spacy.cli import download
    download("en_core_web_sm")
    nlp = spacy.load("en_core_web_sm")

# If using a legal model like Blackstone, load it here instead
# try:
#     nlp_legal = spacy.load("en_blackstone_model")
# except OSError:
#     print("Downloading spaCy model 'en_blackstone_model'...")
#     # You would need to find the correct way to download/install the Blackstone model
#     # download("en_blackstone_model") # This might not work directly
#     nlp_legal = spacy.load("en_blackstone_model")


def extract_entities(text: str) -> list[dict]:
    """
    Extract entities from text using spaCy (and potentially LexNLP).

    Args:
        text: The input text.

    Returns:
        A list of dictionaries, where each dictionary represents an entity.
    """
    doc = nlp(text)
    extracted_entities = []

    # SpaCy NER
    for ent in doc.ents:
        extracted_entities.append({
            "text": ent.text,
            "type": ent.label_,  # SpaCy's entity type
            "metadata": {"start_char": ent.start_char, "end_char": ent.end_char}
            # Add more metadata as needed
        })

    # Placeholder for LexNLP entity extraction (example for organizations)
    # If LexNLP is integrated and configured, you would call its functions here
    # organizations = lexnlp.extract.en.entities.organization.get_organizations(text)
    # for org_text, metadata in organizations:
    #     extracted_entities.append({
    #         "text": org_text,
    #         "type": "Organization", # LexNLP might provide more specific types
    #         "metadata": metadata
    #     })

    # Further processing to standardize entity types, resolve overlaps, etc.
    # This is a simplified placeholder.

    return extracted_entities


def extract_declarations(text: str, entities: list) -> list[dict]:
    """
    Extract declarations (statements) from text and link them to entities.

    Args:
        text: The input text.
        entities: A list of extracted entities from extract_entities.

    Returns:
        A list of dictionaries, where each dictionary represents a declaration.
    """
    # This is a complex task that would require more sophisticated NLP.
    # Placeholder implementation: treat each sentence as a potential declaration
    # and try to link it to entities found within that sentence.

    doc = nlp(text)
    extracted_declarations = []
    entity_map = {entity["text"]: entity for entity in entities} # Simple mapping by text

    for sent in doc.sents:
        declaration_text = sent.text
        made_by_entities = []
        affects_entities = []

        # Simple approach: check if any extracted entity text appears in the sentence
        # A more advanced approach would use dependency parsing, coreference resolution, etc.
        for entity in entities:
            if entity["text"] in declaration_text:
                # Placeholder logic: Assume entities in the sentence could be
                # either the maker or the affected party.
                if entity["type"] in ["PERSON", "ORG", "Government", "Country"]: # Example entity types that might make declarations
                     made_by_entities.append(entity.get("entity_id", entity["text"])) # Use entity_id if available, else text

                affects_entities.append(entity.get("entity_id", entity["text"])) # Assume any entity in sentence is affected

        # Remove duplicates and refine entity IDs if needed
        made_by_entities = list(set(made_by_entities))
        affects_entities = list(set(affects_entities))


        extracted_declarations.append({
            "text": declaration_text,
            # You would need a unique ID for each declaration
            "declaration_id": str(uuid.uuid4()), # Requires importing uuid
            "madeByEntity": made_by_entities, # List of entity IDs or identifiers
            "affectsEntity": affects_entities, # List of entity IDs or identifiers
            "metadata": {"sentence_start": sent.start_char, "sentence_end": sent.end_char}
            # Add metadata like sentiment, topic, etc. later
        })

    # Note: This placeholder declaration extraction is very basic.
    # A real implementation would need to identify actual declarative sentences,
    # resolve pronouns, and use deeper linguistic analysis to determine
    # subject, object, and other relationships to accurately link entities.


    return extracted_declarations

# You would also need to import uuid for declaration_id generation if used
# import uuid
