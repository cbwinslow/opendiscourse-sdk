import sys
from pathlib import Path

# Ensure project root is on sys.path
sys.path.append(str(Path(__file__).resolve().parents[2]))

import logging

from opendiscourse.entity_extractor import (
    extract_entities,
    save_entity,
    save_entity_mention,
    save_entity_relationship,
)

# Set up logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)

# Read test document
with open("test_document.txt", encoding="utf-8") as f:
    test_content = f.read()

# Extract entities
entities = extract_entities(test_content)

print("\nExtracted Entities:")
for entity in entities:
    print(f"- {entity['text']} ({entity['type']})")

# Save entities to database
for entity in entities:
    entity_id = save_entity(entity)
    if entity_id is not None:
        logging.info("Saved entity: %s with ID: %s", entity["text"], entity_id)

print("\nEntity Relationships:")
# Infer relationships
for i, entity in enumerate(entities):
    for j in range(i + 1, len(entities)):
        other_entity = entities[j]
        # Check for membership relationships
        if entity["type"] == "GOVERNMENT_BODY" and other_entity["type"] == "PERSON":
            logging.info("- %s is a member of %s", other_entity["text"], entity["text"])
            entity_id = save_entity(entity)
            other_entity_id = save_entity(other_entity)
            if entity_id is not None and other_entity_id is not None:
                save_entity_relationship(
                    {
                        "entity_id": entity_id,
                        "related_entity_id": other_entity_id,
                        "relationship_type": "MEMBER_OF",
                        "confidence": 0.8,
                    }
                )

print("\nEntity Mentions:")
# Save entity mentions
for entity in entities:
    entity_id = save_entity(entity)
    if entity_id is not None:
        mention = {
            "text": entity["text"],
            "type": entity["type"],
            "confidence": entity["confidence"],
        }
        save_entity_mention(mention, 1, entity_id)  # Using test document ID 1
        print(f"- Mention: {mention['text']}")
