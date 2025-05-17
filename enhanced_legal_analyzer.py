# enhanced_legal_analyzer.py
# Enhanced application for legal document analysis with advanced features

import os
from dotenv import load_dotenv
from legal_document_processor import LegalDocumentProcessor
from legal_embedding_store import LegalEmbeddingStore
from legal_qa_chain import LegalQAChain
from document_manager import DocumentManager
from legal_analyzer_tools import LegalAnalysisTools
from contract_risk_analyzer import ContractRiskAnalyzer
from legal_document_comparison import LegalDocumentComparison

def main():
    """Main function to run the Enhanced Legal Document Analysis system"""
    # Load environment variables
    load_dotenv()
    
    # Check if API keys are available
    if not os.getenv("GROQ_API_KEY"):
        print("Error: GROQ_API_KEY not found in .env file")
        return
        
    if not os.getenv("PINECONE_API_KEY"):
        print("Error: PINECONE_API_KEY not found in .env file")
        return
    
    print("Enhanced Legal Document Analysis System initialized!")
    print("--------------------------------------------------")
    
    # Initialize components
    doc_processor = LegalDocumentProcessor()
    embedding_store = LegalEmbeddingStore()
    doc_manager = DocumentManager()
    legal_tools = LegalAnalysisTools()
    risk_analyzer = ContractRiskAnalyzer()
    doc_comparison = LegalDocumentComparison()
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
        
        # Add to document manager
        doc_type = input("Enter document type (contract, statute, lease, etc.): ")
        doc_id = doc_manager.add_document(document_text, file_path, doc_type)
        print(f"Document added with ID: {doc_id}")
        
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
    
    # Function to list loaded documents
    def list_documents():
        documents = doc_manager.list_documents()
        
        if not documents:
            print("No documents loaded.")
            return
        
        print("\n----- Loaded Documents -----")
        for i, (doc_id, metadata) in enumerate(documents):
            print(f"{i+1}. ID: {doc_id}")
            print(f"   Filename: {metadata['filename']}")
            print(f"   Type: {metadata['doc_type']}")
            print(f"   Size: {metadata['char_count']} characters")
            print()
    
    # Function to generate document summary
    def generate_summary():
        if not doc_manager.current_document_id:
            print("No document loaded. Please load a document first.")
            return
        
        doc_text, metadata = doc_manager.get_document()
        
        print(f"\nGenerating summary for document: {metadata['filename']}...")
        summary = legal_tools.generate_legal_summary(doc_text)
        
        print("\n----- Document Summary -----")
        print(f"Document Type: {summary['document_type']}")
        
        if summary['parties']:
            print("\nParties:")
            for party in summary['parties']:
                print(f"- {party['name']} ({party['type']})")
        
        if summary['dates']:
            print("\nKey Dates:")
            for date in summary['dates']:
                print(f"- {date['type']}: {date['value']}")
        
        if summary['governing_law']:
            print(f"\nGoverning Law: {summary['governing_law']}")
        
        print("\nKey Sections:")
        for section in summary['key_sections']:
            print(f"- {section['number']}: {section['title']}")
        
        if summary['financial_terms']:
            print("\nFinancial Terms:")
            for i, term in enumerate(summary['financial_terms'][:3]):  # Show first 3 only
                print(f"- {term['amount']} ({term['context'][:30]}...)")
    
    # Function to extract contract details
    def extract_contract_details():
        if not doc_manager.current_document_id:
            print("No document loaded. Please load a document first.")
            return
        
        doc_text, metadata = doc_manager.get_document()
        
        print(f"\nExtracting details from document: {metadata['filename']}...")
        details = legal_tools.extract_contract_details(doc_text)
        
        print("\n----- Contract Details -----")
        
        if 'effective_date' in details:
            print(f"Effective Date: {details['effective_date']}")
        
        if details['parties']:
            print("\nParties:")
            for party in details['parties']:
                print(f"- Name: {party['name']}")
                if party['type']:
                    print(f"  Type: {party['type']}")
                if party['jurisdiction']:
                    print(f"  Jurisdiction: {party['jurisdiction']}")
                if party['address']:
                    print(f"  Address: {party['address']}")
        
        if details['financial_terms']:
            print("\nFinancial Terms:")
            for i, term in enumerate(details['financial_terms'][:5]):  # Show first 5 only
                print(f"- Amount: {term['amount']}")
                print(f"  Context: {term['context']}")
                print()
    
    # Function to analyze contract risks
    def analyze_contract_risks():
        if not doc_manager.current_document_id:
            print("No document loaded. Please load a document first.")
            return
        
        doc_text, metadata = doc_manager.get_document()
        
        print(f"\nAnalyzing risks in document: {metadata['filename']}...")
        analysis = risk_analyzer.analyze_contract(doc_text)
        
        # Get improvement suggestions
        suggestions = risk_analyzer.suggest_improvements(analysis)
        
        # Display results
        print("\n----- Contract Risk Analysis -----")
        print(f"Overall Risk Score: {analysis['risk_score']:.1f}/100")
        
        print("\nRisk Categories:")
        for category, data in analysis['risk_categories'].items():
            print(f"- {category.replace('_', ' ').title()}: {data['score']:.1f}/100 ({data['matches']} issues found)")
        
        if analysis['missing_provisions']:
            print("\nMissing Provisions:")
            for provision in analysis['missing_provisions']:
                print(f"- {provision.replace('_', ' ').title()}")
        
        if analysis['ambiguous_clauses']:
            print("\nAmbiguous Language (top 3):")
            for i, item in enumerate(analysis['ambiguous_clauses'][:3]):
                print(f"- \"{item['term']}\" - Context: \"{item['context'][:50]}...\"")
        
        if analysis['one_sided_terms']:
            print("\nOne-sided Terms (top 3):")
            for i, item in enumerate(analysis['one_sided_terms'][:3]):
                print(f"- \"{item['term']}\" - Context: \"{item['context'][:50]}...\"")
        
        print("\nRecommendations:")
        for advice in suggestions['general_advice']:
            print(f"- {advice}")
        
        if suggestions['specific_suggestions']:
            print("\nSpecific Improvements:")
            for suggestion in suggestions['specific_suggestions']:
                print(f"- {suggestion}")

    # Function to compare documents
    def compare_documents():
        # List available documents
        documents = doc_manager.list_documents()
        
        if len(documents) < 2:
            print("You need at least two documents loaded to perform a comparison.")
            return
        
        print("\nSelect two documents to compare:")
        for i, (doc_id, metadata) in enumerate(documents):
            print(f"{i+1}. {metadata['filename']}")
        
        try:
            # Get user selections
            doc1_idx = int(input("\nSelect first document number: ")) - 1
            doc2_idx = int(input("Select second document number: ")) - 1
            
            if doc1_idx < 0 or doc1_idx >= len(documents) or doc2_idx < 0 or doc2_idx >= len(documents):
                print("Invalid document selection.")
                return
                
            if doc1_idx == doc2_idx:
                print("You must select two different documents.")
                return
            
            # Get document texts
            doc1_id = documents[doc1_idx][0]
            doc2_id = documents[doc2_idx][0]
            
            doc1_text, doc1_metadata = doc_manager.get_document(doc1_id)
            doc2_text, doc2_metadata = doc_manager.get_document(doc2_id)
            
            print(f"\nComparing {doc1_metadata['filename']} with {doc2_metadata['filename']}...")
            
            # Perform comparison
            results = doc_comparison.compare_documents(doc1_text, doc2_text)
            
            # Display results
            print("\n----- Document Comparison Results -----")
            
            print("\nCommon Sections:")
            for section in results['common_sections']:
                comparison = results['section_comparisons'][section]
                similarity = comparison['similarity_score']
                print(f"- {section.replace('_', ' ').title()}: {similarity:.1f}% similar")
            
            if results['unique_to_doc1']:
                print(f"\nSections only in {doc1_metadata['filename']}:")
                for section in results['unique_to_doc1']:
                    print(f"- {section.replace('_', ' ').title()}")
            
            if results['unique_to_doc2']:
                print(f"\nSections only in {doc2_metadata['filename']}:")
                for section in results['unique_to_doc2']:
                    print(f"- {section.replace('_', ' ').title()}")
            
            # Option to compare a specific section in detail
            print("\nWould you like to compare a specific section in detail?")
            section_choice = input("Enter section name (or press Enter to skip): ").lower()
            
            if section_choice and section_choice in results['common_sections']:
                detailed = doc_comparison.compare_specific_provision(doc1_text, doc2_text, section_choice)
                
                if detailed['comparison']:
                    comparison = detailed['comparison']
                    print(f"\n----- Detailed Comparison of {section_choice.replace('_', ' ').title()} Section -----")
                    print(f"Similarity: {comparison['similarity_score']:.1f}%")
                    print(f"Length in doc1: {comparison['doc1_length']} characters")
                    print(f"Length in doc2: {comparison['doc2_length']} characters")
                    
                    if comparison['key_differences']['added']:
                        print("\nKey additions:")
                        for addition in comparison['key_differences']['added'][:3]:  # Show top 3
                            print(f"+ {addition}")
                    
                    if comparison['key_differences']['removed']:
                        print("\nKey removals:")
                        for removal in comparison['key_differences']['removed'][:3]:  # Show top 3
                            print(f"- {removal}")
        
        except ValueError:
            print("Invalid input. Please enter a number.")
        except Exception as e:
            print(f"Error comparing documents: {e}")
    
    # Main interaction loop
    while True:
        print("\nEnhanced Legal Document Analysis System - Choose an option:")
        print("1. Load a legal document")
        print("2. List loaded documents")
        print("3. Ask a question about the document")
        print("4. Search for specific sections or clauses")
        print("5. Generate document summary")
        print("6. Extract contract details")
        print("7. Analyze contract risks")
        print("8. Compare two documents")
        print("9. Exit")
        
        choice = input("\nEnter your choice (1-9): ")
        
        if choice == "1":
            load_document()
            
        elif choice == "2":
            list_documents()
            
        elif choice == "3":
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
                
        elif choice == "4":
            if not embedding_store.vector_store:
                print("No document loaded. Please load a document first.")
                continue
                
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
                
        elif choice == "5":
            generate_summary()
            
        elif choice == "6":
            extract_contract_details()
            
        elif choice == "7":
            analyze_contract_risks()
            
        elif choice == "8":
            compare_documents()
                
        elif choice == "9":
            print("Thank you for using the Enhanced Legal Document Analysis System!")
            break
            
        else:
            print("Invalid choice. Please try again.")

if __name__ == "__main__":
    main()