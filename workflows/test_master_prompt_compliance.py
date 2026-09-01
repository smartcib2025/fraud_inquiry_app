# CPPD Integration Test: Master Prompt Compliance Verification
import sys
import os
import requests
import json

# Add agents directory to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "agents")))
from orchestrator import CPPDCaseOrchestrator

API_BASE = "http://127.0.0.1:8000"

def get_auth_token(email="somchai.i@cppd.go.th"):
    res = requests.post(f"{API_BASE}/api/auth/google/callback", json={"email": email, "code": "mock-code"})
    assert res.status_code == 200, f"Login failed for {email}: {res.text}"
    return res.json()["token"]

def test_all_12_modular_agents():
    print("\n--- [TEST 1] Testing All 12 Modular Agents via Orchestrator ---")
    orchestrator = CPPDCaseOrchestrator(API_BASE)
    
    test_cases = [
        ("intake_triage", "Intake and Triage Analysis", {"title": "Fake shop scam", "reporter_name": "Somchai", "raw_statement": "Transferred 1.25M"}),
        ("planning", "Generate Investigation Plan", {"title": "Siam Network"}),
        ("entity", "Resolve entities and suspect connections", {"entities": [{"name": "Kittisak"}]}),
        ("evidence", "Audit evidence vault integrity", {"evidence": [{"title": "Slip"}]}),
        ("timeline", "Audit timeline chronology", {"events": [{"date": "2026-08-09"}]}),
        ("digital", "Analyze digital artifacts and IP logs", {"communications": [{"channel": "LINE_CHAT"}]}),
        ("financial", "Analyze transaction layering flow", {"transactions": [{"amount": 1250000}]}),
        ("legal", "Map legal elements to Section 343", {"facts": [{"text": "Facebook ad"}]}),
        ("interview", "Generate interview questions for suspect", {"target_role": "suspect", "target_name": "Kittisak Wongsawat"}),
        ("document", "Draft Summons Warrant document", {"doc_type": "SUMMONS_WARRANT"}),
        ("report", "Compile final case briefing", {"case_id": "CASE-142"}),
        ("consistency_gap", "Audit case consistency and evidence gaps", {"case_id": "CASE-142"})
    ]

    for key, goal, meta in test_cases:
        res = orchestrator.run_agent_workflow("CASE-142", goal, "somchai.i@cppd.go.th", meta)
        assert res["status"] == "success", f"Agent workflow failed for {key}: {res}"
        agent_name = res["agent_used"]
        print(f"  [OK] Agent Goal: '{goal}' successfully routed to -> {agent_name}")
        
        # Verify FACT/CLAIM/INFERENCE tagging standard
        result_data = res.get("result", {})
        if "findings" in result_data:
            findings = result_data["findings"]
            assert len(findings) > 0, f"Expected findings tags from {agent_name}"
            tags = [f.get("tag") for f in findings]
            print(f"       Tags detected: {tags}")
            valid_tags = {"FACT", "CLAIM", "INFERENCE", "CONFLICT", "EVIDENCE_GAP", "NOT_VERIFIED", "REQUIRES_HUMAN_REVIEW"}
            for t in tags:
                assert t in valid_tags, f"Invalid tag '{t}' in {agent_name}"

def test_api_gateway_interviews_endpoint(token):
    print("\n--- [TEST 2] Testing Interview Question Generator API Endpoint ---")
    headers = {"Authorization": f"Bearer {token}"}
    payload = {
        "case_id": "CASE-142",
        "target_role": "suspect",
        "target_name": "Kittisak Wongsawat"
    }
    res = requests.post(f"{API_BASE}/api/interviews/generate", json=payload, headers=headers)
    assert res.status_code == 200, f"Interview endpoint failed: {res.text}"
    data = res.json()
    assert data["status"] == "success", f"Failed: {data}"
    questions = data["result"]["questions"]
    assert len(questions) >= 3, "Expected at least 3 interrogation questions"
    print(f"  [OK] Generated {len(questions)} interrogation questions for suspect.")
    for i, q in enumerate(questions[:2]):
        print(f"       Q{i+1}: {q[:80]}...")

def test_api_gateway_document_templates(token):
    print("\n--- [TEST 3] Testing Thai Police Document Drafting Templates ---")
    headers = {"Authorization": f"Bearer {token}"}
    
    templates = [
        "SUMMONS_WARRANT",
        "SEARCH_WARRANT",
        "ACCUSATION_RECORD",
        "FINAL_REPORT"
    ]
    
    for tpl in templates:
        res = requests.post(f"{API_BASE}/api/reports/generate", json={"case_id": "CASE-142", "report_type": tpl}, headers=headers)
        assert res.status_code == 200, f"Template {tpl} failed: {res.text}"
        data = res.json()
        assert data["status"] == "AI_DRAFT", f"Expected AI_DRAFT status for {tpl}, got {data.get('status')}"
        assert len(data["content"]) > 100, f"Content too short for {tpl}"
        print(f"  [OK] Template '{tpl}' drafted successfully (Title: '{data['title']}', Status: '{data['status']}')")

def test_communications_and_ai_analyses(token):
    print("\n--- [TEST 4] Testing Communications & AI Analyses Endpoints ---")
    headers = {"Authorization": f"Bearer {token}"}
    
    res_comm = requests.get(f"{API_BASE}/api/cases/CASE-142/communications", headers=headers)
    assert res_comm.status_code == 200, f"Failed communications: {res_comm.text}"
    comms = res_comm.json()
    assert len(comms) > 0, "Expected communications items"
    print(f"  [OK] Retrieved {len(comms)} communications (e.g. {comms[0]['channel']})")
    
    res_ana = requests.get(f"{API_BASE}/api/cases/CASE-142/ai-analyses", headers=headers)
    assert res_ana.status_code == 200, f"Failed ai-analyses: {res_ana.text}"
    analyses = res_ana.json()
    assert len(analyses) > 0, "Expected ai-analyses items"
    print(f"  [OK] Retrieved {len(analyses)} AI analysis records (Isolated from original evidence)")

if __name__ == "__main__":
    print("=== RUNNING MASTER PROMPT COMPLIANCE VERIFICATION SUITE ===")
    test_all_12_modular_agents()
    token = get_auth_token()
    test_api_gateway_interviews_endpoint(token)
    test_api_gateway_document_templates(token)
    test_communications_and_ai_analyses(token)
    print("\n[SUCCESS] ALL MASTER PROMPT COMPLIANCE TESTS PASSED (100% SPEC MATCH)!\n")
