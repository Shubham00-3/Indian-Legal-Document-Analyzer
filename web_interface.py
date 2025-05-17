# web_interface.py
# Streamlit web interface for RAG QA System with document management for Indian legal documents

import streamlit as st
import os
import tempfile
import pandas as pd
import altair as alt
from dotenv import load_dotenv
import matplotlib.pyplot as plt
import io
import base64

# Import our components
from enhanced_document_processor import EnhancedDocumentProcessor
from embedding_store import EmbeddingStore
from qa_chain import QAChain
from document_manager import DocumentManager
from document_comparison import DocumentComparison
from citation_analyzer import CitationAnalyzer

# Load environment variables
load_dotenv()

# Page title
st.title("Indian Legal Document RAG QA System")

# Check for API keys
groq_key = os.getenv("GROQ_API_KEY")
pinecone_key = os.getenv("PINECONE_API_KEY")

if not groq_key or not pinecone_key:
    st.error("⚠️ API keys missing! Please ensure GROQ_API_KEY and PINECONE_API_KEY are set in your .env file.")
    st.stop()

# Initialize session state for components
if 'initialized' not in st.session_state:
    st.session_state.doc_processor = EnhancedDocumentProcessor()
    st.session_state.embedding_store = EmbeddingStore()
    st.session_state.doc_manager = DocumentManager()
    st.session_state.qa_chain = None
    st.session_state.document_metadata = {}
    # Add the document comparison tool
    st.session_state.doc_comparison = DocumentComparison(st.session_state.doc_processor)
    # Add the citation analyzer
    st.session_state.citation_analyzer = CitationAnalyzer()
    st.session_state.initialized = True

# Sidebar navigation
st.sidebar.title("Navigation")
page = st.sidebar.radio(
    "Select a page:",
    ["Upload Document", "Document Manager", "Ask Questions", "Document Analysis", "Document Comparison", "Citation Analysis"]
)

# Function to process an uploaded document
def process_document(uploaded_file, doc_type="Act"):
    # Save uploaded file to a temporary file
    with tempfile.NamedTemporaryFile(delete=False, suffix='.' + uploaded_file.name.split('.')[-1]) as tmp_file:
        tmp_file.write(uploaded_file.getvalue())
        tmp_path = tmp_file.name
    
    # Load and process the document
    document_text = st.session_state.doc_processor.load_document(tmp_path)
    
    if document_text:
        # Extract metadata if it's not a basic text file
        if tmp_path.lower().endswith('.pdf'):
            metadata_dict = st.session_state.doc_processor.extract_metadata(document_text)
            st.session_state.document_metadata[uploaded_file.name] = metadata_dict
        
        # Add to document manager
        doc_id = st.session_state.doc_manager.add_document(
            document_text, 
            uploaded_file.name,
            doc_type
        )
        
        # Split document into chunks
        chunks = st.session_state.doc_processor.split_text(document_text)
        
        if chunks:
            # Create vector store
            vector_store = st.session_state.embedding_store.create_vector_store(chunks)
            
            if vector_store:
                # Initialize QA chain with the current document
                st.session_state.qa_chain = QAChain(vector_store)
                return True, f"Document processed successfully! ID: {doc_id}"
            else:
                return False, "Error: Could not create vector store"
        else:
            return False, "Error: Could not split document into chunks"
    else:
        return False, "Error: Could not load document"

#--------------------- PAGE: UPLOAD DOCUMENT ---------------------
if page == "Upload Document":
    st.header("Upload Document")
    
    uploaded_file = st.file_uploader("Choose a document", type=["txt", "pdf"])
    
    if uploaded_file is not None:
        file_info = f"Selected file: {uploaded_file.name}"
        st.write(file_info)
        
        # Add Indian legal document type selection
        doc_type = st.selectbox(
            "Document Type",
            ["Act", "Rules", "Notification", "Judgment", "Ordinance", 
             "Bill", "Constitution", "Amendment", "Regulation", 
             "Contract", "Agreement", "Legal Memo", "Policy", "Other"]
        )
        
        # Add additional metadata inputs for Indian legal documents
        if doc_type in ["Act", "Rules", "Notification", "Judgment", "Ordinance", "Bill"]:
            col1, col2 = st.columns(2)
            with col1:
                year = st.text_input("Year", placeholder="e.g., 2023")
            with col2:
                jurisdiction = st.selectbox(
                    "Jurisdiction",
                    ["Central", "Andhra Pradesh", "Arunachal Pradesh", "Assam", "Bihar", 
                     "Chhattisgarh", "Goa", "Gujarat", "Haryana", "Himachal Pradesh", 
                     "Jharkhand", "Karnataka", "Kerala", "Madhya Pradesh", "Maharashtra", 
                     "Manipur", "Meghalaya", "Mizoram", "Nagaland", "Odisha", "Punjab", 
                     "Rajasthan", "Sikkim", "Tamil Nadu", "Telangana", "Tripura", 
                     "Uttar Pradesh", "Uttarakhand", "West Bengal"]
                )
        
        if st.button("Process Document"):
            with st.spinner("Processing document..."):
                success, message = process_document(uploaded_file, doc_type)
                if success:
                    st.success(message)
                    
                    # Get the current document
                    current_doc, current_meta = st.session_state.doc_manager.get_document()
                    
                    # Show basic document stats
                    st.write(f"Document length: {current_meta['char_count']} characters")
                    
                    # If PDF, show metadata if available
                    if uploaded_file.name in st.session_state.document_metadata:
                        metadata = st.session_state.document_metadata[uploaded_file.name]
                        with st.expander("Document Metadata"):
                            # Display sections
                            if metadata["sections"]:
                                st.subheader("Sections")
                                for section in metadata["sections"]:
                                    st.write(f"**{section['number']}**: {section['title']}")
                            
                            # Display dates
                            if metadata["dates"]:
                                st.subheader("Dates Mentioned")
                                st.write(", ".join(metadata["dates"]))
                            
                            # Display entities
                            if metadata["entities"]:
                                st.subheader("Entities Mentioned")
                                st.write(", ".join(metadata["entities"]))
                    
                    # Show a preview
                    with st.expander("Document Preview"):
                        preview_length = min(1000, len(current_doc))
                        st.write(current_doc[:preview_length] + "..." if preview_length < len(current_doc) else current_doc)
                else:
                    st.error(message)

#--------------------- PAGE: DOCUMENT MANAGER ---------------------
elif page == "Document Manager":
    st.header("Document Manager")
    
    documents = st.session_state.doc_manager.list_documents()
    
    if not documents:
        st.info("No documents loaded yet. Upload a document to get started.")
    else:
        st.write(f"You have {len(documents)} document(s) loaded:")
        
        for doc_id, metadata in documents:
            with st.expander(f"{metadata['filename']} ({doc_id})"):
                st.write(f"**Type:** {metadata['doc_type']}")
                st.write(f"**Size:** {metadata['char_count']} characters")
                
                # Actions
                col1, col2 = st.columns(2)
                with col1:
                    if st.button(f"Make Active", key=f"activate_{doc_id}"):
                        # Set as current document and update QA chain
                        st.session_state.doc_manager.current_document_id = doc_id
                        
                        # We need to reload the vector store and QA chain
                        doc_text, _ = st.session_state.doc_manager.get_document(doc_id)
                        chunks = st.session_state.doc_processor.split_text(doc_text)
                        vector_store = st.session_state.embedding_store.create_vector_store(chunks)
                        st.session_state.qa_chain = QAChain(vector_store)
                        
                        st.success(f"Document {doc_id} set as active.")
                        st.experimental_rerun()
                
                with col2:
                    if st.button(f"Delete", key=f"delete_{doc_id}"):
                        # Remove document
                        st.session_state.doc_manager.remove_document(doc_id)
                        st.success(f"Document {doc_id} removed.")
                        st.experimental_rerun()
                
                # If extracted metadata exists for this file, show it
                if metadata['filename'] in st.session_state.document_metadata:
                    doc_metadata = st.session_state.document_metadata[metadata['filename']]
                    st.write("**Document Analysis:**")
                    
                    # Display section count
                    section_count = len(doc_metadata["sections"])
                    st.write(f"- Sections: {section_count}")
                    
                    # Display entity count
                    entity_count = len(doc_metadata["entities"])
                    st.write(f"- Entities: {entity_count}")
                    
                    # Display date count
                    date_count = len(doc_metadata["dates"])
                    st.write(f"- Dates: {date_count}")
                
                # Preview - Fixed nested expander
                st.subheader("Document Preview")
                doc_text, _ = st.session_state.doc_manager.get_document(doc_id)
                preview_length = min(500, len(doc_text))
                st.write(doc_text[:preview_length] + "..." if preview_length < len(doc_text) else doc_text)
        
        # Show active document
        current_id = st.session_state.doc_manager.current_document_id
        if current_id:
            _, current_meta = st.session_state.doc_manager.get_document(current_id)
            st.info(f"Active document: {current_meta['filename']} (ID: {current_id})")

#--------------------- PAGE: ASK QUESTIONS ---------------------
elif page == "Ask Questions":
    st.header("Ask Questions")
    
    documents = st.session_state.doc_manager.list_documents()
    
    if not documents:
        st.warning("Please upload and process a document first.")
    elif not st.session_state.qa_chain:
        st.warning("Please select an active document to ask questions.")
    else:
        # Show active document
        current_id = st.session_state.doc_manager.current_document_id
        _, current_meta = st.session_state.doc_manager.get_document(current_id)
        st.info(f"Active document: {current_meta['filename']}")
        
        # Add some example questions for Indian legal documents
        st.write("Suggested questions for Indian legal documents:")
        example_questions = [
            "What are the key provisions of this document?",
            "What penalties or fines are mentioned in this document?",
            "What is the jurisdiction of this law?",
            "Who are the key authorities mentioned in this document?",
            "What are the compliance requirements mentioned?",
            "What are the rights and obligations established in this document?"
        ]
        
        selected_example = st.selectbox("Select an example question:", 
                                       ["Select..."] + example_questions)
        
        # Use the selected example or let user enter their own question
        if selected_example != "Select...":
            question = selected_example
        else:
            question = st.text_input("Or enter your own question:")
        
        if question and st.button("Get Answer"):
            with st.spinner("Searching for answer..."):
                result = st.session_state.qa_chain.ask(question)
                
                st.subheader("Answer")
                st.write(result["result"])
                
                st.subheader("Sources")
                for i, doc in enumerate(result["source_documents"]):
                    # Fixed to use markdown and code blocks instead of expanders
                    st.markdown(f"**Source {i+1}**")
                    st.code(doc.page_content, language=None)

#--------------------- PAGE: DOCUMENT ANALYSIS ---------------------
elif page == "Document Analysis":
    st.header("Document Analysis")
    
    documents = st.session_state.doc_manager.list_documents()
    
    if not documents:
        st.warning("Please upload and process a document first.")
    else:
        # Get active document
        current_id = st.session_state.doc_manager.current_document_id
        if not current_id:
            st.warning("Please select an active document in the Document Manager.")
        else:
            current_doc, current_meta = st.session_state.doc_manager.get_document(current_id)
            st.info(f"Analyzing document: {current_meta['filename']} (ID: {current_id})")
            
            # Check if we have metadata for this document
            if current_meta['filename'] in st.session_state.document_metadata:
                doc_metadata = st.session_state.document_metadata[current_meta['filename']]
                
                # Display sections
                if doc_metadata["sections"]:
                    st.subheader("Document Structure")
                    st.write(f"This document contains {len(doc_metadata['sections'])} identified sections:")
                    
                    for section in doc_metadata["sections"]:
                        st.write(f"**Section {section['number']}**: {section['title']}")
                
                # Display entities
                if doc_metadata["entities"]:
                    st.subheader("Identified Entities")
                    unique_entities = list(set(doc_metadata["entities"]))
                    st.write(f"This document mentions {len(unique_entities)} distinct organizations:")
                    
                    for entity in unique_entities:
                        st.write(f"- {entity}")
                
                # Display dates
                if doc_metadata["dates"]:
                    st.subheader("Referenced Dates")
                    unique_dates = list(set(doc_metadata["dates"]))
                    st.write(f"This document references {len(unique_dates)} distinct dates:")
                    
                    for date in unique_dates:
                        st.write(f"- {date}")
                
                # Add legal analysis options specific to Indian legal documents
                st.subheader("Legal Analysis")
                analysis_option = st.selectbox(
                    "Select Analysis Type:",
                    ["Citation Analysis", "Compliance Requirements", "Definitions", "Penalties and Liabilities"]
                )
                
                if st.button("Perform Analysis"):
                    with st.spinner("Analyzing document..."):
                        if analysis_option == "Citation Analysis":
                            st.write("**Case Citations Analysis**")
                            # Use the citation analyzer to extract citations
                            citation_report = st.session_state.citation_analyzer.generate_citation_report(current_doc)
                            
                            st.write(f"Found {citation_report['total_citations']} citations in the document:")
                            
                            # Display citation counts by type
                            citation_data = {"Type": [], "Count": []}
                            for citation_type, count in citation_report["citation_counts"].items():
                                if count > 0:
                                    citation_data["Type"].append(citation_type.replace("_", " ").title())
                                    citation_data["Count"].append(count)
                            
                            # Create a bar chart
                            if citation_data["Count"]:
                                chart = alt.Chart(pd.DataFrame(citation_data)).mark_bar().encode(
                                    x=alt.X('Type', title='Citation Type'),
                                    y=alt.Y('Count', title='Number of Citations'),
                                    color=alt.Color('Type', legend=None)
                                ).properties(
                                    title='Citations by Type',
                                    width=600,
                                    height=300
                                )
                                st.altair_chart(chart, use_container_width=True)
                            
                            # Display specific citations by type
                            for citation_type, citations in citation_report["all_citations"].items():
                                if citations:
                                    with st.expander(f"{citation_type.replace('_', ' ').title()} ({len(citations)})"):
                                        for citation in citations:
                                            st.write(f"- {citation}")
                            
                        elif analysis_option == "Compliance Requirements":
                            st.write("**Compliance Requirements**")
                            # Create a query for compliance requirements
                            result = st.session_state.qa_chain.ask("What are the key compliance requirements mentioned in this document?")
                            st.write(result["result"])
                            
                        elif analysis_option == "Definitions":
                            st.write("**Legal Definitions**")
                            # Create a query for definitions
                            result = st.session_state.qa_chain.ask("What are the important definitions provided in this document?")
                            st.write(result["result"])
                            
                        elif analysis_option == "Penalties and Liabilities":
                            st.write("**Penalties and Liabilities**")
                            # Create a query for penalties
                            result = st.session_state.qa_chain.ask("What are the penalties, fines, or liabilities mentioned in this document?")
                            st.write(result["result"])
            else:
                st.warning("No detailed metadata available for this document. Upload a PDF document to enable enhanced analysis.")

#--------------------- PAGE: DOCUMENT COMPARISON ---------------------
elif page == "Document Comparison":
    st.header("Document Comparison")
    
    documents = st.session_state.doc_manager.list_documents()
    
    if len(documents) < 2:
        st.warning("Please upload at least two documents to use the comparison feature.")
    else:
        # Create document selection dropdowns
        doc_options = {}
        for doc_id, metadata in documents:
            doc_options[doc_id] = f"{metadata['filename']} ({metadata['doc_type']})"
        
        col1, col2 = st.columns(2)
        with col1:
            doc1_id = st.selectbox("First Document", 
                                 list(doc_options.keys()), 
                                 format_func=lambda x: doc_options[x],
                                 key="doc1_select")
        with col2:
            # Exclude the first document from the second dropdown
            remaining_options = {k: v for k, v in doc_options.items() if k != doc1_id}
            doc2_id = st.selectbox("Second Document", 
                                 list(remaining_options.keys()), 
                                 format_func=lambda x: doc_options[x],
                                 key="doc2_select")
        
        if st.button("Compare Documents"):
            with st.spinner("Comparing documents... This may take a moment."):
                # Retrieve document texts and metadata
                doc1_text, doc1_meta = st.session_state.doc_manager.get_document(doc1_id)
                doc2_text, doc2_meta = st.session_state.doc_manager.get_document(doc2_id)
                
                # Perform comparison
                comparison_results = st.session_state.doc_comparison.compare_documents(
                    doc1_text, doc1_meta, doc2_text, doc2_meta
                )
                
                # Display results
                st.subheader("Comparison Results")
                
                # Show similarity score
                st.metric("Overall Text Similarity", 
                         f"{comparison_results['similarity_score'] * 100:.1f}%")
                
                # Create tabs for different aspects of comparison
                tab1, tab2, tab3, tab4 = st.tabs([
                    "Key Differences", "Shared References", "Section Comparison", "Text Diff"
                ])
                
                with tab1:
                    st.write("#### Document Comparison Overview")
                    
                    # Create a basic comparison table
                    comparison_data = {
                        "Metric": ["Entities", "Case Citations", "Statutes Referenced"],
                        f"{doc1_meta['filename']} Only": [
                            comparison_results["doc1_unique"]["entity_count"],
                            comparison_results["doc1_unique"]["citation_count"],
                            comparison_results["doc1_unique"]["statute_count"]
                        ],
                        "Shared": [
                            len(comparison_results["shared_entities"]),
                            len(comparison_results["shared_citations"]),
                            len(comparison_results["shared_statutes"])
                        ],
                        f"{doc2_meta['filename']} Only": [
                            comparison_results["doc2_unique"]["entity_count"],
                            comparison_results["doc2_unique"]["citation_count"],
                            comparison_results["doc2_unique"]["statute_count"]
                        ]
                    }
                    
                    st.table(pd.DataFrame(comparison_data))
                    
                    # Create a basic bar chart for the comparison
                    chart_data = pd.DataFrame({
                        f"{doc1_meta['filename']}": [
                            comparison_results["doc1_unique"]["entity_count"],
                            comparison_results["doc1_unique"]["citation_count"],
                            comparison_results["doc1_unique"]["statute_count"]
                        ],
                        "Shared": [
                            len(comparison_results["shared_entities"]),
                            len(comparison_results["shared_citations"]),
                            len(comparison_results["shared_statutes"])
                        ],
                        f"{doc2_meta['filename']}": [
                            comparison_results["doc2_unique"]["entity_count"],
                            comparison_results["doc2_unique"]["citation_count"],
                            comparison_results["doc2_unique"]["statute_count"]
                        ]
                    }, index=["Entities", "Case Citations", "Statutes"])
                    
                    st.bar_chart(chart_data)
                
                with tab2:
                    st.write("#### Shared References")
                    
                    # Show shared entities
                    if comparison_results["shared_entities"]:
                        # Fixed to use markdown instead of expander
                        st.markdown(f"**Shared Entities ({len(comparison_results['shared_entities'])})**")
                        for entity in comparison_results["shared_entities"]:
                            st.write(f"- {entity}")
                    else:
                        st.info("No shared entities found.")
                    
                    # Show shared citations
                    if comparison_results["shared_citations"]:
                        # Fixed to use markdown instead of expander
                        st.markdown(f"**Shared Case Citations ({len(comparison_results['shared_citations'])})**")
                        for citation in comparison_results["shared_citations"]:
                            st.write(f"- {citation}")
                    else:
                        st.info("No shared case citations found.")
                    
                    # Show shared statutes
                    if comparison_results["shared_statutes"]:
                        # Fixed to use markdown instead of expander
                        st.markdown(f"**Shared Statutes ({len(comparison_results['shared_statutes'])})**")
                        for statute in comparison_results["shared_statutes"]:
                            st.write(f"- {statute}")
                    else:
                        st.info("No shared statutes found.")
                
                with tab3:
                    st.write("#### Section Comparison")
                    
                    if comparison_results["section_comparison"]:
                        st.write(f"Found {len(comparison_results['section_comparison'])} sections with the same number in both documents:")
                        
                        # Table for section comparison
                        section_data = []
                        for section_match in comparison_results["section_comparison"]:
                            section_data.append({
                                "Section": section_match["section"],
                                f"{doc1_meta['filename']} Title": section_match["title1"],
                                f"{doc2_meta['filename']} Title": section_match["title2"],
                                "Similarity": f"{section_match['similarity'] * 100:.0f}%"
                            })
                        
                        st.table(pd.DataFrame(section_data))
                    else:
                        st.info("No matching section numbers found between the two documents.")
                
                with tab4:
                    st.write("#### Text Differences")
                    st.write("First 200 differences between the documents:")
                    
                    if comparison_results["diff"]:
                        for diff_type, line in comparison_results["diff"]:
                            if diff_type == "added":
                                st.markdown(f"<span style='color:green'>+ {line}</span>", unsafe_allow_html=True)
                            elif diff_type == "removed":
                                st.markdown(f"<span style='color:red'>- {line}</span>", unsafe_allow_html=True)
                            else:
                                st.text(line)
                    else:
                        st.info("No significant text differences detected.")

#--------------------- PAGE: CITATION ANALYSIS ---------------------
elif page == "Citation Analysis":
    st.header("Citation Analysis")
    
    documents = st.session_state.doc_manager.list_documents()
    
    if not documents:
        st.warning("Please upload and process at least one document first.")
    else:
        st.write("This tool analyzes legal citations across your documents.")
        
        # Option to analyze a single document or all documents
        analysis_type = st.radio(
            "Analysis Type",
            ["Single Document Analysis", "Cross-Document Citation Network"]
        )
        
        if analysis_type == "Single Document Analysis":
            # Document selection
            doc_options = {}
            for doc_id, metadata in documents:
                doc_options[doc_id] = f"{metadata['filename']} ({metadata['doc_type']})"
            
            selected_doc_id = st.selectbox(
                "Select Document to Analyze",
                list(doc_options.keys()),
                format_func=lambda x: doc_options[x]
            )
            
            if st.button("Analyze Citations"):
                with st.spinner("Analyzing citations in the document..."):
                    # Get document text
                    doc_text, doc_meta = st.session_state.doc_manager.get_document(selected_doc_id)
                    
                    # Generate citation report
                    citation_report = st.session_state.citation_analyzer.generate_citation_report(doc_text)
                    
                    # Display results
                    st.subheader(f"Citation Analysis for {doc_meta['filename']}")
                    
                    # Summary
                    st.write(f"Found {citation_report['total_citations']} citations in this document.")
                    
                    # Citation chart
                    if citation_report['total_citations'] > 0:
                        # Create data for pie chart
                        citation_data = {"Type": [], "Count": []}
                        for citation_type, count in citation_report["citation_counts"].items():
                            if count > 0:
                                citation_data["Type"].append(citation_type.replace("_", " ").title())
                                citation_data["Count"].append(count)
                        
                        # Create a pie chart
                        if citation_data["Count"]:
                            fig, ax = plt.subplots(figsize=(8, 6))
                            ax.pie(citation_data["Count"], labels=citation_data["Type"], autopct='%1.1f%%',
                                  startangle=90, shadow=False)
                            ax.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle
                            
                            # Convert to base64 for display
                            buf = io.BytesIO()
                            fig.savefig(buf, format='png', dpi=100, bbox_inches='tight')
                            buf.seek(0)
                            img_str = base64.b64encode(buf.read()).decode('utf-8')
                            
                            st.markdown(f"<img src='data:image/png;base64,{img_str}' alt='Citation Type Distribution' width='600'/>", 
                                      unsafe_allow_html=True)
                            plt.close(fig)
                        
                        # Display by type
                        for citation_type, citations in citation_report["all_citations"].items():
                            if citations:
                                with st.expander(f"{citation_type.replace('_', ' ').title()} ({len(citations)})"):
                                    for citation in citations:
                                        st.write(f"- {citation}")
                    else:
                        st.info("No citations were detected in this document.")
        
        else:  # Cross-Document Citation Network
            if len(documents) < 2:
                st.warning("Please upload at least two documents to generate a citation network.")
            else:
                if st.button("Generate Citation Network"):
                    with st.spinner("Generating citation network across all documents..."):
                        # Prepare document data
                        doc_data = []
                        for doc_id, metadata in documents:
                            doc_text, _ = st.session_state.doc_manager.get_document(doc_id)
                            doc_data.append((doc_id, doc_text, metadata))
                        
                        # Build citation network
                        network = st.session_state.citation_analyzer.build_citation_network(doc_data)
                        
                        # Render network visualization
                        if len(network.nodes()) > 1:  # Only if we have a meaningful network
                            st.subheader("Citation Network Visualization")
                            
                            # Plot and get base64 image
                            img_str = st.session_state.citation_analyzer.plot_citation_network(network)
                            
                            # Display the image
                            st.markdown(f"<img src='data:image/png;base64,{img_str}' alt='Citation Network' width='100%'/>", 
                                      unsafe_allow_html=True)
                            
                            # Network statistics
                            st.subheader("Network Statistics")
                            
                            # Count node types
                            node_types = {}
                            for node, data in network.nodes(data=True):
                                node_type = data.get('type', 'unknown')
                                node_types[node_type] = node_types.get(node_type, 0) + 1
                            
                            # Display stats
                            stats_data = {
                                "Metric": ["Documents", "Citations", "Connections"],
                                "Count": [
                                    node_types.get('document', 0),
                                    sum(count for node_type, count in node_types.items() if node_type != 'document'),
                                    network.number_of_edges()
                                ]
                            }
                            
                            st.table(pd.DataFrame(stats_data))
                            
                            # Legend
                            st.markdown("""
                            **Legend:**
                            - **Blue nodes**: Documents
                            - **Red nodes**: Case citations
                            - **Green nodes**: Statute citations
                            - **Yellow nodes**: Constitution citations
                            - **Purple nodes**: Section citations
                            
                            Edges indicate that a document cites a particular legal reference, or that two documents share common citations.
                            """)
                        else:
                            st.info("No citation relationships were detected between documents.")

# Footer
st.sidebar.markdown("---")
st.sidebar.info("Indian Legal Document RAG QA System - A tool for analyzing Indian laws and legal documents")