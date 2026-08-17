# CPPD Phase 3 Integration Tests
import urllib.request
import json

API_BASE = "http://127.0.0.1:8000"

def test_transaction_layering():
    print("[Test] Testing transaction ingestion and layering detection...")
    
    # Structuring ledger payload
    tx_payload = [
        {"source_account": None, "target_account": "401-229-3388", "amount": 1950000.0, "transaction_date": "2026-08-11T10:00:00Z"},
        {"source_account": None, "target_account": "401-229-3388", "amount": 1980000.0, "transaction_date": "2026-08-11T12:00:00Z"},
        # Fast transfer out (layering)
        {"source_account": "401-229-3388", "target_account": "702-888-1123", "amount": 3800000.0, "transaction_date": "2026-08-11T15:00:00Z"}
    ]
    
    req_data = json.dumps(tx_payload).encode('utf-8')
    req = urllib.request.Request(
        f"{API_BASE}/api/transactions/import?case_id=CASE-142",
        data=req_data,
        headers={"Content-Type": "application/json"}
    )
    res = urllib.request.urlopen(req)
    result = json.loads(res.read().decode('utf-8'))
    print("[Test] Ingestion Response:")
    print(json.dumps(result, indent=2))
    
    # Assert layering was detected
    alerts = result["alerts"]
    alert_types = [a["type"] for a in alerts]
    print(f"Detected alerts: {alert_types}")
    assert "STRUCTURING" in alert_types, "Expected Structuring alert"
    assert "LAYERING_VELOCITY" in alert_types, "Expected Layering Velocity alert"
    assert "CIRCULAR_TRANSFER" in alert_types, "Expected Circular Transfer alert"
    print("[OK] Transaction structuring and layering successfully analyzed.")

def test_chronology_and_readiness():
    print("[Test] Querying computed case readiness and statement timeline...")
    
    # Query timeline contradictions
    res = urllib.request.urlopen(f"{API_BASE}/api/cases/CASE-142/timeline")
    timeline = json.loads(res.read().decode('utf-8'))
    print("[Test] Timeline Contradictions Report:")
    print(json.dumps(timeline, indent=2))
    
    events = timeline["events"]
    assert len(events) > 0, "Timeline events list should not be empty"
    assert any(e["status"] == "contradictory" for e in events), "Expected contradictory alibi event"
    print("[OK] Chronology contradiction checker compiled correctly.")
    
    # Query readiness score
    res = urllib.request.urlopen(f"{API_BASE}/api/cases/CASE-142/readiness")
    readiness = json.loads(res.read().decode('utf-8'))
    print("[Test] Case Readiness Summary:")
    print(json.dumps(readiness, indent=2))
    
    assert readiness["readiness_percentage"] >= 70, "Readiness score should reflect verified items"
    print("[OK] Case readiness metrics calculated successfully.")

if __name__ == "__main__":
    try:
        test_transaction_layering()
        test_chronology_and_readiness()
        print("\n[OK] ALL PHASE 3 INTEGRATION TESTS PASSED.")
    except Exception as e:
        print(f"\n[FAIL] TEST FAILURE: {e}")
        import traceback
        traceback.print_exc()
