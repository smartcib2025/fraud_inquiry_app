# CPPD Agent: Unified Case Orchestrator (12 Modular Agents Router)
import sys
import os
import json
from typing import Dict, Any, Optional

# Add local path to import sub-agents
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from intake_triage_agent import IntakeCaseTriageAgent
from investigation_planning_agent import InvestigationPlanningAgent
from person_entity_agent import PersonEntityAgent
from evidence_analysis_agent import EvidenceAnalysisAgent
from timeline_agent import TimelineAgent
from digital_evidence_agent import DigitalEvidenceAgent
from financial_transaction_agent import FinancialTransactionAgent
from legal_mapping_agent import LegalMappingAgent
from statement_interview_agent import StatementInterviewAgent
from document_drafting_agent import DocumentDraftingAgent
from investigation_report_agent import InvestigationReportAgent
from consistency_gap_agent import ConsistencyGapReviewAgent

class CPPDCaseOrchestrator:
    def __init__(self, api_url: str = "http://localhost:8000"):
        self.api_url = api_url
        self.agents = {
            "intake_triage": IntakeCaseTriageAgent(api_url),
            "planning": InvestigationPlanningAgent(api_url),
            "entity": PersonEntityAgent(api_url),
            "evidence": EvidenceAnalysisAgent(api_url),
            "timeline": TimelineAgent(api_url),
            "digital": DigitalEvidenceAgent(api_url),
            "financial": FinancialTransactionAgent(api_url),
            "legal": LegalMappingAgent(api_url),
            "interview": StatementInterviewAgent(api_url),
            "document": DocumentDraftingAgent(api_url),
            "report": InvestigationReportAgent(api_url),
            "consistency_gap": ConsistencyGapReviewAgent(api_url)
        }

    def run_agent_workflow(self, case_id: str, request_goal: str, request_user: str, payload: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Main orchestration loop:
        1. Validates requesting user permissions (RBAC check).
        2. Routes goal dynamically to the optimal modular agent among the 12 specialized agents.
        3. Returns standardized FACT/CLAIM/INFERENCE tagged output.
        """
        print(f"[Orchestrator Agent] Invoked for case: {case_id} by user: {request_user} with goal: {request_goal}")
        meta = payload or {}

        # Access check simulation
        if request_user == "somchai.i@cppd.go.th" and case_id == "CASE-112":
            return {"status": "error", "message": "Permission Denied: Investigator is not assigned to this case."}

        goal = request_goal.lower()

        if "interview" in goal or "question" in goal or "สอบปากคำ" in goal:
            agent = self.agents["interview"]
            target_role = meta.get("target_role", "suspect")
            target_name = meta.get("target_name", "Kittisak Wongsawat")
            result = agent.generate_interview_questions(case_id, target_role, target_name)
            agent_name = "StatementInterviewAgent"

        elif "document" in goal or "draft" in goal or "warrant" in goal or "หมาย" in goal or "คำร้อง" in goal:
            agent = self.agents["document"]
            doc_type = meta.get("doc_type", "SUMMONS_WARRANT")
            result = agent.draft_document(case_id, doc_type, meta)
            agent_name = "DocumentDraftingAgent"

        elif "financial" in goal or "transaction" in goal or "structuring" in goal:
            agent = self.agents["financial"]
            result = agent.analyze_transactions(case_id, meta.get("transactions", []))
            agent_name = "FinancialTransactionAgent"

        elif "planning" in goal or "plan" in goal or "task" in goal:
            agent = self.agents["planning"]
            result = agent.generate_investigation_plan(case_id, meta)
            agent_name = "InvestigationPlanningAgent"

        elif "digital" in goal or "chat" in goal or "ip" in goal:
            agent = self.agents["digital"]
            result = agent.analyze_digital_artifacts(case_id, meta.get("communications", []))
            agent_name = "DigitalEvidenceAgent"

        elif "legal" in goal or "law" in goal or "section" in goal or "มาตรา" in goal:
            agent = self.agents["legal"]
            result = agent.evaluate_legal_elements(case_id, meta.get("facts", []))
            agent_name = "LegalMappingAgent"

        elif "gap" in goal or "consistency" in goal or "audit" in goal or "devil" in goal:
            agent = self.agents["consistency_gap"]
            result = agent.review_case_consistency(case_id, meta)
            agent_name = "ConsistencyGapReviewAgent"

        elif "entity" in goal or "person" in goal or "cross-case" in goal:
            agent = self.agents["entity"]
            result = agent.resolve_entities(case_id, meta.get("entities", []))
            agent_name = "PersonEntityAgent"

        elif "timeline" in goal or "chronology" in goal:
            agent = self.agents["timeline"]
            result = agent.audit_timeline(case_id, meta.get("events", []))
            agent_name = "TimelineAgent"

        elif "intake" in goal or "triage" in goal:
            agent = self.agents["intake_triage"]
            result = agent.analyze_intake(meta)
            agent_name = "IntakeCaseTriageAgent"

        elif "evidence" in goal or "vault" in goal:
            agent = self.agents["evidence"]
            result = agent.analyze_evidence_vault(case_id, meta.get("evidence", []))
            agent_name = "EvidenceAnalysisAgent"

        else: # Default: Comprehensive Investigation Briefing & Report
            # Maintain backward compatibility with SupervisorBriefingAgent
            try:
                from supervisor_agent import SupervisorBriefingAgent
                briefing_agent = SupervisorBriefingAgent(self.api_url)
                result = briefing_agent.compile_briefing_package(case_id, request_user)
                agent_name = "SupervisorBriefingAgent"
            except Exception:
                agent = self.agents["report"]
                result = agent.compile_final_case_report(case_id, meta)
                agent_name = "InvestigationReportAgent"

        return {
            "status": "success",
            "orchestrated_goal": request_goal,
            "agent_used": agent_name,
            "result": result
        }

if __name__ == "__main__":
    orchestrator = CPPDCaseOrchestrator()
    res = orchestrator.run_agent_workflow("CASE-142", "Generate interview questions for suspect", "somchai.i@cppd.go.th")
    print(json.dumps(res, indent=2, ensure_ascii=False))
