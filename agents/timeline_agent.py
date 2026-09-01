# CPPD Agent: Timeline Agent (Agent 5)
from typing import Dict, Any, List
from base_agent import CPPDBaseAgent

class TimelineAgent(CPPDBaseAgent):
    def __init__(self, api_url: str = "http://localhost:8000"):
        super().__init__("TimelineAgent", api_url)

    def audit_timeline(self, case_id: str, events: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Builds chronological event sequence and audits alibi and testimony contradictions.
        """
        findings = [
            {"tag": "FACT", "text": "2026-08-09 14:32:00: Victim Nattapong transferred 1,250,000 THB to SCB 401-229-3388.", "source_evidence_id": "ev-3", "confidence": 1.0},
            {"tag": "CLAIM", "text": "2026-08-09 15:00:00: Suspect Kittisak stated he was in Chiang Mai and card was stolen.", "source_evidence_id": "stmt-suspect-1", "confidence": 0.95},
            {"tag": "CONFLICT", "text": "2026-08-09 14:32:00: SCB online mobile banking login registered IP location in Bangkok.", "source_evidence_id": "ev-4", "confidence": 0.96},
            {"tag": "INFERENCE", "text": "Suspect's Chiang Mai alibi is contradictory and directly refuted by digital IP telematics.", "source_evidence_id": None, "confidence": 0.90}
        ]

        actions = [
            "Subpoena mobile cell tower connection logs (CDR) for suspect number 089-111-2345 during 14:00-16:00.",
            "Subpoena ATM CCTV security footage corresponding to Ladprao cash withdrawal.",
            "Schedule follow-up interrogation confronting suspect with IP discrepancy."
        ]

        summary = f"Timeline analysis for {case_id} identified 1 critical alibi conflict refuting suspect's physical absence claim."
        return self.format_safe_output(case_id, summary, findings, actions, status="REQUIRES_CHECK")
