# legal_embedding_store.py
# Enhanced embedding store for legal documents

import os
from dotenv import load_dotenv
from embedding_store import EmbeddingStore
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_pinecone import PineconeVectorStore
from pinecone import Pinecone, ServerlessSpec
import uuid
import json

# Load environment variables
load_dotenv()

class LegalEmbeddingStore(EmbeddingStore):
    def __init__(self):
        """Initialize the embedding store for legal documents"""
        super().__init__()
        
        # We're using the parent class initialization, but could add
        # legal-specific embeddings models in the future
    
    def create_vector_store(self, chunks_with_metadata):
        """
        Create a vector store from text chunks with metadata
        
        Parameters:
        - chunks_with_metadata: List of dictionaries with 'content' and 'metadata'
        
        Returns:
        - Pinecone vector store object
        """
        if not chunks_with_metadata:
            print("No chunks provided")
            return None
        
        # Create a namespace for this document
        namespace = f"legal_doc_{uuid.uuid4().hex[:8]}"
        
        # Create vector store
        print(f"Creating legal vector store in Pinecone (namespace: {namespace})...")
        
        try:
            # Extract texts and metadatas
            texts = [chunk["content"] for chunk in chunks_with_metadata]
            metadatas = [chunk["metadata"] for chunk in chunks_with_metadata]
            
            # Create the vector store with metadata
            self.vector_store = PineconeVectorStore.from_texts(
                texts=texts,
                embedding=self.embeddings,
                index_name=self.index_name,
                namespace=namespace,
                metadatas=metadatas
            )
            
            # Store the namespace for future use
            self.current_namespace = namespace
            
            print("Legal vector store created successfully in Pinecone")
            return self.vector_store
            
        except Exception as e:
            print(f"Error creating legal vector store: {e}")
            return None
    
    def search_by_metadata(self, metadata_filter, top_k=5):
        """
        Search for documents by metadata
        
        Parameters:
        - metadata_filter: Dictionary of metadata filters
        - top_k: Number of results to return
        
        Returns:
        - List of matching documents
        """
        if not self.vector_store:
            print("No vector store initialized")
            return []
        
        try:
            # Convert filter to Pinecone filter format
            filter_dict = {}
            for key, value in metadata_filter.items():
                if isinstance(value, list):
                    # If it's a list, use $in operator
                    filter_dict[key] = {"$in": value}
                else:
                    # Otherwise exact match
                    filter_dict[key] = value
            
            # Create a dummy query vector (using average of corpus)
            # This is a trick to search by metadata only
            results = self.vector_store.similarity_search(
                query="",  # Empty query to focus on metadata
                k=top_k,
                filter=filter_dict,
                namespace=self.current_namespace
            )
            
            return results
        
        except Exception as e:
            print(f"Error searching by metadata: {e}")
            return []