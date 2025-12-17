# embedding_store.py
# Unified embedding store for document embeddings with Pinecone

import os
import uuid
from typing import Optional, List, Dict, Any
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class EmbeddingStore:
    """
    Unified embedding store that handles:
    - HuggingFace embeddings
    - Pinecone vector storage
    - Metadata-based search
    """
    
    def __init__(self):
        """Initialize the embedding store with HuggingFace embeddings and Pinecone"""
        # Get Pinecone credentials from environment variables
        self.api_key = os.getenv("PINECONE_API_KEY")
        self.environment = os.getenv("PINECONE_ENVIRONMENT")
        self.index_name = os.getenv("PINECONE_INDEX_NAME")
        
        if not self.api_key or not self.environment or not self.index_name:
            raise ValueError(
                "Pinecone credentials not found. Please set PINECONE_API_KEY, "
                "PINECONE_ENVIRONMENT, and PINECONE_INDEX_NAME in your .env file"
            )
        
        # Initialize Pinecone
        from pinecone import Pinecone, ServerlessSpec
        self.pc = Pinecone(api_key=self.api_key)
        
        # Check if index exists, create it if it doesn't
        existing_indexes = [index.name for index in self.pc.list_indexes()]
        if self.index_name not in existing_indexes:
            print(f"Index {self.index_name} not found, creating...")
            self.pc.create_index(
                name=self.index_name,
                dimension=384,  # Dimension for all-MiniLM-L6-v2
                metric="cosine",
                spec=ServerlessSpec(
                    cloud="aws",
                    region=self.environment
                )
            )
            print(f"Index {self.index_name} created")
        
        # Initialize embeddings
        from langchain_community.embeddings import HuggingFaceEmbeddings
        self.embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2"
        )
        
        # Initialize vector store
        self.vector_store = None
        self.current_namespace = None
        
        print(f"Embedding store initialized with Pinecone index: {self.index_name}")
    
    def create_vector_store(self, chunks_with_metadata: List[Dict[str, Any]]) -> Optional[Any]:
        """
        Create a vector store from text chunks with metadata
        
        Parameters:
        - chunks_with_metadata: List of dicts with 'content' and 'metadata' keys
        
        Returns:
        - Pinecone vector store object
        """
        if not chunks_with_metadata:
            print("No chunks provided")
            return None
        
        # Create a namespace for this document
        namespace = f"legal_doc_{uuid.uuid4().hex[:8]}"
        
        print(f"Creating vector store in Pinecone (namespace: {namespace})...")
        
        try:
            from langchain_pinecone import PineconeVectorStore
            
            # Handle both formats: list of dicts or list of strings
            if isinstance(chunks_with_metadata[0], dict):
                texts = [chunk["content"] for chunk in chunks_with_metadata]
                metadatas = [chunk.get("metadata", {}) for chunk in chunks_with_metadata]
            else:
                texts = chunks_with_metadata
                metadatas = None
            
            # Create the vector store
            self.vector_store = PineconeVectorStore.from_texts(
                texts=texts,
                embedding=self.embeddings,
                index_name=self.index_name,
                namespace=namespace,
                metadatas=metadatas
            )
            
            self.current_namespace = namespace
            print("Vector store created successfully")
            return self.vector_store
            
        except Exception as e:
            print(f"Error creating vector store: {e}")
            return None
    
    def get_vector_store(self, namespace: Optional[str] = None) -> Optional[Any]:
        """
        Get an existing vector store from Pinecone
        
        Parameters:
        - namespace: Optional namespace to use
        
        Returns:
        - Pinecone vector store object
        """
        namespace = namespace or self.current_namespace
        
        if not namespace:
            print("No namespace specified and no current namespace found")
            return None
        
        print(f"Loading vector store from Pinecone (namespace: {namespace})...")
        
        try:
            from langchain_pinecone import PineconeVectorStore
            
            self.vector_store = PineconeVectorStore(
                embedding=self.embeddings,
                index_name=self.index_name,
                namespace=namespace
            )
            
            print("Vector store loaded successfully")
            return self.vector_store
            
        except Exception as e:
            print(f"Error loading vector store: {e}")
            return None
    
    def search_by_metadata(self, metadata_filter: Dict[str, Any], top_k: int = 5) -> List[Any]:
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
                    filter_dict[key] = {"$in": value}
                else:
                    filter_dict[key] = value
            
            results = self.vector_store.similarity_search(
                query="",
                k=top_k,
                filter=filter_dict,
                namespace=self.current_namespace
            )
            
            return results
        
        except Exception as e:
            print(f"Error searching by metadata: {e}")
            return []
