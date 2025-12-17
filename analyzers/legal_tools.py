# legal_analyzer_tools.py
# Advanced tools for legal document analysis

import re

class LegalAnalysisTools:
    def __init__(self):
        """Initialize legal analysis tools"""
        pass
    
    def extract_contract_details(self, text):
        """
        Extract key contract details like parties, dates, and values
        
        Parameters:
        - text: The document text
        
        Returns:
        - Dictionary of extracted details
        """
        details = {}
        
        # Extract effective date
        date_patterns = [
            r'effective as of\s+([A-Za-z]+\s+\d{1,2},\s+\d{4})',
            r'dated\s+([A-Za-z]+\s+\d{1,2},\s+\d{4})',
            r'dated\s+this\s+(\d{1,2}(?:st|nd|rd|th)?\s+day\s+of\s+[A-Za-z]+,\s+\d{4})'
        ]
        
        for pattern in date_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                details["effective_date"] = match.group(1)
                break
        
        # Extract parties
        parties_pattern = r'between\s+([^,]+),\s+a[n]?\s+([^,]+),?(?:\s+organized\s+under\s+the\s+laws\s+of\s+([^,]+))?[^,]*,\s+(?:with\s+)?(?:its\s+)?(?:principal\s+)?(?:place\s+of\s+business\s+at\s+)?([^,]+)'
        parties_matches = re.finditer(parties_pattern, text, re.IGNORECASE)
        
        parties = []
        for i, match in enumerate(parties_matches):
            try:
                party = {
                    "name": match.group(1).strip(),
                    "type": match.group(2).strip() if match.group(2) else None,
                    "jurisdiction": match.group(3).strip() if match.group(3) else None,
                    "address": match.group(4).strip() if match.group(4) else None
                }
                parties.append(party)
            except:
                continue
                
        details["parties"] = parties
        
        # Extract monetary values
        money_pattern = r'\$\s?(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)'
        money_matches = re.finditer(money_pattern, text)
        
        financial_terms = []
        for match in money_matches:
            # Get surrounding context (100 chars)
            start = max(0, match.start() - 50)
            end = min(len(text), match.end() + 50)
            context = text[start:end]
            
            financial_terms.append({
                "amount": match.group(0),
                "context": context
            })
            
        details["financial_terms"] = financial_terms
        
        return details
    
    def compare_sections(self, text1, text2, section_name):
        """
        Compare specific sections between two documents
        
        Parameters:
        - text1: First document text
        - text2: Second document text
        - section_name: Name of the section to compare (e.g., "confidentiality")
        
        Returns:
        - Dictionary with comparison results
        """
        # Pattern to find named sections
        section_pattern = r'(?:SECTION\s+\d+\.\s+' + section_name + r'|' + section_name + r'\s+\d+\.)(.*?)(?:SECTION|$)'
        
        # Find the sections in both documents
        section1_match = re.search(section_pattern, text1, re.IGNORECASE | re.DOTALL)
        section2_match = re.search(section_pattern, text2, re.IGNORECASE | re.DOTALL)
        
        section1 = section1_match.group(1).strip() if section1_match else None
        section2 = section2_match.group(1).strip() if section2_match else None
        
        return {
            "found_in_doc1": section1 is not None,
            "found_in_doc2": section2 is not None,
            "section1": section1,
            "section2": section2,
            "approximate_length1": len(section1) if section1 else 0,
            "approximate_length2": len(section2) if section2 else 0
        }
    
    def identify_clause_type(self, text):
        """
        Identify the type of legal clause from text
        
        Parameters:
        - text: Text of clause
        
        Returns:
        - Identified clause type and confidence
        """
        # Dictionary mapping clause types to keywords
        clause_keywords = {
            "confidentiality": ["confidential", "disclose", "non-disclosure", "proprietary", "secret"],
            "intellectual_property": ["intellectual property", "copyright", "patent", "trademark", "ownership", "license"],
            "termination": ["terminate", "termination", "cancellation", "expiration", "discontinue"],
            "payment": ["payment", "fee", "compensation", "invoice", "expense"],
            "liability": ["liability", "limitation", "indemnification", "indemnify", "warranty"],
            "governing_law": ["governing law", "jurisdiction", "arbitration", "dispute", "venue"]
        }
        
        # Convert to lowercase for case-insensitive matching
        text_lower = text.lower()
        
        # Count matches for each clause type
        matches = {}
        for clause_type, keywords in clause_keywords.items():
            count = sum(1 for keyword in keywords if keyword.lower() in text_lower)
            matches[clause_type] = count
        
        # Get the clause type with the most matches
        if not matches or max(matches.values()) == 0:
            return {"type": "unknown", "confidence": 0}
            
        best_match = max(matches.items(), key=lambda x: x[1])
        # Normalize confidence score (0-100)
        confidence = min(100, best_match[1] * 20)
        
        return {
            "type": best_match[0],
            "confidence": confidence
        }
    
    def generate_legal_summary(self, text):
        """
        Generate a structured summary of a legal document
        
        Parameters:
        - text: Document text
        
        Returns:
        - Dictionary with document summary
        """
        summary = {
            "document_type": self._determine_document_type(text),
            "key_sections": [],
            "parties": [],
            "dates": [],
            "financial_terms": [],
            "governing_law": None
        }
        
        # Extract parties
        contract_details = self.extract_contract_details(text)
        summary["parties"] = contract_details.get("parties", [])
        
        # Extract dates
        if "effective_date" in contract_details:
            summary["dates"].append({"type": "effective_date", "value": contract_details["effective_date"]})
        
        # Extract financial terms
        summary["financial_terms"] = contract_details.get("financial_terms", [])
        
        # Find key sections
        section_pattern = r'(?:SECTION|ARTICLE)\s+(\d+(?:\.\d+)?)\.\s+([^\n]+)'
        section_matches = re.finditer(section_pattern, text, re.IGNORECASE)
        
        for match in section_matches:
            section_num = match.group(1)
            section_title = match.group(2).strip()
            
            summary["key_sections"].append({
                "number": section_num,
                "title": section_title
            })
        
        # Find governing law
        gov_law_pattern = r'(?:governed by|governing law|subject to).{1,50}(?:laws of|law of)\s+([A-Za-z ]+)'
        gov_law_match = re.search(gov_law_pattern, text, re.IGNORECASE)
        
        if gov_law_match:
            summary["governing_law"] = gov_law_match.group(1).strip()
        
        return summary
    
    def _determine_document_type(self, text):
        """Helper method to determine document type"""
        # Simple heuristic based on keywords
        text_lower = text.lower()
        
        if "consulting agreement" in text_lower or "consulting services" in text_lower:
            return "consulting_agreement"
        elif "employment agreement" in text_lower:
            return "employment_agreement"
        elif "software license" in text_lower:
            return "license_agreement"
        elif "non-disclosure" in text_lower or "confidentiality agreement" in text_lower:
            return "nda"
        elif "purchase agreement" in text_lower or "asset purchase" in text_lower:
            return "purchase_agreement"
        elif "lease" in text_lower and ("property" in text_lower or "premises" in text_lower):
            return "lease_agreement"
        else:
            return "contract"