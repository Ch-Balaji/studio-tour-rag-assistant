"""
Metadata extraction for documents.
Extracts general metadata like chapters, entities, and document structure.
"""

import re
from typing import Dict, List, Set, Any
from pathlib import Path


class MetadataExtractor:
    """Extract general metadata from text"""
    
    def __init__(self):
        """Initialize with general entities"""
        
        # Studio-related entities (for Silverlight Studios)
        self.studio_entities = {
            "Silverlight Studios", "Silverlight", "Studio",
            "Mystwood Academy", "Alexis Ravencroft", "Lord Shadowmere",
            "Maximum Velocity", "Michael Bay Jr", "Thomas Morrison"
        }
        
        # Locations (studio-related)
        self.locations = {
            "Silverlight Studios", "New York Street", "Western Town",
            "Silverlight Gulch", "Suburban Neighborhood", "Evergreen Heights",
            "Henderson House", "Golden Nugget Saloon", "Sheriff's Office",
            "Sound Stage", "Backlot", "Visitor Center"
        }
        
        # Production-related terms
        self.production_terms = {
            "Production", "Filming", "Pre-production", "Post-production",
            "Director", "Producer", "Screenplay", "Script",
            "Visual Effects", "Practical Effects", "Stunt", "Choreography"
        }
        
        # Chapter patterns
        self.chapter_patterns = [
            r"Chapter\s+(\d+)",
            r"CHAPTER\s+(\d+)",
            r"Chapter\s+([A-Za-z]+):",  # For named chapters
            r"^([A-Z][A-Z\s]+)$"  # All caps lines that might be chapter titles
        ]
    
    def extract_document_type(self, filename: str) -> str:
        """
        Extract document type from filename.
        
        Args:
            filename: Name of the file
            
        Returns:
            Document type or empty string if not found
        """
        filename_lower = filename.lower()
        
        # Check for document type keywords
        if "faq" in filename_lower:
            return "faq"
        elif "tour" in filename_lower:
            return "tour"
        elif "production" in filename_lower:
            return "production"
        elif "backlot" in filename_lower:
            return "backlot"
        elif "stage" in filename_lower or "facilities" in filename_lower:
            return "facilities"
        elif "operations" in filename_lower:
            return "operations"
        elif "techniques" in filename_lower:
            return "techniques"
        
        return ""
    
    def extract_chapter(self, text: str) -> str:
        """
        Extract chapter information from text.
        
        Args:
            text: Text chunk
            
        Returns:
            Chapter identifier or empty string
        """
        # Try each chapter pattern
        for pattern in self.chapter_patterns:
            match = re.search(pattern, text[:200])  # Check beginning of text
            if match:
                return match.group(1)
        
        return ""
    
    def extract_entities(self, text: str) -> List[str]:
        """
        Extract mentioned entities (characters, productions, etc.) from text.
        
        Args:
            text: Text chunk
            
        Returns:
            List of unique entities found
        """
        found_entities = set()
        text_lower = text.lower()
        
        for entity in self.studio_entities:
            # Case insensitive search with word boundaries
            pattern = r'\b' + re.escape(entity.lower()) + r'\b'
            if re.search(pattern, text_lower):
                found_entities.add(entity)
        
        return sorted(list(found_entities))
    
    def extract_locations(self, text: str) -> List[str]:
        """
        Extract mentioned locations from text.
        
        Args:
            text: Text chunk
            
        Returns:
            List of unique locations found
        """
        found_locations = set()
        
        for location in self.locations:
            # Case insensitive search
            if location.lower() in text.lower():
                found_locations.add(location)
        
        return sorted(list(found_locations))
    
    def extract_production_terms(self, text: str) -> List[str]:
        """
        Extract mentioned production-related terms from text.
        
        Args:
            text: Text chunk
            
        Returns:
            List of unique production terms found
        """
        found_terms = set()
        text_lower = text.lower()
        
        for term in self.production_terms:
            if term.lower() in text_lower:
                found_terms.add(term)
        
        return sorted(list(found_terms))
    
    def extract_all_metadata(self, text: str, filename: str = "") -> Dict[str, Any]:
        """
        Extract all metadata from text chunk.
        
        Args:
            text: Text chunk
            filename: Source filename
            
        Returns:
            Dictionary containing all extracted metadata
        """
        metadata = {
            "document_type": self.extract_document_type(filename),
            "chapter": self.extract_chapter(text),
            "entities": self.extract_entities(text),
            "locations": self.extract_locations(text),
            "production_terms": self.extract_production_terms(text),
            "has_dialogue": self._has_dialogue(text),
            "text_length": len(text)
        }
        
        return metadata
    
    def _has_dialogue(self, text: str) -> bool:
        """Check if text contains dialogue"""
        # Simple check for quotation marks indicating dialogue
        return '"' in text or "'" in text or """ in text or """ in text
