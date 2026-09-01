# -*- coding: utf-8 -*-
"""
Phase 3 Deep Evidence Intelligence & Chain of Custody Test Suite
Verifies Artifact Hierarchy, SHA-256 Integrity, Custody Ledger, Matrix/Gaps, and Export.
"""
import sys
import os
import unittest
from fastapi.testclient import TestClient

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../services/api-gateway')))
from main import app, db

client = TestClient(app)

class TestPhase3DeepEvidence(unittest.TestCase):
    def setUp(self):
        # Authenticate as investigator Somchai
        res = client.post("/api/auth/google/callback", json={"code": "test", "email": "somchai.i@cppd.go.th"})
        self.assertEqual(res.status_code, 200)
        self.token = res.json()["token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}

        # Authenticate as admin
        res_adm = client.post("/api/auth/google/callback", json={"code": "test", "email": "admin@cppd.go.th"})
        self.assertEqual(res_adm.status_code, 200)
        self.adm_token = res_adm.json()["token"]
        self.adm_headers = {"Authorization": f"Bearer {self.adm_token}"}

    def test_01_artifact_hierarchy_and_parent_links(self):
        """Test creating derived artifacts and ensuring parent file linking."""
        ev_id = "f05d9e5b-ec1d-4009-bf2f-e8b9fb6cb088"
        payload = {
            "artifact_type": "EXTRACTED_CONTENT",
            "parent_file_id": "ef-142-01",
            "original_filename": "extracted_ocr_text.json",
            "mime_type": "application/json",
            "size_bytes": 1024,
            "sha256": "5e884898da28047151d0e56f8dc6292773603d0d6aabbdd62a11ef721d1542d8",
            "metadata_json": {"extractor": "Tesseract_OCR", "confidence": 0.96}
        }
        res = client.post(f"/api/v1/evidence/{ev_id}/artifacts", json=payload, headers=self.headers)
        self.assertEqual(res.status_code, 200)
        art_id = res.json()["artifact"]["id"]

        res_list = client.get(f"/api/v1/evidence/{ev_id}/artifacts", headers=self.headers)
        self.assertEqual(res_list.status_code, 200)
        artifacts = res_list.json()["artifacts"]
        self.assertTrue(any(a["id"] == art_id for a in artifacts))
        print("[PASS] Milestone 2: Artifact Hierarchy & Extraction passed")

    def test_02_sha256_integrity_match_and_mismatch_alarm(self):
        """Test SHA-256 integrity verification and security alarm on hash mismatch."""
        ev_id = "f05d9e5b-ec1d-4009-bf2f-e8b9fb6cb088"
        expected_hash = "a3f82cb304b5f883201de374ffea57bd8c928e1832049e3bfd12cf88c9d21415"

        # 1. Matching verification
        res_match = client.post(f"/api/v1/evidence/{ev_id}/integrity/verify", json={"check_type": "MANUAL", "actual_hash": expected_hash}, headers=self.headers)
        self.assertEqual(res_match.status_code, 200)
        self.assertEqual(res_match.json()["result"], "MATCH")

        # 2. Tampered / Mismatched verification -> Must return 409 Conflict & Security Event
        tampered_hash = "0000000000000000000000000000000000000000000000000000000000000000"
        res_mismatch = client.post(f"/api/v1/evidence/{ev_id}/integrity/verify", json={"check_type": "MANUAL", "actual_hash": tampered_hash}, headers=self.headers)
        self.assertEqual(res_mismatch.status_code, 409)

        # 3. Verify Security Audit Event was logged
        audit_res = client.get("/api/admin/audit-logs?action=EVIDENCE.HASH.MISMATCH", headers=self.adm_headers)
        self.assertEqual(audit_res.status_code, 200)
        logs = audit_res.json() if isinstance(audit_res.json(), list) else audit_res.json().get("logs", [])
        self.assertTrue(any(l.get("action") == "EVIDENCE.HASH.MISMATCH" for l in logs))
        print("[PASS] Milestone 3: SHA-256 Integrity & Tamper Alarms passed")

    def test_03_append_only_chain_of_custody(self):
        """Test transferring custody and logging append-only custody ledger."""
        ev_id = "f05d9e5b-ec1d-4009-bf2f-e8b9fb6cb088"
        transfer_payload = {
            "to_user_id": "ร.ต.อ. สมศักดิ์ สืบสวนไว",
            "to_location": "ห้องสอบสวน 1 (Interrogation Room 1)",
            "reason": "นำหลักฐานไปใช้ประกอบการสอบปากคำผู้ต้องหา",
            "seal_number": "SEAL-CPPD-2026-0912",
            "witnessed_by": "ส.ต.อ. สุรชัย คดีมั่น",
            "condition_after": "ปิดผนึกซองพยานหลักฐานสมบูรณ์"
        }
        res = client.post(f"/api/v1/evidence/{ev_id}/custody/transfer", json=transfer_payload, headers=self.headers)
        self.assertEqual(res.status_code, 200)

        cust_res = client.get(f"/api/v1/evidence/{ev_id}/custody", headers=self.headers)
        self.assertEqual(cust_res.status_code, 200)
        events = cust_res.json()["events"]
        self.assertGreaterEqual(len(events), 2)
        print("[PASS] Milestone 4: Append-Only Chain of Custody passed")

    def test_04_evidence_matrix_and_gap_resolution(self):
        """Test Evidence Matrix generation and resolving Evidence Gap."""
        # 1. Check Matrix
        res_mat = client.get("/api/v1/cases/CASE-142/evidence-matrix", headers=self.headers)
        self.assertEqual(res_mat.status_code, 200)
        matrix = res_mat.json()["matrix"]
        self.assertGreaterEqual(len(matrix), 1)

        # 2. Create and Resolve Gap
        gap_payload = {
            "investigation_issue_id": "iss-142-01",
            "description": "สำเนาทะเบียนราษฎร์ของผู้ต้องหา",
            "required_evidence_type": "OFFICIAL_DOCUMENT"
        }
        res_gap = client.post("/api/v1/cases/CASE-142/evidence-gaps", json=gap_payload, headers=self.headers)
        self.assertEqual(res_gap.status_code, 200)
        gap_id = res_gap.json()["gap"]["id"]

        # Resolve Gap
        res_res = client.patch(f"/api/v1/evidence-gaps/{gap_id}/resolve", json={"resolved_by_evidence_id": "f05d9e5b-ec1d-4009-bf2f-e8b9fb6cb088"}, headers=self.headers)
        self.assertEqual(res_res.status_code, 200)
        self.assertEqual(res_res.json()["gap"]["status"], "RESOLVED")
        print("[PASS] Milestone 7: Evidence Matrix & Gap Resolution passed")

    def test_05_controlled_evidence_export_manifest(self):
        """Test generating structured hash manifest bundle on export."""
        export_payload = {
            "recipient": "พนักงานอัยการ สำนักงานคดีเศรษฐกิจและทรัพยากร",
            "purpose": "ส่งสำนวนการสอบสวนดำเนินคดีตาม ป.วิ.อ. ม.142",
            "selected_evidence_ids": ["f05d9e5b-ec1d-4009-bf2f-e8b9fb6cb088"]
        }
        res = client.post("/api/v1/cases/CASE-142/evidence/export", json=export_payload, headers=self.headers)
        self.assertEqual(res.status_code, 200)
        manifest = res.json()["manifest"]
        self.assertIn("export_package_id", manifest)
        self.assertEqual(manifest["total_items"], 1)
        self.assertEqual(manifest["manifest_items"][0]["sha256"], "a3f82cb304b5f883201de374ffea57bd8c928e1832049e3bfd12cf88c9d21415")
        print("[PASS] Milestone 9: Controlled Evidence Export Manifest passed")

    def test_06_exact_hash_duplicate_detection(self):
        """Test exact SHA-256 duplicate detection across case evidence repository."""
        res = client.get("/api/v1/cases/CASE-142/evidence/duplicates", headers=self.headers)
        self.assertEqual(res.status_code, 200)
        self.assertIn("duplicates", res.json())
        print("[PASS] Milestone 5: Exact Hash Duplicate Detection passed")

if __name__ == "__main__":
    unittest.main()
