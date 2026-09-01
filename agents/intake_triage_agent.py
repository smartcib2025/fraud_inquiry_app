# CPPD Agent: Intake & Case Triage Agent (Agent 1)
from typing import Dict, Any, List
from base_agent import CPPDBaseAgent

class IntakeCaseTriageAgent(CPPDBaseAgent):
    def __init__(self, api_url: str = "http://localhost:8000"):
        super().__init__("IntakeCaseTriageAgent", api_url)

    def analyze_intake(self, complaint: Dict[str, Any]) -> Dict[str, Any]:
        """
        Assesses incoming citizen complaint, extracts initial claims and detects fraud typology.
        """
        title = complaint.get("title", "")
        raw_text = complaint.get("raw_statement", "")
        reporter = complaint.get("reporter_name", "Unknown")
        
        # Categorize typology
        typology = "Online Public Fraud (ฉ้อโกงประชาชน)" if "transfer" in raw_text.lower() or "โอน" in raw_text else "Consumer Protection Violation"
        urgency = "HIGH" if "1,250,000" in raw_text or "1.25M" in raw_text or "million" in raw_text.lower() else "MEDIUM"
        
        findings = [
            {"tag": "CLAIM", "text": f"Reporter {reporter} alleges fraud under context: {title}", "source_evidence_id": complaint.get("id"), "confidence": 0.95},
            {"tag": "INFERENCE", "text": f"Crime Typology classified as: {typology}", "source_evidence_id": None, "confidence": 0.88},
            {"tag": "REQUIRES_HUMAN_REVIEW", "text": f"Triage Priority {urgency}: Recommend officer verification and formal case registration.", "source_evidence_id": None, "confidence": 0.90}
        ]
        
        actions = [
            "Verify complainant national identity and authorization.",
            "Issue summons for transaction records from victim's sending bank.",
            "Promote complaint into active investigation workspace."
        ]
        
        summary = f"Intake complaint triaged with priority [{urgency}] under typology [{typology}]."
        return self.format_safe_output(complaint.get("case_id", "INTAKE-NEW"), summary, findings, actions, status="REQUIRES_HUMAN_REVIEW")
