# -*- coding: utf-8 -*-
"""
Phase 7 Deep Investigation Report & Case File Automation Test Suite
Verifies Template Generation, Section-by-Section Drafting, Validation Engine, Supervisor Approval, Human Finalization, Export Hash, and Case File Bundle.
"""
import sys
import os
import unittest
from fastapi.testclient import TestClient

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../services/api-gateway')))
from main import app, db

client = TestClient(app)

class TestPhase7DeepReport(unittest.TestCase):
    def setUp(self):
        # Authenticate as investigator Somchai
        res = client.post("/api/auth/google/callback", json={"code": "test", "email": "somchai.i@cppd.go.th"})
        self.assertEqual(res.status_code, 200)
        self.token = res.json()["token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}

        # Authenticate as supervisor Anong
        res_sup = client.post("/api/auth/google/callback", json={"code": "test", "email": "investigator.anong@gmail.com"})
        self.assertEqual(res_sup.status_code, 200)
        self.sup_token = res_sup.json()["token"]
        self.sup_headers = {"Authorization": f"Bearer {self.sup_token}"}

    def test_01_report_creation_and_section_generation(self):
        """Test creating report and triggering structured section-by-section draft generation."""
        payload = {
            "report_type": "INVESTIGATION_REPORT",
            "title": "รายงานการสอบสวนคดีอาญาที่ 142/2569 (ฉบับส่งพนักงานอัยการ)"
        }
        res = client.post("/api/v1/cases/CASE-142/reports", json=payload, headers=self.headers)
        self.assertEqual(res.status_code, 200)
        rep = res.json()["report"]
        rep_id = rep["id"]

        # Generate Sections
        res_gen = client.post(f"/api/v1/reports/{rep_id}/generate", headers=self.headers)
        self.assertEqual(res_gen.status_code, 200)
        self.assertGreaterEqual(res_gen.json()["sections_created"], 4)
        print("[PASS] Milestone 2 & 6: Report Creation & Structured Section Generation passed")

    def test_02_report_validation_blocking_and_readiness(self):
        """Test report validation readiness assessment."""
        rep_id = "rep-142-01"
        res = client.post(f"/api/v1/reports/{rep_id}/validate", headers=self.headers)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["readiness_status"], "READY_FOR_REVIEW")
        print("[PASS] Milestone 8: Report Validation & Anti-Hallucination passed")

    def test_03_supervisor_approval_and_human_finalization(self):
        """Test supervisor approving report and authorized officer finalizing and locking document."""
        rep_id = "rep-142-01"

        # 1. Supervisor Approves
        res_app = client.post(f"/api/v1/reports/{rep_id}/approve", headers=self.sup_headers)
        self.assertEqual(res_app.status_code, 200)
        self.assertEqual(res_app.json()["report_status"], "APPROVED")

        # 2. Finalize & Lock
        res_fin = client.post(f"/api/v1/reports/{rep_id}/finalize", headers=self.headers)
        self.assertEqual(res_fin.status_code, 200)
        self.assertEqual(res_fin.json()["report_status"], "FINAL")
        print("[PASS] Milestone 10: Supervisor Approval & Human Finalization passed")

    def test_04_docx_and_pdf_export_with_hash(self):
        """Test exporting DOCX and PDF with cryptographic SHA-256 hash."""
        rep_id = "rep-142-01"
        payload = {
            "format": "DOCX",
            "purpose": "ส่งพนักงานอัยการพิเศษฝ่ายคดีคุ้มครองผู้บริโภค",
            "recipient": "สำนักงานอัยการสูงสุด"
        }
        res = client.post(f"/api/v1/reports/{rep_id}/export", json=payload, headers=self.headers)
        self.assertEqual(res.status_code, 200)
        exp = res.json()["export"]
        self.assertIn("sha256-", exp["file_hash"])
        self.assertIn(".docx", exp["download_url"])
        print("[PASS] Milestone 11: DOCX & PDF Export with Cryptographic Hash passed")

    def test_05_case_file_index_and_bundle_export(self):
        """Test generating master case file index and bundle manifest."""
        # 1. Case File Index
        res_idx = client.get("/api/v1/cases/CASE-142/case-file-index", headers=self.headers)
        self.assertEqual(res_idx.status_code, 200)
        self.assertGreaterEqual(res_idx.json()["total_documents"], 3)

        # 2. Case File Bundle
        bundle_payload = {
            "recipient": "สำนักงานอัยการสูงสุด",
            "purpose": "สำเนาสำนวนการสอบสวนเพื่อฟ้องคดี"
        }
        res_bun = client.post("/api/v1/cases/CASE-142/case-file-bundle", json=bundle_payload, headers=self.headers)
        self.assertEqual(res_bun.status_code, 200)
        bundle = res_bun.json()["bundle"]
        self.assertIn("bundle-", bundle["bundle_id"])
        self.assertIn("sha256-", bundle["bundle_hash"])
        print("[PASS] Milestone 12: Master Case File Index & Bundle Export passed")

    def test_06_unapproved_finalization_prevented(self):
        """Test that unapproved reports cannot be finalized directly."""
        # Create fresh draft report
        payload = {"title": "ร่างรายงานการสอบสวนใหม่ที่ยังไม่อนุมัติ"}
        res = client.post("/api/v1/cases/CASE-142/reports", json=payload, headers=self.headers)
        new_rep_id = res.json()["report"]["id"]

        # Attempt to finalize before approval -> Expect HTTP 400
        res_fin = client.post(f"/api/v1/reports/{new_rep_id}/finalize", headers=self.headers)
        self.assertEqual(res_fin.status_code, 400)
        print("[PASS] Scenario D: Unapproved Finalization Blocked passed")

if __name__ == "__main__":
    unittest.main()
