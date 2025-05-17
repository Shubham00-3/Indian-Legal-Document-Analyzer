# enhanced_document_processor.py
# Extended document processor with PDF support and Indian legal document capabilities

import re
from pypdf import PdfReader
from document_processor import DocumentProcessor
from langchain_text_splitters import RecursiveCharacterTextSplitter

class EnhancedDocumentProcessor(DocumentProcessor):
    def __init__(self, chunk_size=1000, chunk_overlap=200):
        """
        Initialize the enhanced document processor
        
        Parameters:
        - chunk_size: The size of each text chunk in characters
        - chunk_overlap: The overlap between chunks in characters
        """
        super().__init__(chunk_size, chunk_overlap)
        
        # Use a better text splitter that preserves document structure
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
            
    def extract_metadata(self, text):
        """
        Extract basic metadata from Indian legal document text
        
        Parameters:
        - text: Document text
        
        Returns:
        - Dictionary of metadata
        """
        metadata = {
            "sections": [],
            "entities": [],
            "dates": []
        }
        
        # Extract sections (e.g., "Section 1.2 Title" or common Indian format "1. Title")
        section_pattern = re.compile(r'(?i)(?:section|article)\s+(\d+(?:\.\d+)*)\s*[\.:]?\s*([^\n]+)')
        simple_section_pattern = re.compile(r'^(\d+)\.?\s+([A-Z][^\n]+)')
        
        for match in section_pattern.finditer(text):
            metadata["sections"].append({
                "number": match.group(1),
                "title": match.group(2).strip()
            })
        
        for match in simple_section_pattern.finditer(text, re.MULTILINE):
            metadata["sections"].append({
                "number": match.group(1),
                "title": match.group(2).strip()
            })
        
        # Extract dates (expanded pattern for Indian date formats)
        # Include formats like "1st January, 2023" or "1st day of January, 2023"
        date_pattern = re.compile(r'(?:\d{1,2}(?:st|nd|rd|th)?\s+(?:of\s+)?(?:January|February|March|April|May|June|July|August|September|October|November|December),?\s+\d{4})|(?:[A-Z][a-z]+\s+\d{1,2},\s+\d{4})')
        
        for match in date_pattern.finditer(text):
            metadata["dates"].append(match.group(0))
        
        # Extract entities - expanded for Indian organizations and govt bodies
        entity_pattern = re.compile(r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*(?:\s+(?:Inc\.|LLC|Ltd\.|Corporation|Company|Limited)))|([A-Z][a-z]*(?:\s+[A-Z][a-z]+)*\s+(?:Authority|Ministry|Board|Commission|Council|Court|Tribunal|Department))')
        
        for match in entity_pattern.finditer(text):
            entity = match.group(0)
            if entity and entity not in metadata["entities"]:
                metadata["entities"].append(entity)
        
        # Extract Indian statutes by name (common Indian laws)
        statute_pattern = re.compile(r'(?:The\s+)?([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\s+Act,?\s+(?:of\s+)?\d{4})')
        
        statute_references = []
        for match in statute_pattern.finditer(text):
            statute = match.group(0)
            if statute and statute not in statute_references:
                statute_references.append(statute)
        
        metadata["statutes"] = statute_references
        
        # Extract case citations (Indian format)
        case_pattern = re.compile(r'\(\d{4}\)\s+\d+\s+SCC\s+\d+|\d{4}\s+\(\d+\)\s+SCC\s+\d+')
        
        case_citations = []
        for match in case_pattern.finditer(text):
            citation = match.group(0)
            if citation and citation not in case_citations:
                case_citations.append(citation)
        
        metadata["case_citations"] = case_citations
        
        return metadata