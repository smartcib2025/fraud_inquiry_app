# -*- coding: utf-8 -*-
"""
Phase 9 Deep Quality Control & Case Reviewer Test Suite
Verifies Full Case Quality Review, Finding Categorization, Remediation Task Conversion, False Positive & Accepted Risk Handling, Readiness Assessment, and Supervisor Submission Package.
"""
import sys
import os
import unittest
from fastapi.testclient import TestClient

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../services/api-gateway')))
from main import app, db

client = TestClient(app)

class TestPhase9DeepReview(unittest.TestCase):
    def setUp(self):
        # Authenticate as investigator Somchai
        res = client.post("/api/auth/google/callback", json={"code": "test", "email": "somchai.i@cppd.go.th"})
        self.assertEqual(res.status_code, 200)
        self.token = res.json()["token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}

    def test_01_trigger_full_case_quality_review(self):
        """Test running a full quality control case review."""
        payload = {"review_type": "PRE_SUPERVISOR"}
        res = client.post("/api/v1/cases/CASE-142/reviews", json=payload, headers=self.headers)
        self.assertEqual(res.status_code, 200)
        run = res.json()["review_run"]
        findings = res.json()["findings"]
        self.assertEqual(run["status"], "COMPLETED")
        self.assertGreaterEqual(len(findings), 1)
        print("[PASS] Milestone 1 & 2: Full Case Quality Review Run passed")

    def test_02_finding_remediation_task_conversion(self):
        """Test converting a review finding into an actionable remediation task."""
        fnd_id = "fnd-142-02"
        task_payload = {
            "title": "ประสานขอผลตรวจสารเคมีฉบับจริงจากกรมวิทยาศาสตร์การแพทย์",
            "description": "ติดต่อเจ้าหน้าที่เพื่อขอรับหนังสือรับรองฉบับจริงสำหรับประกอบสำนวน"
        }
        res = client.post(f"/api/v1/review-findings/{fnd_id}/create-task", json=task_payload, headers=self.headers)
        self.assertEqual(res.status_code, 200)
        task = res.json()["task"]
        self.assertIn("task-rem-", task["id"])
        self.assertEqual(res.json()["finding_status"], "IN_PROGRESS")
        print("[PASS] Milestone 10: Finding to Remediation Task Conversion passed")

    def test_03_finding_resolution_and_false_positive(self):
        """Test resolving a finding and marking a false positive."""
        # 1. Resolve finding
        fnd_id = "fnd-142-01"
        res_res = client.post(f"/api/v1/review-findings/{fnd_id}/resolve", headers=self.headers)
        self.assertEqual(res_res.status_code, 200)
        self.assertEqual(res_res.json()["finding"]["status"], "RESOLVED")

        # 2. Mark False Positive
        fp_payload = {"reason": "พยานบุคคลยืนยันว่าผู้เสียหายได้ติดต่อผ่านเพจจริง ไม่ถือเป็นข้อขัดแย้ง"}
        res_fp = client.post(f"/api/v1/review-findings/{fnd_id}/false-positive", json=fp_payload, headers=self.headers)
        self.assertEqual(res_fp.status_code, 200)
        self.assertEqual(res_fp.json()["finding"]["status"], "FALSE_POSITIVE")
        print("[PASS] Milestone 10: Finding Resolution & False Positive passed")

    def test_04_accepted_risk_with_human_authority(self):
        """Test accepting residual risk with commander authorization."""
        fnd_id = "fnd-142-02"
        ar_payload = {
            "reason": "มีผลตรวจไฟล์ดิจิทัลพร้อมลายมือชื่ออิเล็กทรอนิกส์แล้ว ยอมรับความเสี่ยงเพื่อเสนอสำนวนตามกำหนดเวลา",
            "authorized_by": "พ.ต.อ. อนงค์ บังคับการ"
        }
        res_ar = client.post(f"/api/v1/review-findings/{fnd_id}/accept-risk", json=ar_payload, headers=self.headers)
        self.assertEqual(res_ar.status_code, 200)
        self.assertEqual(res_ar.json()["finding"]["status"], "ACCEPTED_RISK")
        print("[PASS] Milestone 10: Accepted Risk with Human Authority passed")

    def test_05_case_readiness_assessment(self):
        """Test evaluating overall pre-trial case readiness."""
        res = client.post("/api/v1/cases/CASE-142/readiness-check", headers=self.headers)
        self.assertEqual(res.status_code, 200)
        assessment = res.json()["readiness_assessment"]
        self.assertEqual(assessment["readiness_status"], "READY_FOR_SUPERVISOR_REVIEW")
        self.assertEqual(assessment["source_coverage"], "100%")
        print("[PASS] Milestone 12: Case Readiness Assessment passed")

    def test_06_supervisor_submission_package(self):
        """Test submitting the complete investigation package to the supervisor."""
        sub_payload = {
            "report_id": "rep-142-01",
            "notes": "สำนวนการสอบสวนผ่านการตรวจประเมินคุณภาพเรียบร้อย เสนอเพื่อโปรดพิจารณา"
        }
        res = client.post("/api/v1/cases/CASE-142/submit-supervisor-review", json=sub_payload, headers=self.headers)
        self.assertEqual(res.status_code, 200)
        pkg = res.json()["package"]
        self.assertEqual(pkg["status"], "SUBMITTED_TO_SUPERVISOR")
        print("[PASS] Milestone 12: Supervisor Review Submission Package passed")

if __name__ == "__main__":
    unittest.main()
