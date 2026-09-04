"""
QA Decision Management Module
Provides structures and workflows for QA engineers to review AI recommendations,
record human-in-the-loop decisions, overrides, and audit trails.
"""

from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Optional, Dict, Any


VALID_DECISIONS = {
    # Core QA Engineer Decisions
    "PASS",            # QA Engineer confirms pass
    "HOLD",            # Placed on engineering hold / MRB review / extended burn-in
    "FAIL",            # QA Engineer confirms component rejection
    # Extended QA Engineer Action Codes
    "APPROVE",         # Agree with recommendation / Pass
    "REJECT",          # Confirm component rejection
    "OVERRIDE_PASS",   # Engineer manual override to Pass
    "OVERRIDE_REJECT", # Engineer manual override to Reject
    "REQUEST_RETEST",  # Send component back for probe/screening retest
}


@dataclass
class QADecision:
    component_id: str
    decision: str
    engineer_id: str
    notes: str = ""
    timestamp: Optional[str] = None

    def __post_init__(self):
        if self.decision not in VALID_DECISIONS:
            raise ValueError(
                f"Invalid decision '{self.decision}'. Must be one of {VALID_DECISIONS}"
            )
        if self.timestamp is None:
            self.timestamp = datetime.now().isoformat()

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def create_decision(
    component_id: str,
    decision: str,
    engineer_id: str,
    notes: str = "",
) -> QADecision:
    """Helper factory for creating a verified QA Decision record."""
    return QADecision(
        component_id=component_id,
        decision=decision,
        engineer_id=engineer_id,
        notes=notes,
    )
