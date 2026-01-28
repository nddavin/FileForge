import json
from typing import List, Dict, Any


class Sorter:
    """File sorting service with rule-based categorization"""

    def __init__(self):
        self.default_rules = [
            {
                "name": "Documents",
                "condition": {"extension": ["pdf", "docx", "txt"]},
                "category": "documents",
            },
            {
                "name": "Images",
                "condition": {"extension": ["jpg", "png", "gif"]},
                "category": "images",
            },
            {
                "name": "Videos",
                "condition": {"extension": ["mp4", "avi", "mov"]},
                "category": "videos",
            },
        ]

    def sort_file(self, file_info: Dict[str, Any], rules: List[Dict] = None) -> str:
        """Sort a file based on rules"""
        if rules is None:
            rules = self.default_rules

        for rule in rules:
            if self._matches_rule(file_info, rule):
                return rule["category"]

        return "misc"

    def _matches_rule(self, file_info: Dict[str, Any], rule: Dict) -> bool:
        """Check if file matches a sorting rule"""
        condition = rule.get("condition", {})

        for key, values in condition.items():
            if key in file_info:
                if callable(values):
                    # Handle callable conditions (like lambda functions)
                    if not values(file_info[key]):
                        return False
                elif isinstance(values, list):
                    if file_info[key] not in values:
                        return False
                elif file_info[key] != values:
                    return False

        return True

    def create_rule(self, name: str, condition: Dict, category: str) -> Dict:
        """Create a new sorting rule"""
        return {"name": name, "condition": condition, "category": category}
