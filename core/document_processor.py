# document_processor.py
# Unified document processor for loading and processing legal documents

import os
import re
from typing import Optional, List, Dict, Any
from langchain.text_splitter import RecursiveCharacterTextSplitter


class DocumentProcessor:
    """
    Unified document processor that handles:
    - Loading PDF and TXT files
    - Splitting text into chunks with metadata
    - Extracting legal document metadata (sections, dates, entities)
    """
    
    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200):
        """
        Initialize the document processor
        
        Parameters:
        - chunk_size: Size of each text chunk
        - chunk_overlap: Overlap between chunks
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        
        # Initialize text splitter
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len,
            separators=["\n\n", "\n", ".", " ", ""]
        )
        
        # Legal section patterns for Indian legal documents
        self.section_patterns = [
            r'Section\s+(\d+(?:\.\d+)?)',
            r'Article\s+(\d+(?:\.\d+)?)',
            r'Rule\s+(\d+(?:\.\d+)?)',
            r'Clause\s+(\d+(?:\.\d+)?)',
            r'(?:SECTION|ARTICLE)\s+(\d+(?:\.\d+)*)\s*\.\s*([A-Z][A-Z\s]+)'
        ]
    
    def load_document(self, file_path: str) -> Optional[str]:
        """
        Load a document from a file path (PDF or TXT)
        
        Parameters:
        - file_path: Path to the document
        
        Returns:
        - Document text or None if loading failed
        """
        if not os.path.exists(file_path):
            print(f"File not found: {file_path}")
            return None
        
        file_ext = os.path.splitext(file_path)[1].lower()
        
        try:
            if file_ext == '.pdf':
                return self._load_pdf(file_path)
            elif file_ext == '.txt':
                return self._load_txt(file_path)
            else:
                print(f"Unsupported file type: {file_ext}")
                return None
        except Exception as e:
            print(f"Error loading document: {e}")
            return None
    
    def _load_pdf(self, file_path: str) -> Optional[str]:
        """Load a PDF file"""
        try:
            from pypdf import PdfReader
            
            reader = PdfReader(file_path)
            text = ""
            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
            
            # Check if we got any text
            if not text.strip():
                print("PDF appears to be scanned/image-based. No text could be extracted.")
                print("Try using a text-based PDF or OCR the document first.")
                return None
                
            return text.strip()
        except ImportError:
            print("pypdf not installed. Run: pip install pypdf")
            return None
        except Exception as e:
            print(f"Error loading PDF: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def _load_txt(self, file_path: str) -> Optional[str]:
        """Load a text file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                return file.read()
        except UnicodeDecodeError:
            # Try with different encoding
            with open(file_path, 'r', encoding='latin-1') as file:
                return file.read()
    
    def split_text(self, text: str, include_metadata: bool = True) -> List[Dict[str, Any]]:
        """
        Split text into chunks with optional metadata
        
        Parameters:
        - text: Document text to split
        - include_metadata: Whether to include legal metadata for each chunk
        
        Returns:
        - List of dictionaries with 'content' and 'metadata' keys
        """
        if not text:
            return []
        
        # Split into chunks
        chunks = self.text_splitter.split_text(text)
        
        if not include_metadata:
            return [{"content": chunk, "metadata": {}} for chunk in chunks]
        
        # Add metadata to each chunk
        chunks_with_metadata = []
        for i, chunk in enumerate(chunks):
            metadata = {
                "chunk_index": i,
                "chunk_count": len(chunks),
                "detected_sections": self._detect_sections(chunk),
                "has_definitions": self._has_definitions(chunk),
                "has_penalties": self._has_penalties(chunk)
            }
            chunks_with_metadata.append({
                "content": chunk,
                "metadata": metadata
            })
        
        return chunks_with_metadata
    
    def _detect_sections(self, text: str) -> List[str]:
        """Detect section numbers in text"""
        sections = []
        for pattern in self.section_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                if isinstance(match, tuple):
                    sections.append(match[0])
                else:
                    sections.append(match)
        return sections if sections else ["unknown"]
    
    def _has_definitions(self, text: str) -> bool:
        """Check if chunk contains legal definitions"""
        definition_patterns = [
            r'"[^"]+"\s+means',
            r'shall mean',
            r'is defined as',
            r'Definition[s]?:',
            r'Interpretation:'
        ]
        return any(re.search(p, text, re.IGNORECASE) for p in definition_patterns)
    
    def _has_penalties(self, text: str) -> bool:
        """Check if chunk contains penalties or fines"""
        penalty_patterns = [
            r'penalty',
            r'fine',
            r'imprisonment',
            r'liable to',
            r'punishable',
            r'shall be punished'
        ]
        return any(re.search(p, text, re.IGNORECASE) for p in penalty_patterns)
    
    def extract_metadata(self, text: str) -> Dict[str, Any]:
        """
        Extract comprehensive metadata from document text
        
        Parameters:
        - text: Document text
        
        Returns:
        - Dictionary with extracted metadata
        """
        metadata = {
            "sections": self._extract_all_sections(text),
            "dates": self._extract_dates(text),
            "entities": self._extract_entities(text),
            "monetary_values": self._extract_monetary_values(text)
        }
        return metadata
    
    def _extract_all_sections(self, text: str) -> List[Dict[str, str]]:
        """Extract all section headers with titles"""
        sections = []
        pattern = r'(?:SECTION|ARTICLE|Section|Article)\s+(\d+(?:\.\d+)*)\s*[.:]?\s*([A-Za-z][A-Za-z\s,]+?)(?=\n|$)'
        matches = re.finditer(pattern, text)
        for match in matches:
            sections.append({
                "number": match.group(1),
                "title": match.group(2).strip()
            })
        return sections
    
    def _extract_dates(self, text: str) -> List[str]:
        """Extract dates from text"""
        date_patterns = [
            r'\d{1,2}(?:st|nd|rd|th)?\s+(?:January|February|March|April|May|June|July|August|September|October|November|December),?\s+\d{4}',
            r'(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+\d{4}',
            r'\d{1,2}/\d{1,2}/\d{4}',
            r'\d{4}-\d{2}-\d{2}'
        ]
        dates = []
        for pattern in date_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            dates.extend(matches)
        return list(set(dates))
    
    def _extract_entities(self, text: str) -> List[str]:
        """Extract organization/entity names"""
        entity_patterns = [
            r'(?:The\s+)?([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\s+(?:Ministry|Department|Commission|Authority|Board|Council|Committee|Corporation|Agency))',
            r'Government of (?:India|[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)'
        ]
        entities = []
        for pattern in entity_patterns:
            matches = re.findall(pattern, text)
            entities.extend(matches)
        return list(set(entities))
    
    def _extract_monetary_values(self, text: str) -> List[Dict[str, str]]:
        """Extract monetary values with context"""
        patterns = [
            r'(?:Rs\.?|INR|₹)\s*([\d,]+(?:\.\d{2})?)',
            r'\$\s*([\d,]+(?:\.\d{2})?)'
        ]
        values = []
        for pattern in patterns:
            for match in re.finditer(pattern, text):
                start = max(0, match.start() - 50)
                end = min(len(text), match.end() + 50)
                values.append({
                    "amount": match.group(0),
                    "context": text[start:end]
                })
        return values
