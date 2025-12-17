# document_manager.py
# Manages multiple legal documents in memory

import os
import uuid
from typing import Optional, Dict, List, Tuple, Any


class DocumentManager:
    """Manages multiple legal documents with metadata"""
    
    def __init__(self):
        """Initialize the document manager"""
        self.documents: Dict[str, str] = {}  # doc_id -> text
        self.document_metadata: Dict[str, Dict[str, Any]] = {}  # doc_id -> metadata
        self.current_document_id: Optional[str] = None
    
    def add_document(
        self, 
        document_text: str, 
        file_path: str, 
        doc_type: str = "contract"
    ) -> str:
        """
        Add a document to the manager
        
        Parameters:
        - document_text: The text content of the document
        - file_path: The original file path
        - doc_type: Type of document (contract, statute, case, etc.)
        
        Returns:
        - Document ID
        """
        doc_id = str(uuid.uuid4())[:8]
        
        self.documents[doc_id] = document_text
        self.document_metadata[doc_id] = {
            "file_path": file_path,
            "filename": os.path.basename(file_path),
            "doc_type": doc_type,
            "char_count": len(document_text),
            "added_at": str(uuid.uuid1())
        }
        
        self.current_document_id = doc_id
        return doc_id
    
    def get_document(
        self, 
        doc_id: Optional[str] = None
    ) -> Tuple[Optional[str], Optional[Dict[str, Any]]]:
        """
        Get a document by ID
        
        Parameters:
        - doc_id: Document ID (uses current if None)
        
        Returns:
        - Tuple of (document_text, metadata)
        """
        if doc_id is None:
            doc_id = self.current_document_id
        
        if doc_id not in self.documents:
            return None, None
        
        return self.documents[doc_id], self.document_metadata[doc_id]
    
    def list_documents(self) -> List[Tuple[str, Dict[str, Any]]]:
        """
        List all documents
        
        Returns:
        - List of (doc_id, metadata) tuples
        """
        return [(doc_id, self.document_metadata[doc_id]) 
                for doc_id in self.documents]
    
    def remove_document(self, doc_id: str) -> bool:
        """
        Remove a document
        
        Parameters:
        - doc_id: Document ID to remove
        
        Returns:
        - True if removed, False if not found
        """
        if doc_id not in self.documents:
            return False
        
        del self.documents[doc_id]
        del self.document_metadata[doc_id]
        
        if self.current_document_id == doc_id:
            self.current_document_id = next(iter(self.documents), None)
        
        return True
    
    def set_current_document(self, doc_id: str) -> bool:
        """
        Set the current active document
        
        Parameters:
        - doc_id: Document ID to set as current
        
        Returns:
        - True if set, False if not found
        """
        if doc_id not in self.documents:
            return False
        
        self.current_document_id = doc_id
        return True
