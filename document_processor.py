# document_processor.py
# Handles loading and processing text documents for the RAG system

from langchain_text_splitters import RecursiveCharacterTextSplitter

class DocumentProcessor:
    def __init__(self, chunk_size=1000, chunk_overlap=200):
        """
        Initialize the document processor
        
        Parameters:
        - chunk_size: The size of each text chunk in characters
        - chunk_overlap: The overlap between chunks in characters
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len
        )
    
    def load_document(self, file_path):
        """
        Load a document from a file
        
        Parameters:
        - file_path: Path to the text file
        
        Returns:
        - The document text as a string
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                return file.read()
        except Exception as e:
            print(f"Error loading document: {e}")
            return None
    
    def split_text(self, text):
        """
        Split the text into chunks
        
        Parameters:
        - text: The document text
        
        Returns:
        - A list of text chunks
        """
        if not text:
            return []
        
        chunks = self.text_splitter.split_text(text)
        print(f"Document split into {len(chunks)} chunks")
        return chunks