# contract_risk_analyzer.py
# Specialized module for identifying risks in legal contracts

import re
from collections import defaultdict

class ContractRiskAnalyzer:
    def __init__(self):
        """Initialize the contract risk analyzer"""
        # Risk categories and their associated keywords/patterns
        self.risk_patterns = {
            "ambiguity": [
                "may", "might", "could", "reasonable efforts", "commercially reasonable",
                "best efforts", "good faith", "timely manner", "promptly", "substantial",
                "material", "adequate", "appropriate", "suitable", "satisfactory"
            ],
            "one_sided_terms": [
                "sole discretion", "unilateral", "unilaterally", "at any time", 
                "without notice", "without cause", "without liability", "no liability",
                "shall not be liable", "in its discretion", "may determine"
            ],
            "liability_issues": [
                "unlimited liability", "sole risk", "indemnify.*all", "indemnify.*any",
                "defend and hold harmless", "to the fullest extent", "unlimited indemnification",
                "including but not limited to", "for any reason"
            ],
            "missing_provisions": [
                # Patterns for checking missing provisions will be implemented
                # in the find_missing_provisions method
            ],
            "termination_risks": [
                "immediate termination", "without notice", "terminate immediately",
                "at its convenience", "without cause", "for any reason", "change of control"
            ],
            "confidentiality_risks": [
                "perpetual confidentiality", "unlimited confidentiality", "forever",
                "no time limit", "without restriction", "sole property"
            ],
            "ip_risks": [
                "assign all rights", "assign all intellectual property", "work for hire",
                "exclusively own", "transfer all", "irrevocably assign"
            ]
        }
        
        # Standard provisions that should be present in most contracts
        self.standard_provisions = [
            "termination", "confidentiality", "intellectual property", 
            "indemnification", "governing law", "dispute resolution",
            "force majeure", "assignment", "notices", "entire agreement"
        ]
    
    def analyze_contract(self, text):
        """
        Perform comprehensive risk analysis on contract text
        
        Parameters:
        - text: The contract text
        
        Returns:
        - Dictionary with risk analysis results
        """
        analysis = {
            "risk_score": 0,  # Overall score out of 100
            "risk_categories": {},
            "ambiguous_clauses": [],
            "one_sided_terms": [],
            "liability_issues": [],
            "missing_provisions": [],
            "other_issues": []
        }
        
        # Check for each risk category
        for category, patterns in self.risk_patterns.items():
            if category == "missing_provisions":
                continue  # Handled separately
                
            matches = []
            category_score = 0
            
            for pattern in patterns:
                # For regex patterns
                if any(c in pattern for c in ".*+?()[]{}|^$"):
                    regex_matches = re.finditer(pattern, text, re.IGNORECASE)
                    for match in regex_matches:
                        # Get surrounding context (100 chars)
                        start = max(0, match.start() - 50)
                        end = min(len(text), match.end() + 50)
                        context = text[start:end]
                        matches.append({
                            "term": match.group(0),
                            "context": context
                        })
                        category_score += 1
                # For simple keyword matches
                else:
                    # Use word boundaries to match whole words
                    keyword_pattern = r'\b' + re.escape(pattern) + r'\b'
                    keyword_matches = re.finditer(keyword_pattern, text, re.IGNORECASE)
                    for match in keyword_matches:
                        # Get surrounding context (100 chars)
                        start = max(0, match.start() - 50)
                        end = min(len(text), match.end() + 50)
                        context = text[start:end]
                        matches.append({
                            "term": match.group(0),
                            "context": context
                        })
                        category_score += 1
            
            # Cap category score at 100
            category_score = min(100, category_score * 10)
            
            # Add to analysis
            if category == "ambiguity":
                analysis["ambiguous_clauses"] = matches
            elif category == "one_sided_terms":
                analysis["one_sided_terms"] = matches
            elif category == "liability_issues":
                analysis["liability_issues"] = matches
            else:
                analysis["other_issues"].extend(matches)
            
            analysis["risk_categories"][category] = {
                "score": category_score,
                "matches": len(matches)
            }
        
        # Check for missing provisions
        missing = self.find_missing_provisions(text)
        analysis["missing_provisions"] = missing
        
        # Calculate overall risk score (weighted average)
        if analysis["risk_categories"]:
            total_score = sum(cat["score"] for cat in analysis["risk_categories"].values())
            analysis["risk_score"] = min(100, total_score / len(analysis["risk_categories"]))
            
            # Increase risk score for missing provisions
            if missing:
                analysis["risk_score"] += min(20, len(missing) * 5)
                analysis["risk_score"] = min(100, analysis["risk_score"])
        
        return analysis
    
    def find_missing_provisions(self, text):
        """
        Check for standard provisions that are missing
        
        Parameters:
        - text: The contract text
        
        Returns:
        - List of missing provisions
        """
        missing = []
        text_lower = text.lower()
        
        for provision in self.standard_provisions:
            provision_lower = provision.lower()
            provision_pattern = r'\b' + re.escape(provision_lower) + r'\b'
            
            # Check for synonyms/alternatives as well
            synonyms = self._get_provision_synonyms(provision_lower)
            found = False
            
            # Check for the main term
            if re.search(provision_pattern, text_lower):
                found = True
            else:
                # Check for synonyms
                for synonym in synonyms:
                    synonym_pattern = r'\b' + re.escape(synonym) + r'\b'
                    if re.search(synonym_pattern, text_lower):
                        found = True
                        break
            
            if not found:
                missing.append(provision)
        
        return missing
    
    def _get_provision_synonyms(self, provision):
        """Helper method to get synonyms/alternatives for provisions"""
        synonyms = {
            "termination": ["cancellation", "expiration", "discontinuance"],
            "confidentiality": ["non-disclosure", "private information", "proprietary information"],
            "intellectual property": ["ip rights", "copyrights", "patents", "trademarks"],
            "indemnification": ["indemnity", "hold harmless", "defend"],
            "governing law": ["applicable law", "jurisdiction", "choice of law"],
            "dispute resolution": ["arbitration", "mediation", "settlement of disputes"],
            "force majeure": ["act of god", "unforeseen circumstances", "beyond control"],
            "assignment": ["transfer of rights", "successors", "assigns"],
            "notices": ["notification", "communication"],
            "entire agreement": ["complete agreement", "integration", "merger clause"]
        }
        
        return synonyms.get(provision, [])
    
    def suggest_improvements(self, analysis):
        """
        Generate improvement suggestions based on risk analysis
        
        Parameters:
        - analysis: The risk analysis dictionary
        
        Returns:
        - Dictionary with suggestions
        """
        suggestions = {
            "general_advice": [],
            "specific_suggestions": []
        }
        
        # High-level advice based on risk score
        if analysis["risk_score"] < 30:
            suggestions["general_advice"].append(
                "This contract appears to have a relatively low risk profile, but consider reviewing the specific issues identified.")
        elif analysis["risk_score"] < 60:
            suggestions["general_advice"].append(
                "This contract has a moderate risk profile. Address the identified issues, especially any missing provisions and ambiguous terms.")
        else:
            suggestions["general_advice"].append(
                "This contract has a high risk profile. Consider comprehensive revision to address the numerous issues identified.")
        
        # Specific suggestions based on findings
        if analysis["ambiguous_clauses"]:
            suggestions["general_advice"].append(
                "Replace ambiguous terms with specific, measurable obligations and deadlines.")
            
            # Add specific suggestions for top 3 ambiguous terms
            for item in analysis["ambiguous_clauses"][:3]:
                term = item["term"]
                suggestions["specific_suggestions"].append(
                    f"Replace ambiguous term '{term}' with more specific language defining exact obligations or timelines.")
        
        if analysis["one_sided_terms"]:
            suggestions["general_advice"].append(
                "Review and negotiate one-sided terms to ensure more balanced risk allocation.")
        
        if analysis["liability_issues"]:
            suggestions["general_advice"].append(
                "Address liability concerns, especially any provisions for unlimited liability or overly broad indemnification.")
        
        # Missing provisions
        for provision in analysis["missing_provisions"]:
            suggestions["specific_suggestions"].append(
                f"Add a {provision} provision to address this important area not currently covered in the contract.")
        
        return suggestions