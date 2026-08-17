# CPPD Phase 4 Integration Tests
import urllib.request
import urllib.parse
import json

API_BASE = "http://127.0.0.1:8000"

def test_agent_permissions():
    print("[Test] Testing Orchestrator access controls...")
    
    # CASE-112 is unassigned to Somchai -> should fail with error
    params = urllib.parse.urlencode({
        "case_id": "CASE-112",
        "goal": "briefing",
        "user_email": "somchai.i@cppd.go.th"
    })
    
    req = urllib.request.Request(
        f"{API_BASE}/api/agents/run?{params}",
        method="POST"
    )
    res = urllib.request.urlopen(req)
    result = json.loads(res.read().decode('utf-8'))
    print("[Test] Unassigned Case response:")
    print(json.dumps(result, indent=2))
    assert result["status"] == "error", "Expected authorization failure for unassigned case"
    print("[OK] Access control successfully rejected unauthorized investigator.")

def test_transaction_sandbox():
    print("[Test] Testing Transaction Sandbox Agent analytics execution...")
    
    params = urllib.parse.urlencode({
        "case_id": "CASE-142",
        "goal": "transaction",
        "user_email": "somchai.i@cppd.go.th"
    })
    
    req = urllib.request.Request(
        f"{API_BASE}/api/agents/run?{params}",
        method="POST"
    )
    res = urllib.request.urlopen(req)
    result = json.loads(res.read().decode('utf-8'))
    print("[Test] Sandboxed Pandas stats response:")
    print(json.dumps(result, indent=2))
    
    agent_res = result["result"]
    assert result["status"] == "success", "Agent analysis failed"
    assert agent_res["sandbox_status"] == "terminated_success", "Expected sandboxed process termination"
    assert "metrics" in agent_res, "Expected stats metrics object"
    print("[OK] Sandboxed pandas process executed correctly.")

def test_briefing_compiler():
    print("[Test] Testing Supervisor Briefing Agent report compiler...")
    
    params = urllib.parse.urlencode({
        "case_id": "CASE-142",
        "goal": "briefing",
        "user_email": "somchai.i@cppd.go.th"
    })
    
    req = urllib.request.Request(
        f"{API_BASE}/api/agents/run?{params}",
        method="POST"
    )
    res = urllib.request.urlopen(req)
    result = json.loads(res.read().decode('utf-8'))
    print("[Test] Briefing compiler response:")
    print(json.dumps(result, indent=2))
    
    briefing = result["result"]
    assert result["status"] == "success", "Agent compiler failed"
    assert "briefing_markdown" in briefing, "Expected markdown report body"
    assert "# CPPD COMMAND BRIEFING PACKAGE" in briefing["briefing_markdown"], "Expected report title in markdown"
    print("[OK] Supervisor briefing agent compiled briefing markdown successfully.")

if __name__ == "__main__":
    try:
        test_agent_permissions()
        test_transaction_sandbox()
        test_briefing_compiler()
        print("\n[OK] ALL PHASE 4 INTEGRATION TESTS PASSED.")
    except Exception as e:
        print(f"\n[FAIL] TEST FAILURE: {e}")
        import traceback
        traceback.print_exc()
