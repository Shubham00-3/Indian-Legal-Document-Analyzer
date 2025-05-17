# document_comparison.py
# Handles document comparison functionality for legal documents

import re
import difflib
from collections import Counter

class DocumentComparison:
    def __init__(self, doc_processor=None):
        """Initialize the document comparison tool"""
        self.doc_processor = doc_processor
    
    def compare_documents(self, doc1_text, doc1_meta, doc2_text, doc2_meta):
        """
        Compare two documents and identify similarities and differences
        
        Parameters:
        - doc1_text: Text of first document
        - doc1_meta: Metadata of first document
        - doc2_text: Text of second document
        - doc2_meta: Metadata of second document
        
        Returns:
        - Dictionary with comparison results
        """
        # Text similarity calculation
        similarity = self._calculate_text_similarity(doc1_text, doc2_text)
        
        # Extract metadata if not already done
        doc1_metadata = {}
        doc2_metadata = {}
        
        if self.doc_processor:
            doc1_metadata = self.doc_processor.extract_metadata(doc1_text)
            doc2_metadata = self.doc_processor.extract_metadata(doc2_text)
        
        # Shared elements analysis
        shared_entities = self._get_shared_elements(
            doc1_metadata.get("entities", []), 
            doc2_metadata.get("entities", [])
        )
        
        shared_citations = self._get_shared_elements(
            doc1_metadata.get("case_citations", []), 
            doc2_metadata.get("case_citations", [])
        )
        
        shared_statutes = self._get_shared_elements(
            doc1_metadata.get("statutes", []), 
            doc2_metadata.get("statutes", [])
        )
        
        # Section comparison
        section_comparison = self._compare_sections(
            doc1_metadata.get("sections", []),
            doc2_metadata.get("sections", [])
        )
        
        # Create diff of significant portions
        # Limit to first 50,000 chars to avoid performance issues
        diff_result = self._generate_diff(doc1_text[:50000], doc2_text[:50000])
        
        return {
            "similarity_score": similarity,
            "shared_entities": shared_entities,
            "shared_citations": shared_citations,
            "shared_statutes": shared_statutes,
            "section_comparison": section_comparison,
            "diff": diff_result,
            "doc1_unique": {
                "entity_count": len(doc1_metadata.get("entities", [])) - len(shared_entities),
                "citation_count": len(doc1_metadata.get("case_citations", [])) - len(shared_citations),
                "statute_count": len(doc1_metadata.get("statutes", [])) - len(shared_statutes),
            },
            "doc2_unique": {
                "entity_count": len(doc2_metadata.get("entities", [])) - len(shared_entities),
                "citation_count": len(doc2_metadata.get("case_citations", [])) - len(shared_citations),
                "statute_count": len(doc2_metadata.get("statutes", [])) - len(shared_statutes),
            }
        }
    
    def _calculate_text_similarity(self, text1, text2):
        """Calculate Jaccard similarity between two texts"""
        # Convert to sets of words for comparison
        words1 = set(re.findall(r'\b\w+\b', text1.lower()))
        words2 = set(re.findall(r'\b\w+\b', text2.lower()))
        
        # Calculate Jaccard similarity
        intersection = len(words1.intersection(words2))
        union = len(words1.union(words2))
        
        return round(intersection / union, 4) if union > 0 else 0
    
    def _get_shared_elements(self, list1, list2):
        """Find shared elements between two lists"""
        set1 = set(list1)
        set2 = set(list2)
        return list(set1.intersection(set2))
    
    def _compare_sections(self, sections1, sections2):
        """Compare sections between documents"""
        # Create dictionaries mapping section numbers to titles
        sec1_dict = {s["number"]: s["title"] for s in sections1}
        sec2_dict = {s["number"]: s["title"] for s in sections2}
        
        # Find common section numbers
        common_sections = set(sec1_dict.keys()).intersection(set(sec2_dict.keys()))
        
        # Compare titles of common sections
        section_comparison = []
        for section in common_sections:
            title1 = sec1_dict[section]
            title2 = sec2_dict[section]
            
            # Check if titles are similar
            similarity = difflib.SequenceMatcher(None, title1, title2).ratio()
            
            section_comparison.append({
                "section": section,
                "title1": title1,
                "title2": title2,
                "similarity": round(similarity, 2)
            })
        
        return section_comparison
    
    def _generate_diff(self, text1, text2):
        """Generate a readable diff between two texts"""
        # Split by lines
        lines1 = text1.splitlines()
        lines2 = text2.splitlines()
        
        # Generate diff
        diff = difflib.unified_diff(lines1, lines2, lineterm='')
        
        # Convert to readable format
        readable_diff = []
        for line in diff:
            if line.startswith('+') and not line.startswith('+++'):
                readable_diff.append(("added", line[1:]))
            elif line.startswith('-') and not line.startswith('---'):
                readable_diff.append(("removed", line[1:]))
            elif not line.startswith('@@') and not line.startswith('---') and not line.startswith('+++'):
                readable_diff.append(("unchanged", line))
        
        # Limit the diff size to avoid overwhelming the UI
        return readable_diff[:200]  # Return first 200 diff lines