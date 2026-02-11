import os
import uuid

import weaviate

# Weaviate connection details (replace with your actual details or use environment variables)
WEAVIATE_URL = os.getenv("WEAVIATE_URL", "http://localhost:8080")
WEAVIATE_API_KEY = os.getenv("WEAVIATE_API_KEY", None)  # Replace with your API key if authentication is enabled

def get_weaviate_client(url=WEAVIATE_URL, api_key=WEAVIATE_API_KEY):
    """Establishes and returns a Weaviate client."""
    try:
        if api_key:
            auth_config = weaviate.auth.AuthApiKey(api_key=api_key)
            client = weaviate.Client(url=WEAVIATE_URL, auth_client_secret=auth_config)
        else:
            client = weaviate.Client(url=WEAVIATE_URL)
        client.check_connection()
        print("Connected to Weaviate!")
        return client
    except Exception as e:
        print(f"Failed to connect to Weaviate: {e}")
        return None

def create_weaviate_schema(client):
    """Defines and creates the schema in Weaviate."""
    if not client:
        print("Weaviate client not available. Cannot create schema.")
        return

    schema = {
        "classes": [
            {
                "class": "Document",
                "description": "Represents an ingested document.",
                "properties": [
                    {"name": "doc_id", "dataType": ["text"], "description": "Unique identifier for the document."},
                    {"name": "title", "dataType": ["text"], "description": "Title of the document."},
                    {"name": "content", "dataType": ["text"], "description": "Full text content of the document."},
                    {"name": "url", "dataType": ["text"], "description": "Source URL of the document."},
                    {"name": "publicationDate", "dataType": ["date"], "description": "Publication date of the document."},
                    {"name": "documentType", "dataType": ["text"], "description": "Type of document (e.g., bill, report, speech)."},
                    {"name": "source", "dataType": ["text"], "description": "Source of the document (e.g., GovInfo, committee website)."},
                    {"name": "metadata", "dataType": ["object"], "description": "Additional metadata as a JSON object.", "nestedProperties": [{"name": "key", "dataType": ["text"]},{"name": "value", "dataType": ["text"]}]}, # Example nested property definition
 {"name": "hasEntity", "dataType": ["Entity"], "description": "Relationship to the Entity class (one-to-many)."},
                    {"name": "hasDeclaration", "dataType": ["Declaration"], "description": "Relationship to the Declaration class (one-to-many)."}
                ]
            },
            {
                "class": "Entity",
                "description": "Represents an extracted entity (Person, Government, Country, Organization, etc.).",
                "properties": [
                    {"name": "entity_id", "dataType": ["text"], "description": "Unique identifier for the entity."},
                    {"name": "text", "dataType": ["text"], "description": "Text of the extracted entity."},
                    {"name": "type", "dataType": ["text"], "description": "Type of entity (e.g., Person, Organization, Location, Government, Country)."},
                    {"name": "relevance", "dataType": ["number"], "description": "Relevance score of the entity."},
                    {"name": "metadata", "dataType": ["object"], "description": "Additional metadata as a JSON object.", "nestedProperties": [{"name": "key", "dataType": ["text"]},{"name": "value", "dataType": ["text"]}]},
 {"name": "appearsInDocument", "dataType": ["Document"], "description": "Relationship to the Document class (many-to-one)."},
 {"name": "madeDeclaration", "dataType": ["Declaration"], "description": "Relationship to the Declaration class (one-to-many) - for entities that make declarations (e.g., Persons)."},
 {"name": "affectedByDeclaration", "dataType": ["Declaration"], "description": "Relationship to the Declaration class (one-to-many) - for entities that are affected by declarations (e.g., Persons, Governments, Countries)."},
 {"name": "isMemberOf", "dataType": ["Membership"], "description": "Relationship to the Membership class (one-to-many) - for entities that are members of an organization/government (e.g., Persons)."},
 {"name": "hasMember", "dataType": ["Membership"], "description": "Relationship to the Membership class (one-to-many) - for entities that have members (e.g., Governments, Countries, Organizations)."},
                    {"name": "biasScore", "dataType": ["number"], "description": "Bias score of the entity (e.g., based on their declarations)."},
                    {"name": "truthfulnessScore", "dataType": ["number"], "description": "Truthfulness score of the entity (e.g., based on their declarations)."},
                    {"name": "socialMediaLinks", "dataType": ["text[]"], "description": "Array of social media links."},
                    {"name": "publicationLinks", "dataType": ["text[]"], "description": "Array of publication links."},
                    {"name": "publicAppearanceLinks", "dataType": ["text[]"], "description": "Array of public appearance links."}
                ]
            },
            {
                "class": "Declaration",
                "description": "Represents a statement made by an entity within a document.",
                "properties": [
                    {"name": "declaration_id", "dataType": ["text"], "description": "Unique identifier for the declaration."},
                    {"name": "text", "dataType": ["text"], "description": "Text content of the declaration."},
 {"name": "inDocument", "dataType": ["Document"], "description": "Relationship to the Document class (many-to-one)."},
 {"name": "madeByEntity", "dataType": ["Entity"], "description": "Relationship to the Entity class (many-to-one) - the entity that made the declaration."},
 {"name": "affectsEntity", "dataType": ["Entity"], "description": "Relationship to the Entity class (many-to-many) - entities that are affected by the declaration."},
                    {"name": "factCheckResult", "dataType": ["object"], "description": "Result of the fact-checking process as a JSON object.", "nestedProperties": [{"name": "key", "dataType": ["text"]},{"name": "value", "dataType": ["text"]}]},
                    {"name": "biasAnalysisResult", "dataType": ["object"], "description": "Result of the bias analysis process as a JSON object.", "nestedProperties": [{"name": "key", "dataType": ["text"]},{"name": "value", "dataType": ["text"]}]}
                ]
            },
            {
                "class": "Membership",
                "description": "Represents the membership of an individual in an organization, government, or country.",
                "properties": [
                    {"name": "membership_id", "dataType": ["text"], "description": "Unique identifier for the membership."},
                    {"name": "member", "dataType": ["Entity"], "description": "Relationship to the Entity class (many-to-one) - the individual member."},
 {"name": "organization", "dataType": ["Entity"], "description": "Relationship to the Entity class (many-to-one) - the organization, government, or country."},
 {"name": "role", "dataType": ["text"], "description": "Role of the member within the organization."},
                    {"name": "startDate", "dataType": ["date"], "description": "Start date of the membership."},
                    {"name": "endDate", "dataType": ["date"], "description": "End date of the membership (if applicable)."},
                    {"name": "metadata", "dataType": ["object"], "description": "Additional metadata as a JSON object.", "nestedProperties": [{"name": "key", "dataType": ["text"]},{"name": "value", "dataType": ["text"]}]}
                ]
            }
        ]
    }

    try:
        client.schema.create(schema)
        print("Weaviate schema created successfully.")
    except Exception as e:
        print(f"Failed to create Weaviate schema: {e}")

def add_data_object(client, data_object, class_name, uuid=None):
    """Adds a data object to a specified class in Weaviate."""
    if not client:
        print("Weaviate client not available. Cannot add data.")
        return None
    try:
        if uuid:
            client.data_object.create(data_object, class_name, uuid=uuid)
            print(f"Added data object to class '{class_name}' with uuid '{uuid}'.")
            return uuid
        else:
            result = client.data_object.create(data_object, class_name)
            print(f"Added data object to class '{class_name}'.")
            return result
    except Exception as e:
        print(f"Failed to add data object to class '{class_name}': {e}")
        return None

def add_document(client, document_data):
    """Adds a document to the 'Document' class."""
    document_uuid = uuid.uuid4()
    data_object = {
        "doc_id": document_data.get("doc_id"),
        "title": document_data.get("title"),
        "content": document_data.get("content"),
        "url": document_data.get("url"),
        "publicationDate": document_data.get("publicationDate"), # Ensure this is in ISO 8601 format
        "documentType": document_data.get("documentType"),
        "source": document_data.get("source"),
        "metadata": document_data.get("metadata"),
    }
    return add_data_object(client, data_object, "Document", uuid=str(document_uuid))

def add_entity(client, entity_data, appears_in_document_id=None):
    """Adds an entity to the 'Entity' class."""
    entity_uuid = uuid.uuid4()
    data_object = {
        "entity_id": entity_data.get("entity_id"),
        "text": entity_data.get("text"),
        "type": entity_data.get("type"),
        "relevance": entity_data.get("relevance"),
        "metadata": entity_data.get("metadata"),
        "biasScore": entity_data.get("biasScore"),
        "truthfulnessScore": entity_data.get("truthfulnessScore"),
        "socialMediaLinks": entity_data.get("socialMediaLinks"),
        "publicationLinks": entity_data.get("publicationLinks"),
        "publicAppearanceLinks": entity_data.get("publicAppearanceLinks"),
    }
    entity_uuid_str = str(entity_uuid)
    added_uuid = add_data_object(client, data_object, "Entity", uuid=entity_uuid_str)

    if added_uuid and appears_in_document_id:
        # Link entity to document
        client.data_object.reference.add(
            from_uuid=added_uuid,
            from_property_name="appearsInDocument",
            to_uuid=appears_in_document_id,
            to_class_name="Document"
        )
        print(f"Linked entity '{added_uuid}' to document '{appears_in_document_id}'.")

    return added_uuid

def add_declaration(client, declaration_data, in_document_id=None, made_by_entity_id=None, affects_entity_ids=None):
    """Adds a declaration to the 'Declaration' class."""
    declaration_uuid = uuid.uuid4()
    data_object = {
        "declaration_id": declaration_data.get("declaration_id"),
        "text": declaration_data.get("text"),
        "factCheckResult": declaration_data.get("factCheckResult"),
        "biasAnalysisResult": declaration_data.get("biasAnalysisResult"),
    }
    declaration_uuid_str = str(declaration_uuid)
    added_uuid = add_data_object(client, data_object, "Declaration", uuid=declaration_uuid_str)

    if added_uuid:
        if in_document_id:
            # Link declaration to document
            client.data_object.reference.add(
                from_uuid=added_uuid,
                from_property_name="inDocument",
                to_uuid=in_document_id,
                to_class_name="Document"
            )
            print(f"Linked declaration '{added_uuid}' to document '{in_document_id}'.")

        if made_by_entity_id:
            # Link declaration to the entity that made it
            client.data_object.reference.add(
                from_uuid=added_uuid,
                from_property_name="madeByEntity",
                to_uuid=made_by_entity_id,
                to_class_name="Entity"
            )
            print(f"Linked declaration '{added_uuid}' to entity '{made_by_entity_id}'.")

        if affects_entity_ids:
            # Link declaration to entities it affects
            for entity_id in affects_entity_ids:
                client.data_object.reference.add(
                    from_uuid=added_uuid,
                    from_property_name="affectsEntity",
                    to_uuid=entity_id,
                    to_class_name="Entity"
                )
            print(f"Linked declaration '{added_uuid}' to affected entities: {affects_entity_ids}.")

    return added_uuid

def add_membership(client, membership_data, member_entity_id=None, organization_entity_id=None):
    """Adds a membership to the 'Membership' class."""
    membership_uuid = uuid.uuid4()
    data_object = {
        "membership_id": membership_data.get("membership_id"),
        "role": membership_data.get("role"),
        "startDate": membership_data.get("startDate"), # Ensure this is in ISO 8601 format
        "endDate": membership_data.get("endDate"), # Ensure this is in ISO 8601 format
        "metadata": membership_data.get("metadata"),
    }
    membership_uuid_str = str(membership_uuid)
    added_uuid = add_data_object(client, data_object, "Membership", uuid=membership_uuid_str)

    if added_uuid:
        if member_entity_id:
            # Link membership to the member entity
            client.data_object.reference.add(
                from_uuid=added_uuid,
                from_property_name="member",
                to_uuid=member_entity_id,
                to_class_name="Entity"
            )
            print(f"Linked membership '{added_uuid}' to member entity '{member_entity_id}'.")

        if organization_entity_id:
            # Link membership to the organization entity
            client.data_object.reference.add(
                from_uuid=added_uuid,
                from_property_name="organization",
                to_uuid=organization_entity_id,
                to_class_name="Entity"
            )
            print(f"Linked membership '{added_uuid}' to organization entity '{organization_entity_id}'.")

    return added_uuid

def get_document_by_id(client, doc_id):
    """Retrieves a document from Weaviate by its doc_id."""
    if not client:
        print("Weaviate client not available. Cannot query.")
        return None
    try:
        # Assuming doc_id is a unique property indexed for filtering
        result = client.query.get("Document", ["doc_id", "title", "url"]).with_where({
            "path": ["doc_id"],
            "operator": "Equal",
            "valueText": doc_id
        }).do()
        if result and "data" in result and "Get" in result["data"] and "Document" in result["data"]["Get"]:
            return result["data"]["Get"]["Document"]
        else:
            return None
    except Exception as e:
        print(f"Error querying document by doc_id '{doc_id}': {e}")
        return None


# Example usage (assuming Weaviate is running)
if __name__ == "__main__":
    weaviate_client = get_weaviate_client()
    if weaviate_client:
        # Optional: Delete existing schema before creating a new one (use with caution!)
        # try:
        #     weaviate_client.schema.delete_all()
        #     print("Existing schema deleted.")
        # except Exception as e:
        #     print(f"Failed to delete existing schema: {e}")

        create_weaviate_schema(weaviate_client)