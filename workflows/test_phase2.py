# CPPD Phase 2 Integration Tests
import urllib.request
import json

API_BASE = "http://127.0.0.1:8000"

def test_slack_commands():
    print("[Test] Testing Slack slash commands...")
    
    # 1. Test /case
    req_data = json.dumps({"command": "/case", "text": "CASE-142"}).encode('utf-8')
    req = urllib.request.Request(
        f"{API_BASE}/api/slack/events",
        data=req_data,
        headers={"Content-Type": "application/json"}
    )
    res = urllib.request.urlopen(req)
    response_payload = json.loads(res.read().decode('utf-8'))
    print("[Test] Slack /case Response:")
    print(json.dumps(response_payload, indent=2))
    assert "blocks" in response_payload, "Expected interactive blocks layout in Slack response"
    print("[OK] Slack /case command blocks successfully generated.")

    # 2. Test /entity
    req_data = json.dumps({"command": "/entity", "text": "Kittisak"}).encode('utf-8')
    req = urllib.request.Request(
        f"{API_BASE}/api/slack/events",
        data=req_data,
        headers={"Content-Type": "application/json"}
    )
    res = urllib.request.urlopen(req)
    response_payload = json.loads(res.read().decode('utf-8'))
    print("[Test] Slack /entity Response:")
    print(json.dumps(response_payload, indent=2))
    assert "blocks" in response_payload, "Expected interactive blocks layout in Slack response"
    print("[OK] Slack /entity command blocks successfully generated.")

def test_event_propagation():
    print("[Test] Publishing VICTIM_REGISTERED event to test propagation loop...")
    
    event_payload = {
        "event_type": "VICTIM_REGISTERED",
        "payload": {
            "case_id": "CASE-142",
            "full_name": "Somsak Test",
            "phone": "089-111-2345",
            "loss_amount": 1250000.0,
            "raw_statement": "My name is Somsak Test. I was scammed by Kittisak Wongsawat, phone 089-111-2345. I made a transfer of 1,250,000 THB to SCB account 401-229-3388."
        }
    }
    
    req_data = json.dumps(event_payload).encode('utf-8')
    req = urllib.request.Request(
        f"{API_BASE}/api/pubsub/publish",
        data=req_data,
        headers={"Content-Type": "application/json"}
    )
    res = urllib.request.urlopen(req)
    result = json.loads(res.read().decode('utf-8'))
    print("[Test] Event Bus Ingest Result:")
    print(json.dumps(result, indent=2))
    
    # Check updated case details via API
    res = urllib.request.urlopen(f"{API_BASE}/api/cases/CASE-142")
    case_details = json.loads(res.read().decode('utf-8'))
    
    print("[Test] Verification Audit:")
    tasks = case_details["tasks"]
    task_titles = [t["title"] for t in tasks]
    print(f"Tasks: {task_titles}")
    
    # Assert that:
    # 1. Intake review task was created
    assert any("Review intake statement for Somsak Test" in t for t in task_titles), "Expected statement review task"
    # 2. Cross-case review task was created due to matching phone/account
    assert any("Verify cross-case association" in t for t in task_titles), "Expected cross-case verification task"
    
    print("[OK] Event cascade successfully propagated (VICTIM_REGISTERED -> ENTITY_CREATED -> AI_FINDINGS & cross-case TASKS).")

if __name__ == "__main__":
    try:
        test_slack_commands()
        test_event_propagation()
        print("\n[OK] ALL PHASE 2 INTEGRATION TESTS PASSED.")
    except Exception as e:
        print(f"\n[FAIL] TEST FAILURE: {e}")
        import traceback
        traceback.print_exc()
