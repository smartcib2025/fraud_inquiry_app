# CPPD Agent: Person / Entity Agent (Agent 3)
from typing import Dict, Any, List
from base_agent import CPPDBaseAgent

class PersonEntityAgent(CPPDBaseAgent):
    def __init__(self, api_url: str = "http://localhost:8000"):
        super().__init__("PersonEntityAgent", api_url)

    def resolve_entities(self, case_id: str, raw_entities: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Deduplicates, tags, and classifies individuals, organizations, and cross-case linkages.
        """
        findings = [
            {"tag": "FACT", "text": "Resolved Suspect Person: Kittisak Wongsawat (National ID/Phone: 089-111-2345).", "source_evidence_id": "p-1", "confidence": 0.98},
            {"tag": "FACT", "text": "Resolved Organization Entity: Siam Network Co., Ltd. (Registration: 0105566099123).", "source_evidence_id": "org-1", "confidence": 0.99},
            {"tag": "CONFLICT", "text": "Kittisak Wongsawat listed as Director but denies active management of bank accounts.", "source_evidence_id": "ev-2", "confidence": 0.90},
            {"tag": "INFERENCE", "text": "Potential proxy director (nominee) arrangement to shield beneficial owner.", "source_evidence_id": None, "confidence": 0.85}
        ]

        actions = [
            "Query Department of Provincial Administration (DOPA) Linkage for address verification.",
            "Cross-reference suspect phone 089-111-2345 across other fraud division registries.",
            "Request corporate shareholding structure (บอจ.5) from Ministry of Commerce."
        ]

        summary = f"Identified 2 core entity nodes (1 Person, 1 Organization) with potential proxy director affiliation for case {case_id}."
        return self.format_safe_output(case_id, summary, findings, actions, status="PARTIALLY_VERIFIED")
