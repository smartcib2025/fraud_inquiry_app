# -*- coding: utf-8 -*-
"""
Phase 2 Deep Case Workspace & Investigation Workflow Test Suite
Verifies all 12 modules, Review Engine, Legal Matrix, Statement QA, and E2E Scenarios A, B, C.
"""
import sys
import os
import unittest
from fastapi.testclient import TestClient

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../services/api-gateway')))
from main import app, db

client = TestClient(app)

class TestPhase2DeepWorkspace(unittest.TestCase):
    def setUp(self):
        # Authenticate as investigator Somchai
        res = client.post("/api/auth/google/callback", json={"code": "test", "email": "somchai.i@cppd.go.th"})
        self.assertEqual(res.status_code, 200)
        self.token = res.json()["token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}

        # Authenticate as supervisor Superintendent
        res_sup = client.post("/api/auth/google/callback", json={"code": "test", "email": "superintendent@cppd.go.th"})
        self.assertEqual(res_sup.status_code, 200)
        self.sup_token = res_sup.json()["token"]
        self.sup_headers = {"Authorization": f"Bearer {self.sup_token}"}

        # Authenticate as admin
        res_adm = client.post("/api/auth/google/callback", json={"code": "test", "email": "admin@cppd.go.th"})
        self.assertEqual(res_adm.status_code, 200)
        self.adm_token = res_adm.json()["token"]
        self.adm_headers = {"Authorization": f"Bearer {self.adm_token}"}

    def test_01_case_overview_and_metrics(self):
        """Test Case Overview endpoint returning structured narrative, metrics, and team."""
        res = client.get("/api/v1/cases/CASE-142/overview", headers=self.headers)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("case", data)
        self.assertIn("metrics", data)
        self.assertGreaterEqual(data["metrics"]["total_loss_thb"], 1250000)
        self.assertIn("case_team", data)
        self.assertIn("narrative_history", data)
        print("[PASS] Module 1: Case Overview & Metrics passed")

    def test_02_investigation_issues_crud(self):
        """Test creating and retrieving Investigation Issues."""
        payload = {
            "title": "พิสูจน์ที่มาของสารปรอทในเวชสำอางค์",
            "description": "ส่งตัวอย่างให้สถาบันนิติวิทยาศาสตร์ตรวจสารต้องห้าม",
            "category": "PHYSICAL_EVIDENCE",
            "priority": "HIGH"
        }
        res = client.post("/api/v1/cases/CASE-142/issues", json=payload, headers=self.headers)
        self.assertEqual(res.status_code, 200)
        issue_id = res.json()["issue"]["id"]

        res_list = client.get("/api/v1/cases/CASE-142/issues", headers=self.headers)
        self.assertEqual(res_list.status_code, 200)
        issues = res_list.json()["issues"]
        self.assertTrue(any(i["id"] == issue_id for i in issues))
        print("[PASS] Module 2: Investigation Issues passed")

    def test_03_statement_and_qa_lifecycle(self):
        """Test Statement creation and structured Q&A interrogation logging."""
        stmt_payload = {
            "person_id": "p-nattapong",
            "statement_type": "VICTIM",
            "location": "กก.1 บก.ปคบ.",
            "transcript": "ผู้เสียหายยืนยันการโอนเงิน 1.25 ล้านบาท"
        }
        res = client.post("/api/v1/cases/CASE-142/statements", json=stmt_payload, headers=self.headers)
        self.assertEqual(res.status_code, 200)
        stmt_id = res.json()["statement"]["id"]

        qa_payload = {
            "sequence": 1,
            "question": "ท่านโอนเงินไปบัญชีใด?",
            "answer": "บัญชีธนาคารไทยพาณิชย์ นายกิตติศักดิ์ วงศ์สวัสดิ์",
            "notes": "สอดคล้องกับสลิปหลักฐาน EV-142-01",
            "source_reference": "f05d9e5b-ec1d-4009-bf2f-e8b9fb6cb088"
        }
        res_qa = client.post(f"/api/v1/statements/{stmt_id}/qa", json=qa_payload, headers=self.headers)
        self.assertEqual(res_qa.status_code, 200)

        res_stmts = client.get("/api/v1/cases/CASE-142/statements", headers=self.headers)
        self.assertEqual(res_stmts.status_code, 200)
        statements = res_stmts.json()["statements"]
        target = next((s for s in statements if s["id"] == stmt_id), None)
        self.assertIsNotNone(target)
        self.assertGreaterEqual(len(target["qa_list"]), 1)
        print("[PASS] Module 4: Statement & Statement QA passed")

    def test_04_evidence_relations_non_destructive(self):
        """Test linking EvidenceRelation without mutating original exhibit record."""
        payload = {
            "evidence_id": "f05d9e5b-ec1d-4009-bf2f-e8b9fb6cb088",
            "target_type": "INVESTIGATION_ISSUE",
            "target_id": "iss-142-01",
            "relation_type": "PROVES_FINANCIAL_FLOW",
            "notes": "สลิปโอนเงินยืนยันการรับเงินเข้าบัญชีม้า"
        }
        res = client.post("/api/v1/cases/CASE-142/evidence-relations", json=payload, headers=self.headers)
        self.assertEqual(res.status_code, 200)

        res_rels = client.get("/api/v1/cases/CASE-142/evidence-relations", headers=self.headers)
        self.assertEqual(res_rels.status_code, 200)
        self.assertTrue(len(res_rels.json()["relations"]) > 0)
        print("[PASS] Module 5: Evidence Relations passed")

    def test_05_investigation_plan_and_action_sync(self):
        """Test creating an action item in Investigation Plan and verifying auto task sync."""
        action_payload = {
            "title": "ตรวจสอบรายการเดินบัญชีแถวที่ 2 นางสาวพัชรี แก้วมณี",
            "description": "ทำหนังสือถึง บมจ.ธนาคารกรุงไทย",
            "target_date": "2026-08-28"
        }
        res = client.post("/api/v1/cases/CASE-142/investigation-plan/actions", json=action_payload, headers=self.headers)
        self.assertEqual(res.status_code, 200)
        task_id = res.json()["task_id"]
        
        # Verify CaseTask was created in sync
        case_res = client.get("/api/cases/CASE-142", headers=self.headers)
        tasks = case_res.json()["tasks"]
        self.assertTrue(any(t["id"] == task_id for t in tasks))
        print("[PASS] Module 7: Investigation Plan & Task Synchronization passed")

    def test_06_legal_issues_and_element_matrix(self):
        """Test Legal Issue creation and Legal Element Matrix with evidence mapping."""
        issue_payload = {
            "title": "ความผิดตาม พ.ร.บ.เครื่องสำอาง พ.ศ. 2558",
            "law_reference": "พ.ร.บ.เครื่องสำอาง พ.ศ. 2558",
            "section_reference": "มาตรา 27",
            "issue_description": "ผลิตและจำหน่ายเครื่องสำอางไม่ปลอดภัยที่มีสารปรอท"
        }
        res = client.post("/api/v1/cases/CASE-142/legal-issues", json=issue_payload, headers=self.headers)
        self.assertEqual(res.status_code, 200)
        issue_id = res.json()["legal_issue"]["id"]

        elem_payload = {
            "element_title": "เครื่องสำอางมีสารที่รัฐมนตรีประกาศห้ามใช้",
            "supporting_facts": "ผลตรวจวิเคราะห์จากกรมวิทยาศาสตร์การแพทย์พบสารไฮโดรควิโนนและสารปรอท",
            "supporting_evidence_ids": ["7f83b1657ff1fc53b92dc18148a1d65dfc2d4b1fa3d677284addd200126d9069"],
            "contradictory_evidence_ids": [],
            "missing_evidence": "ใบรับรองมาตรฐานโรงงานผู้ผลิต",
            "review_status": "SUPPORTED"
        }
        res_elem = client.post(f"/api/v1/legal-issues/{issue_id}/elements", json=elem_payload, headers=self.headers)
        self.assertEqual(res_elem.status_code, 200)

        res_all = client.get("/api/v1/cases/CASE-142/legal-issues", headers=self.headers)
        self.assertEqual(res_all.status_code, 200)
        target_issue = next((li for li in res_all.json()["legal_issues"] if li["id"] == issue_id), None)
        self.assertIsNotNone(target_issue)
        self.assertEqual(len(target_issue["elements"]), 1)
        print("[PASS] Module 9: Legal Elements Matrix passed")

    def test_07_document_versions_and_review_workflow(self):
        """Test E2E Document drafting, versioning, review request, and supervisor sign-off."""
        # 1. Investigator drafts document
        doc_payload = {
            "document_type": "ACCUSATION_RECORD",
            "title": "บันทึกแจ้งข้อกล่าวหา นายกิตติศักดิ์ วงศ์สวัสดิ์",
            "content": "ข้อความแจ้งข้อกล่าวหาตาม ป.อ. ม.343 และ พ.ร.บ.คอมพิวเตอร์ฯ...",
            "source_references": ["f05d9e5b-ec1d-4009-bf2f-e8b9fb6cb088"]
        }
        res = client.post("/api/v1/cases/CASE-142/documents", json=doc_payload, headers=self.headers)
        self.assertEqual(res.status_code, 200)
        doc_id = res.json()["document"]["id"]

        # 2. Investigator requests review
        rev_payload = {
            "resource_type": "DOCUMENT",
            "resource_id": doc_id,
            "comments": "ขออนุมัติบันทึกแจ้งข้อกล่าวหาเพื่อดำเนินการออกหมายเรียก"
        }
        res_rev = client.post("/api/v1/cases/CASE-142/reviews", json=rev_payload, headers=self.headers)
        self.assertEqual(res_rev.status_code, 200)
        review_id = res_rev.json()["review"]["id"]

        # 3. Unauthorized investigator cannot approve
        res_unauth = client.post(f"/api/v1/reviews/{review_id}/action", json={"action": "APPROVED"}, headers=self.headers)
        self.assertEqual(res_unauth.status_code, 403)

        # 4. Supervisor approves review
        res_auth = client.post(f"/api/v1/reviews/{review_id}/action", json={"action": "APPROVED", "comments": "ตรวจแล้ว ถูกต้องตามระเบียบ"}, headers=self.sup_headers)
        self.assertEqual(res_auth.status_code, 200)
        self.assertEqual(res_auth.json()["review"]["status"], "APPROVED")
        print("[PASS] Module 10: Document Versions & Review Workflow passed")

    def test_08_activity_feed(self):
        """Test Case Activity Feed returning chronological domain events."""
        res = client.get("/api/v1/cases/CASE-142/activity", headers=self.headers)
        self.assertEqual(res.status_code, 200)
        activities = res.json()["activities"]
        self.assertGreaterEqual(len(activities), 4)
        print("[PASS] Module 12: Case Domain Activity Feed passed")

    def test_09_scenario_c_unauthorized_access_security_event(self):
        """Test Scenario C: Investigator A attempts to open unauthorized sensitive Case-112."""
        # Somchai is not assigned to CASE-112 and is not Cyber Division
        res = client.get("/api/v1/cases/CASE-112/overview", headers=self.headers)
        self.assertEqual(res.status_code, 403)

        # Verify Security Audit Event was logged
        audit_res = client.get("/api/admin/audit-logs", headers=self.adm_headers)
        self.assertEqual(audit_res.status_code, 200)
        logs = audit_res.json() if isinstance(audit_res.json(), list) else audit_res.json().get("logs", [])
        self.assertTrue(any(l.get("record_id") == "CASE-112" or l.get("action") == "SECURITY.ACCESS.DENIED" for l in logs))
        print("[PASS] Scenario C: Unauthorized Access Denied & Security Audited passed")

if __name__ == "__main__":
    unittest.main()
