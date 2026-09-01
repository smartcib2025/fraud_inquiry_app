# -*- coding: utf-8 -*-
"""
Phase 8 Deep Official Documents & Warrants Test Suite
Verifies Official Letter Generation, Search & Arrest Warrant Application Workflows, Identity/Location Verification, Validation Engine, Human Finalization, and SHA-256 Hash Exports.
"""
import sys
import os
import unittest
from fastapi.testclient import TestClient

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../services/api-gateway')))
from main import app, db

client = TestClient(app)

class TestPhase8DeepDocuments(unittest.TestCase):
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

    def test_01_official_document_creation_and_generation(self):
        """Test creating an official letter and generating content."""
        payload = {
            "document_type": "BANK_INFORMATION_REQUEST",
            "title": "หนังสือขออายัดบัญชีเงินฝากและขอรายการเดินบัญชี ธนาคารไทยพาณิชย์",
            "document_number": "ตช 0026.1/142"
        }
        res = client.post("/api/v1/cases/CASE-142/documents", json=payload, headers=self.headers)
        self.assertEqual(res.status_code, 200)
        doc = res.json()["document"]
        doc_id = doc["id"]

        # Generate content
        res_gen = client.post(f"/api/v1/documents/{doc_id}/generate", headers=self.headers)
        self.assertEqual(res_gen.status_code, 200)
        self.assertIn("ธนาคารไทยพาณิชย์", res_gen.json()["content_draft"])
        print("[PASS] Milestone 2 & 4: Official Document Creation & Generation passed")

    def test_02_search_warrant_application_and_draft(self):
        """Test creating a search warrant application with target premises and evidence links."""
        payload = {
            "target_type": "PREMISES",
            "target_location": "เลขที่ 12/5 ถนนลาดพร้าว แขวงจอมพล เขตจตุจักร กรุงเทพมหานคร",
            "target_person_id": "p-kittisak",
            "purpose": "ตรวจค้นและยึดอุปกรณ์คอมพิวเตอร์ โทรศัพท์มือถือ และเวชสำอางค์ของกลาง",
            "facts_supporting_request": "ตรวจพบบันทึกการเข้าใช้งานระบบผ่าน IP ในกรุงเทพฯ และใช้เป็นสถานที่รับโอนเงิน",
            "evidence_ids": ["11b7df3c-6622-48df-9cb9-ef77ba4c28f1"],
            "legal_basis": "ป.วิ.อ. มาตรา 69, 70"
        }
        res = client.post("/api/v1/cases/CASE-142/search-warrant-applications", json=payload, headers=self.headers)
        self.assertEqual(res.status_code, 200)
        swa = res.json()["search_warrant_application"]
        swa_id = swa["id"]

        # Generate Draft
        res_gen = client.post(f"/api/v1/search-warrant-applications/{swa_id}/generate", headers=self.headers)
        self.assertEqual(res_gen.status_code, 200)
        self.assertIn("DRAFT ONLY -- SUBJECT TO COURT AUTHORIZATION", res_gen.json()["draft_content"])
        print("[PASS] Milestone 5 & 6: Search Warrant Application & Draft Matrix passed")

    def test_03_arrest_warrant_application_and_identity_verification(self):
        """Test creating an arrest warrant application with verified identity."""
        payload = {
            "target_person_id": "p-kittisak",
            "facts_supporting_request": "มีพยานหลักฐานตามสมควรว่าผู้ต้องหาได้ร่วมกันฉ้อโกงประชาชนและนำเข้าข้อมูลคอมพิวเตอร์อันเป็นเท็จ",
            "evidence_ids": ["f05d9e5b-ec1d-4009-bf2f-e8b9fb6cb088", "11b7df3c-6622-48df-9cb9-ef77ba4c28f1"],
            "legal_basis": "ป.วิ.อ. มาตรา 66",
            "risk_factors": "ความเสียหายมูลค่า 1.25 ล้านบาท และผู้ต้องหาเริ่มปิดเพจหลบหนี"
        }
        res = client.post("/api/v1/cases/CASE-142/arrest-warrant-applications", json=payload, headers=self.headers)
        self.assertEqual(res.status_code, 200)
        awa = res.json()["arrest_warrant_application"]
        awa_id = awa["id"]

        # Generate Draft
        res_gen = client.post(f"/api/v1/arrest-warrant-applications/{awa_id}/generate", headers=self.headers)
        self.assertEqual(res_gen.status_code, 200)
        self.assertIn("นายกิตติศักดิ์ วงศ์สวัสดิ์", res_gen.json()["draft_content"])
        print("[PASS] Milestone 7 & 8: Arrest Warrant Application & Identity Verification passed")

    def test_04_document_validation_and_anti_fabrication(self):
        """Test document validation readiness checks."""
        doc_id = "doc-142-01"
        res = client.post(f"/api/v1/documents/{doc_id}/validate", headers=self.headers)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["readiness_status"], "READY_FOR_REVIEW")
        print("[PASS] Milestone 9: Document Validation & Anti-Fabrication passed")

    def test_05_supervisor_approval_and_human_finalization(self):
        """Test supervisor approving document and officer finalizing and locking."""
        doc_id = "doc-142-01"

        # 1. Supervisor Approves
        res_app = client.post(f"/api/v1/documents/{doc_id}/approve", headers=self.sup_headers)
        self.assertEqual(res_app.status_code, 200)
        self.assertEqual(res_app.json()["document_status"], "APPROVED")

        # 2. Finalize & Lock
        res_fin = client.post(f"/api/v1/documents/{doc_id}/finalize", headers=self.headers)
        self.assertEqual(res_fin.status_code, 200)
        self.assertEqual(res_fin.json()["document_status"], "FINAL")
        print("[PASS] Milestone 11: Supervisor Approval & Human Finalization passed")

    def test_06_docx_and_pdf_export_with_hash(self):
        """Test exporting official document with cryptographic SHA-256 hash."""
        doc_id = "doc-142-01"
        payload = {
            "format": "DOCX",
            "purpose": "ส่งธนาคารไทยพาณิชย์เพื่อขออายัดบัญชี",
            "recipient": "ธนาคารไทยพาณิชย์ จำกัด (มหาชน)"
        }
        res = client.post(f"/api/v1/documents/{doc_id}/export", json=payload, headers=self.headers)
        self.assertEqual(res.status_code, 200)
        exp = res.json()["export"]
        self.assertIn("sha256-", exp["file_hash"])
        self.assertIn(".docx", exp["download_url"])
        print("[PASS] Milestone 12: Official Export with Cryptographic Hash passed")

if __name__ == "__main__":
    unittest.main()
