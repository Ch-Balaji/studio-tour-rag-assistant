"""
Simple query enhancement for RAG system.
Handles common abbreviations and query expansion.
"""

from typing import List, Dict, Set
import re


class QueryEnhancer:
    """Simple query enhancer for general RAG domain"""
    
    def __init__(self):
        """Initialize with general expansions"""
        
        # Common abbreviations and terms (generic)
        self.abbreviations = {
            # Studio-related abbreviations
            "ss": "silverlight studios",
            "studio": "silverlight studios",
            # General abbreviations
            "faq": "frequently asked questions",
            "t&a": "tours and attractions",
        }
        
        # Common term expansions (for better retrieval)
        self.term_expansions = {
            "tour": ["studio tour", "backlot tour", "production tour"],
            "production": ["film production", "movie production", "filming"],
            "backlot": ["backlot sets", "outdoor sets", "permanent sets"],
            "stage": ["sound stage", "soundstage", "production stage"],
        }
    
    def enhance_query(self, query: str) -> str:
        """
        Enhance query with simple expansions.
        
        Args:
            query: Original user query
            
        Returns:
            Enhanced query string
        """
        # Keep original query and create lowercase version for matching
        original_query = query
        lower_query = query.lower()
        enhanced_parts = []
        
        # Work with a copy of the original query for modifications
        modified_query = original_query
        
        # Check for abbreviations first
        for abbr, full_form in self.abbreviations.items():
            # Use word boundary regex for better matching
            pattern = r'\b' + re.escape(abbr) + r'\b'
            if re.search(pattern, lower_query, re.IGNORECASE):
                # Replace abbreviation with full form, preserving case where possible
                modified_query = re.sub(pattern, full_form, modified_query, flags=re.IGNORECASE)
                lower_query = modified_query.lower()
        
        # Add the modified query (preserving original case)
        enhanced_parts.append(modified_query)
        
        # Check for term expansions
        for term, expansions in self.term_expansions.items():
            pattern = r'\b' + re.escape(term) + r'\b'
            if re.search(pattern, lower_query, re.IGNORECASE):
                # Add expansions that aren't already in the query
                for expansion in expansions:
                    if expansion.lower() not in lower_query:
                        enhanced_parts.append(expansion)
                        break  # Only add first expansion to keep it simple
        
        # Join unique parts with OR operator for retrieval
        # Keep original query first for better relevance
        enhanced_query = " OR ".join(enhanced_parts[:3])  # Limit to 3 variations max
        
        return enhanced_query
    
    def get_query_keywords(self, query: str) -> List[str]:
        """
        Extract important keywords from query for filtering.
        
        Args:
            query: User query
            
        Returns:
            List of important keywords
        """
        # Convert to lowercase
        lower_query = query.lower()
        
        # Extract important domain-specific terms
        keywords = []
        
        # Studio-related terms
        studio_terms = [
            "silverlight studios", "studio tour", "backlot", "sound stage",
            "production", "filming", "mystwood academy", "maximum velocity"
        ]
        
        for term in studio_terms:
            if term in lower_query:
                keywords.append(term)
        
        # Tour-related terms
        tour_terms = [
            "tour", "visitor", "backlot", "stage", "production", "facilities"
        ]
        
        for term in tour_terms:
            if term in lower_query and term not in keywords:
                keywords.append(term)
        
        return keywords
