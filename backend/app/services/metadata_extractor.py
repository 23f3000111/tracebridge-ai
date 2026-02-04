"""
TraceBridge AI - Metadata Extractor Service
Auto-detects standards, requirement IDs, test IDs, and risk IDs from text.
"""

import re
from typing import List, Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


# Standard patterns to detect in text
STANDARD_PATTERNS = {
    "ISO 10993": r"\bISO\s*10993(?:-\d+)?\b",
    "IEC 62304": r"\bIEC\s*62304\b",
    "ISO 14971": r"\bISO\s*14971\b",
    "IEC 60601": r"\bIEC\s*60601(?:-\d+(?:-\d+)?)?\b",
    "ISO 13485": r"\bISO\s*13485\b",
    "IEC 62366": r"\bIEC\s*62366(?:-\d+)?\b",
    "FDA 21 CFR": r"\b21\s*CFR\s*\d+(?:\.\d+)?\b",
    "HIPAA": r"\bHIPAA\b",
    "GDPR": r"\bGDPR\b",
}

# ID patterns to detect
ID_PATTERNS = {
    "requirement": [
        r"\bREQ[-_]?\d+(?:\.\d+)*\b",
        r"\bSRS[-_]?\d+(?:\.\d+)*\b",
        r"\bSYS[-_]?\d+(?:\.\d+)*\b",
        r"\bUR[-_]?\d+\b",
        r"\bFR[-_]?\d+\b",
    ],
    "test_case": [
        r"\bTC[-_]?\d+(?:\.\d+)*\b",
        r"\bTEST[-_]?\d+(?:\.\d+)*\b",
        r"\bVT[-_]?\d+\b",
        r"\bSVT[-_]?\d+\b",
        r"\bUT[-_]?\d+\b",
    ],
    "risk": [
        r"\bRISK[-_]?\d+(?:\.\d+)*\b",
        r"\bHAZ[-_]?\d+(?:\.\d+)*\b",
        r"\bFMEA[-_]?\d+\b",
        r"\bRM[-_]?\d+\b",
    ],
}


def detect_standards(text: str) -> List[str]:
    """
    Detect regulatory standards referenced in text.
    
    Args:
        text: Text to analyze
        
    Returns:
        List of detected standard names
    """
    if not text:
        return []
    
    detected = set()
    text_upper = text.upper()
    
    for standard_name, pattern in STANDARD_PATTERNS.items():
        if re.search(pattern, text, re.IGNORECASE):
            detected.add(standard_name)
    
    return sorted(list(detected))


def detect_requirement_ids(text: str) -> List[str]:
    """
    Detect requirement IDs in text.
    
    Args:
        text: Text to analyze
        
    Returns:
        List of detected requirement IDs
    """
    if not text:
        return []
    
    detected = set()
    
    for pattern in ID_PATTERNS["requirement"]:
        matches = re.findall(pattern, text, re.IGNORECASE)
        detected.update(match.upper() for match in matches)
    
    return sorted(list(detected))[:10]  # Limit to 10 IDs per chunk


def detect_test_case_ids(text: str) -> List[str]:
    """
    Detect test case IDs in text.
    
    Args:
        text: Text to analyze
        
    Returns:
        List of detected test case IDs
    """
    if not text:
        return []
    
    detected = set()
    
    for pattern in ID_PATTERNS["test_case"]:
        matches = re.findall(pattern, text, re.IGNORECASE)
        detected.update(match.upper() for match in matches)
    
    return sorted(list(detected))[:10]


def detect_risk_ids(text: str) -> List[str]:
    """
    Detect risk/hazard IDs in text.
    
    Args:
        text: Text to analyze
        
    Returns:
        List of detected risk IDs
    """
    if not text:
        return []
    
    detected = set()
    
    for pattern in ID_PATTERNS["risk"]:
        matches = re.findall(pattern, text, re.IGNORECASE)
        detected.update(match.upper() for match in matches)
    
    return sorted(list(detected))[:10]


def detect_section_heading(text: str) -> Optional[str]:
    """
    Try to detect section heading from first line of text.
    
    Args:
        text: Text to analyze
        
    Returns:
        Detected section heading or None
    """
    if not text:
        return None
    
    # Get first non-empty line
    lines = text.strip().split('\n')
    first_line = lines[0].strip() if lines else ""
    
    # Check if it looks like a heading (short, possibly numbered)
    if len(first_line) < 100:
        # Check for numbered heading patterns
        heading_patterns = [
            r"^\d+(?:\.\d+)*\s+[A-Z]",  # "1.2.3 Introduction"
            r"^[A-Z][A-Z\s]+$",  # "INTRODUCTION"
            r"^(?:Section|Chapter|Part)\s+\d+",  # "Section 1"
        ]
        
        for pattern in heading_patterns:
            if re.match(pattern, first_line):
                return first_line[:80]
    
    return None


def extract_all_metadata(text: str) -> Dict[str, Any]:
    """
    Extract all detectable metadata from text.
    
    Args:
        text: Text to analyze
        
    Returns:
        Dictionary with all detected metadata
    """
    return {
        "standards_referenced": detect_standards(text),
        "requirement_ids": detect_requirement_ids(text),
        "test_case_ids": detect_test_case_ids(text),
        "risk_ids": detect_risk_ids(text),
        "section_heading": detect_section_heading(text),
    }


def aggregate_standards_from_chunks(chunks_metadata: List[Dict[str, Any]]) -> List[str]:
    """
    Aggregate all unique standards from multiple chunks.
    
    Args:
        chunks_metadata: List of chunk metadata dictionaries
        
    Returns:
        Unique list of all standards found
    """
    all_standards = set()
    
    for metadata in chunks_metadata:
        standards = metadata.get("standards_referenced", [])
        if isinstance(standards, list):
            all_standards.update(standards)
    
    return sorted(list(all_standards))
