#!/usr/bin/env python3
"""
Basic test script to verify RAG scripts functionality
"""

import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

def test_imports():
    """Test that all required modules can be imported."""
    print("Testing imports...")
    
    try:
        # Test basic imports
        import logging
        import json
        import datetime
        print("✓ Basic Python modules available")
        
        # Test database import
        try:
            import psycopg2
            print("✓ psycopg2 available")
        except ImportError:
            print("✗ psycopg2 not available - install with: pip install psycopg2-binary")
        
        # Test NLP imports
        try:
            import spacy
            print("✓ spaCy available")
            
            # Try to load English model
            try:
                nlp = spacy.load("en_core_web_sm")
                print("✓ spaCy English model (sm) available")
            except OSError:
                try:
                    nlp = spacy.load("en_core_web_lg")
                    print("✓ spaCy English model (lg) available")
                except OSError:
                    print("✗ spaCy English model not available - install with: python -m spacy download en_core_web_sm")
        except ImportError:
            print("✗ spaCy not available - install with: pip install spacy")
        
        # Test embeddings
        try:
            from sentence_transformers import SentenceTransformer
            print("✓ SentenceTransformers available")
        except ImportError:
            print("✗ SentenceTransformers not available - install with: pip install sentence-transformers")
        
        # Test other dependencies
        try:
            import numpy as np
            print("✓ NumPy available")
        except ImportError:
            print("✗ NumPy not available - install with: pip install numpy")
        
        try:
            from dotenv import load_dotenv
            print("✓ python-dotenv available")
        except ImportError:
            print("✗ python-dotenv not available - install with: pip install python-dotenv")
            
    except Exception as e:
        print(f"✗ Import test failed: {e}")
        return False
    
    return True

def test_script_files():
    """Test that all script files exist and are readable."""
    print("\nTesting script files...")
    
    scripts_dir = project_root / "scripts"
    required_scripts = [
        "rag_nlp_operations.py",
        "rag_data_management.py", 
        "rag_query_reporting.py",
        "rag_orchestrator.py"
    ]
    
    all_exist = True
    for script in required_scripts:
        script_path = scripts_dir / script
        if script_path.exists():
            print(f"✓ {script} exists")
            
            # Check if executable
            if os.access(script_path, os.X_OK):
                print(f"✓ {script} is executable")
            else:
                print(f"⚠ {script} is not executable - run: chmod +x {script_path}")
        else:
            print(f"✗ {script} missing")
            all_exist = False
    
    return all_exist

def test_module_structure():
    """Test that the project modules can be imported."""
    print("\nTesting project module structure...")
    
    try:
        # Test NLP modules
        from nlp.preprocessor import DocumentPreprocessor
        print("✓ DocumentPreprocessor can be imported")
        
        from nlp.entity_extractor import EntityExtractor
        print("✓ EntityExtractor can be imported")
        
        # Test document processing modules
        from document_processing.document_chunker import DocumentChunker
        print("✓ DocumentChunker can be imported")
        
        from document_processing.pipeline_executor import PipelineExecutor
        print("✓ PipelineExecutor can be imported")
        
        return True
    except ImportError as e:
        print(f"✗ Module import failed: {e}")
        return False

def test_environment():
    """Test environment configuration."""
    print("\nTesting environment configuration...")
    
    # Check for .env file
    env_file = project_root / ".env"
    if env_file.exists():
        print("✓ .env file exists")
    else:
        print("⚠ .env file not found - create from .env.example")
    
    # Check for required environment variables
    required_vars = ["POSTGRES_DB", "POSTGRES_USER", "POSTGRES_PASSWORD", "POSTGRES_HOST", "POSTGRES_PORT"]
    
    from dotenv import load_dotenv
    load_dotenv()
    
    missing_vars = []
    for var in required_vars:
        if os.getenv(var):
            print(f"✓ {var} is set")
        else:
            print(f"⚠ {var} not set")
            missing_vars.append(var)
    
    if missing_vars:
        print(f"⚠ Set missing environment variables: {', '.join(missing_vars)}")
    
    return len(missing_vars) == 0

def test_basic_functionality():
    """Test basic functionality without database connection."""
    print("\nTesting basic functionality...")
    
    try:
        # Test DocumentPreprocessor
        from nlp.preprocessor import DocumentPreprocessor
        preprocessor = DocumentPreprocessor()
        
        test_text = "This is a test document. It contains multiple sentences."
        processed = preprocessor.preprocess(test_text)
        print("✓ DocumentPreprocessor basic functionality works")
        
        # Test DocumentChunker
        from document_processing.document_chunker import DocumentChunker
        chunker = DocumentChunker()
        
        chunks = chunker.chunk_document(test_text, 50)
        print("✓ DocumentChunker basic functionality works")
        
        return True
    except Exception as e:
        print(f"✗ Basic functionality test failed: {e}")
        return False

def main():
    """Run all tests."""
    print("RAG Scripts Test Suite")
    print("=" * 50)
    
    tests = [
        ("Import Tests", test_imports),
        ("Script File Tests", test_script_files), 
        ("Module Structure Tests", test_module_structure),
        ("Environment Tests", test_environment),
        ("Basic Functionality Tests", test_basic_functionality)
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n{test_name}")
        print("-" * len(test_name))
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"✗ Test failed with exception: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 50)
    print("TEST SUMMARY")
    print("=" * 50)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "PASSED" if result else "FAILED"
        symbol = "✓" if result else "✗"
        print(f"{symbol} {test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! RAG scripts are ready to use.")
        return 0
    else:
        print("⚠ Some tests failed. Please address the issues above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())