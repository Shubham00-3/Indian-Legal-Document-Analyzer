# web_interface.py
# Streamlit web interface for Indian Legal Document RAG QA System

import streamlit as st
import os
import sys
import tempfile
import pandas as pd
import altair as alt
import matplotlib.pyplot as plt
import io
import base64
from dotenv import load_dotenv

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import core components
from core.document_processor import DocumentProcessor
from core.embedding_store import EmbeddingStore
from core.qa_chain import QAChain
from core.document_manager import DocumentManager

# Import analyzers
from analyzers.comparison import DocumentComparison
from analyzers.citation_analyzer import CitationAnalyzer

# Load environment variables
load_dotenv()


def main():
    """Main function to run the Streamlit app"""
    
    # Page config
    st.set_page_config(
        page_title="Indian Legal Document Analyzer",
        page_icon="⚖️",
        layout="wide"
    )
    
    # Page title
    st.title("⚖️ Indian Legal Document RAG QA System")
    
    # Check for API keys
    groq_key = os.getenv("GROQ_API_KEY")
    pinecone_key = os.getenv("PINECONE_API_KEY")
    
    if not groq_key or not pinecone_key:
        st.error("⚠️ API keys missing! Please ensure GROQ_API_KEY and PINECONE_API_KEY are set in your .env file.")
        st.stop()
    
    # Initialize session state
    if 'initialized' not in st.session_state:
        st.session_state.doc_processor = DocumentProcessor()
        st.session_state.embedding_store = EmbeddingStore()
        st.session_state.doc_manager = DocumentManager()
        st.session_state.qa_chain = None
        st.session_state.document_metadata = {}
        st.session_state.doc_comparison = DocumentComparison(st.session_state.doc_processor)
        st.session_state.citation_analyzer = CitationAnalyzer()
        st.session_state.initialized = True
    
    # Sidebar navigation
    st.sidebar.title("Navigation")
    page = st.sidebar.radio(
        "Select a page:",
        ["Upload Document", "Document Manager", "Ask Questions", 
         "Document Analysis", "Document Comparison", "Citation Analysis"]
    )
    
    # Page routing
    if page == "Upload Document":
        render_upload_page()
    elif page == "Document Manager":
        render_manager_page()
    elif page == "Ask Questions":
        render_qa_page()
    elif page == "Document Analysis":
        render_analysis_page()
    elif page == "Document Comparison":
        render_comparison_page()
    elif page == "Citation Analysis":
        render_citation_page()
    
    # Footer
    st.sidebar.markdown("---")
    st.sidebar.info("Indian Legal Document RAG QA System v2.0")


def process_document(uploaded_file, doc_type="Act"):
    """Process an uploaded document"""
    with tempfile.NamedTemporaryFile(delete=False, suffix='.' + uploaded_file.name.split('.')[-1]) as tmp_file:
        tmp_file.write(uploaded_file.getvalue())
        tmp_path = tmp_file.name
    
    document_text = st.session_state.doc_processor.load_document(tmp_path)
    
    if document_text:
        # Extract metadata for PDFs
        if tmp_path.lower().endswith('.pdf'):
            metadata_dict = st.session_state.doc_processor.extract_metadata(document_text)
            st.session_state.document_metadata[uploaded_file.name] = metadata_dict
        
        # Add to document manager
        doc_id = st.session_state.doc_manager.add_document(
            document_text, uploaded_file.name, doc_type
        )
        
        # Split and create embeddings
        chunks = st.session_state.doc_processor.split_text(document_text)
        
        if chunks:
            vector_store = st.session_state.embedding_store.create_vector_store(chunks)
            if vector_store:
                st.session_state.qa_chain = QAChain(vector_store)
                return True, f"Document processed successfully! ID: {doc_id}"
            return False, "Error: Could not create vector store"
        return False, "Error: Could not split document"
    return False, "Error: Could not load document"


def render_upload_page():
    """Render the document upload page"""
    st.header("📄 Upload Document")
    
    uploaded_file = st.file_uploader("Choose a document", type=["txt", "pdf"])
    
    if uploaded_file:
        st.write(f"Selected: **{uploaded_file.name}**")
        
        doc_type = st.selectbox(
            "Document Type",
            ["Act", "Rules", "Notification", "Judgment", "Ordinance", 
             "Bill", "Constitution", "Amendment", "Regulation", 
             "Contract", "Agreement", "Legal Memo", "Policy", "Other"]
        )
        
        if st.button("Process Document", type="primary"):
            with st.spinner("Processing document..."):
                success, message = process_document(uploaded_file, doc_type)
                if success:
                    st.success(message)
                    doc, meta = st.session_state.doc_manager.get_document()
                    st.write(f"Document length: {meta['char_count']:,} characters")
                    
                    with st.expander("Preview"):
                        st.write(doc[:1000] + "..." if len(doc) > 1000 else doc)
                else:
                    st.error(message)


def render_manager_page():
    """Render the document manager page"""
    st.header("📚 Document Manager")
    
    documents = st.session_state.doc_manager.list_documents()
    
    if not documents:
        st.info("No documents loaded yet. Upload a document to get started.")
        return
    
    st.write(f"You have **{len(documents)}** document(s) loaded:")
    
    for doc_id, metadata in documents:
        with st.expander(f"{metadata['filename']} ({doc_id})"):
            st.write(f"**Type:** {metadata['doc_type']}")
            st.write(f"**Size:** {metadata['char_count']:,} characters")
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button(f"Make Active", key=f"activate_{doc_id}"):
                    st.session_state.doc_manager.set_current_document(doc_id)
                    doc_text, _ = st.session_state.doc_manager.get_document(doc_id)
                    chunks = st.session_state.doc_processor.split_text(doc_text)
                    vector_store = st.session_state.embedding_store.create_vector_store(chunks)
                    st.session_state.qa_chain = QAChain(vector_store)
                    st.success(f"Document {doc_id} set as active.")
                    st.rerun()
            
            with col2:
                if st.button(f"Delete", key=f"delete_{doc_id}"):
                    st.session_state.doc_manager.remove_document(doc_id)
                    st.success(f"Document {doc_id} removed.")
                    st.rerun()
    
    current_id = st.session_state.doc_manager.current_document_id
    if current_id:
        _, current_meta = st.session_state.doc_manager.get_document(current_id)
        st.info(f"Active document: {current_meta['filename']} (ID: {current_id})")


def render_qa_page():
    """Render the Q&A page"""
    st.header("❓ Ask Questions")
    
    documents = st.session_state.doc_manager.list_documents()
    
    if not documents:
        st.warning("Please upload and process a document first.")
        return
    
    if not st.session_state.qa_chain:
        st.warning("Please select an active document to ask questions.")
        return
    
    current_id = st.session_state.doc_manager.current_document_id
    _, current_meta = st.session_state.doc_manager.get_document(current_id)
    st.info(f"Active document: {current_meta['filename']}")
    
    example_questions = [
        "What are the key provisions of this document?",
        "What penalties or fines are mentioned?",
        "What is the jurisdiction of this law?",
        "Who are the key authorities mentioned?",
        "What are the compliance requirements?",
        "What are the rights and obligations established?"
    ]
    
    selected = st.selectbox("Example questions:", ["Select..."] + example_questions)
    question = selected if selected != "Select..." else st.text_input("Or enter your own:")
    
    if question and st.button("Get Answer", type="primary"):
        with st.spinner("Analyzing..."):
            result = st.session_state.qa_chain.ask(question)
            
            st.subheader("Answer")
            st.write(result.get("result", "No answer found."))
            
            if "citations" in result:
                st.subheader("Citations")
                for citation in result["citations"]:
                    st.write(f"- {citation}")
            
            if "source_documents" in result:
                st.subheader("Sources")
                for i, doc in enumerate(result["source_documents"][:3]):
                    st.markdown(f"**Source {i+1}**")
                    st.code(doc.page_content[:500], language=None)


def render_analysis_page():
    """Render the document analysis page"""
    st.header("🔍 Document Analysis")
    
    current_id = st.session_state.doc_manager.current_document_id
    if not current_id:
        st.warning("Please select an active document in the Document Manager.")
        return
    
    doc_text, meta = st.session_state.doc_manager.get_document(current_id)
    st.info(f"Analyzing: {meta['filename']}")
    
    # Extract metadata
    doc_metadata = st.session_state.doc_processor.extract_metadata(doc_text)
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Sections", len(doc_metadata.get("sections", [])))
        st.metric("Dates", len(doc_metadata.get("dates", [])))
    with col2:
        st.metric("Entities", len(doc_metadata.get("entities", [])))
        st.metric("Monetary Values", len(doc_metadata.get("monetary_values", [])))
    
    if doc_metadata.get("sections"):
        with st.expander("Sections"):
            for s in doc_metadata["sections"]:
                st.write(f"**Section {s['number']}**: {s['title']}")
    
    if doc_metadata.get("entities"):
        with st.expander("Entities"):
            for e in doc_metadata["entities"]:
                st.write(f"- {e}")


def render_comparison_page():
    """Render document comparison page"""
    st.header("⚖️ Document Comparison")
    
    documents = st.session_state.doc_manager.list_documents()
    
    if len(documents) < 2:
        st.warning("Please upload at least two documents to compare.")
        return
    
    doc_options = {doc_id: f"{meta['filename']} ({meta['doc_type']})" 
                   for doc_id, meta in documents}
    
    col1, col2 = st.columns(2)
    with col1:
        doc1_id = st.selectbox("First Document", list(doc_options.keys()),
                               format_func=lambda x: doc_options[x])
    with col2:
        remaining = {k: v for k, v in doc_options.items() if k != doc1_id}
        doc2_id = st.selectbox("Second Document", list(remaining.keys()),
                               format_func=lambda x: doc_options[x])
    
    if st.button("Compare", type="primary"):
        with st.spinner("Comparing..."):
            doc1_text, doc1_meta = st.session_state.doc_manager.get_document(doc1_id)
            doc2_text, doc2_meta = st.session_state.doc_manager.get_document(doc2_id)
            
            results = st.session_state.doc_comparison.compare_documents(
                doc1_text, doc1_meta, doc2_text, doc2_meta
            )
            
            st.metric("Overall Similarity", f"{results['similarity_score'] * 100:.1f}%")
            
            st.subheader("Comparison Overview")
            st.write(f"Shared entities: {len(results['shared_entities'])}")
            st.write(f"Shared citations: {len(results['shared_citations'])}")
            st.write(f"Shared statutes: {len(results['shared_statutes'])}")


def render_citation_page():
    """Render citation analysis page"""
    st.header("📖 Citation Analysis")
    
    documents = st.session_state.doc_manager.list_documents()
    
    if not documents:
        st.warning("Please upload a document first.")
        return
    
    doc_options = {doc_id: f"{meta['filename']}" for doc_id, meta in documents}
    selected_id = st.selectbox("Select Document", list(doc_options.keys()),
                               format_func=lambda x: doc_options[x])
    
    if st.button("Analyze Citations", type="primary"):
        with st.spinner("Analyzing..."):
            doc_text, doc_meta = st.session_state.doc_manager.get_document(selected_id)
            report = st.session_state.citation_analyzer.generate_citation_report(doc_text)
            
            st.subheader(f"Citations in {doc_meta['filename']}")
            st.metric("Total Citations", report['total_citations'])
            
            for ctype, citations in report['all_citations'].items():
                if citations:
                    with st.expander(f"{ctype.replace('_', ' ').title()} ({len(citations)})"):
                        for c in citations:
                            st.write(f"- {c}")


if __name__ == "__main__":
    main()
