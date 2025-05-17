# legal_analyzer.py
# Main application for legal document analysis

import os
from dotenv import load_dotenv
from legal_document_processor import LegalDocumentProcessor
from legal_embedding_store import LegalEmbeddingStore
from legal_qa_chain import LegalQAChain

def main():
    """Main function to run the Legal Document Analysis system"""
    # Load environment variables
    load_dotenv()
    
    # Check if API keys are available
    if not os.getenv("GROQ_API_KEY"):
        print("Error: GROQ_API_KEY not found in .env file")
        return
        
    if not os.getenv("PINECONE_API_KEY"):
        print("Error: PINECONE_API_KEY not found in .env file")
        return
    
    print("Legal Document Analysis System initialized!")
    print("------------------------------------------")
    
    # Initialize components
    doc_processor = LegalDocumentProcessor()
    embedding_store = LegalEmbeddingStore()
    qa_chain = None
    
    # Function to load a legal document
    def load_document():
        file_path = input("Enter the path to your legal document (PDF or TXT): ")
        
        # Load document
        print(f"Loading document from {file_path}...")
        document_text = doc_processor.load_document(file_path)
        
        if not document_text:
            print("Error: Could not load document")
            return False
            
        print(f"Document loaded: {len(document_text)} characters")
        
        # Split document into chunks with legal metadata
        chunks_with_metadata = doc_processor.split_text(document_text)
        
        if not chunks_with_metadata:
            print("Error: Could not split document into chunks")
            return False
            
        # Create vector store
        vector_store = embedding_store.create_vector_store(chunks_with_metadata)
        
        if not vector_store:
            print("Error: Could not create vector store")
            return False
            
        # Initialize QA chain
        nonlocal qa_chain
        qa_chain = LegalQAChain(vector_store)
        
        print("\nLegal document processed and ready for analysis!")
        print(f"Namespace: {embedding_store.current_namespace}")
        
        return True
    
    # Function to search for specific legal sections
    def search_sections():
        if not embedding_store.vector_store:
            print("No document loaded. Please load a document first.")
            return
            
        section_query = input("Enter section number or keyword to search for: ")
        
        # If it looks like a section number, search by metadata
        if section_query.replace('.', '').isdigit():
            print(f"\nSearching for Section {section_query}...")
            results = embedding_store.search_by_metadata(
                {"detected_sections": section_query}, 
                top_k=3
            )
        else:
            # Otherwise, do a semantic search
            print(f"\nSearching for content about '{section_query}'...")
            results = embedding_store.vector_store.similarity_search(
                section_query, 
                k=3
            )
        
        # Display results
        if results:
            print(f"\n----- Found {len(results)} relevant sections -----")
            for i, doc in enumerate(results):
                print(f"\nResult {i+1}:")
                
                # Show metadata if available
                if hasattr(doc, 'metadata') and doc.metadata:
                    sections = doc.metadata.get('detected_sections', [])
                    if sections and sections[0] != "unknown":
                        print(f"Section(s): {', '.join(sections)}")
                
                # Show content
                content = doc.page_content
                if len(content) > 300:
                    content = content[:300] + "..."
                print(content)
                print()
        else:
            print("No matching sections found.")
    
    # Main interaction loop
    while True:
        print("\nLegal Document Analysis System - Choose an option:")
        print("1. Load a legal document")
        print("2. Ask a question about the document")
        print("3. Search for specific sections or clauses")
        print("4. Exit")
        
        choice = input("\nEnter your choice (1-4): ")
        
        if choice == "1":
            load_document()
            
        elif choice == "2":
            if not qa_chain:
                print("No document loaded. Please load a document first.")
                continue
                
            question = input("\nEnter your legal question: ")
            
            print("\nAnalyzing document for answer...")
            result = qa_chain.ask(question)
            
            print("\n----- Answer -----")
            print(result["result"])
            
            # Show citations if available
            if "citations" in result and result["citations"]:
                print("\n----- Citations -----")
                for citation in result["citations"]:
                    print(citation)
            
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
            search_sections()
                
        elif choice == "4":
            print("Thank you for using the Legal Document Analysis System!")
            break
            
        else:
            print("Invalid choice. Please try again.")

if __name__ == "__main__":
    main()