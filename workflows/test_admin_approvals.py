# CPPD Investigation OS - Admin Approval Gate & Toggle Verification
import urllib.request
import urllib.parse
import json

API_BASE = "http://127.0.0.1:8000"

def try_login_with_email(email):
    payload = {"code": "mock-oauth-code", "email": email}
    req_data = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(
        f"{API_BASE}/api/auth/google/callback",
        data=req_data,
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    try:
        res = urllib.request.urlopen(req)
        data = json.loads(res.read().decode('utf-8'))
        return data, res.code
    except urllib.error.HTTPError as e:
        return json.loads(e.read().decode('utf-8')), e.code

def fetch_admin_users(token):
    req = urllib.request.Request(
        f"{API_BASE}/api/admin/users",
        headers={"Authorization": f"Bearer {token}"}
    )
    res = urllib.request.urlopen(req)
    return json.loads(res.read().decode('utf-8'))

def set_approval_status(token, user_id, approved):
    payload = {"approved": approved}
    req_data = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(
        f"{API_BASE}/api/admin/users/{user_id}/approve",
        data=req_data,
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
        method="POST"
    )
    res = urllib.request.urlopen(req)
    return json.loads(res.read().decode('utf-8'))

def test_admin_approvals():
    print("[Test] Initializing self-registration approval gate validation...")

    # 0. Ensure clerk starts unapproved
    admin_res, _ = try_login_with_email("admin@cppd.go.th")
    set_approval_status(admin_res["token"], "p-clerk", approved=False)

    # 1. Clerk attempts login -> Should fail (approved=False by default)
    print("\n[Test] 1. Unapproved user login attempt (clerk.a@cppd.go.th)...")
    res_data, code = try_login_with_email("clerk.a@cppd.go.th")
    print(f"Response: {res_data} | Code: {code}")
    assert code == 403
    assert "pending administrator approval" in res_data["detail"]
    print("[OK] Pending user correctly blocked at login gate.")

    # 2. Login as admin
    print("\n[Test] 2. Log in as Administrator (admin@cppd.go.th)...")
    admin_res, admin_code = try_login_with_email("admin@cppd.go.th")
    assert admin_code == 200
    admin_token = admin_res["token"]
    print("[OK] Admin login successful.")

    # 3. Retrieve user list
    print("\n[Test] 3. Fetching user list as admin...")
    users = fetch_admin_users(admin_token)
    clerk_profile = next((u for u in users if u["email"] == "clerk.a@cppd.go.th"), None)
    assert clerk_profile is not None
    assert clerk_profile["approved"] is False
    print(f"[OK] Found clerk profile in admin database. Approved status: {clerk_profile['approved']}.")

    # 4. Approve clerk account
    print("\n[Test] 4. Admin approving clerk.a@cppd.go.th access...")
    approve_res = set_approval_status(admin_token, "p-clerk", approved=True)
    assert approve_res["status"] == "success"
    assert approve_res["user"]["approved"] is True
    print("[OK] Clerk status updated to Approved.")

    # 5. Clerk attempts login again -> Should succeed!
    print("\n[Test] 5. Approved user login attempt (clerk.a@cppd.go.th)...")
    clerk_res, clerk_code = try_login_with_email("clerk.a@cppd.go.th")
    print(f"Response: {clerk_res} | Code: {clerk_code}")
    assert clerk_code == 200
    assert clerk_res["status"] == "success"
    print("[OK] Newly approved user successfully authenticated.")

    # 6. Revoke clerk account
    print("\n[Test] 6. Revoking clerk.a@cppd.go.th access as admin...")
    revoke_res = set_approval_status(admin_token, "p-clerk", approved=False)
    assert revoke_res["status"] == "success"
    assert revoke_res["user"]["approved"] is False
    print("[OK] Clerk status updated back to Pending/Revoked.")

    # 7. Clerk attempts login again -> Should fail with 403!
    print("\n[Test] 7. Revoked user login attempt...")
    res_data_final, code_final = try_login_with_email("clerk.a@cppd.go.th")
    assert code_final == 403
    print("[OK] Revoked user successfully blocked at login gate.")

if __name__ == "__main__":
    try:
        test_admin_approvals()
        print("\n[OK] ADMIN USER APPROVAL SYSTEM TESTS PASSED.")
    except Exception as e:
        print(f"\n[FAIL] TEST FAILURE: {e}")
        import traceback
        traceback.print_exc()
