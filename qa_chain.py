# qa_chain.py
# Handles the QA chain for generating answers using Groq and Pinecone

import os
from dotenv import load_dotenv
from langchain.chains.retrieval_qa.base import RetrievalQA
from langchain.prompts import PromptTemplate
from langchain_groq import ChatGroq

# Load environment variables
load_dotenv()

class QAChain:
    def __init__(self, vector_store=None, model_name="llama3-70b-8192"):
        """
        Initialize the QA chain
        
        Parameters:
        - vector_store: Pinecone vector store
        - model_name: Groq model name to use
        """
        # Get Groq API key from environment
        self.api_key = os.getenv("GROQ_API_KEY")
        if not self.api_key:
            raise ValueError("GROQ_API_KEY not found in environment variables")
            
        self.vector_store = vector_store
        self.model_name = model_name
        self.qa_chain = None
        
        # Initialize if vector store is provided
        if self.vector_store:
            self._initialize_chain()
    
    def _initialize_chain(self):
        """Initialize the QA chain with the LLM and retriever"""
        # Initialize the Groq language model
        llm = ChatGroq(
            groq_api_key=self.api_key,
            model_name=self.model_name
        )
        
        # Create a retriever from the vector store
        retriever = self.vector_store.as_retriever(
            search_type="similarity",
            search_kwargs={"k": 3}  # Return top 3 most relevant chunks
        )
        
        # Define a custom prompt template that instructs the model how to use the context
        template = """You are a helpful AI assistant. Use the following pieces of context to answer the question at the end.
If you don't know the answer based on the context, say "I don't know" or "I can't find information about that in this document."
Don't try to make up an answer.

Context:
{context}

Question: {question}

Answer:
"""
        prompt = PromptTemplate(
            template=template,
            input_variables=["context", "question"]
        )
        
        # Create the QA chain
        self.qa_chain = RetrievalQA.from_chain_type(
            llm=llm,
            chain_type="stuff",  # 'stuff' puts all retrieved docs into the prompt
            retriever=retriever,
            return_source_documents=True,
            verbose=True,
            chain_type_kwargs={
                "prompt": prompt
            }
        )
        
        print(f"QA Chain initialized with {self.model_name}")
    
    def set_vector_store(self, vector_store):
        """Set or update the vector store"""
        self.vector_store = vector_store
        self._initialize_chain()
    
    def ask(self, question):
        """
        Ask a question and get an answer
        
        Parameters:
        - question: The question to ask
        
        Returns:
        - The answer and source documents
        """
        if not self.qa_chain:
            print("QA Chain not initialized")
            return {"answer": "System not ready. Please load a document first."}
        
        print(f"Question: {question}")
        try:
            # Get the answer
            result = self.qa_chain({"query": question})
            return result
        except Exception as e:
            print(f"Error getting answer: {e}")
            return {"answer": f"Error: {str(e)}"}