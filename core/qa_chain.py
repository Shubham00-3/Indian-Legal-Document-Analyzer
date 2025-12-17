# qa_chain.py
# Unified QA chain for legal document question answering

import os
from typing import Optional, Dict, Any, List
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class QAChain:
    """
    Unified QA chain that handles:
    - Groq LLM integration
    - Legal-specific prompts
    - Citation extraction
    """
    
    def __init__(self, vector_store=None, model_name: str = "llama-3.3-70b-versatile"):
        """
        Initialize the QA chain
        
        Parameters:
        - vector_store: Pinecone vector store with document embeddings
        - model_name: Groq model name to use
        """
        self.api_key = os.getenv("GROQ_API_KEY")
        if not self.api_key:
            raise ValueError("GROQ_API_KEY not found in environment variables")
        
        self.vector_store = vector_store
        self.model_name = model_name
        self.qa_chain = None
        
        if self.vector_store:
            self._initialize_chain()
    
    def _initialize_chain(self):
        """Initialize the QA chain with legal-specific prompt"""
        from langchain_groq import ChatGroq
        from langchain.chains.retrieval_qa.base import RetrievalQA
        from langchain.prompts import PromptTemplate
        
        # Initialize the Groq LLM
        llm = ChatGroq(
            groq_api_key=self.api_key,
            model_name=self.model_name
        )
        
        # Create retriever from vector store
        retriever = self.vector_store.as_retriever(
            search_type="similarity",
            search_kwargs={"k": 5}  # Top 5 chunks for legal context
        )
        
        # Legal-specific prompt template
        legal_template = """You are a legal document analysis assistant specializing in Indian law. 
Use the following pieces of legal text to answer the question at the end.

If the answer can be found directly in the text, cite the specific section or article number.
If you need to make a legal interpretation, clearly indicate that you are interpreting the text.
If the text does not contain sufficient information, explain what information is missing.
Do not make definitive legal conclusions without adequate support from the document.

Legal Text:
{context}

Question: {question}

Answer (with citations where applicable):
"""
        
        prompt = PromptTemplate(
            template=legal_template,
            input_variables=["context", "question"]
        )
        
        # Create the QA chain
        self.qa_chain = RetrievalQA.from_chain_type(
            llm=llm,
            chain_type="stuff",
            retriever=retriever,
            return_source_documents=True,
            verbose=True,
            chain_type_kwargs={"prompt": prompt}
        )
        
        print(f"QA Chain initialized with {self.model_name}")
    
    def set_vector_store(self, vector_store):
        """Set or update the vector store"""
        self.vector_store = vector_store
        self._initialize_chain()
    
    def ask(self, question: str) -> Dict[str, Any]:
        """
        Ask a question and get an answer with citations
        
        Parameters:
        - question: The question to ask
        
        Returns:
        - Dictionary with 'result', 'source_documents', and 'citations'
        """
        if not self.qa_chain:
            return {"result": "System not ready. Please load a document first."}
        
        print(f"Question: {question}")
        
        try:
            result = self.qa_chain({"query": question})
            
            # Extract section citations from source documents
            if "source_documents" in result:
                citations = self._extract_citations(result["source_documents"])
                if citations:
                    result["citations"] = citations
            
            return result
            
        except Exception as e:
            print(f"Error getting answer: {e}")
            return {"result": f"Error: {str(e)}"}
    
    def _extract_citations(self, source_documents: List[Any]) -> List[str]:
        """Extract section citations from source document metadata"""
        citations = []
        for doc in source_documents:
            if hasattr(doc, 'metadata') and doc.metadata:
                sections = doc.metadata.get('detected_sections', [])
                if sections and sections[0] != "unknown":
                    for section in sections:
                        citations.append(f"Section {section}")
        
        # Remove duplicates while preserving order
        return list(dict.fromkeys(citations))
