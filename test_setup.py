#!/usr/bin/env python3
"""
Test script to verify the setup is working correctly
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_imports():
    """Test if all required modules can be imported"""
    print("Testing imports...")
    
    try:
        import fastapi
        print("✅ FastAPI imported successfully")
    except ImportError as e:
        print(f"❌ FastAPI import failed: {e}")
        return False
    
    try:
        import uvicorn
        print("✅ Uvicorn imported successfully")
    except ImportError as e:
        print(f"❌ Uvicorn import failed: {e}")
        return False
    
    try:
        import sentence_transformers
        print("✅ Sentence Transformers imported successfully")
    except ImportError as e:
        print(f"❌ Sentence Transformers import failed: {e}")
        return False
    
    try:
        import google.generativeai
        print("✅ Google Generative AI imported successfully")
    except ImportError as e:
        print(f"❌ Google Generative AI import failed: {e}")
        return False
    
    try:
        import magic
        print("✅ Python Magic imported successfully")
    except ImportError as e:
        print(f"❌ Python Magic import failed: {e}")
        return False
    
    return True

def test_database():
    """Test database connection"""
    print("\nTesting database connection...")
    
    try:
        from services.embedding_service import EmbeddingService
        from config import Config
        
        print(f"Database URL: {Config.DATABASE_URL}")
        
        # Test embedding service initialization
        embedding_service = EmbeddingService(
            database_url=Config.DATABASE_URL,
            model_name=Config.EMBEDDING_MODEL
        )
        print("✅ Database connection successful")
        print(f"✅ Database type: {embedding_service.db_type}")
        
        # Test basic operations
        test_chunks = ["This is a test document chunk.", "Another test chunk for verification."]
        chunks_stored = embedding_service.store_embeddings("test_doc", test_chunks)
        print(f"✅ Stored {chunks_stored} test embeddings")
        
        # Test search
        results = embedding_service.search_similar("test document", top_k=5)
        print(f"✅ Search returned {len(results)} results")
        
        return True
        
    except Exception as e:
        print(f"❌ Database test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_config():
    """Test configuration loading"""
    print("\nTesting configuration...")
    
    try:
        from config import Config
        
        print(f"✅ Google API Key: {'Set' if Config.GOOGLE_API_KEY else 'Not set'}")
        print(f"✅ Database URL: {Config.DATABASE_URL}")
        print(f"✅ Embedding Model: {Config.EMBEDDING_MODEL}")
        print(f"✅ Reranker Model: {Config.RERANKER_MODEL}")
        
        if not Config.GOOGLE_API_KEY:
            print("⚠️  Warning: Google API key not set. Some features may not work.")
        
        return True
        
    except Exception as e:
        print(f"❌ Configuration test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🧪 Testing Document Search API Setup")
    print("=" * 50)
    
    # Test imports
    if not test_imports():
        print("\n❌ Import tests failed. Please install missing dependencies.")
        return False
    
    # Test configuration
    if not test_config():
        print("\n❌ Configuration test failed. Please check your .env file.")
        return False
    
    # Test database
    if not test_database():
        print("\n❌ Database test failed. Please check your database configuration.")
        return False
    
    print("\n🎉 All tests passed! Your setup is ready.")
    print("\nYou can now run:")
    print("  python run_local.py")
    print("  or")
    print("  start_local.bat")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 