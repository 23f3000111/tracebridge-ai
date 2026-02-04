"""
TraceBridge AI - Gap Analysis Service
Generates structured gap reports comparing FDA requirements vs user evidence.
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

from app.config import settings
from app.models import GapItem, Citation
from app.services.vector_store import query_chunks
from app.services.llm import generate_grounded_answer, extract_citations

logger = logging.getLogger(__name__)


# FDA requirement templates by focus area
FDA_REQUIREMENTS = {
    "V&V": [
        {
            "area": "Software Development",
            "requirements": [
                "Evidence of software development lifecycle per IEC 62304",
                "Software verification test results with traceability to requirements",
                "Unit testing documentation with coverage metrics",
                "Integration testing documentation",
                "System testing documentation"
            ]
        },
        {
            "area": "Requirements Traceability", 
            "requirements": [
                "Traceability matrix linking requirements to design to tests",
                "Verification that all requirements have associated tests",
                "Risk-based test coverage justification"
            ]
        },
        {
            "area": "Risk Management",
            "requirements": [
                "Risk management file per ISO 14971",
                "Hazard analysis documentation",
                "Risk control verification evidence",
                "Residual risk evaluation"
            ]
        }
    ],
    "Biocomp": [
        {
            "area": "Biological Evaluation",
            "requirements": [
                "Biological evaluation plan per ISO 10993-1",
                "Material characterization data",
                "Biocompatibility endpoint justification"
            ]
        },
        {
            "area": "Testing",
            "requirements": [
                "Cytotoxicity testing (ISO 10993-5)",
                "Sensitization testing (ISO 10993-10)",
                "Irritation testing (ISO 10993-10 or 23)",
                "Test reports with pass/fail conclusions"
            ]
        }
    ],
    "Software": [
        {
            "area": "Software Documentation",
            "requirements": [
                "Software Requirements Specification (SRS)",
                "Software Design Specification",
                "Software Development Plan",
                "Software level of concern determination"
            ]
        },
        {
            "area": "Cybersecurity",
            "requirements": [
                "Cybersecurity risk assessment",
                "Threat modeling documentation",
                "Security controls documentation",
                "Vulnerability testing results"
            ]
        }
    ],
    "Risk": [
        {
            "area": "Risk Management Process",
            "requirements": [
                "Risk management plan",
                "Risk analysis (FMEA, FTA, or equivalent)",
                "Risk evaluation with severity/probability",
                "Risk control measures"
            ]
        },
        {
            "area": "Risk Verification",
            "requirements": [
                "Verification of risk control effectiveness",
                "Production and post-production monitoring plan",
                "Benefit-risk analysis"
            ]
        }
    ],
    "General": [
        {
            "area": "Device Description",
            "requirements": [
                "Intended use statement",
                "Device specifications",
                "Operating principles",
                "Predicate device comparison"
            ]
        }
    ]
}

# Severity mapping based on requirement importance
SEVERITY_MAPPING = {
    "critical": ["risk management", "safety", "harm", "hazard", "iso 14971"],
    "high": ["verification", "validation", "testing", "iec 62304", "traceability"],
    "medium": ["documentation", "plan", "specification", "design"],
    "low": ["format", "template", "labeling"]
}

# Timeline estimates (rules-based)
TIMELINE_ESTIMATES = {
    "critical": "2-4 weeks",
    "high": "1-2 weeks", 
    "medium": "3-5 days",
    "low": "1-2 days"
}

# Cost estimates (rules-based placeholders)
COST_ESTIMATES = {
    "critical": "$5,000 - $15,000 (estimate)",
    "high": "$2,000 - $5,000 (estimate)",
    "medium": "$500 - $2,000 (estimate)",
    "low": "$200 - $500 (estimate)"
}


def determine_severity(requirement: str) -> str:
    """Determine severity based on requirement keywords."""
    req_lower = requirement.lower()
    
    for severity, keywords in SEVERITY_MAPPING.items():
        if any(kw in req_lower for kw in keywords):
            return severity
    
    return "medium"


def generate_remediation_steps(requirement: str, severity: str) -> List[str]:
    """Generate remediation steps based on requirement."""
    req_lower = requirement.lower()
    
    steps = []
    
    if "test" in req_lower:
        steps.extend([
            "Review existing test documentation",
            "Create or update test protocol",
            "Execute required tests",
            "Document results with pass/fail conclusions"
        ])
    elif "traceability" in req_lower:
        steps.extend([
            "Create requirements traceability matrix",
            "Link requirements to design elements",
            "Link design elements to verification activities",
            "Verify complete coverage"
        ])
    elif "risk" in req_lower:
        steps.extend([
            "Review risk management file",
            "Perform hazard analysis if missing",
            "Document risk controls",
            "Verify risk control effectiveness"
        ])
    elif "plan" in req_lower or "documentation" in req_lower:
        steps.extend([
            "Review FDA guidance for document requirements",
            "Create document outline",
            "Complete required sections",
            "Review and approve"
        ])
    else:
        steps.extend([
            f"Review FDA requirements for: {requirement}",
            "Assess current documentation gaps",
            "Create or update required documentation",
            "Obtain appropriate review and approval"
        ])
    
    return steps


async def generate_gap_report(
    device_name: str,
    focus_area: str,
    doc_ids: List[str] = None
) -> List[GapItem]:
    """
    Generate a gap report for a device.
    
    Args:
        device_name: Name of the device
        focus_area: V&V, Biocomp, Software, Risk, or General
        doc_ids: Optional list of doc_ids to search
        
    Returns:
        List of GapItem objects
    """
    gaps = []
    
    # Get requirements for focus area
    area_requirements = FDA_REQUIREMENTS.get(focus_area, FDA_REQUIREMENTS["General"])
    
    for area_group in area_requirements:
        area_name = area_group["area"]
        
        for requirement in area_group["requirements"]:
            # Search for evidence
            query = f"{requirement} for {device_name}"
            
            # Build filter
            chunks = query_chunks(
                query=query,
                device_name=device_name if device_name else None,
                top_k=3
            )
            
            # Filter by doc_ids if specified
            if doc_ids:
                chunks = [c for c in chunks if c.get("metadata", {}).get("doc_id") in doc_ids]
            
            # Determine if gap exists
            has_evidence = len(chunks) > 0 and chunks[0].get("distance", 1) < 0.5
            
            if not has_evidence:
                severity = determine_severity(requirement)
                
                # Generate citations from any partial evidence
                fda_citations = []  # Would come from FDA guidance docs if indexed
                user_citations = extract_citations(chunks[:2]) if chunks else []
                
                gap = GapItem(
                    gap_title=f"Missing: {requirement}",
                    missing_requirement=f"{area_name}: {requirement}",
                    severity=severity,
                    fda_requirement_citations=fda_citations,
                    user_evidence_citations=user_citations,
                    remediation_steps=generate_remediation_steps(requirement, severity),
                    estimated_timeline=TIMELINE_ESTIMATES[severity],
                    estimated_cost=COST_ESTIMATES[severity]
                )
                
                gaps.append(gap)
    
    # Sort by severity
    severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
    gaps.sort(key=lambda g: severity_order.get(g.severity, 2))
    
    return gaps
