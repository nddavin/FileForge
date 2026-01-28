import re
from typing import Dict, Any, List


class Extractor:
    """Data extraction service for various file types"""

    def __init__(self):
        self.patterns = {
            "email": r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",
            "phone": r"\b\d{3}[-.]?\d{3}[-.]?\d{4}\b",
            "ssn": r"\b\d{3}-\d{2}-\d{4}\b",
            "credit_card": r"\b\d{4}[- ]?\d{4}[- ]?\d{4}[- ]?\d{4}\b",
        }

    def extract_text(self, content: str) -> Dict[str, Any]:
        """Extract structured data from text content"""
        extracted = {
            "emails": self._extract_pattern(content, "email"),
            "phones": self._extract_pattern(content, "phone"),
            "ssns": self._extract_pattern(content, "ssn"),
            "credit_cards": self._extract_pattern(content, "credit_card"),
            "word_count": len(content.split()),
            "character_count": len(content),
        }

        return extracted

    def _extract_pattern(self, text: str, pattern_name: str) -> List[str]:
        """Extract matches for a specific pattern"""
        pattern = self.patterns.get(pattern_name)
        if not pattern:
            return []

        matches = re.findall(pattern, text)
        return list(set(matches))  # Remove duplicates

    def extract_metadata(self, file_info: Dict[str, Any]) -> Dict[str, Any]:
        """Extract metadata based on file type"""
        metadata = {"basic_info": file_info, "extracted_data": {}}

        # Type-specific extraction
        if file_info.get("type") == "document":
            metadata["extracted_data"] = self._extract_document_metadata(file_info)
        elif file_info.get("type") == "image":
            metadata["extracted_data"] = self._extract_image_metadata(file_info)

        return metadata

    def _extract_document_metadata(self, file_info: Dict) -> Dict[str, Any]:
        """Extract document-specific metadata"""
        return {
            "has_text": True,
            "estimated_reading_time": file_info.get("size", 0)
            // 1000,  # Rough estimate
            "language_detected": "en",
        }

    def _extract_image_metadata(self, file_info: Dict) -> Dict[str, Any]:
        """Extract image-specific metadata"""
        return {
            "resolution": f"{file_info.get('width', 0)}x{file_info.get('height', 0)}",
            "aspect_ratio": file_info.get("width", 1)
            / max(file_info.get("height", 1), 1),
        }
