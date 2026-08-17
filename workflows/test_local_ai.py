# CPPD Local AI Verification & Privacy Route Tests
import urllib.request
import urllib.parse
import json
import sys
import os

API_BASE = "http://127.0.0.1:8000"

# Inject paths to import CPPDEnvironmentRouter directly
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../services/ai-router')))
from ai_router import CPPDEnvironmentRouter

def test_save_ai_settings():
    print("[Test] Testing AI Settings API POST...")
    
    settings_payload = {
        "mode": "local_pc",
        "local_endpoint": "http://127.0.0.1:8000/api/mock-local-ai/v1",
        "local_model": "llama3"
    }
    
    req_data = json.dumps(settings_payload).encode('utf-8')
    req = urllib.request.Request(
        f"{API_BASE}/api/settings/ai",
        data=req_data,
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    res = urllib.request.urlopen(req)
    result = json.loads(res.read().decode('utf-8'))
    print("[Test] Settings Save Response:")
    print(json.dumps(result, indent=2))
    
    assert result["status"] == "success", "Failed to save settings"
    assert result["settings"]["mode"] == "local_pc"
    print("[OK] Local AI Settings saved successfully.")

def test_local_ai_routing():
    print("[Test] Verifying AI Router routes requests to local endpoint...")
    
    router = CPPDEnvironmentRouter()
    # Check that settings loaded are indeed local_pc
    settings = router.load_settings()
    print(f"Active Router Settings: {settings}")
    assert settings["mode"] == "local_pc"
    assert "mock-local-ai" in settings["local_endpoint"]
    
    # Trigger summarization
    summary = router.summarize_statement("Confidential witness data text.")
    print(f"Summary Output: {summary}")
    assert "Mock Response" in summary
    assert "confidential" in summary.lower()
    print("[OK] AI router successfully routed confidential statement locally.")

def reset_ai_settings():
    print("[Test] Resetting AI Settings back to Cloud Gemini...")
    settings_payload = {
        "mode": "cloud",
        "local_endpoint": "http://localhost:11434/v1",
        "local_model": "llama3"
    }
    req_data = json.dumps(settings_payload).encode('utf-8')
    req = urllib.request.Request(
        f"{API_BASE}/api/settings/ai",
        data=req_data,
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    urllib.request.urlopen(req)
    print("[OK] AI Router reset complete.")

if __name__ == "__main__":
    try:
        test_save_ai_settings()
        test_local_ai_routing()
        reset_ai_settings()
        print("\n[OK] ALL LOCAL AI PRIVACY ROUTE TESTS PASSED.")
    except Exception as e:
        print(f"\n[FAIL] TEST FAILURE: {e}")
        # Make sure we reset settings even if test fails
        try:
            reset_ai_settings()
        except:
            pass
        import traceback
        traceback.print_exc()
