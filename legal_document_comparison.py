# legal_document_comparison.py
# Module for comparing legal documents and provisions

import re
import difflib
from collections import defaultdict

class LegalDocumentComparison:
    def __init__(self):
        """Initialize legal document comparison module"""
        # Common section titles to look for when comparing documents
        self.common_sections = [
            "confidentiality", "intellectual property", "termination",
            "indemnification", "liability", "payment", "term", "governing law",
            "dispute resolution", "warranties", "force majeure"
        ]
    
    def extract_section(self, document, section_name):
        """
        Extract a specific section from a document
        
        Parameters:
        - document: Document text
        - section_name: Name of section to extract (e.g., "confidentiality")
        
        Returns:
        - Extracted section text or None if not found
        """
        # Try different patterns for section headers
        patterns = [
            # Pattern for "SECTION X. TITLE" format
            r'(?:SECTION|ARTICLE)\s+\d+(?:\.\d+)*\s*\.\s*' + section_name + r'\s*\n(.*?)(?:(?:SECTION|ARTICLE)\s+\d+(?:\.\d+)*\s*\.|$)',
            # Pattern for "X. TITLE" format
            r'\d+(?:\.\d+)*\s*\.\s*' + section_name + r'\s*\n(.*?)(?:\d+(?:\.\d+)*\s*\.|$)',
            # Pattern for just the title (case insensitive)
            r'(?i)(?<!\w)' + re.escape(section_name) + r'(?!\w).*?\n(.*?)(?=\n\s*\n|\n\s*[A-Z]|\Z)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, document, re.IGNORECASE | re.DOTALL)
            if match:
                return match.group(1).strip()
        
        return None
    
    def compare_documents(self, doc1, doc2):
        """
        Compare two documents and identify differences
        
        Parameters:
        - doc1: First document text
        - doc2: Second document text
        
        Returns:
        - Dictionary with comparison results
        """
        results = {
            "common_sections": [],
            "unique_to_doc1": [],
            "unique_to_doc2": [],
            "section_comparisons": {}
        }
        
        # Extract sections from both documents
        doc1_sections = self._extract_all_sections(doc1)
        doc2_sections = self._extract_all_sections(doc2)
        
        # Find common and unique sections
        all_sections = set(doc1_sections.keys()) | set(doc2_sections.keys())
        
        for section in all_sections:
            if section in doc1_sections and section in doc2_sections:
                results["common_sections"].append(section)
                
                # Compare the content of this section
                similarity = self._calculate_similarity(doc1_sections[section], doc2_sections[section])
                
                results["section_comparisons"][section] = {
                    "similarity_score": similarity,
                    "doc1_length": len(doc1_sections[section]),
                    "doc2_length": len(doc2_sections[section])
                }
            elif section in doc1_sections:
                results["unique_to_doc1"].append(section)
            else:
                results["unique_to_doc2"].append(section)
        
        # Compare specific important sections in more detail
        for section_name in self.common_sections:
            if section_name in results["common_sections"]:
                detailed_comparison = self._compare_section_detailed(
                    doc1_sections[section_name], 
                    doc2_sections[section_name]
                )
                results["section_comparisons"][section_name]["detailed"] = detailed_comparison
        
        return results
    
    def compare_specific_provision(self, doc1, doc2, provision_name):
        """
        Compare a specific provision between two documents
        
        Parameters:
        - doc1: First document text
        - doc2: Second document text
        - provision_name: Name of provision to compare
        
        Returns:
        - Dictionary with comparison results
        """
        # Extract the provisions from both documents
        provision1 = self.extract_section(doc1, provision_name)
        provision2 = self.extract_section(doc2, provision_name)
        
        result = {
            "found_in_doc1": provision1 is not None,
            "found_in_doc2": provision2 is not None,
            "comparison": None
        }
        
        # If found in both documents, compare them
        if provision1 and provision2:
            similarity = self._calculate_similarity(provision1, provision2)
            
            # Generate a diff for detailed comparison
            diff = list(difflib.ndiff(provision1.split(), provision2.split()))
            
            result["comparison"] = {
                "similarity_score": similarity,
                "doc1_length": len(provision1),
                "doc2_length": len(provision2),
                "diff": diff,
                "key_differences": self._extract_key_differences(diff)
            }
        
        return result
    
    def _extract_all_sections(self, document):
        """Helper to extract all detectable sections from a document"""
        sections = {}
        
        # Pattern to find sections with headers
        section_pattern = r'(?:SECTION|ARTICLE)\s+(\d+(?:\.\d+)*)\s*\.\s*([A-Z][A-Z\s]+)'
        matches = re.finditer(section_pattern, document)
        
        for match in matches:
            section_num = match.group(1)
            section_title = match.group(2).strip().lower()
            
            # Find the content of this section
            start_pos = match.end()
            next_section = re.search(r'(?:SECTION|ARTICLE)\s+\d+(?:\.\d+)*\s*\.', document[start_pos:])
            
            if next_section:
                end_pos = start_pos + next_section.start()
                section_content = document[start_pos:end_pos].strip()
            else:
                # Last section in document
                section_content = document[start_pos:].strip()
            
            # Store by section title
            sections[section_title] = section_content
            
            # Also try to extract by common alternative names
            for common_section in self.common_sections:
                if common_section in section_title:
                    sections[common_section] = section_content
        
        # Also try to extract common sections by name if not found by heading
        for section_name in self.common_sections:
            if section_name not in sections:
                section_content = self.extract_section(document, section_name)
                if section_content:
                    sections[section_name] = section_content
        
        return sections
    
    def _calculate_similarity(self, text1, text2):
        """Calculate similarity score between two texts"""
        return difflib.SequenceMatcher(None, text1, text2).ratio() * 100
    
    def _compare_section_detailed(self, section1, section2):
        """Perform detailed comparison of two sections"""
        words1 = section1.split()
        words2 = section2.split()
        
        # Calculate stats
        stats = {
            "word_count1": len(words1),
            "word_count2": len(words2),
            "word_difference": abs(len(words1) - len(words2)),
            "added_words": [],
            "removed_words": [],
            "common_words": set(words1) & set(words2),
            "similarity_score": self._calculate_similarity(section1, section2)
        }
        
        # Generate diff
        diff = list(difflib.ndiff(words1, words2))
        
        # Analyze diff to find added/removed words
        for word in diff:
            if word.startswith('- '):
                stats["removed_words"].append(word[2:])
            elif word.startswith('+ '):
                stats["added_words"].append(word[2:])
        
        return stats
    
    def _extract_key_differences(self, diff):
        """Extract key differences from a diff result"""
        key_diffs = {
            "added": [],
            "removed": []
        }
        
        # Look for consecutive additions or removals
        current_addition = []
        current_removal = []
        
        for item in diff:
            if item.startswith('+ '):
                current_addition.append(item[2:])
                if current_removal:
                    if len(current_removal) > 2:  # Only track significant changes
                        key_diffs["removed"].append(' '.join(current_removal))
                    current_removal = []
            elif item.startswith('- '):
                current_removal.append(item[2:])
                if current_addition:
                    if len(current_addition) > 2:  # Only track significant changes
                        key_diffs["added"].append(' '.join(current_addition))
                    current_addition = []
            else:
                # Handle end of sequences
                if current_addition and len(current_addition) > 2:
                    key_diffs["added"].append(' '.join(current_addition))
                if current_removal and len(current_removal) > 2:
                    key_diffs["removed"].append(' '.join(current_removal))
                current_addition = []
                current_removal = []
        
        # Handle any remaining sequences
        if current_addition and len(current_addition) > 2:
            key_diffs["added"].append(' '.join(current_addition))
        if current_removal and len(current_removal) > 2:
            key_diffs["removed"].append(' '.join(current_removal))
        
        return key_diffs