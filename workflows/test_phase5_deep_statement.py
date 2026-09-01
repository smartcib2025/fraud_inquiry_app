# -*- coding: utf-8 -*-
"""
Phase 5 Deep Statement & Interview Copilot Test Suite
Verifies Live Interview Lifecycle, AI Question Generation, Contradiction Checks, Completeness Audit, and Versioned AI Drafting.
"""
import sys
import os
import unittest
from fastapi.testclient import TestClient

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../services/api-gateway')))
from main import app, db

client = TestClient(app)

class TestPhase5DeepStatement(unittest.TestCase):
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

    def test_01_statement_lifecycle_and_live_interview(self):
        """Test starting interview, adding questions/answers, and completing lifecycle."""
        stat_id = "stat-142-01"

        # 1. Start Interview
        res_start = client.post(f"/api/v1/statements/{stat_id}/start", headers=self.headers)
        self.assertEqual(res_start.status_code, 200)
        self.assertEqual(res_start.json()["statement_status"], "IN_PROGRESS")

        # 2. Add Interview Question
        q_payload = {
            "sequence": 3,
            "question_type": "EVIDENCE_BASED",
            "topic": "การตรวจพิสูจน์เวชสำอางค์",
            "question_text": "ท่านได้นำผลิตภัณฑ์ดังกล่าวไปส่งตรวจที่ใด และได้รับผลการตรวจอย่างไร?",
            "purpose": "ยืนยันผลการตรวจหาสารเคมีอันตราย"
        }
        res_q = client.post(f"/api/v1/statements/{stat_id}/questions", json=q_payload, headers=self.headers)
        self.assertEqual(res_q.status_code, 200)
        q_id = res_q.json()["question"]["id"]

        # 3. Record Answer
        ans_payload = {
            "question_id": q_id,
            "sequence": 3,
            "answer_text": "ข้าพเจ้าได้ส่งตัวอย่างเซรั่มให้ห้องปฏิบัติการเอกชนและกรมวิทยาศาสตร์การแพทย์ตรวจ พบสารไฮโดรควิโนนและสารปรอทเกินมาตรฐานอย่างร้ายแรง",
            "answer_type": "VERBATIM"
        }
        res_ans = client.post(f"/api/v1/statements/{stat_id}/answers", json=ans_payload, headers=self.headers)
        self.assertEqual(res_ans.status_code, 200)

        # 4. Complete Interview
        res_comp = client.post(f"/api/v1/statements/{stat_id}/complete", headers=self.headers)
        self.assertEqual(res_comp.status_code, 200)
        self.assertEqual(res_comp.json()["statement_status"], "COMPLETED")
        print("[PASS] Milestone 2 & 3: Statement Lifecycle & Question/Answer Engine passed")

    def test_02_ai_question_generation_and_suggested_status(self):
        """Test AI generating interrogatory questions preserved in SUGGESTED status."""
        stat_id = "stat-142-01"
        res = client.post(f"/api/v1/statements/{stat_id}/ai/questions", headers=self.headers)
        self.assertEqual(res.status_code, 200)
        questions = res.json()["suggested_questions"]
        self.assertGreaterEqual(len(questions), 2)
        self.assertTrue(all(q["status"] == "SUGGESTED" for q in questions))
        self.assertTrue(any("สลิปการโอนเงิน" in q["question_text"] for q in questions))
        print("[PASS] Milestone 4: AI Question Generation & Suggested Status passed")

    def test_03_ai_followup_and_contradiction_detection(self):
        """Test AI detecting contradictions and generating follow-up prompts."""
        stat_id = "stat-142-01"

        # 1. Check Consistency
        res_con = client.post(f"/api/v1/statements/{stat_id}/ai/consistency", headers=self.headers)
        self.assertEqual(res_con.status_code, 200)
        consistency = res_con.json()["consistency"]
        self.assertEqual(consistency["contradictions_found"], 1)

        # 2. Check Follow-up Suggestions
        res_fol = client.post(f"/api/v1/statements/{stat_id}/ai/follow-up", headers=self.headers)
        self.assertEqual(res_fol.status_code, 200)
        followups = res_fol.json()["follow_up_questions"]
        self.assertGreaterEqual(len(followups), 1)
        self.assertTrue(any("เชียงใหม่" in f["question_text"] for f in followups))
        print("[PASS] Milestone 5 & 6: AI Follow-up & Contradiction Detection passed")

    def test_04_ai_completeness_audit(self):
        """Test AI completeness audit checklist."""
        stat_id = "stat-142-01"
        res = client.post(f"/api/v1/statements/{stat_id}/ai/completeness", headers=self.headers)
        self.assertEqual(res.status_code, 200)
        checklist = res.json()["checklist"]
        self.assertGreaterEqual(len(checklist), 4)
        self.assertTrue(any(c["status"] == "MISSING_INFORMATION" for c in checklist))
        print("[PASS] Milestone 8: AI Statement Completeness Audit passed")

    def test_05_ai_statement_draft_and_versioning(self):
        """Test generating official AI draft statement with versioning and no-fabrication rule."""
        stat_id = "stat-142-01"
        res = client.post(f"/api/v1/statements/{stat_id}/ai/draft", json={"template_type": "POLICE_STATEMENT_FORM_1"}, headers=self.headers)
        self.assertEqual(res.status_code, 200)
        draft = res.json()["draft"]
        self.assertIn("AI-ASSISTED DRAFT", draft)
        self.assertIn("1,250,000 บาท", draft)
        self.assertIn("[ข้อมูลยังไม่ครบ / ต้องตรวจสอบ", draft)

        # Verify Statement Version was created
        version = res.json()["version"]
        self.assertEqual(version["statement_id"], stat_id)
        self.assertGreaterEqual(version["version_number"], 1)
        print("[PASS] Milestone 9 & 10: AI Statement Drafting & Version History passed")

    def test_06_supervisor_review_and_approval(self):
        """Test submitting statement for supervisor review and approving."""
        stat_id = "stat-142-01"

        # 1. Submit for Review
        res_sub = client.post(f"/api/v1/statements/{stat_id}/submit-review", headers=self.headers)
        self.assertEqual(res_sub.status_code, 200)
        self.assertEqual(res_sub.json()["statement_status"], "IN_REVIEW")

        # 2. Supervisor Approves
        res_app = client.post(f"/api/v1/statements/{stat_id}/approve", headers=self.sup_headers)
        self.assertEqual(res_app.status_code, 200)
        self.assertEqual(res_app.json()["statement_status"], "APPROVED")
        print("[PASS] Milestone 10: Supervisor Review & Approval Workflow passed")

if __name__ == "__main__":
    unittest.main()
