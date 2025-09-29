#!/usr/bin/env python3
"""
Script to embed all JSON data from source directory into Qdrant vector store.
"""

import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Any

# Add the app directory to the Python path
sys.path.append(str(Path(__file__).parent.parent))

from app.core.config import settings
from app.models.embedding import get_embeddings
from app.models.vector_store import MessageVectorStore
from langchain_core.documents import Document


def load_json_files(source_dir: str) -> List[Dict[str, Any]]:
    """
    Load all JSON files from the source directory.
    
    Args:
        source_dir (str): Path to source directory
        
    Returns:
        List[Dict[str, Any]]: List of data from all JSON files
    """
    data = []
    source_path = Path(source_dir)
    
    if not source_path.exists():
        print(f"Source directory {source_dir} does not exist!")
        return data
    
    # Find all JSON files
    json_files = list(source_path.glob("*.json"))
    
    if not json_files:
        print(f"No JSON files found in {source_dir}")
        return data
    
    print(f"Found {len(json_files)} JSON files:")
    
    for json_file in json_files:
        print(f"  - {json_file.name}")
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                file_data = json.load(f)
                
                # If the file contains a list, extend the data
                if isinstance(file_data, list):
                    data.extend(file_data)
                else:
                    # If it's a single object, append it
                    data.append(file_data)
                    
        except Exception as e:
            print(f"Error loading {json_file}: {e}")
    
    print(f"Total items loaded: {len(data)}")
    return data


def create_documents_from_data(data: List[Dict[str, Any]]) -> List[Document]:
    """
    Convert data items to Document objects for vector store.
    
    Args:
        data (List[Dict[str, Any]]): List of data items
        
    Returns:
        List[Document]: List of Document objects
    """
    documents = []
    
    for item in data:
        # Extract content and metadata
        content = item.get('content', '')
        item_id = item.get('id', '')
        
        # Create metadata
        metadata = {
            'type': 'hsk_knowledge',
            'source': 'hsk_data',
            'item_id': str(item_id),
            'session_id': 'hsk_knowledge_base',  # Special session ID for knowledge base
        }
        
        # Create document
        doc = Document(page_content=content, metadata=metadata)
        documents.append(doc)
    
    return documents


def embed_data_to_qdrant(documents: List[Document], collection_name: str = "hsk_knowledge"):
    """
    Embed documents into Qdrant vector store.
    
    Args:
        documents (List[Document]): List of documents to embed
        collection_name (str): Name of the collection in Qdrant
    """
    print(f"Embedding {len(documents)} documents into Qdrant collection: {collection_name}")
    
    # Initialize vector store with custom collection name
    vector_store = MessageVectorStore(namespace=collection_name)
    
    # Add documents to vector store
    try:
        ids = vector_store.vector_store.add_documents(documents)
        print(f"Successfully embedded {len(ids)} documents")
        print(f"Document IDs: {ids[:5]}...")  # Show first 5 IDs
        
    except Exception as e:
        print(f"Error embedding documents: {e}")
        raise


def main():
    """Main function to run the embedding process."""
    print("Starting HSK data embedding process...")
    
    # Configuration
    source_dir = "source"
    collection_name = "hsk_knowledge"
    
    # Load data from JSON files
    print("\n1. Loading JSON data from source directory...")
    data = load_json_files(source_dir)
    
    if not data:
        print("No data found. Exiting.")
        return
    
    # Convert to documents
    print("\n2. Converting data to documents...")
    documents = create_documents_from_data(data)
    print(f"Created {len(documents)} documents")
    
    # Embed into Qdrant
    print("\n3. Embedding documents into Qdrant...")
    embed_data_to_qdrant(documents, collection_name)
    
    print("\n✅ Embedding process completed successfully!")
    print(f"Collection '{collection_name}' now contains {len(documents)} HSK knowledge items")


if __name__ == "__main__":
    main()
