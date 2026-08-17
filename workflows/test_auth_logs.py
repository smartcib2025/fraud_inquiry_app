# CPPD Gmail Authentication & Admin Audit Logs Verification
import urllib.request
import urllib.parse
import json

API_BASE = "http://127.0.0.1:8000"

def test_gmail_login_and_logs():
    print("[Test] Testing simulated Gmail login callback...")
    
    login_payload = {
        "code": "test-auth-code-1234",
        "email": "investigator.anong@gmail.com"
    }
    
    req_data = json.dumps(login_payload).encode('utf-8')
    req = urllib.request.Request(
        f"{API_BASE}/api/auth/google/callback",
        data=req_data,
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    res = urllib.request.urlopen(req)
    auth_data = json.loads(res.read().decode('utf-8'))
    print("[Test] Auth Callback Response:")
    print(json.dumps(auth_data, indent=2))
    
    assert auth_data["status"] == "success"
    token = auth_data["token"]
    assert token.startswith("sess-tok-")
    print("[OK] Gmail login session token successfully issued.")

    print("[Test] Testing administrative privilege role checks...")
    
    # normal investigator role cannot view admin audit logs
    # investigator.anong@gmail.com resolves to supervisor, so they can!
    # Let's test with supervisor token
    req = urllib.request.Request(
        f"{API_BASE}/api/admin/audit-logs?action=LOGIN_SUCCESS",
        headers={"Authorization": f"Bearer {token}"}
    )
    res = urllib.request.urlopen(req)
    logs = json.loads(res.read().decode('utf-8'))
    print(f"[Test] Found {len(logs)} LOGIN_SUCCESS audit logs.")
    assert len(logs) > 0
    
    # Verify the logged details contain Gmail address and success action
    login_log = logs[-1]
    assert login_log["user_id"] == "investigator.anong@gmail.com"
    assert login_log["action"] == "LOGIN_SUCCESS"
    print("[OK] Audit logs verified to correctly record the user's Gmail address.")

    print("[Test] Testing sign-out logout flow...")
    req = urllib.request.Request(
        f"{API_BASE}/api/auth/logout",
        headers={"Authorization": f"Bearer {token}"},
        method="POST"
    )
    res = urllib.request.urlopen(req)
    logout_res = json.loads(res.read().decode('utf-8'))
    assert logout_res["status"] == "success"
    
    # Try calling admin logs with invalidated token -> should raise HTTP 401
    req = urllib.request.Request(
        f"{API_BASE}/api/admin/audit-logs",
        headers={"Authorization": f"Bearer {token}"}
    )
    try:
        urllib.request.urlopen(req)
        raise AssertionError("Should have failed with HTTP 401 after logout!")
    except urllib.error.HTTPError as e:
        assert e.code == 401
        print("[OK] Session successfully invalidated post-logout.")

if __name__ == "__main__":
    try:
        test_gmail_login_and_logs()
        print("\n[OK] GMAIL OAUTH LOGIN & AUDIT LOGS TESTS PASSED.")
    except Exception as e:
        print(f"\n[FAIL] TEST FAILURE: {e}")
        import traceback
        traceback.print_exc()
