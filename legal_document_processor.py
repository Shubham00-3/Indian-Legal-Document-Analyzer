# legal_document_processor.py
# Extended document processor with legal document capabilities

import re
from pypdf import PdfReader
from document_processor import DocumentProcessor
from langchain_text_splitters import RecursiveCharacterTextSplitter

class LegalDocumentProcessor(DocumentProcessor):
    def __init__(self, chunk_size=1000, chunk_overlap=200):
        """
        Initialize the legal document processor
        
        Parameters:
        - chunk_size: The size of each text chunk in characters
        - chunk_overlap: The overlap between chunks in characters
        """
        super().__init__(chunk_size, chunk_overlap)
        
        # Use a text splitter that better respects legal document structure
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separators=["\n\n", "\n", ". ", " ", ""],
            length_function=len
        )
    
    def load_document(self, file_path):
        """
        Load a document from various file formats
        
        Parameters:
        - file_path: Path to the file
        
        Returns:
        - The document text as a string
        """
        try:
            # Check file extension
            if file_path.lower().endswith('.pdf'):
                return self._load_pdf(file_path)
            else:
                # Use the parent class method for text files
                return super().load_document(file_path)
        except Exception as e:
            print(f"Error loading document: {e}")
            return None
    
    def _load_pdf(self, file_path):
        """Load text from a PDF file"""
        try:
            print(f"Loading PDF document: {file_path}")
            reader = PdfReader(file_path)
            text = ""
            
            # Extract text from each page
            for page in reader.pages:
                text += page.extract_text() + "\n\n"
            
            print(f"PDF loaded successfully: {len(text)} characters")
            return text
        except Exception as e:
            print(f"Error loading PDF: {e}")
            return None
            
    def split_text(self, text):
        """
        Split the text into chunks with basic legal metadata
        
        Parameters:
        - text: The document text
        
        Returns:
        - A list of text chunks with metadata
        """
        if not text:
            return []
        
        # Basic section detection
        section_pattern = re.compile(r'(?i)(?:section|article|clause)\s+(\d+[.\d]*)')
        
        # Split text into chunks
        basic_chunks = self.text_splitter.split_text(text)
        chunks_with_metadata = []
        
        # Add basic metadata to each chunk
        for i, chunk in enumerate(basic_chunks):
            # Find potential section numbers in this chunk
            section_matches = section_pattern.findall(chunk)
            
            # Add metadata
            metadata = {
                "chunk_id": i,
                "detected_sections": section_matches if section_matches else ["unknown"]
            }
            
            chunks_with_metadata.append({
                "content": chunk,
                "metadata": metadata
            })
        
        print(f"Document split into {len(chunks_with_metadata)} chunks with legal metadata")
        return chunks_with_metadata