import requests
import sys

def main():
    url = "http://127.0.0.1:8000/api/evidence/upload"
    
    # 1. Login using OAuth Callback simulation endpoint
    login_url = "http://127.0.0.1:8000/api/auth/google/callback"
    login_res = requests.post(login_url, json={"code": "mock-code", "email": "admin@cppd.go.th"})
    if login_res.status_code != 200:
        print(f"[FAIL] Authentication failed: {login_res.text}")
        sys.exit(1)
    
    token = login_res.json()["token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # 2. Upload file that triggers OCR simulation (e.g. filename has 'slip')
    files = {
        "file": ("transfer_slip.png", b"MOCK_IMAGE_BYTES", "image/png")
    }
    data = {
        "case_id": "CASE-142",
        "title": "Kasikorn Suspect Transfer Slip",
        "description": "Simulated upload of transfer slip",
        "type": "bank_statement"
    }
    
    print("Testing OCR upload...")
    res = requests.post(url, headers=headers, data=data, files=files)
    if res.status_code != 200:
        print(f"[FAIL] Upload failed with status {res.status_code}: {res.text}")
        sys.exit(1)
        
    res_json = res.json()
    print("Response Status:", res_json.get("status"))
    ocr_result = res_json.get("ocr_result", {})
    print("OCR Status:", ocr_result.get("status"))
    print("OCR Extracted Bank:", ocr_result.get("bank"))
    print("OCR Extracted Account:", ocr_result.get("account"))
    print("OCR Extracted Amount:", ocr_result.get("amount"))
    
    if ocr_result.get("status") == "extracted" and ocr_result.get("amount") == 1250000.0:
        print("[OK] OCR Ingestion & transaction seeding working successfully!")
    else:
        print("[FAIL] OCR extraction mismatch")
        sys.exit(1)

if __name__ == "__main__":
    main()
