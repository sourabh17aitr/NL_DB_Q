"""
Utility functions for Vector DB UI
"""
import os
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional
import logging

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent.parent))

import chromadb
from langchain_community.vectorstores import Chroma
import streamlit as st

from config.vector_config import VECTOR_DB_SCHEMA_DIR, VECTOR_DB_SCHEMA_NAME
from config.models import get_vector_embeddings

logger = logging.getLogger(__name__)


@st.cache_data(ttl=300)
def get_vector_store_info() -> Optional[Dict[str, Any]]:
    """
    Get information about available vector stores.
    
    Returns:
        Dictionary containing vector store information
    """
    try:
        if not os.path.exists(VECTOR_DB_SCHEMA_DIR):
            return None
        
        # List all subdirectories (collections) and also check root
        collections = []
        paths_to_check = [VECTOR_DB_SCHEMA_DIR]
        
        # Add subdirectories that contain chroma.sqlite3
        for item in os.listdir(VECTOR_DB_SCHEMA_DIR):
            item_path = os.path.join(VECTOR_DB_SCHEMA_DIR, item)
            if os.path.isdir(item_path):
                chroma_file = os.path.join(item_path, "chroma.sqlite3")
                if os.path.exists(chroma_file):
                    paths_to_check.append(item_path)
        
        # Check each path for collections
        for check_path in paths_to_check:
            try:
                client = chromadb.PersistentClient(path=check_path)
                chroma_collections = client.list_collections()
                
                for collection in chroma_collections:
                    doc_count = collection.count()
                    
                    # Get sample metadata
                    sample_metadata = {}
                    if doc_count > 0:
                        sample = collection.get(limit=1)
                        if sample and sample.get('metadatas'):
                            sample_metadata = sample['metadatas'][0]
                    
                    collections.append({
                        'name': collection.name,
                        'path': check_path,
                        'document_count': doc_count,
                        'metadata_count': len(sample_metadata),
                        'sample_metadata': sample_metadata
                    })
            except Exception as e:
                logger.error(f"Error loading collection from {check_path}: {e}")
                continue
        
        return {
            'collections': collections,
            'db_type': 'Chroma',
            'base_path': VECTOR_DB_SCHEMA_DIR
        }
    
    except Exception as e:
        logger.error(f"Error getting vector store info: {e}")
        return None


@st.cache_data(ttl=300)
def get_all_documents() -> List[Dict[str, Any]]:
    """
    Get all documents from all collections in the vector store.
    
    Returns:
        List of documents with their content and metadata
    """
    try:
        documents = []
        
        if not os.path.exists(VECTOR_DB_SCHEMA_DIR):
            return documents
        
        # Check root directory and subdirectories
        paths_to_check = [VECTOR_DB_SCHEMA_DIR]
        
        # Add subdirectories that contain chroma.sqlite3
        for item in os.listdir(VECTOR_DB_SCHEMA_DIR):
            item_path = os.path.join(VECTOR_DB_SCHEMA_DIR, item)
            if os.path.isdir(item_path):
                chroma_file = os.path.join(item_path, "chroma.sqlite3")
                if os.path.exists(chroma_file):
                    paths_to_check.append(item_path)
        
        # Iterate through all paths
        for check_path in paths_to_check:
            try:
                client = chromadb.PersistentClient(path=check_path)
                chroma_collections = client.list_collections()
                
                for collection in chroma_collections:
                    # Get all documents from collection
                    results = collection.get()
                    
                    if results and results.get('documents'):
                        for idx, doc in enumerate(results['documents']):
                            metadata = results['metadatas'][idx] if results.get('metadatas') else {}
                            doc_id = results['ids'][idx] if results.get('ids') else f"doc_{idx}"
                            
                            documents.append({
                                'id': doc_id,
                                'content': doc,
                                'metadata': metadata,
                                'collection': collection.name
                            })
            except Exception as e:
                logger.error(f"Error loading documents from {check_path}: {e}")
                continue
        
        return documents
    
    except Exception as e:
        logger.error(f"Error getting all documents: {e}")
        return []


def search_vector_store(query: str, k: int = 5) -> List[Dict[str, Any]]:
    """
    Search the vector store with a query.
    
    Args:
        query: Search query string
        k: Number of results to return
    
    Returns:
        List of search results with content, metadata, and scores
    """
    try:
        results = []
        
        if not os.path.exists(VECTOR_DB_SCHEMA_DIR):
            return results
        
        # Check root directory and subdirectories
        paths_to_check = [VECTOR_DB_SCHEMA_DIR]
        
        # Add subdirectories that contain chroma.sqlite3
        for item in os.listdir(VECTOR_DB_SCHEMA_DIR):
            item_path = os.path.join(VECTOR_DB_SCHEMA_DIR, item)
            if os.path.isdir(item_path):
                chroma_file = os.path.join(item_path, "chroma.sqlite3")
                if os.path.exists(chroma_file):
                    paths_to_check.append(item_path)
        
        # Search in all paths
        for check_path in paths_to_check:
            try:
                client = chromadb.PersistentClient(path=check_path)
                chroma_collections = client.list_collections()
                
                for collection in chroma_collections:
                    # Use Langchain Chroma for similarity search
                    vectorstore = Chroma(
                        client=client,
                        collection_name=collection.name,
                        embedding_function=get_vector_embeddings()
                    )
                    
                    # Perform similarity search
                    search_results = vectorstore.similarity_search_with_score(query, k=k)
                    
                    for doc, score in search_results:
                        results.append({
                            'content': doc.page_content,
                            'metadata': doc.metadata,
                            'similarity_score': score,
                            'collection': collection.name
                        })
            except Exception as e:
                logger.error(f"Error searching in {check_path}: {e}")
                continue
        
        # Sort by similarity score (lower is better for distance metrics)
        results.sort(key=lambda x: x['similarity_score'])
        
        return results[:k]
    
    except Exception as e:
        logger.error(f"Error searching vector store: {e}")
        return []


@st.cache_data(ttl=300)
def get_collection_stats() -> Dict[str, Any]:
    """
    Get detailed statistics about collections.
    
    Returns:
        Dictionary with collection statistics
    """
    try:
        stats = {
            'total_collections': 0,
            'total_documents': 0,
            'total_tables': 0,
            'database_types': 0,
            'collections': {},
            'db_type_distribution': {}
        }
        
        documents = get_all_documents()
        
        if not documents:
            return stats
        
        # Group by collection
        collections_dict = {}
        for doc in documents:
            coll_name = doc.get('collection', 'Unknown')
            if coll_name not in collections_dict:
                collections_dict[coll_name] = []
            collections_dict[coll_name].append(doc)
        
        stats['total_collections'] = len(collections_dict)
        stats['total_documents'] = len(documents)
        
        # Collect database types
        db_types = set()
        all_tables = set()
        
        for coll_name, coll_docs in collections_dict.items():
            tables = set()
            db_type = None
            database = None
            
            for doc in coll_docs:
                metadata = doc.get('metadata', {})
                
                # Collect table names
                table_name = metadata.get('table_name')
                if table_name:
                    tables.add(table_name)
                    all_tables.add(table_name)
                
                # Get DB type and database name
                if not db_type:
                    db_type = metadata.get('db_type', 'Unknown')
                    db_types.add(db_type)
                
                if not database:
                    database = metadata.get('database_name', 'Unknown')
            
            # Store collection stats
            stats['collections'][coll_name] = {
                'document_count': len(coll_docs),
                'table_count': len(tables),
                'tables': sorted(list(tables)),
                'db_type': db_type,
                'database': database
            }
            
            # Count DB type distribution
            if db_type:
                stats['db_type_distribution'][db_type] = stats['db_type_distribution'].get(db_type, 0) + 1
        
        stats['database_types'] = len(db_types)
        stats['total_tables'] = len(all_tables)
        
        return stats
    
    except Exception as e:
        logger.error(f"Error getting collection stats: {e}")
        return {}


def get_collection_list() -> List[str]:
    """
    Get list of all collection names.
    
    Returns:
        List of collection names
    """
    try:
        collections = []
        
        if not os.path.exists(VECTOR_DB_SCHEMA_DIR):
            return collections
        
        # Check root directory and subdirectories
        paths_to_check = [VECTOR_DB_SCHEMA_DIR]
        
        # Add subdirectories that contain chroma.sqlite3
        for item in os.listdir(VECTOR_DB_SCHEMA_DIR):
            item_path = os.path.join(VECTOR_DB_SCHEMA_DIR, item)
            if os.path.isdir(item_path):
                chroma_file = os.path.join(item_path, "chroma.sqlite3")
                if os.path.exists(chroma_file):
                    paths_to_check.append(item_path)
        
        # Get collections from all paths
        for check_path in paths_to_check:
            try:
                client = chromadb.PersistentClient(path=check_path)
                chroma_collections = client.list_collections()
                
                for collection in chroma_collections:
                    collections.append(collection.name)
            except Exception as e:
                logger.error(f"Error listing collections in {check_path}: {e}")
                continue
        
        return collections
    
    except Exception as e:
        logger.error(f"Error getting collection list: {e}")
        return []
