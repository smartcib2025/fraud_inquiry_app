# CPPD Agent: Case Orchestrator
import sys
import os
import json
from typing import Dict, Any

class CPPDCaseOrchestrator:
    def __init__(self, api_url: str = "http://localhost:8000"):
        self.api_url = api_url

    def run_agent_workflow(self, case_id: str, request_goal: str, request_user: str) -> Dict[str, Any]:
        """
        Main orchestration loop:
        1. Validates requesting user permissions.
        2. Parses the request goal (e.g. "transaction_briefing", "readiness_briefing").
        3. Invokes sub-agents (Transaction Agent or Supervisor Agent).
        4. Synthesizes findings and outputs the package.
        """
        print(f"[Orchestrator Agent] Invoked for case: {case_id} by user: {request_user} with goal: {request_goal}")
        
        # Simulating access permission checks
        if request_user == "somchai.i@cppd.go.th" and case_id == "CASE-112":
            print("[Orchestrator Agent] Permission Denied: Somchai is not assigned to CASE-112.")
            return {"status": "error", "message": "Permission Denied: Investigator is not assigned to this case."}

        # Route work
        if "transaction" in request_goal.lower():
            # Delegate to Transaction Sandbox Agent
            from transaction_agent import TransactionSandboxAgent
            agent = TransactionSandboxAgent(self.api_url)
            result = agent.execute_sandbox_analysis(case_id)
            return {
                "status": "success",
                "orchestrated_goal": request_goal,
                "agent_used": "TransactionSandboxAgent",
                "result": result
            }
        else:
            # Default to compiling complete Case Briefing Package (Supervisor Agent)
            from supervisor_agent import SupervisorBriefingAgent
            agent = SupervisorBriefingAgent(self.api_url)
            briefing = agent.compile_briefing_package(case_id, request_user)
            return {
                "status": "success",
                "orchestrated_goal": request_goal,
                "agent_used": "SupervisorBriefingAgent",
                "result": briefing
            }

if __name__ == "__main__":
    orchestrator = CPPDCaseOrchestrator()
    res = orchestrator.run_agent_workflow("CASE-142", "Generate complete Case Briefing", "somchai.i@cppd.go.th")
    print(json.dumps(res, indent=2))
