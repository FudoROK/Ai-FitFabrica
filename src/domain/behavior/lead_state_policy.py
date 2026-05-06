from __future__ import annotations

from ..models import Lead


INITIAL_STAGE = "cold"
INITIAL_STATUS = "cold"


def apply_initial_lead_state(lead: Lead) -> Lead:
    if not lead.stage:
        lead.stage = INITIAL_STAGE
    if not lead.status:
        lead.status = INITIAL_STATUS
    return lead
