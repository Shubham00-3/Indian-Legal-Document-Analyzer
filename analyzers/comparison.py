# comparison.py
# Unified document comparison module

import re
import difflib
from collections import defaultdict
from typing import Dict, List, Any, Optional, Tuple


class DocumentComparison:
    """
    Unified document comparison that handles:
    - Section-by-section comparison
    - Similarity scoring
    - Diff generation
    - Legal entity/citation comparison
    """
    
    def __init__(self, doc_processor=None):
        """
        Initialize document comparison
        
        Parameters:
        - doc_processor: Optional DocumentProcessor for metadata extraction
        """
        self.doc_processor = doc_processor
        
        # Common legal section titles
        self.common_sections = [
            "confidentiality", "intellectual property", "termination",
            "indemnification", "liability", "payment", "term", "governing law",
            "dispute resolution", "warranties", "force majeure"
        ]
    
    def compare_documents(
        self, 
        doc1_text: str, 
        doc1_meta: Dict[str, Any],
        doc2_text: str, 
        doc2_meta: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Compare two documents comprehensively
        
        Returns dictionary with:
        - similarity_score: Overall text similarity
        - shared_entities, shared_citations, shared_statutes
        - doc1_unique, doc2_unique: Unique elements in each
        - section_comparison: Matching sections
        - diff: Line-by-line differences
        """
        results = {
            "similarity_score": self._calculate_similarity(doc1_text, doc2_text),
            "shared_entities": [],
            "shared_citations": [],
            "shared_statutes": [],
            "doc1_unique": {"entity_count": 0, "citation_count": 0, "statute_count": 0},
            "doc2_unique": {"entity_count": 0, "citation_count": 0, "statute_count": 0},
            "section_comparison": [],
            "diff": []
        }
        
        # Extract metadata if processor available
        if self.doc_processor:
            meta1 = self.doc_processor.extract_metadata(doc1_text)
            meta2 = self.doc_processor.extract_metadata(doc2_text)
            
            # Compare entities
            entities1 = set(meta1.get("entities", []))
            entities2 = set(meta2.get("entities", []))
            results["shared_entities"] = list(entities1 & entities2)
            results["doc1_unique"]["entity_count"] = len(entities1 - entities2)
            results["doc2_unique"]["entity_count"] = len(entities2 - entities1)
        
        # Extract and compare citations
        citations1 = self._extract_citations(doc1_text)
        citations2 = self._extract_citations(doc2_text)
        
        results["shared_citations"] = list(set(citations1["cases"]) & set(citations2["cases"]))
        results["shared_statutes"] = list(set(citations1["statutes"]) & set(citations2["statutes"]))
        
        results["doc1_unique"]["citation_count"] = len(set(citations1["cases"]) - set(citations2["cases"]))
        results["doc2_unique"]["citation_count"] = len(set(citations2["cases"]) - set(citations1["cases"]))
        results["doc1_unique"]["statute_count"] = len(set(citations1["statutes"]) - set(citations2["statutes"]))
        results["doc2_unique"]["statute_count"] = len(set(citations2["statutes"]) - set(citations1["statutes"]))
        
        # Compare sections
        sections1 = self._extract_sections(doc1_text)
        sections2 = self._extract_sections(doc2_text)
        
        for section_num in set(sections1.keys()) & set(sections2.keys()):
            similarity = self._calculate_similarity(
                sections1[section_num]["content"],
                sections2[section_num]["content"]
            )
            results["section_comparison"].append({
                "section": section_num,
                "title1": sections1[section_num]["title"],
                "title2": sections2[section_num]["title"],
                "similarity": similarity
            })
        
        # Generate diff (first 200 lines)
        results["diff"] = self._generate_diff(doc1_text, doc2_text)[:200]
        
        return results
    
    def compare_specific_provision(
        self, 
        doc1: str, 
        doc2: str, 
        provision_name: str
    ) -> Dict[str, Any]:
        """Compare a specific provision between two documents"""
        provision1 = self._extract_section_by_name(doc1, provision_name)
        provision2 = self._extract_section_by_name(doc2, provision_name)
        
        result = {
            "found_in_doc1": provision1 is not None,
            "found_in_doc2": provision2 is not None,
            "comparison": None
        }
        
        if provision1 and provision2:
            similarity = self._calculate_similarity(provision1, provision2)
            diff = list(difflib.ndiff(provision1.split(), provision2.split()))
            
            result["comparison"] = {
                "similarity_score": similarity,
                "doc1_length": len(provision1),
                "doc2_length": len(provision2),
                "key_differences": self._extract_key_differences(diff)
            }
        
        return result
    
    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """Calculate similarity score between two texts (0-1)"""
        return difflib.SequenceMatcher(None, text1, text2).ratio()
    
    def _extract_citations(self, text: str) -> Dict[str, List[str]]:
        """Extract legal citations from text"""
        citations = {"cases": [], "statutes": []}
        
        # Case citations (SCC, AIR, etc.)
        case_patterns = [
            r'\(\d{4}\)\s+\d+\s+SCC\s+\d+',
            r'AIR\s+\d{4}\s+SC\s+\d+',
        ]
        for pattern in case_patterns:
            citations["cases"].extend(re.findall(pattern, text))
        
        # Statute citations
        statute_pattern = r'(?:The\s+)?([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\s+Act,?\s+(?:of\s+)?\d{4})'
        citations["statutes"] = re.findall(statute_pattern, text)
        
        return citations
    
    def _extract_sections(self, text: str) -> Dict[str, Dict[str, str]]:
        """Extract sections with their content"""
        sections = {}
        pattern = r'(?:SECTION|ARTICLE)\s+(\d+(?:\.\d+)*)\s*\.?\s*([A-Z][A-Z\s]+)'
        
        matches = list(re.finditer(pattern, text))
        for i, match in enumerate(matches):
            section_num = match.group(1)
            section_title = match.group(2).strip()
            
            start = match.end()
            end = matches[i+1].start() if i+1 < len(matches) else len(text)
            content = text[start:end].strip()
            
            sections[section_num] = {"title": section_title, "content": content}
        
        return sections
    
    def _extract_section_by_name(self, text: str, section_name: str) -> Optional[str]:
        """Extract a section by its name"""
        patterns = [
            r'(?:SECTION|ARTICLE)\s+\d+(?:\.\d+)*\s*\.\s*' + section_name + r'\s*\n(.*?)(?:(?:SECTION|ARTICLE)\s+\d+|$)',
            r'(?i)(?<!\w)' + re.escape(section_name) + r'(?!\w).*?\n(.*?)(?=\n\s*\n|\n\s*[A-Z]|\Z)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
            if match:
                return match.group(1).strip()
        return None
    
    def _generate_diff(self, text1: str, text2: str) -> List[Tuple[str, str]]:
        """Generate line-by-line diff"""
        lines1 = text1.splitlines()
        lines2 = text2.splitlines()
        
        diff = []
        for line in difflib.unified_diff(lines1, lines2, lineterm=''):
            if line.startswith('+') and not line.startswith('+++'):
                diff.append(("added", line[1:]))
            elif line.startswith('-') and not line.startswith('---'):
                diff.append(("removed", line[1:]))
        
        return diff
    
    def _extract_key_differences(self, diff: List[str]) -> Dict[str, List[str]]:
        """Extract key differences from a word diff"""
        key_diffs = {"added": [], "removed": []}
        
        current_add = []
        current_remove = []
        
        for item in diff:
            if item.startswith('+ '):
                current_add.append(item[2:])
                if current_remove and len(current_remove) > 2:
                    key_diffs["removed"].append(' '.join(current_remove))
                current_remove = []
            elif item.startswith('- '):
                current_remove.append(item[2:])
                if current_add and len(current_add) > 2:
                    key_diffs["added"].append(' '.join(current_add))
                current_add = []
            else:
                if current_add and len(current_add) > 2:
                    key_diffs["added"].append(' '.join(current_add))
                if current_remove and len(current_remove) > 2:
                    key_diffs["removed"].append(' '.join(current_remove))
                current_add = []
                current_remove = []
        
        return key_diffs
