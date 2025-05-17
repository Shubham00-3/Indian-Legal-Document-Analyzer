# citation_analyzer.py
# Analyzes and extracts citation networks from legal documents

import re
import networkx as nx
import matplotlib.pyplot as plt
from collections import defaultdict
import io
import base64

class CitationAnalyzer:
    def __init__(self):
        """Initialize the citation analyzer"""
        # Regular expressions for detecting various citation types
        self.patterns = {
            "case_citations": [
                r'\(\d{4}\)\s+\d+\s+SCC\s+\d+',  # SCC format
                r'\d{4}\s+\(\d+\)\s+SCC\s+\d+',  # Alternative SCC format
                r'AIR\s+\d{4}\s+SC\s+\d+',       # AIR SC format
                r'\(\d{4}\)\s+\d+\s+SCR\s+\d+',  # SCR format
            ],
            "statute_citations": [
                r'(?:The\s+)?([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\s+Act,?\s+(?:of\s+)?\d{4})',  # Act format
                r'(?:The\s+)?([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\s+Rules,?\s+(?:of\s+)?\d{4})',  # Rules format
                r'(?:The\s+)?([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\s+Regulation,?\s+(?:of\s+)?\d{4})',  # Regulation format
            ],
            "constitution_citations": [
    r'[Aa]rticle\s+(\d+(?:\(\d+\))?(?:\([a-z]\))?)', # Basic pattern
    r'[Aa]rticle\s+(\d+)(?:\((\d+)(?:\(([a-z])\))?)?\)', # More specific pattern to capture structured references
    r'[Aa]rticle\s+(\d+(?:\(\d+\))?(?:\([a-z]\))?)\s+of\s+the\s+Constitution',
],
            "section_citations": [
                r'Section\s+(\d+(?:\([a-z]\))?)\s+of\s+the\s+([A-Za-z\s]+)',  # Section format
                r'under\s+[Ss]ection\s+(\d+(?:\([a-z]\))?)',  # Alternative section format
            ]
        }
    
    def extract_citations(self, text):
        """
        Extract all citations from text
        
        Parameters:
        - text: Document text
        
        Returns:
        - Dictionary with citation types and matches
        """
        citations = {}
        
        for citation_type, patterns in self.patterns.items():
            matches = []
            for pattern in patterns:
                found = re.findall(pattern, text)
                # Handle both string matches and tuple matches from regex groups
                for match in found:
                    if isinstance(match, tuple):
                        # For multi-group matches, join with a space
                        matches.append(" ".join([m for m in match if m]))
                    else:
                        matches.append(match)
            
            # Remove duplicates while preserving order
            unique_matches = []
            for item in matches:
                if item not in unique_matches:
                    unique_matches.append(item)
            
            citations[citation_type] = unique_matches
        
        return citations
    
    def build_citation_network(self, documents):
        """
        Build a citation network from multiple documents
        
        Parameters:
        - documents: List of (doc_id, text, metadata) tuples
        
        Returns:
        - NetworkX graph object
        """
        G = nx.DiGraph()
        
        # Extract citations from each document
        doc_citations = {}
        for doc_id, text, metadata in documents:
            doc_name = metadata.get('filename', doc_id)
            G.add_node(doc_name, type='document')
            
            citations = self.extract_citations(text)
            doc_citations[doc_name] = citations
            
            # Add citation nodes
            for citation_type, matches in citations.items():
                for citation in matches:
                    citation_str = f"{citation_type}:{citation}"
                    if not G.has_node(citation_str):
                        G.add_node(citation_str, type=citation_type)
                    G.add_edge(doc_name, citation_str)
        
        # Add connections between documents that cite the same sources
        citation_to_docs = defaultdict(list)
        for doc_name, citations in doc_citations.items():
            for citation_type, matches in citations.items():
                for citation in matches:
                    citation_str = f"{citation_type}:{citation}"
                    citation_to_docs[citation_str].append(doc_name)
        
        # Connect documents that share citations
        for citation, citing_docs in citation_to_docs.items():
            if len(citing_docs) > 1:
                for i in range(len(citing_docs)):
                    for j in range(i+1, len(citing_docs)):
                        G.add_edge(citing_docs[i], citing_docs[j], shared=citation)
        
        return G
    
    def plot_citation_network(self, graph):
        """
        Plot the citation network visualization as a base64 encoded image
        
        Parameters:
        - graph: NetworkX graph object
        
        Returns:
        - Base64 encoded image string for embedding in HTML
        """
        plt.figure(figsize=(12, 8))
        
        # Node colors based on type
        colors = []
        for node in graph.nodes():
            node_type = graph.nodes[node].get('type', '')
            if node_type == 'document':
                colors.append('skyblue')
            elif node_type == 'case_citations':
                colors.append('tomato')
            elif node_type == 'statute_citations':
                colors.append('lightgreen')
            elif node_type == 'constitution_citations':
                colors.append('gold')
            elif node_type == 'section_citations':
                colors.append('orchid')
            else:
                colors.append('gray')
        
        # Draw the network
        pos = nx.spring_layout(graph, seed=42)
        nx.draw_networkx_nodes(graph, pos, node_size=700, node_color=colors, alpha=0.8)
        nx.draw_networkx_edges(graph, pos, edge_color='gray', alpha=0.5, arrows=True)
        
        # Adjust labels to abbreviate long nodes
        labels = {}
        for node in graph.nodes():
            if len(node) > 30:
                labels[node] = node[:27] + "..."
            else:
                labels[node] = node
        
        nx.draw_networkx_labels(graph, pos, labels=labels, font_size=8)
        
        plt.axis('off')
        plt.tight_layout()
        
        # Save figure to a bytes buffer
        buf = io.BytesIO()
        plt.savefig(buf, format='png', dpi=150, bbox_inches='tight')
        plt.close()
        
        # Encode the bytes as base64 for HTML embedding
        buf.seek(0)
        img_str = base64.b64encode(buf.read()).decode('utf-8')
        
        return img_str
    
    def generate_citation_report(self, text):
        """
        Generate a report of citations in a document
        
        Parameters:
        - text: Document text
        
        Returns:
        - Dictionary with citation analysis
        """
        citations = self.extract_citations(text)
        
        # Count citation types
        citation_counts = {k: len(v) for k, v in citations.items()}
        total_citations = sum(citation_counts.values())
        
        # Identify most cited references
        all_citations = []
        for citation_type, matches in citations.items():
            for citation in matches:
                all_citations.append((citation_type, citation))
        
        # Count occurrences of each citation
        citation_frequency = defaultdict(int)
        for citation in all_citations:
            citation_frequency[citation] += 1
        
        # Get top citations
        top_citations = sorted(citation_frequency.items(), key=lambda x: x[1], reverse=True)[:5]
        
        return {
            "citation_counts": citation_counts,
            "total_citations": total_citations,
            "top_citations": top_citations,
            "all_citations": dict(citations),  # Convert to regular dict for JSON serialization
        }