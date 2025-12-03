#!/usr/bin/env python3
"""
OpenDiscourse LangChain Integration Demo

This script demonstrates how to use the LangChain integrations
in the OpenDiscourse project for document ingestion and querying.

Usage:
    python examples/langchain_demo.py

Requirements:
    - LangChain packages installed
    - Sample documents in ./data/sample_documents/
    - Environment variables configured (optional)
"""

import os
import sys
import logging
from pathlib import Path
from datetime import datetime

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from opendiscourse.langchain_integrations import (
    OpenDiscourseRAGService,
    create_bill_metadata,
    create_committee_metadata,
)

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_sample_documents():
    """Create sample documents for demonstration."""
    sample_dir = Path("./data/sample_documents")
    sample_dir.mkdir(parents=True, exist_ok=True)
    
    # Sample Bill Text
    bill_text = """
    H.R. 1234 - The Digital Democracy Enhancement Act
    
    118th Congress (2023-2024)
    
    SECTION 1. SHORT TITLE.
    This Act may be cited as the "Digital Democracy Enhancement Act".
    
    SECTION 2. FINDINGS.
    Congress finds the following:
    (1) Digital platforms have become essential tools for civic engagement.
    (2) Citizens require better access to government information and decision-making processes.
    (3) Technology can enhance transparency and accountability in government.
    
    SECTION 3. DIGITAL GOVERNMENT TRANSPARENCY.
    (a) REQUIREMENT.—The head of each Federal agency shall establish and maintain 
    a comprehensive digital platform for public access to agency information.
    
    (b) FEATURES.—Each digital platform shall include:
    (1) Real-time access to agency proceedings and decisions.
    (2) Machine-readable data formats for all published information.
    (3) Public comment systems with automated response tracking.
    
    SECTION 4. FUNDING.
    There are authorized to be appropriated $50,000,000 for fiscal year 2024
    to carry out this Act.
    """
    
    # Sample Committee Document
    committee_text = """
    House Committee on Science, Space, and Technology
    Markup Session - H.R. 1234
    Date: March 15, 2024
    
    COMMITTEE MARKUP SUMMARY
    
    The Committee met to consider H.R. 1234, the Digital Democracy Enhancement Act.
    
    OPENING STATEMENTS:
    
    Chairwoman Smith: "This legislation represents a crucial step forward in making
    our government more accessible and transparent to the American people. In an age
    where citizens expect instant access to information, we must modernize how
    government communicates and engages with the public."
    
    Ranking Member Johnson: "While I support the goals of transparency, we must
    ensure that this legislation does not create undue burdens on federal agencies
    or compromise sensitive information."
    
    WITNESS TESTIMONY:
    
    Dr. Sarah Chen, Digital Government Institute: "Current government digital
    infrastructure lags significantly behind private sector standards. This bill
    would help bridge that gap."
    
    COMMITTEE DISCUSSION:
    
    The Committee discussed several amendments, including:
    - Amendment 1: Exemption for classified information (ADOPTED 25-3)
    - Amendment 2: Implementation timeline extension (ADOPTED 18-10)
    - Amendment 3: Additional funding provisions (FAILED 12-16)
    
    FINAL VOTE:
    The Committee voted 22-6 to report H.R. 1234 favorably to the House.
    """
    
    # Sample Federal Register Entry
    federal_register_text = """
    Federal Register / Vol. 89, No. 45 / Wednesday, March 6, 2024
    
    DEPARTMENT OF TECHNOLOGY AND INNOVATION
    
    Digital Government Standards; Proposed Rule
    
    AGENCY: Department of Technology and Innovation
    ACTION: Proposed rule
    
    SUMMARY: The Department of Technology and Innovation proposes to establish
    minimum digital accessibility standards for all federal agency websites and
    digital platforms. This rule would implement requirements under the Digital
    Democracy Enhancement Act.
    
    DATES: Comments must be received on or before May 6, 2024.
    
    SUPPLEMENTARY INFORMATION:
    
    I. Background
    
    The Digital Democracy Enhancement Act directs federal agencies to improve
    digital accessibility and transparency. This proposed rule establishes
    specific technical standards and implementation timelines.
    
    II. Proposed Standards
    
    A. Website Accessibility
    All federal websites must comply with WCAG 2.1 Level AA standards.
    
    B. Data Formats
    All published data must be available in machine-readable formats,
    including JSON, XML, and CSV.
    
    C. Response Times
    Agencies must respond to public comments within 30 business days.
    
    III. Implementation Timeline
    
    Phase 1 (6 months): Major agency websites
    Phase 2 (12 months): All agency digital platforms
    Phase 3 (18 months): Full compliance across all systems
    
    IV. Cost Analysis
    
    The estimated cost of implementation is $25 million annually across
    all affected agencies.
    """
    
    # Write sample documents
    with open(sample_dir / "hr1234_bill.txt", "w") as f:
        f.write(bill_text)
    
    with open(sample_dir / "committee_markup_hr1234.txt", "w") as f:
        f.write(committee_text)
    
    with open(sample_dir / "federal_register_digital_standards.txt", "w") as f:
        f.write(federal_register_text)
    
    logger.info(f"Created sample documents in {sample_dir}")
    return sample_dir


def demo_basic_usage():
    """Demonstrate basic RAG service usage."""
    print("\n" + "="*60)
    print("DEMO 1: Basic RAG Service Usage")
    print("="*60)
    
    # Initialize the RAG service
    rag_service = OpenDiscourseRAGService(
        vector_store_path="./data/demo_chroma_db",
        embedding_model="sentence-transformers/all-MiniLM-L6-v2",
        llm_provider="huggingface"
    )
    
    print(f"✓ Initialized RAG service with {rag_service.llm_provider} LLM")
    
    # Create sample documents
    sample_dir = create_sample_documents()
    
    # Ingest documents
    print(f"\n📁 Ingesting documents from {sample_dir}")
    results = rag_service.ingest_directory(
        str(sample_dir),
        "**/*.txt",
        "legislative"
    )
    
    total_chunks = sum(results.values())
    print(f"✓ Ingested {len(results)} files ({total_chunks} chunks)")
    
    # Get collection info
    info = rag_service.get_collection_info()
    print(f"📊 Collection: {info['total_documents']} documents, {len(info['document_types'])} types")
    
    return rag_service


def demo_querying(rag_service):
    """Demonstrate querying capabilities."""
    print("\n" + "="*60)
    print("DEMO 2: Querying Documents")
    print("="*60)
    
    # Example queries
    queries = [
        "What is the Digital Democracy Enhancement Act about?",
        "How much funding is authorized for this legislation?",
        "What are the implementation phases for the digital standards?",
        "Which committee considered this bill?",
        "What amendments were proposed during committee markup?"
    ]
    
    for i, question in enumerate(queries, 1):
        print(f"\n🤔 Query {i}: {question}")
        
        try:
            result = rag_service.query(question)
            print(f"💬 Answer: {result.answer}")
            print(f"📚 Sources: {len(result.source_documents)} documents")
            
            # Show source preview
            if result.source_documents:
                source = result.source_documents[0]
                preview = source.page_content[:150] + "..." if len(source.page_content) > 150 else source.page_content
                print(f"📄 Source preview: {preview}")
        
        except Exception as e:
            print(f"❌ Error: {e}")


def demo_search(rag_service):
    """Demonstrate document search capabilities."""
    print("\n" + "="*60)
    print("DEMO 3: Document Search")
    print("="*60)
    
    # Search for documents
    search_queries = [
        "funding appropriations",
        "committee vote",
        "digital accessibility standards",
        "implementation timeline"
    ]
    
    for query in search_queries:
        print(f"\n🔍 Searching for: '{query}'")
        
        try:
            docs = rag_service.search_similar_documents(query, k=2)
            print(f"📋 Found {len(docs)} relevant documents:")
            
            for i, doc in enumerate(docs, 1):
                source = doc.metadata.get('source', 'Unknown')
                preview = doc.page_content[:100] + "..." if len(doc.page_content) > 100 else doc.page_content
                print(f"  {i}. {source}")
                print(f"     Preview: {preview}")
        
        except Exception as e:
            print(f"❌ Search error: {e}")


def demo_metadata_usage():
    """Demonstrate metadata creation and usage."""
    print("\n" + "="*60)
    print("DEMO 4: Metadata and Specialized Functions")
    print("="*60)
    
    # Create bill metadata
    bill_metadata = create_bill_metadata(
        bill_number="H.R. 1234",
        congress_session="118th",
        committee="House Committee on Science, Space, and Technology"
    )
    
    print(f"📋 Bill metadata created:")
    print(f"   Bill: {bill_metadata.bill_number}")
    print(f"   Congress: {bill_metadata.congress_session}")
    print(f"   Committee: {bill_metadata.committee}")
    print(f"   Type: {bill_metadata.document_type}")
    
    # Create committee metadata
    committee_metadata = create_committee_metadata(
        committee_name="House Committee on Science, Space, and Technology",
        congress_session="118th"
    )
    
    print(f"\n🏛️ Committee metadata created:")
    print(f"   Committee: {committee_metadata.committee}")
    print(f"   Congress: {committee_metadata.congress_session}")
    print(f"   Type: {committee_metadata.document_type}")


def demo_filtered_queries(rag_service):
    """Demonstrate filtered querying."""
    print("\n" + "="*60)
    print("DEMO 5: Filtered Queries")
    print("="*60)
    
    # Query with filters
    question = "What are the key provisions of this legislation?"
    
    # Query all documents
    print(f"🔍 Query (no filter): {question}")
    result_all = rag_service.query(question)
    print(f"💬 Answer: {result_all.answer[:200]}...")
    print(f"📚 Sources: {len(result_all.source_documents)} documents")
    
    # Query with document type filter
    print(f"\n🔍 Query (legislative filter): {question}")
    result_filtered = rag_service.query(
        question,
        filters={"document_type": "legislative"}
    )
    print(f"💬 Answer: {result_filtered.answer[:200]}...")
    print(f"📚 Sources: {len(result_filtered.source_documents)} documents")


def demo_api_preview():
    """Show how to start the API server."""
    print("\n" + "="*60)
    print("DEMO 6: API Server Usage")
    print("="*60)
    
    print("🚀 To start the RAG API server, run:")
    print("   python -m opendiscourse.langchain_integrations.rag_api")
    print("")
    print("📖 API Documentation will be available at:")
    print("   http://localhost:8001/api/v1/rag/docs")
    print("")
    print("🔧 Example API calls:")
    print("   GET  /api/v1/rag/health")
    print("   POST /api/v1/rag/query")
    print("   POST /api/v1/rag/search") 
    print("   GET  /api/v1/rag/collection")
    print("")
    print("🔑 Set API_TOKEN environment variable for protected endpoints")


def main():
    """Run the complete demo."""
    print("🎯 OpenDiscourse LangChain Integration Demo")
    print("=" * 60)
    
    try:
        # Run demos
        rag_service = demo_basic_usage()
        demo_querying(rag_service)
        demo_search(rag_service)
        demo_metadata_usage()
        demo_filtered_queries(rag_service)
        demo_api_preview()
        
        print("\n" + "="*60)
        print("✅ Demo completed successfully!")
        print("✨ Your RAG system is ready for government document analysis!")
        print("="*60)
        
    except Exception as e:
        logger.error(f"Demo failed: {e}")
        print(f"\n❌ Demo failed: {e}")
        print("💡 Make sure all dependencies are installed:")
        print("   pip install langchain langchain-community langchain-text-splitters")
        print("   pip install sentence-transformers chromadb")
        
    finally:
        # Cleanup note
        print(f"\n🧹 Note: Demo data stored in ./data/")
        print("   You can safely delete this directory if needed.")


if __name__ == "__main__":
    main()

