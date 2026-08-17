# CPPD Investigation OS - Multi-Level Role Access Boundaries Verification
import urllib.request
import urllib.parse
import json

API_BASE = "http://127.0.0.1:8000"

def get_token_for_email(email):
    # Simulated OAuth callback to retrieve token
    payload = {"code": "mock-oauth-code", "email": email}
    req_data = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(
        f"{API_BASE}/api/auth/google/callback",
        data=req_data,
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    res = urllib.request.urlopen(req)
    auth_data = json.loads(res.read().decode('utf-8'))
    return auth_data["token"]

def fetch_cases_list(token):
    req = urllib.request.Request(
        f"{API_BASE}/api/cases",
        headers={"Authorization": f"Bearer {token}"}
    )
    res = urllib.request.urlopen(req)
    return json.loads(res.read().decode('utf-8'))

def fetch_case_detail(token, case_id):
    req = urllib.request.Request(
        f"{API_BASE}/api/cases/{case_id}",
        headers={"Authorization": f"Bearer {token}"}
    )
    try:
        res = urllib.request.urlopen(req)
        return json.loads(res.read().decode('utf-8')), res.code
    except urllib.error.HTTPError as e:
        return None, e.code

def test_rbac_boundaries():
    print("[Test] Initializing hierarchical access validation...")

    # 1. Admin checks
    print("\n[Test] Testing Admin Access (admin@cppd.go.th)...")
    admin_token = get_token_for_email("admin@cppd.go.th")
    admin_cases = fetch_cases_list(admin_token)
    print(f"Admin sees {len(admin_cases)} cases: {[c['id'] for c in admin_cases]}")
    assert len(admin_cases) == 3
    
    # 2. Commander checks (ผบก.)
    print("\n[Test] Testing Commander Access (commander@cppd.go.th)...")
    commander_token = get_token_for_email("commander@cppd.go.th")
    commander_cases = fetch_cases_list(commander_token)
    print(f"Commander sees {len(commander_cases)} cases: {[c['id'] for c in commander_cases]}")
    assert len(commander_cases) == 3

    # 3. Deputy Commander checks (รอง ผบก.)
    print("\n[Test] Testing Deputy Commander Access (deputy.commander@cppd.go.th)...")
    dep_commander_token = get_token_for_email("deputy.commander@cppd.go.th")
    dep_commander_cases = fetch_cases_list(dep_commander_token)
    print(f"Deputy Commander sees {len(dep_commander_cases)} cases: {[c['id'] for c in dep_commander_cases]}")
    assert len(dep_commander_cases) == 3

    # 4. Deputy Superintendent checks (รอง ผกก. / หัวหน้างานสอบสวน)
    print("\n[Test] Testing Deputy Superintendent Access (deputy.superintendent@cppd.go.th)...")
    dep_super_token = get_token_for_email("deputy.superintendent@cppd.go.th")
    dep_super_cases = fetch_cases_list(dep_super_token)
    print(f"Deputy Superintendent sees {len(dep_super_cases)} cases: {[c['id'] for c in dep_super_cases]}")
    assert len(dep_super_cases) == 3

    # 5. Superintendent checks (ผกก. - Financial Crimes)
    print("\n[Test] Testing Superintendent Access (superintendent@cppd.go.th)...")
    super_token = get_token_for_email("superintendent@cppd.go.th")
    super_cases = fetch_cases_list(super_token)
    print(f"Superintendent sees {len(super_cases)} cases: {[c['id'] for c in super_cases]}")
    # Should see Siam Network Ledger (Financial Crimes) and Phuket Cyber (Financial Crimes)
    # but not Bangkok Shell Company (Cyber Division)
    assert len(super_cases) == 2
    assert "CASE-112" not in [c["id"] for c in super_cases]
    print("[OK] Superintendent correctly restricted to division unit cases.")

    # 6. Investigator checks (พนักงานสอบสวน - somchai.i@cppd.go.th)
    print("\n[Test] Testing Investigator Access (somchai.i@cppd.go.th)...")
    somchai_token = get_token_for_email("somchai.i@cppd.go.th")
    somchai_cases = fetch_cases_list(somchai_token)
    print(f"Investigator sees {len(somchai_cases)} cases: {[c['id'] for c in somchai_cases]}")
    assert len(somchai_cases) == 1
    assert somchai_cases[0]["id"] == "CASE-142"

    # Verify Investigator cannot fetch details of other cases (CASE-087, CASE-112)
    _, code_ok = fetch_case_detail(somchai_token, "CASE-142")
    assert code_ok == 200
    _, code_forbidden = fetch_case_detail(somchai_token, "CASE-087")
    assert code_forbidden == 403
    print("[OK] Investigator correctly blocked from viewing unassigned cases.")

    # 7. Case Clerk checks (เสมียนคดี - clerk.a@cppd.go.th)
    print("\n[Test] Testing Case Clerk Access (clerk.a@cppd.go.th)...")
    clerk_token = get_token_for_email("clerk.a@cppd.go.th")
    clerk_cases = fetch_cases_list(clerk_token)
    print(f"Clerk sees {len(clerk_cases)} cases: {[c['id'] for c in clerk_cases]}")
    assert len(clerk_cases) == 1
    assert clerk_cases[0]["id"] == "CASE-142"

    _, code_forbidden_clerk = fetch_case_detail(clerk_token, "CASE-112")
    assert code_forbidden_clerk == 403
    print("[OK] Case Clerk correctly restricted to assigned case memberships.")

if __name__ == "__main__":
    try:
        test_rbac_boundaries()
        print("\n[OK] MULTI-LEVEL RBAC HIERARCHY ACCESS TESTS PASSED.")
    except Exception as e:
        print(f"\n[FAIL] TEST FAILURE: {e}")
        import traceback
        traceback.print_exc()
