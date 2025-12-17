# cli.py
# Command-line interface for Indian Legal Document Analyzer

import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
from core.document_processor import DocumentProcessor
from core.embedding_store import EmbeddingStore
from core.qa_chain import QAChain
from core.document_manager import DocumentManager
from analyzers.risk_analyzer import ContractRiskAnalyzer
from analyzers.legal_tools import LegalAnalysisTools

# Load environment variables
load_dotenv()


def main():
    """Main CLI function"""
    
    # Validate API keys
    if not os.getenv("GROQ_API_KEY"):
        print("Error: GROQ_API_KEY not found in .env file")
        return
    if not os.getenv("PINECONE_API_KEY"):
        print("Error: PINECONE_API_KEY not found in .env file")
        return
    
    print("=" * 60)
    print("  Indian Legal Document Analyzer - CLI")
    print("=" * 60)
    
    # Initialize components
    doc_processor = DocumentProcessor()
    embedding_store = EmbeddingStore()
    doc_manager = DocumentManager()
    legal_tools = LegalAnalysisTools()
    risk_analyzer = ContractRiskAnalyzer()
    qa_chain = None
    
    def load_document():
        nonlocal qa_chain
        file_path = input("\nEnter document path (PDF or TXT): ").strip()
        
        if not os.path.exists(file_path):
            print(f"Error: File not found: {file_path}")
            return False
        
        print(f"Loading {file_path}...")
        text = doc_processor.load_document(file_path)
        
        if not text:
            print("Error: Could not load document")
            return False
        
        doc_type = input("Document type (contract/statute/judgment): ").strip() or "contract"
        doc_id = doc_manager.add_document(text, file_path, doc_type)
        print(f"Document loaded (ID: {doc_id}, {len(text):,} chars)")
        
        print("Creating embeddings...")
        chunks = doc_processor.split_text(text)
        vector_store = embedding_store.create_vector_store(chunks)
        
        if vector_store:
            qa_chain = QAChain(vector_store)
            print("✓ Document ready for analysis!")
            return True
        return False
    
    def ask_question():
        if not qa_chain:
            print("Please load a document first.")
            return
        
        question = input("\nYour question: ").strip()
        if not question:
            return
        
        print("\nAnalyzing...")
        result = qa_chain.ask(question)
        
        print("\n" + "=" * 40)
        print("ANSWER:")
        print("=" * 40)
        print(result.get("result", "No answer found."))
        
        if "citations" in result:
            print("\nCitations:", ", ".join(result["citations"]))
    
    def analyze_risks():
        doc_id = doc_manager.current_document_id
        if not doc_id:
            print("Please load a document first.")
            return
        
        text, meta = doc_manager.get_document()
        print(f"\nAnalyzing risks in {meta['filename']}...")
        
        analysis = risk_analyzer.analyze_contract(text)
        suggestions = risk_analyzer.suggest_improvements(analysis)
        
        print("\n" + "=" * 40)
        print(f"RISK SCORE: {analysis['risk_score']:.1f}/100")
        print("=" * 40)
        
        print("\nRisk Categories:")
        for cat, data in analysis["risk_categories"].items():
            print(f"  - {cat.replace('_', ' ').title()}: {data['score']:.0f}/100")
        
        if analysis["missing_provisions"]:
            print("\nMissing Provisions:")
            for p in analysis["missing_provisions"]:
                print(f"  - {p.replace('_', ' ').title()}")
        
        print("\nRecommendations:")
        for advice in suggestions["general_advice"][:3]:
            print(f"  • {advice}")
    
    def generate_summary():
        doc_id = doc_manager.current_document_id
        if not doc_id:
            print("Please load a document first.")
            return
        
        text, meta = doc_manager.get_document()
        print(f"\nSummarizing {meta['filename']}...")
        
        summary = legal_tools.generate_legal_summary(text)
        
        print("\n" + "=" * 40)
        print("DOCUMENT SUMMARY")
        print("=" * 40)
        print(f"Type: {summary['document_type']}")
        
        if summary["parties"]:
            print("\nParties:")
            for p in summary["parties"]:
                print(f"  - {p['name']}")
        
        if summary["key_sections"]:
            print(f"\nSections ({len(summary['key_sections'])}):")
            for s in summary["key_sections"][:5]:
                print(f"  - {s['number']}: {s['title']}")
    
    # Main menu loop
    while True:
        print("\n" + "-" * 40)
        print("MENU:")
        print("  1. Load document")
        print("  2. Ask a question")
        print("  3. Analyze risks")
        print("  4. Generate summary")
        print("  5. Exit")
        print("-" * 40)
        
        choice = input("Choice (1-5): ").strip()
        
        if choice == "1":
            load_document()
        elif choice == "2":
            ask_question()
        elif choice == "3":
            analyze_risks()
        elif choice == "4":
            generate_summary()
        elif choice == "5":
            print("\nGoodbye!")
            break
        else:
            print("Invalid choice.")


if __name__ == "__main__":
    main()
