# document_manager.py
# Manages multiple legal documents

import os
import uuid
from collections import defaultdict

class DocumentManager:
    def __init__(self):
        """Initialize the document manager"""
        self.documents = {}  # Document ID -> Document text
        self.document_metadata = {}  # Document ID -> Metadata
        self.current_document_id = None
    
    def add_document(self, document_text, file_path, doc_type="contract"):
        """
        Add a document to the manager
        
        Parameters:
        - document_text: The text content of the document
        - file_path: The original file path
        - doc_type: Type of document (contract, statute, case, etc.)
        
        Returns:
        - Document ID
        """
        # Generate a unique ID for this document
        doc_id = str(uuid.uuid4())[:8]
        
        # Store the document
        self.documents[doc_id] = document_text
        
        # Extract filename without path
        filename = os.path.basename(file_path)
        
        # Store basic metadata
        self.document_metadata[doc_id] = {
            "file_path": file_path,
            "filename": filename,
            "doc_type": doc_type,
            "char_count": len(document_text),
            "added_at": str(uuid.uuid1())  # Timestamp as string
        }
        
        # Set as current document
        self.current_document_id = doc_id
        
        return doc_id
    
    def get_document(self, doc_id=None):
        """
        Get a document by ID
        
        Parameters:
        - doc_id: The document ID (uses current document if None)
        
        Returns:
        - Document text and metadata
        """
        # Use current document if no ID specified
        if doc_id is None:
            doc_id = self.current_document_id
        
        if doc_id not in self.documents:
            return None, None
            
        return self.documents[doc_id], self.document_metadata[doc_id]
    
    def list_documents(self):
        """
        List all documents
        
        Returns:
        - List of document IDs and their metadata
        """
        return [(doc_id, self.document_metadata[doc_id]) 
                for doc_id in self.documents]
    
    def remove_document(self, doc_id):
        """
        Remove a document
        
        Parameters:
        - doc_id: The document ID
        """
        if doc_id in self.documents:
            del self.documents[doc_id]
            del self.document_metadata[doc_id]
            
            # Update current document if removed
            if self.current_document_id == doc_id:
                self.current_document_id = next(iter(self.documents)) if self.documents else None