# CPPD Agent: Investigation Planning Agent (Agent 2)
from typing import Dict, Any, List
from base_agent import CPPDBaseAgent

class InvestigationPlanningAgent(CPPDBaseAgent):
    def __init__(self, api_url: str = "http://localhost:8000"):
        super().__init__("InvestigationPlanningAgent", api_url)

    def generate_investigation_plan(self, case_id: str, case_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Formulates a comprehensive, evidence-driven investigation checklist & action plan.
        """
        title = case_data.get("title", "Active Case")
        findings = [
            {"tag": "FACT", "text": f"Case {case_id} initialized with title: {title}", "source_evidence_id": case_id, "confidence": 1.0},
            {"tag": "EVIDENCE_GAP", "text": "Bank KYC documentation for beneficiary account not yet secured.", "source_evidence_id": None, "confidence": 0.90},
            {"tag": "INFERENCE", "text": "Suspect network likely utilizing proxy mule accounts to layer proceeds.", "source_evidence_id": None, "confidence": 0.85},
            {"tag": "REQUIRES_HUMAN_REVIEW", "text": "Proposed 4-stage investigation action plan requires supervisory sign-off.", "source_evidence_id": None, "confidence": 0.95}
        ]

        actions = [
            "Stage 1: Coordinate with Anti-Money Laundering Office (AMLO) / Bank to freeze target account 401-229-3388.",
            "Stage 2: Issue Section 132 Criminal Procedure Code inquiry warrant to telecommunication provider for MSISDN 089-111-2345.",
            "Stage 3: Subpoena Department of Business Development (DBD) corporate filings for Siam Network Co., Ltd.",
            "Stage 4: Prepare witness interrogation protocol for primary victim."
        ]

        summary = f"Investigation Plan for {case_id} formulated across 4 operational stages targeting victim evidence, digital breadcrumbs, and financial freeze."
        return self.format_safe_output(case_id, summary, findings, actions, status="REQUIRES_HUMAN_REVIEW")
