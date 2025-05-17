# embedding_store.py
# Handles document embeddings and vector storage with Pinecone

import os
from dotenv import load_dotenv
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_pinecone import PineconeVectorStore
from pinecone import Pinecone, ServerlessSpec
import uuid

# Load environment variables
load_dotenv()

class EmbeddingStore:
    def __init__(self):
        """
        Initialize the embedding store with HuggingFace embeddings and Pinecone
        """
        # Get Pinecone credentials from environment variables
        self.api_key = os.getenv("PINECONE_API_KEY")
        self.environment = os.getenv("PINECONE_ENVIRONMENT")
        self.index_name = os.getenv("PINECONE_INDEX_NAME")
        
        if not self.api_key or not self.environment or not self.index_name:
            raise ValueError("Pinecone credentials not found in environment variables")
        
        # Initialize Pinecone with the new API
        self.pc = Pinecone(api_key=self.api_key)
        
        # Check if index exists, create it if it doesn't
        if self.index_name not in [index.name for index in self.pc.list_indexes()]:
            print(f"Index {self.index_name} not found, creating...")
            # Create the index with the new API
            self.pc.create_index(
                name=self.index_name,
                dimension=384,  # Dimension for the all-MiniLM-L6-v2 model
                metric="cosine",
                spec=ServerlessSpec(
                    cloud="aws",
                    region=self.environment
                )
            )
            print(f"Index {self.index_name} created")
        
        # Initialize embeddings
        self.embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2"
        )
        
        # Initialize vector store
        self.vector_store = None
        self.current_namespace = None
        
        print(f"Embedding store initialized with Pinecone index: {self.index_name}")
    
    def create_vector_store(self, text_chunks):
        """
        Create a vector store from text chunks
        
        Parameters:
        - text_chunks: List of text chunks
        
        Returns:
        - Pinecone vector store object
        """
        if not text_chunks:
            print("No text chunks provided")
            return None
        
        # Create a namespace for this document
        # This helps keep different documents separate in the same index
        namespace = f"doc_{uuid.uuid4().hex[:8]}"
        
        # Create vector store
        print(f"Creating vector store in Pinecone (namespace: {namespace})...")
        
        try:
            # Create the vector store
            self.vector_store = PineconeVectorStore.from_texts(
                texts=text_chunks,
                embedding=self.embeddings,
                index_name=self.index_name,
                namespace=namespace
            )
            
            # Store the namespace for future use
            self.current_namespace = namespace
            
            print("Vector store created successfully in Pinecone")
            return self.vector_store
            
        except Exception as e:
            print(f"Error creating vector store: {e}")
            return None
    
    def get_vector_store(self, namespace=None):
        """
        Get an existing vector store from Pinecone
        
        Parameters:
        - namespace: Optional namespace to use (otherwise uses current namespace)
        
        Returns:
        - Pinecone vector store object
        """
        namespace = namespace or getattr(self, 'current_namespace', None)
        
        if not namespace:
            print("No namespace specified and no current namespace found")
            return None
        
        print(f"Loading vector store from Pinecone (namespace: {namespace})...")
        
        try:
            # Connect to the existing vector store
            self.vector_store = PineconeVectorStore(
                embedding=self.embeddings,
                index_name=self.index_name,
                namespace=namespace
            )
            
            print("Vector store loaded successfully from Pinecone")
            return self.vector_store
            
        except Exception as e:
            print(f"Error loading vector store: {e}")
            return None