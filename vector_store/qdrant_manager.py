import qdrant_client
from qdrant_client.http.models import Distance, VectorParams, PointStruct, PayloadSchemaType

class QdrantManager:
    def __init__(self, host="localhost", port=6333):
        self.client = qdrant_client.QdrantClient(host=host, port=port)
        self.collections = ["documents", "entities", "declarations", "memberships"]

    def create_collections(self, vector_size=768, distance=Distance.COSINE):
        """
        Creates the necessary collections in Qdrant.

        Args:
            vector_size (int): The size of the vector embeddings.
            distance (Distance): The distance metric for vector comparison.

        for collection_name in self.collections:
            try:
                self.client.get_collection(collection_name=collection_name)
                print(f"Collection '{collection_name}' already exists.")
            except Exception:
                print(f"Creating collection '{collection_name}'...")
                self.client.recreate_collection(
                    collection_name=collection_name,
                    vectors_config=VectorParams(size=vector_size, distance=distance),
                )
                print(f"Collection '{collection_name}' created.")

    def upsert_document(self, doc_id, title, content, url, publication_date, document_type, source, metadata, entity_ids=None, declaration_ids=None, vector=None):
        """
        Upserts a document into the 'documents' collection. # Corrected indentation
        """
        payload = {
            "doc_id": doc_id,
            "title": title,
            "url": url,
            "publicationDate": publication_date, # Consider consistent date format
            "documentType": document_type,
            "source": source,
            "metadata": metadata,
            "entity_ids": entity_ids if entity_ids is not None else [],
            "declaration_ids": declaration_ids if declaration_ids is not None else []
        }
        self.client.upsert(
            collection_name="documents",
            wait=True,
            points=[
                PointStruct(
                    id=str(doc_id), # Using doc_id as the point ID
                    vector=vector,
                    payload=payload
                )
            ]
        )
        print(f"Document '{doc_id}' upserted.")

    def upsert_entity(self, entity_id, text, type, relevance, metadata, document_ids=None, madeDeclaration_ids=None, affectedByDeclaration_ids=None, isMemberOf_ids=None, hasMember_ids=None, bias_score=None, truthfulness_score=None, social_media_links=None, publication_links=None, public_appearance_links=None, vector=None):
        """
        Upserts an entity into the 'entities' collection. # Corrected indentation
        """
        payload = {
            "entity_id": entity_id,
            "text": text,
            "type": type,
            "relevance": relevance,
            "metadata": metadata,
            "document_ids": document_ids if document_ids is not None else [],
            "madeDeclaration_ids": madeDeclaration_ids if madeDeclaration_ids is not None else [],
            "affectedByDeclaration_ids": affectedByDeclaration_ids if affectedByDeclaration_ids is not None else [],
            "isMemberOf_ids": isMemberOf_ids if isMemberOf_ids is not None else [],
            "hasMember_ids": hasMember_ids if hasMember_ids is not None else [],
            "biasScore": bias_score,
            "truthfulnessScore": truthfulness_score,
            "socialMediaLinks": social_media_links if social_media_links is not None else [],
            "publicationLinks": publication_links if publication_links is not None else [],
            "publicAppearanceLinks": public_appearance_links if public_appearance_links is not None else []
        }
        self.client.upsert(
            collection_name="entities",
            wait=True,
            points=[
                PointStruct(
                    id=str(entity_id), # Using entity_id as the point ID
                    vector=vector,
                    payload=payload
                )
            ]
        )
        print(f"Entity '{entity_id}' upserted.")

    def upsert_declaration(self, declaration_id, text, document_id, madeByEntity_id, affectsEntity_ids=None, fact_check_result=None, bias_analysis_result=None, vector=None):
        """
        Upserts a declaration into the 'declarations' collection. # Corrected indentation
        """
        payload = {
            "declaration_id": declaration_id,
            "text": text,
            "document_id": document_id,
            "madeByEntity_id": madeByEntity_id,
            "affectsEntity_ids": affectsEntity_ids if affectsEntity_ids is not None else [],
            "factCheckResult": fact_check_result,
            "biasAnalysisResult": bias_analysis_result
        }
        self.client.upsert(
            collection_name="declarations",
            wait=True,
            points=[
                PointStruct(
                    id=str(declaration_id), # Using declaration_id as the point ID
                    vector=vector,
                    payload=payload
                )
            ]
        )
        print(f"Declaration '{declaration_id}' upserted.")

    def upsert_membership(self, membership_id, member_id, organization_id, role, start_date, end_date, metadata, vector=None):
        """
        Upserts a membership into the 'memberships' collection. # Corrected indentation
        """
        payload = {
            "membership_id": membership_id,
            "member_id": member_id,
            "organization_id": organization_id,
            "role": role,
            "startDate": start_date, # Consider consistent date format
            "endDate": end_date,     # Consider consistent date format
            "metadata": metadata
        }
        self.client.upsert(
            collection_name="memberships",
            wait=True,
            points=[
                PointStruct(
                    id=str(membership_id), # Using membership_id as the point ID
                    vector=vector, # Optional vector for membership
                    payload=payload
                )
            ]
        )
        print(f"Membership '{membership_id}' upserted.")

if __name__ == '__main__':
    # Example Usage:
    qdrant_manager = QdrantManager()
    qdrant_manager.create_collections()

    # Example data (replace with actual data from ingestion)
    doc_vector = [0.1] * 768 # Example vector
    entity_vector = [0.2] * 768 # Example vector
    declaration_vector = [0.3] * 768 # Example vector

    qdrant_manager.upsert_document(
        doc_id="doc1",
        title="Sample Document",
        content="This is the content of a sample document.",
        url="http://example.com/doc1",
        publication_date="2023-01-01",
        document_type="Report",
        source="Example Source",
        metadata={"version": 1},
        vector=doc_vector
    )

    qdrant_manager.upsert_entity(
        entity_id="person1",
        text="John Doe",
        type="Person",
        relevance=0.9,
        metadata={"occupation": "Politician"},
        document_ids=["doc1"],
        vector=entity_vector
    )

    qdrant_manager.upsert_declaration(
        declaration_id="dec1",
        text="We should support this bill.",
        document_id="doc1",
        madeByEntity_id="person1",
        vector=declaration_vector
    )

    qdrant_manager.upsert_membership(
        membership_id="mem1",
        member_id="person1",
        organization_id="gov1",
        role="Senator",
        start_date="2022-01-01",
        end_date=None,
        metadata={}
    )