# -*- coding: utf-8 -*-
"""
Phase 11 Deep Supervisor Review, Command Approval & Case Governance Test Suite
Verifies Supervisor Review Submissions, AI Supervisor Briefing, Direction Lifecycle, Return for Correction & Resubmission, Version-Bound Approvals, Separation of Duties, Recusal, Delegation, and Case Closure Requests.
"""
import sys
import os
import unittest
from fastapi.testclient import TestClient

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../services/api-gateway')))
from main import app, db

client = TestClient(app)

class TestPhase11DeepGovernance(unittest.TestCase):
    def setUp(self):
        # Authenticate as investigator Somchai
        res = client.post("/api/auth/google/callback", json={"code": "test", "email": "somchai.i@cppd.go.th"})
        self.assertEqual(res.status_code, 200)
        self.token = res.json()["token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}

        # Authenticate as Superintendent
        res_sup = client.post("/api/auth/google/callback", json={"code": "test", "email": "superintendent@cppd.go.th"})
        self.assertEqual(res_sup.status_code, 200)
        self.sup_token = res_sup.json()["token"]
        self.sup_headers = {"Authorization": f"Bearer {self.sup_token}"}

    def test_01_submit_and_get_supervisor_review(self):
        """Test submitting case for supervisor review and fetching review detail with AI brief."""
        payload = {
            "review_type": "INVESTIGATION_REPORT",
            "review_level": "SUPERINTENDENT",
            "report_version_id": "rep-142-01",
            "notes": "สำนวนและรายงานการสอบสวนพร้อมตรวจเสนอ ผกก.1 บก.ปคบ."
        }
        res_sub = client.post("/api/v1/cases/CASE-142/supervisor-reviews", json=payload, headers=self.headers)
        self.assertEqual(res_sub.status_code, 200)
        rev = res_sub.json()["review"]
        self.assertEqual(rev["status"], "SUBMITTED")
        srev_id = rev["id"]

        # Fetch detail
        res_get = client.get(f"/api/v1/supervisor-reviews/{srev_id}", headers=self.sup_headers)
        self.assertEqual(res_get.status_code, 200)
        data = res_get.json()
        self.assertEqual(data["review"]["id"], srev_id)
        self.assertIn("items_requiring_attention", data["ai_supervisor_brief"])
        print("[PASS] Milestone 2 & 4: Supervisor Review Submission & AI Briefing passed")

    def test_02_supervisor_comments_and_directions(self):
        """Test adding comments and issuing supervisor directions."""
        srev_id = "srev-142-01"
        
        # 1. Add comment
        com_payload = {
            "resource_type": "REPORT_SECTION",
            "resource_id": "sec-facts",
            "comment": "ให้เพิ่มเติมรายละเอียดวันเวลาที่ตรวจยึดของกลางให้ตรงกับบันทึกการตรวจยึด",
            "severity": "HIGH"
        }
        res_com = client.post(f"/api/v1/supervisor-reviews/{srev_id}/comments", json=com_payload, headers=self.sup_headers)
        self.assertEqual(res_com.status_code, 200)
        self.assertEqual(res_com.json()["comment"]["status"], "OPEN")

        # 2. Issue direction
        dir_payload = {
            "title": "สอบปากคำเจ้าหน้าที่กรมวิทยาศาสตร์การแพทย์ผู้ตรวจพิสูจน์",
            "description": "เพื่อยืนยันชนิดและปริมาณสารอันตรายที่ผสมในเครื่องสำอาง",
            "direction_type": "REINTERVIEW",
            "priority": "HIGH"
        }
        res_dir = client.post("/api/v1/cases/CASE-142/directions", json=dir_payload, headers=self.sup_headers)
        self.assertEqual(res_dir.status_code, 200)
        self.assertEqual(res_dir.json()["direction"]["status"], "ISSUED")
        print("[PASS] Milestone 5: Supervisor Comments & Directions passed")

    def test_03_direction_acknowledgment_and_completion(self):
        """Test acknowledging direction and submitting completion with evidence link."""
        sdir_id = "sdir-142-01"

        # 1. Acknowledge
        res_ack = client.post(f"/api/v1/directions/{sdir_id}/acknowledge", headers=self.headers)
        self.assertEqual(res_ack.status_code, 200)
        self.assertEqual(res_ack.json()["direction"]["status"], "ACKNOWLEDGED")

        # 2. Complete
        comp_payload = {
            "completion_note": "สอบปากคำเภสัชกรผู้ตรวจพิสูจน์เรียบร้อยและบันทึกเป็นคำให้การพยานแล้ว",
            "linked_statement_ids": ["stat-142-expert"]
        }
        res_comp = client.post(f"/api/v1/directions/{sdir_id}/complete", json=comp_payload, headers=self.headers)
        self.assertEqual(res_comp.status_code, 200)
        self.assertEqual(res_comp.json()["direction"]["status"], "COMPLETED")
        print("[PASS] Milestone 5: Direction Acknowledgment & Completion passed")

    def test_04_return_for_correction_and_resubmission(self):
        """Test returning a review for correction and subsequent resubmission."""
        srev_id = "srev-142-01"

        # 1. Supervisor Returns Case
        ret_payload = {
            "reason": "พยานเอกสารยังไม่ครบถ้วนตามข้อสังเกต",
            "required_corrections": ["แนบเอกสารรับรองผลตรวจพิสูจน์", "แก้ไขยอดความเสียหายในรายงาน"]
        }
        res_ret = client.post(f"/api/v1/supervisor-reviews/{srev_id}/return", json=ret_payload, headers=self.sup_headers)
        self.assertEqual(res_ret.status_code, 200)
        self.assertEqual(res_ret.json()["review"]["status"], "RETURNED")

        # 2. Investigator Resubmits
        resub_payload = {
            "changes_made": "ได้แนบเอกสารรับรองผลตรวจและปรับปรุงยอดความเสียหายในรายงานฉบับ v2 เรียบร้อยแล้ว",
            "directions_addressed": ["sdir-142-01"]
        }
        res_resub = client.post(f"/api/v1/supervisor-reviews/{srev_id}/resubmit", json=resub_payload, headers=self.headers)
        self.assertEqual(res_resub.status_code, 200)
        self.assertEqual(res_resub.json()["review"]["status"], "RESUBMITTED")
        print("[PASS] Milestone 6: Return for Correction & Resubmission passed")

    def test_05_version_bound_approval_and_separation_of_duties(self):
        """Test version-bound formal approval request and separation of duties enforcement."""
        req_payload = {
            "case_id": "CASE-142",
            "resource_type": "INVESTIGATION_REPORT",
            "resource_id": "rep-142-01",
            "resource_version": "v2.0",
            "resource_hash": "b732c4e512404a011733cfb7b190d62c65bf0bcda32b57b277d9ad9f146e",
            "approver_role": "SUPERINTENDENT"
        }
        res_req = client.post("/api/v1/approval-requests", json=req_payload, headers=self.headers)
        self.assertEqual(res_req.status_code, 200)
        appr_id = res_req.json()["approval_request"]["id"]

        # 1. Investigator (Maker) tries to approve own request -> Expect 403 Separation of Duties
        act_payload = {"decision_reason": "อนุมัติรายงานการสอบสวน", "authority_role": "INVESTIGATOR"}
        res_self = client.post(f"/api/v1/approval-requests/{appr_id}/approve", json=act_payload, headers=self.headers)
        self.assertEqual(res_self.status_code, 403)
        self.assertIn("Separation of Duties", res_self.json()["detail"])

        # 2. Superintendent Approves -> Expect Success
        res_ok = client.post(f"/api/v1/approval-requests/{appr_id}/approve", json=act_payload, headers=self.sup_headers)
        self.assertEqual(res_ok.status_code, 200)
        self.assertEqual(res_ok.json()["approval_request"]["status"], "APPROVED")
        print("[PASS] Milestone 7, 8 & 9: Version-Bound Approval & Separation of Duties passed")

    def test_06_recusal_delegation_and_case_closure(self):
        """Test reviewer conflict recusal, authority delegation, and case closure request."""
        # 1. Recusal
        rec_payload = {
            "review_id": "srev-142-01",
            "case_id": "CASE-142",
            "conflict_reason": "มีความเกี่ยวข้องทางเครือญาติกับหนึ่งในพยาน",
            "reassigned_reviewer_id": "superintendent@cppd.go.th"
        }
        res_rec = client.post("/api/v1/governance/recusal", json=rec_payload, headers=self.headers)
        self.assertEqual(res_rec.status_code, 200)
        self.assertEqual(res_rec.json()["status"], "success")

        # 2. Delegation
        del_payload = {
            "delegated_to_id": "superintendent@cppd.go.th",
            "scope": "SUPERVISOR_REVIEW",
            "start_time": "2026-08-16T08:00:00Z",
            "end_time": "2026-08-25T18:00:00Z",
            "authority_limit": "APPROVE_INVESTIGATION_REPORTS",
            "reason": "ไปราชการต่างจังหวัด มอบหมายให้ปฏิบัติหน้าที่แทน"
        }
        res_del = client.post("/api/v1/governance/delegate", json=del_payload, headers=self.sup_headers)
        self.assertEqual(res_del.status_code, 200)
        self.assertEqual(res_del.json()["status"], "success")

        # 3. Case Closure Request
        cls_payload = {
            "reason": "สรุปสำนวนการสอบสวนสั่งฟ้องผู้ต้องหา ส่งตัวพร้อมสำนวนให้อัยการเรียบร้อย",
            "report_version_id": "rep-142-01"
        }
        res_cls = client.post("/api/v1/cases/CASE-142/closure-request", json=cls_payload, headers=self.headers)
        self.assertEqual(res_cls.status_code, 200)
        self.assertEqual(res_cls.json()["closure_request"]["status"], "PENDING_SUPERVISOR_APPROVAL")
        print("[PASS] Milestone 10 & 11: Recusal, Delegation & Case Closure Request passed")

if __name__ == "__main__":
    unittest.main()
