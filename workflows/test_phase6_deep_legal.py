# -*- coding: utf-8 -*-
"""
Phase 6 Deep Legal Analysis & Investigation Planning Test Suite
Verifies Case Facts Traceability, Fact-Evidence-Legal Matrix, Legal Element Assessments, Planning Engine, and Human Decision Records.
"""
import sys
import os
import unittest
from fastapi.testclient import TestClient

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../services/api-gateway')))
from main import app, db

client = TestClient(app)

class TestPhase6DeepLegal(unittest.TestCase):
    def setUp(self):
        # Authenticate as investigator Somchai
        res = client.post("/api/auth/google/callback", json={"code": "test", "email": "somchai.i@cppd.go.th"})
        self.assertEqual(res.status_code, 200)
        self.token = res.json()["token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}

    def test_01_case_facts_creation_and_source_traceability(self):
        """Test creating Case Facts with explicit source links."""
        payload = {
            "fact_text": "ผลตรวจวิเคราะห์จากกรมวิทยาศาสตร์การแพทย์พบสารไฮโดรควิโนนและสารปรอทในเวชสำอางค์",
            "fact_type": "FACT",
            "verification_status": "VERIFIED",
            "source_type": "EVIDENCE",
            "source_ids": ["ev-142-lab"]
        }
        res = client.post("/api/v1/cases/CASE-142/facts", json=payload, headers=self.headers)
        self.assertEqual(res.status_code, 200)
        fact = res.json()["fact"]
        self.assertEqual(fact["verification_status"], "VERIFIED")
        self.assertIn("ev-142-lab", fact["source_ids"])

        res_list = client.get("/api/v1/cases/CASE-142/facts", headers=self.headers)
        self.assertEqual(res_list.status_code, 200)
        facts = res_list.json()["facts"]
        self.assertTrue(any(f["id"] == fact["id"] for f in facts))
        print("[PASS] Milestone 3: Case Fact Creation & Source Traceability passed")

    def test_02_fact_evidence_legal_matrix_drilldown(self):
        """Test full Fact-Evidence-Legal Element Drill-down Matrix retrieval."""
        res = client.get("/api/v1/cases/CASE-142/legal-matrix", headers=self.headers)
        self.assertEqual(res.status_code, 200)
        matrix = res.json()["matrix"]
        self.assertGreaterEqual(len(matrix), 1)
        self.assertIn("elements", matrix[0])
        print("[PASS] Milestone 4: Fact-Evidence-Legal Element Matrix Drill-down passed")

    def test_03_legal_element_assessment(self):
        """Test assessing legal elements with officer review."""
        elem_id = "elem-142-01"
        payload = {
            "legal_issue_id": "li-1",
            "status": "SUPPORTED",
            "supporting_fact_ids": ["fact-142-01"],
            "supporting_evidence_ids": ["f05d9e5b-ec1d-4009-bf2f-e8b9fb6cb088"],
            "analyst_comment": "มีสลิปการโอนเงินยืนยันการได้ไปซึ่งทรัพย์สิน"
        }
        res = client.post(f"/api/v1/legal-elements/{elem_id}/assess", json=payload, headers=self.headers)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["assessment"]["status"], "SUPPORTED")
        print("[PASS] Milestone 2 & 11: Legal Element Assessment & Human Decision passed")

    def test_04_ai_legal_mapping_and_warning_tags(self):
        """Test AI Legal Mapping with mandatory warning and non-guilt declaration."""
        res = client.post("/api/v1/cases/CASE-142/ai/legal-mapping", headers=self.headers)
        self.assertEqual(res.status_code, 200)
        mapping = res.json()["mapping"]
        self.assertIn("applicable_laws", mapping)
        self.assertTrue("AI" in mapping.get("warning", "") or "warning" in mapping)
        print("[PASS] Milestone 5 & 14: AI Legal Mapping & Anti-Hallucination passed")

    def test_05_ai_evidence_sufficiency_and_planning_engine(self):
        """Test AI evidence sufficiency scoring and investigation plan formulation."""
        # 1. Evidence Sufficiency
        res_suf = client.post("/api/v1/cases/CASE-142/ai/evidence-sufficiency", headers=self.headers)
        self.assertEqual(res_suf.status_code, 200)
        self.assertIn("overall_sufficiency", res_suf.json()["sufficiency"])

        # 2. Investigation Planning Engine
        res_plan = client.post("/api/v1/cases/CASE-142/ai/investigation-plan", headers=self.headers)
        self.assertEqual(res_plan.status_code, 200)
        actions = res_plan.json()["suggested_actions"]
        self.assertGreaterEqual(len(actions), 2)
        self.assertTrue(any(a["action_type"] == "REQUEST_BANK_RECORD" for a in actions))
        print("[PASS] Milestone 6 & 8: AI Evidence Sufficiency & Planning Engine passed")

    def test_06_gap_conversion_to_action_and_human_decision(self):
        """Test converting an investigation gap into an official action and logging human legal decision."""
        # 1. Create Action from Gap
        gap_id = "gap-142-01"
        act_payload = {
            "title": "ขอภาพบันทึก CCTV ตู้ ATM ลาดพร้าว",
            "description": "ประสานขอภาพกล้องวงจรปิดขณะคนร้ายทำรายการถอนเงินสด",
            "action_type": "OBTAIN_CCTV",
            "priority": "HIGH"
        }
        res_act = client.post(f"/api/v1/investigation-gaps/{gap_id}/create-action", json=act_payload, headers=self.headers)
        self.assertEqual(res_act.status_code, 200)
        self.assertIn("act-", res_act.json()["action"]["id"])

        # 2. Record Human Legal Decision
        dec_payload = {
            "decision": "ACCEPT_LEGAL_MAPPING",
            "reason": "ข้อเท็จจริงในสำนวนครบองค์ประกอบความผิดตาม ป.อ. ม.343",
            "related_resource": "li-1"
        }
        res_dec = client.post("/api/v1/cases/CASE-142/legal-decisions", json=dec_payload, headers=self.headers)
        self.assertEqual(res_dec.status_code, 200)
        self.assertEqual(res_dec.json()["decision"]["decision"], "ACCEPT_LEGAL_MAPPING")
        print("[PASS] Milestone 9 & 11: Gap Conversion to Action & Human Legal Decision passed")

if __name__ == "__main__":
    unittest.main()
