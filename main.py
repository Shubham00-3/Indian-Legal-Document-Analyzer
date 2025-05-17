# main.py
# Main application file for the RAG QA system
# This ties together document processing, embedding, and question answering

import os
from dotenv import load_dotenv
from document_processor import DocumentProcessor
from embedding_store import EmbeddingStore
from qa_chain import QAChain

def main():
    """Main function to run the RAG QA system"""
    # Load environment variables
    load_dotenv()
    
    # Check if API keys are available
    if not os.getenv("GROQ_API_KEY"):
        print("Error: GROQ_API_KEY not found in .env file")
        return
        
    if not os.getenv("PINECONE_API_KEY"):
        print("Error: PINECONE_API_KEY not found in .env file")
        return
    
    print("RAG QA System initialized!")
    print("-------------------------")
    
    # Initialize components
    doc_processor = DocumentProcessor()
    embedding_store = EmbeddingStore()
    qa_chain = None
    
    # Function to load a document
    def load_document():
        file_path = input("Enter the path to your text file: ")
        
        # Load document
        print(f"Loading document from {file_path}...")
        document_text = doc_processor.load_document(file_path)
        
        if not document_text:
            print("Error: Could not load document")
            return False
            
        print(f"Document loaded: {len(document_text)} characters")
        
        # Split document into chunks
        chunks = doc_processor.split_text(document_text)
        
        if not chunks:
            print("Error: Could not split document into chunks")
            return False
            
        # Create vector store
        vector_store = embedding_store.create_vector_store(chunks)
        
        if not vector_store:
            print("Error: Could not create vector store")
            return False
            
        # Initialize QA chain
        nonlocal qa_chain
        qa_chain = QAChain(vector_store)
        
        print("\nDocument processed and ready for questions!")
        print(f"Namespace: {embedding_store.current_namespace}")
        
        return True
    
    # Main interaction loop
    while True:
        print("\nRAG QA System - Choose an option:")
        print("1. Load a document")
        print("2. Ask a question about the loaded document")
        print("3. Exit")
        
        choice = input("\nEnter your choice (1-3): ")
        
        if choice == "1":
            load_document()
            
        elif choice == "2":
            if not qa_chain:
                print("No document loaded. Please load a document first.")
                continue
                
            question = input("\nEnter your question: ")
            
            print("\nSearching for answer...")
            result = qa_chain.ask(question)
            
            print("\n----- Answer -----")
            print(result["result"])
            
            print("\n----- Sources -----")
            for i, doc in enumerate(result["source_documents"]):
                print(f"Source {i+1}:")
                # Print only the first 200 characters if the content is long
                content = doc.page_content
                if len(content) > 200:
                    content = content[:200] + "..."
                print(content)
                print()
                
        elif choice == "3":
            print("Thank you for using the RAG QA System!")
            break
            
        else:
            print("Invalid choice. Please try again.")

if __name__ == "__main__":
    main()