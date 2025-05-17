# legal_qa_chain.py
# Enhanced QA chain for legal document analysis

import os
from dotenv import load_dotenv
from qa_chain import QAChain
from langchain.prompts import PromptTemplate
from langchain.chains.retrieval_qa.base import RetrievalQA
from langchain_groq import ChatGroq

# Load environment variables
load_dotenv()

class LegalQAChain(QAChain):
    def __init__(self, vector_store=None, model_name="llama3-70b-8192"):
        """
        Initialize the legal QA chain
        
        Parameters:
        - vector_store: Vector store with legal document embeddings
        - model_name: Groq model name to use
        """
        # Call parent constructor
        super().__init__(vector_store, model_name)
    
    def _initialize_chain(self):
        """Initialize the QA chain with legal-specific prompt"""
        # Initialize the Groq language model
        llm = ChatGroq(
            groq_api_key=self.api_key,
            model_name=self.model_name
        )
        
        # Create a retriever from the vector store
        retriever = self.vector_store.as_retriever(
            search_type="similarity",
            search_kwargs={"k": 5}  # Return top 5 most relevant chunks for legal context
        )
        
        # Define a custom prompt template for legal analysis
        legal_template = """You are a legal document analysis assistant. Use the following pieces of legal text to answer the question at the end.

If the answer can be found directly in the text, cite the specific section or article number. If you need to make a legal interpretation, clearly indicate that you are interpreting the text and not quoting it directly.

Remember that legal analysis requires precision and caution. If the text does not contain sufficient information to answer confidently, explain what information is missing. Do not make definitive legal conclusions without adequate support from the document.

Legal Text:
{context}

Question: {question}

Answer (with citations where applicable):
"""
        
        legal_prompt = PromptTemplate(
            template=legal_template,
            input_variables=["context", "question"]
        )
        
        # Create the QA chain with legal prompt
        self.qa_chain = RetrievalQA.from_chain_type(
            llm=llm,
            chain_type="stuff",  # 'stuff' puts all retrieved docs into the prompt
            retriever=retriever,
            return_source_documents=True,
            verbose=True,
            chain_type_kwargs={
                "prompt": legal_prompt
            }
        )
        
        print(f"Legal QA Chain initialized with {self.model_name}")
    
    def ask(self, question):
        """
        Ask a question about legal document and get an answer with citations
        
        Parameters:
        - question: The question to ask
        
        Returns:
        - The answer with citations and source documents
        """
        # Use parent class to get basic response
        result = super().ask(question)
        
        # Enhance the result with section citations
        if result and "source_documents" in result:
            # Extract section information from metadata
            citations = []
            for doc in result["source_documents"]:
                if hasattr(doc, 'metadata') and doc.metadata:
                    sections = doc.metadata.get('detected_sections', [])
                    if sections and sections[0] != "unknown":
                        for section in sections:
                            citations.append(f"Section {section}")
            
            # Add citations to the result
            if citations:
                unique_citations = list(set(citations))  # Remove duplicates
                result["citations"] = unique_citations
        
        return result