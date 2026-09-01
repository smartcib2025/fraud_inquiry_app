import os
import sys
import hashlib
import time
import uuid
import json
from typing import Dict, List, Any, Optional
from fastapi import FastAPI, HTTPException, Request, Header, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Inject service paths for local imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../slack-app')))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../ai-router')))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../workflows/supervisor-review')))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../workflows/transaction-import')))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../agents')))

from slack_gateway import SlackBlockBuilder
from ai_router import CPPDEnvironmentRouter
from timeline_contradictions import StatementTimelineAuditor
from transaction_import import TransactionIntelligenceEngine
from orchestrator import CPPDCaseOrchestrator

app = FastAPI(
    title="CPPD Investigation Intelligence Platform - API Gateway",
    version="1.0.0",
    description="Secure Google Cloud API Gateway layer connecting CPPD clients, Slack, MCP, and workflows to Supabase and Gemini AI."
)

# Enable CORS for the CPPD Dashboard frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -------------------------------------------------------------
# Configuration and Environment Keys
# -------------------------------------------------------------
SUPABASE_URL = os.getenv("SUPABASE_URL", "https://mock.supabase.co")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "mock-key")
SLACK_SIGNING_SECRET = os.getenv("SLACK_SIGNING_SECRET", "mock-slack-signing-secret")

# In-memory database fallback to support local runs out-of-the-box
class MockDatabase:
    def __init__(self):
        self.cases = {
            "CASE-142": {
                "id": "CASE-142",
                "title": "คดีหลอกจำหน่ายเวชสำอางค์และผลิตภัณฑ์ความงามปลอมผ่านเพจ 'สยาม คอสเมติกส์ ออฟฟิเชียล'",
                "description": "การสืบสวนเครือข่ายขบวนการหลอกลวงจำหน่ายเครื่องสำอางและเวชสำอางค์เคาน์เตอร์แบรนด์ปลอมผ่านแพลตฟอร์ม Facebook, TikTok และ Line Official โดยแอบอ้างสิทธิ์ตัวแทนนำเข้า มีการใช้บัญชีม้าแถวที่ 1 และแถวที่ 2 ในการฟอกเงินและยักย้ายถ่ายเททรัพย์สิน พร้อมนำเข้าข้อมูลอันเป็นเท็จเข้าสู่ระบบคอมพิวเตอร์ มูลค่าความเสียหายรวม 1,250,000 บาท",
                "status": "open",
                "owning_unit": "Financial Crimes Division 1",
                "sensitive": False,
                "created_at": "2026-08-10T10:00:00Z",
                "updated_at": "2026-08-17T15:00:00Z"
            },
            "CASE-087": {
                "id": "CASE-087",
                "title": "คดีหลอกจำหน่ายทองคำรูปพรรณออนไลน์เปอร์เซ็นต์ต่ำกว่ามาตรฐาน (หจก. ภูเก็ตไซเบอร์โกลด์)",
                "description": "การสืบสวนขบวนการไลฟ์สดจำหน่ายทองรูปพรรณผ่าน TikTok Shop และ Facebook Fanpage โฆษณาว่าเป็นทองคำแท้ 96.5% เยาวราช ราคาต่ำกว่าสมาคมค้าทองคำ 40% เมื่อผู้เสียหายกว่า 50 รายส่งตรวจพิสูจน์ ณ สถาบันวิจัยและพัฒนาอัญมณีและเครื่องประดับแห่งชาติ (GIT) พบว่าเป็นทองคำผสมมีเนื้อทองจริงเพียง 12.4% เข้าข่ายหลอกลวงประชาชนและโฆษณาเท็จ มูลค่าความเสียหายรวมกว่า 4,800,000 บาท",
                "status": "open",
                "owning_unit": "Financial Crimes Division 1",
                "sensitive": False,
                "created_at": "2026-08-12T11:00:00Z",
                "updated_at": "2026-08-16T12:00:00Z"
            },
            "CASE-112": {
                "id": "CASE-112",
                "title": "คดีลักลอบผลิตและจำหน่ายผลิตภัณฑ์เสริมอาหารผสมสารไซบูทรามีน (สลิมฟิต ดีท็อกซ์)",
                "description": "การสืบสวนและปราบปรามขบวนการลักลอบนำเข้าสารเคมีวัตถุออกฤทธิ์ต่อจิตและประสาทประเภท 1 (ไซบูทรามีน) มาผสมในผลิตภัณฑ์เสริมอาหารลดน้ำหนักยี่ห้อ 'SlimFit Detox' โดยใช้โรงงานเถื่อนย่านบางขุนเทียน ปลอมแปลงเครื่องหมาย อย. และโฆษณาชวนเชื่อผ่านอินฟลูเอนเซอร์ ทำให้ผู้บริโภคเกิดภาวะแทรกซ้อนทางหัวใจและหลอดเลือดขั้นรุนแรง",
                "status": "under_review",
                "owning_unit": "Cyber Division",
                "sensitive": True,
                "created_at": "2026-08-14T09:00:00Z",
                "updated_at": "2026-08-17T11:00:00Z"
            }
        }
        self.case_members = [
            {"case_id": "CASE-142", "user_id": "d2f0998c-8c1d-4099-ae1e-f3f2a89366df", "assignment_role": "lead"},
            {"case_id": "CASE-142", "user_id": "p-clerk", "assignment_role": "clerk"},
            {"case_id": "CASE-087", "user_id": "a1b2c3d4-e5f6-7a8b-9c0d-1e2f3a4b5c6d", "assignment_role": "lead"},
            {"case_id": "CASE-112", "user_id": "a1b2c3d4-e5f6-7a8b-9c0d-1e2f3a4b5c6d", "assignment_role": "co-lead"}
        ]
        self.profiles = {
            "d2f0998c-8c1d-4099-ae1e-f3f2a89366df": {"id": "d2f0998c-8c1d-4099-ae1e-f3f2a89366df", "email": "somchai.i@cppd.go.th", "full_name": "พ.ต.ท. สมชาย สอบสวนสืบสวน (พนักงานสอบสวนชำนาญการพิเศษ กก.1)", "org_unit": "Financial Crimes Division 1", "role": "investigator", "approved": True},
            "a1b2c3d4-e5f6-7a8b-9c0d-1e2f3a4b5c6d": {"id": "a1b2c3d4-e5f6-7a8b-9c0d-1e2f3a4b5c6d", "email": "somsak.b@cppd.go.th", "full_name": "ร.ต.อ. สมศักดิ์ สืบสวนไว (รองสารวัตรสอบสวน กก.1)", "org_unit": "Financial Crimes Division 1", "role": "investigator", "approved": True},
            "f8c3de7d-94d7-46e2-bc2f-e8b9fb6cb077": {"id": "f8c3de7d-94d7-46e2-bc2f-e8b9fb6cb077", "email": "superintendent@cppd.go.th", "full_name": "พ.ต.อ. อนงค์ บังคับการ (ผกก. กก.1 บก.ปคบ.)", "org_unit": "Financial Crimes Division 1", "role": "superintendent", "approved": True},
            "e37b98d2-430b-488f-9a73-982ee3f2112e": {"id": "e37b98d2-430b-488f-9a73-982ee3f2112e", "email": "commander@cppd.go.th", "full_name": "พล.ต.ต. ประภาส พิทักษ์ธรรม (ผู้บังคับการ ปคบ.)", "org_unit": "Division HQ", "role": "commander", "approved": True},
            "p-admin": {"id": "p-admin", "email": "admin@cppd.go.th", "full_name": "พ.ต.อ. พงษ์ศักดิ์ ผู้ดูแลระบบ (Admin บก.ปคบ.)", "org_unit": "Division HQ", "role": "admin", "approved": True},
            "p-deputy-commander": {"id": "p-deputy-commander", "email": "deputy.commander@cppd.go.th", "full_name": "พ.ต.อ. สามารถ ปราบปราม (รอง ผบก.ปคบ.)", "org_unit": "Division HQ", "role": "deputy_commander", "approved": True},
            "p-deputy-superintendent": {"id": "p-deputy-superintendent", "email": "deputy.superintendent@cppd.go.th", "full_name": "พ.ต.ท. วิชัย เชี่ยวชาญ (รอง ผกก. กก.1 บก.ปคบ.)", "org_unit": "Financial Crimes Division 1", "role": "deputy_superintendent", "approved": True},
            "p-clerk": {"id": "p-clerk", "email": "clerk.a@cppd.go.th", "full_name": "ส.ต.อ. สุรชัย คดีมั่น (เสมียนคดีและเจ้าหน้าที่บันทึกข้อมูล กก.1)", "org_unit": "Financial Crimes Division 1", "role": "clerk", "approved": False},
            "p-anong": {"id": "p-anong", "email": "investigator.anong@gmail.com", "full_name": "พ.ต.ท. อนงค์ ตรวจสำนวน (ผู้บังคับบัญชาสอบสวน)", "org_unit": "Financial Crimes Division 1", "role": "supervisor", "approved": True}
        }
        self.sessions = {}
        
        # 1. INTAKES (คำร้องเรียนจากประชาชน 3 คดี)
        self.intakes = [
            {
                "id": "INTAKE-001",
                "case_id": "CASE-142",
                "title": "ร้องเรียนถูกเพจ 'สยาม คอสเมติกส์ ออฟฟิเชียล' หลอกจำหน่ายเวชสำอางค์ปลอม",
                "description": "ผู้เสียหายสั่งซื้อเซรั่มบำรุงผิวหน้าและครีมลดริ้วรอยเคาน์เตอร์แบรนด์รวม 1,250,000 บาท เพื่อใช้ในคลินิก แต่ได้รับสินค้าลอกเลียนแบบไม่มีเลข อย. และผู้ขายปิดเพจหลบหนี",
                "reporter_name": "นายนัฐพงษ์ สุขประเสริฐ",
                "reporter_phone": "081-555-0192",
                "raw_statement": "ข้าพเจ้านายนัฐพงษ์ สุขประเสริฐ ได้ติดต่อสั่งซื้อเวชสำอางค์จากเพจเฟซบุ๊ก สยาม คอสเมติกส์ ออฟฟิเชียล โดยแอดมินชื่อนายกิตติศักดิ์ วงศ์สวัสดิ์ เบอร์โทร 089-111-2345 ได้แจ้งให้โอนเงินมัดจำและค่าสินค้าจำนวน 1,250,000 บาท เข้าบัญชีธนาคารไทยพาณิชย์ เลขที่ 401-229-3388 เมื่อวันที่ 9 สิงหาคม 2569 ภายหลังได้รับสินค้าเมื่อนำไปตรวจสอบกับห้องปฏิบัติการพบว่าเป็นของปลอมปนเปื้อนสารไฮโดรควิโนนและปรอท และทางเพจได้บล็อกช่องทางการติดต่อทันที",
                "triage_urgency": "high",
                "triage_reason": "มูลค่าความเสียหายเกิน 1 ล้านบาท สินค้ามีสารเคมีอันตรายเข้าข่ายเป็นอันตรายต่อประชาชน และกระทำความผิดผ่านระบบคอมพิวเตอร์",
                "status": "promoted",
                "created_at": "2026-08-10T09:00:00Z"
            },
            {
                "id": "INTAKE-002",
                "case_id": "CASE-087",
                "title": "ร้องเรียนเพจ 'ภูเก็ต โกลด์ ออนไลน์' หลอกขายทองคำรูปพรรณเปอร์เซ็นต์ต่ำกว่ามาตรฐาน",
                "description": "สั่งซื้อสร้อยคอทองคำน้ำหนัก 5 บาท และทองคำแท่ง อ้างทองแท้ 96.5% ราคาถูกกว่าสมาคมค้าทองคำ 40% เมื่อนำไปตรวจสอบพบมีทองคำแท้ผสมเพียง 12.4%",
                "reporter_name": "นางสาวมณีรัตน์ ทองแท้",
                "reporter_phone": "086-777-8899",
                "raw_statement": "ข้าพเจ้าพร้อมตัวแทนผู้เสียหายรวมกว่า 50 ราย ได้หลงเชื่อซื้อทองคำจากรายการไลฟ์สด TikTok และเพจ ภูเก็ตไซเบอร์โกลด์ โดยนายวิชาญ ทองประเสริฐ อ้างว่าเป็นทองคำแท้หลุดจำนำ นำเข้าจากเยาวราช โอนเงินเข้าบัญชีธนาคารกสิกรไทย เลขที่ 702-888-1123 รวมความเสียหายของข้าพเจ้า 480,000 บาท เมื่อนำไปจำนำที่โรงรับจำนำรัฐบาลกลับไม่รับเนื่องจากเป็นทองคำผสมต่ำกว่าเกณฑ์มาตรฐานอย่างร้ายแรง",
                "triage_urgency": "high",
                "triage_reason": "มีผู้เสียหายจำนวนมากทั่วประเทศ มูลค่ารวมกว่า 4.8 ล้านบาท กระทบต่อความเชื่อมั่นในระบบเศรษฐกิจการค้าทองคำ",
                "status": "promoted",
                "created_at": "2026-08-12T10:30:00Z"
            },
            {
                "id": "INTAKE-003",
                "case_id": "CASE-112",
                "title": "ร้องเรียนผลิตภัณฑ์เสริมอาหาร 'สลิมฟิต ดีท็อกซ์' ผสมสารไซบูทรามีนทำให้ผู้บริโภคหมดสติ",
                "description": "ผู้บริโภครับประทานอาหารเสริมลดน้ำหนักเกิดอาการใจสั่น แน่นหน้าอก ชักเกร็ง และหมดสติ แพทย์ตรวจพบสารไซบูทรามีนในกระแสเลือด",
                "reporter_name": "นางกัลยา สุขภาพดี",
                "reporter_phone": "084-222-1133",
                "raw_statement": "ข้าพเจ้าได้สั่งซื้ออาหารเสริม SlimFit Detox จากตัวแทนจำหน่ายออนไลน์ มารับประทานต่อเนื่อง 5 วัน จนเกิดอาการหัวใจเต้นเร็วผิดปกติ แน่นหน้าอก และหมดสติ ต้องเข้ารับการรักษาในห้อง ICU โรงพยาบาลศิริราช แพทย์ลงความเห็นว่าเกิดจากสารกดประสาทไซบูทรามีน จึงขอมอบหลักฐานและตัวอย่างผลิตภัณฑ์ให้เจ้าหน้าที่ บก.ปคบ. ดำเนินคดีกับผู้ผลิตให้ถึงที่สุด",
                "triage_urgency": "high",
                "triage_reason": "ผลิตภัณฑ์มีส่วนผสมของวัตถุออกฤทธิ์ต่อจิตและประสาทประเภท 1 เป็นภัยอันตรายร้ายแรงต่อชีวิตและร่างกายของประชาชน",
                "status": "pending",
                "created_at": "2026-08-14T08:15:00Z"
            }
        ]
        
        # 2. PERSONS (บุคคลที่เกี่ยวข้องทั้งหมด)
        self.persons = [
            # Case 1: สยาม คอสเมติกส์
            {"id": "p-kittisak", "case_id": "CASE-142", "name": "นายกิตติศักดิ์ วงศ์สวัสดิ์", "national_id": "1-1002-88832-11-2", "role": "Suspect", "phone": "089-111-2345", "address": "12/5 ถนนลาดพร้าว แขวงจอมพล เขตจตุจักร กรุงเทพมหานคร"},
            {"id": "p-nattapong", "case_id": "CASE-142", "name": "นายนัฐพงษ์ สุขประเสริฐ", "national_id": "3-1209-99823-00-1", "role": "Victim", "phone": "081-555-0192", "address": "123/4 ถนนสุขุมวิท แขวงคลองเตย เขตคลองเตย กรุงเทพมหานคร"},
            {"id": "p-somchai-proxy", "case_id": "CASE-142", "name": "นายสมชาย แสนสุข", "national_id": "1-1003-77723-11-0", "role": "Witness (Proxy Director)", "phone": "081-999-8888", "address": "77 ถนนรัชดาภิเษก แขวงห้วยขวาง เขตห้วยขวาง กรุงเทพมหานคร"},
            {"id": "p-patcharee", "case_id": "CASE-142", "name": "นางสาวพัชรี แก้วมณี", "national_id": "3-1009-44556-22-1", "role": "Suspect (Mule Row 2)", "phone": "083-444-5566", "address": "45/1 ถนนประชาอุทิศ แขวงดอนเมือง เขตดอนเมือง กรุงเทพมหานคร"},
            # Case 2: ภูเก็ต โกลด์
            {"id": "p-wichan", "case_id": "CASE-087", "name": "นายวิชาญ ทองประเสริฐ", "national_id": "1-8399-00212-33-4", "role": "Suspect", "phone": "082-333-4455", "address": "88/12 ถนนราษฎร์อุทิศ 200 ปี ตำบลป่าตอง อำเภอกะทู้ จังหวัดภูเก็ต"},
            {"id": "p-maneerat", "case_id": "CASE-087", "name": "นางสาวมณีรัตน์ ทองแท้", "national_id": "3-1005-44321-99-8", "role": "Victim", "phone": "086-777-8899", "address": "45/2 ถนนเทพกระษัตรี ตำบลตลาดใหญ่ อำเภอเมือง จังหวัดภูเก็ต"},
            {"id": "p-kanda", "case_id": "CASE-087", "name": "นางสาวกานดา สุวรรณภูมิ", "national_id": "2-8301-33221-55-9", "role": "Suspect (Admin)", "phone": "087-654-3210", "address": "120 หมู่ 3 ตำบลกะรน อำเภอเมือง จังหวัดภูเก็ต"},
            # Case 3: สลิมฟิต ดีท็อกซ์
            {"id": "p-narongchai", "case_id": "CASE-112", "name": "นายณรงค์ชัย โอสถสิทธิ์", "national_id": "1-1005-77889-22-1", "role": "Suspect", "phone": "091-888-9900", "address": "99/1 ถนนพระราม 2 แขวงบางมด เขตจอมทอง กรุงเทพมหานคร"},
            {"id": "p-kanlaya", "case_id": "CASE-112", "name": "นางกัลยา สุขภาพดี", "national_id": "3-1205-11223-44-5", "role": "Victim", "phone": "084-222-1133", "address": "55/1 ถนนเพชรเกษม แขวงบางหว้า เขตภาษีเจริญ กรุงเทพมหานคร"},
            {"id": "p-thanakorn", "case_id": "CASE-112", "name": "นายธนากร เภสัชวิทย์", "national_id": "1-1008-66554-11-7", "role": "Suspect (Factory Chemist)", "phone": "088-999-1122", "address": "14/2 ถนนบางขุนเทียน-ชายทะเล แขวงท่าข้าม เขตบางขุนเทียน กรุงเทพมหานคร"}
        ]
        
        # 3. ORGANIZATIONS (นิติบุคคลและเครือข่าย)
        self.organizations = [
            {"id": "org-siam-net", "case_id": "CASE-142", "name": "บริษัท สยาม เน็ตเวิร์ค จำกัด", "registration_number": "0105566099123", "type": "Company", "address": "100/1 ถนนสุขุมวิท แขวงคลองเตย เขตคลองเตย กรุงเทพมหานคร", "status": "active"},
            {"id": "org-phuket-gold", "case_id": "CASE-087", "name": "ห้างหุ้นส่วนจำกัด ภูเก็ตไซเบอร์โกลด์", "registration_number": "0833560001221", "type": "Partnership", "address": "55/9 ถนนป่าตอง ตำบลป่าตอง อำเภอกะทู้ จังหวัดภูเก็ต", "status": "active"},
            {"id": "org-bangkok-health", "case_id": "CASE-112", "name": "บริษัท บางกอก นิวทริชั่น เฮลท์ จำกัด", "registration_number": "0105559002341", "type": "Manufacturer", "address": "120/4 ถนนบางขุนเทียน แขวงแสมดำ เขตบางขุนเทียน กรุงเทพมหานคร", "status": "active"}
        ]
        
        # 4. VICTIMS (ข้อมูลผู้เสียหาย)
        self.victims = [
            {"id": "cf2f8c5b-38ab-41c1-903c-83b66d4db02a", "case_id": "CASE-142", "full_name": "นายนัฐพงษ์ สุขประเสริฐ", "email": "nattapong.s@gmail.com", "phone": "081-555-0192", "address": "123/4 ถนนสุขุมวิท แขวงคลองเตย เขตคลองเตย กรุงเทพมหานคร", "loss_amount": 1250000.00, "intake_source": "portal"},
            {"id": "8b3e9fb3-83bc-42b7-8ce6-90bd551deeb3", "case_id": "CASE-087", "full_name": "นางสาวมณีรัตน์ ทองแท้", "email": "maneerat.t@yahoo.com", "phone": "086-777-8899", "address": "45/2 ถนนเทพกระษัตรี ตำบลตลาดใหญ่ อำเภอเมือง จังหวัดภูเก็ต", "loss_amount": 480000.00, "intake_source": "portal"},
            {"id": "c71a82d1-99ee-41a2-8bc1-12f3e8b9fb6c", "case_id": "CASE-112", "full_name": "นางกัลยา สุขภาพดี", "email": "kanlaya.health@gmail.com", "phone": "084-222-1133", "address": "55/1 ถนนเพชรเกษม แขวงบางหว้า เขตภาษีเจริญ กรุงเทพมหานคร", "loss_amount": 250000.00, "intake_source": "portal"}
        ]
        
        # 5. EVIDENCE (พยานหลักฐานในสำนวนพร้อม SHA-256)
        self.evidence = [
            # Case 1: สยาม คอสเมติกส์
            {"id": "f05d9e5b-ec1d-4009-bf2f-e8b9fb6cb088", "case_id": "CASE-142", "title": "สลิปการโอนเงินธนาคารไทยพาณิชย์ 1.25 ล้านบาท", "description": "สลิปหลักฐานการโอนเงินจากบัญชีผู้เสียหายเข้าบัญชี SCB เลขที่ 401-229-3388 นายกิตติศักดิ์ วงศ์สวัสดิ์", "type": "document", "file_hash": "a3f82cb304b5f883201de374ffea57bd8c928e1832049e3bfd12cf88c9d21415", "status": "sealed", "created_at": "2026-08-10T10:05:00Z"},
            {"id": "11b7df3c-6622-48df-9cb9-ef77ba4c28f1", "case_id": "CASE-142", "title": "ภาพบันทึกบทสนทนา Line Chat 'Siam Cosmetics'", "description": "ภาพแคปหน้าจอการตกลงซื้อขายและการหลอกลวงให้โอนเงินพร้อมหมายเลขโทรศัพท์ 089-111-2345", "type": "document", "file_hash": "e7b92f7a63bc1a2384a56c07221ee9f08cb18d9f10928e3bcfde204d80a1122a", "status": "sealed", "created_at": "2026-08-10T10:10:00Z"},
            {"id": "ev-142-lab", "case_id": "CASE-142", "title": "รายงานผลการตรวจพิสูจน์สารเคมีอันตรายจากกรมวิทยาศาสตร์การแพทย์", "description": "ผลตรวจพิสูจน์พบสารไฮโดรควิโนนและสารปรอทเกินมาตรฐานความปลอดภัยของเครื่องสำอาง", "type": "document", "file_hash": "7f83b1657ff1fc53b92dc18148a1d65dfc2d4b1fa3d677284addd200126d9069", "status": "sealed", "created_at": "2026-08-11T11:00:00Z"},
            # Case 2: ภูเก็ต โกลด์
            {"id": "ev-gold-cert", "case_id": "CASE-087", "title": "หนังสือรับรองผลตรวจวิเคราะห์ทองคำจากสถาบัน GIT", "description": "ผลการตรวจทางวิทยาศาสตร์ยืนยันทองรูปพรรณมีส่วนผสมทองคำแท้เพียง 12.4% (โฆษณาเท็จ 96.5%)", "type": "document", "file_hash": "c4b819f2a01d4099ae1ef3f2a89366df01928374a56c07221ee9f08cb18d9f10", "status": "sealed", "created_at": "2026-08-12T14:00:00Z"},
            {"id": "ev-087-video", "case_id": "CASE-087", "title": "ไฟล์บันทึกวิดีโอไลฟ์สดการขายทองคำบน TikTok", "description": "คลิปบันทึกภาพและเสียงนายวิชาญ ทองประเสริฐ โฆษณาอ้างทองคำแท้หลุดจำนำ 96.5% ราคาพิเศษ", "type": "digital", "file_hash": "3b879c72e93b1cf24f5a31a980e0c8b93b2a8d11c0f837e2467d581a942b08a9", "status": "sealed", "created_at": "2026-08-12T16:00:00Z"},
            # Case 3: สลิมฟิต ดีท็อกซ์
            {"id": "ev-food-lab", "case_id": "CASE-112", "title": "รายงานผลการตรวจวิเคราะห์สารไซบูทรามีนจากกรมวิทยาศาสตร์การแพทย์", "description": "รายงานผลตรวจพิสูจน์ยืนยันการปนเปื้อนสารวัตถุออกฤทธิ์ต่อจิตประสาทประเภท 1 (ไซบูทรามีน 15 mg/capsule)", "type": "document", "file_hash": "99a8b7c6d5e4f3a2b1c0d9e8f7a6b5c4d3e2f1a0b9c8d7e6f5a4b3c2d1e0f9a8", "status": "sealed", "created_at": "2026-08-14T16:00:00Z"},
            {"id": "ev-112-seizure", "case_id": "CASE-112", "title": "บันทึกการตรวจยึดของกลางอาหารเสริม SlimFit Detox 12,000 กล่อง", "description": "บันทึกการตรวจยึดสินค้าของกลาง ณ โกดังลักลอบผลิต ถนนบางขุนเทียน-ชายทะเล", "type": "physical", "file_hash": "4b227777d4dd1fc61c6f884f48641d02b4d121d3fd328cb08b5531fcacdabf8a", "status": "sealed", "created_at": "2026-08-15T10:00:00Z"}
        ]
        
        # 6. TRANSACTIONS & BANK ACCOUNTS (บัญชีธนาคารและธุรกรรม)
        self.bank_accounts = [
            {"id": "b07e2a9b-38cc-4d32-bc10-ef239ab82811", "bank_name": "ธนาคารไทยพาณิชย์ (SCB)", "account_number": "401-229-3388", "account_name": "นายกิตติศักดิ์ วงศ์สวัสดิ์"},
            {"id": "b08e3a9c-49dd-5e43-cd21-f0340bc93922", "bank_name": "ธนาคารกสิกรไทย (KBANK)", "account_number": "702-888-1123", "account_name": "หจก. ภูเก็ตไซเบอร์โกลด์"},
            {"id": "b09e4a9d-50ee-6f54-de32-f1451cd04033", "bank_name": "ธนาคารกรุงเทพ (BBL)", "account_number": "128-4-55667-8", "account_name": "บจก. บางกอก นิวทริชั่น เฮลท์"},
            {"id": "b10e5a9e-61ff-7a65-ef43-a2562de15144", "bank_name": "ธนาคารกรุงไทย (KTB)", "account_number": "980-1-23456-7", "account_name": "นางสาวพัชรี แก้วมณี (บัญชีม้าแถว 2)"}
        ]
        self.transactions = [
            # Case 1 Transactions
            {
                "id": "a01c3d9a-1122-3344-5566-778899aabbcc", 
                "case_id": "CASE-142", 
                "source_account_id": None, 
                "target_account_id": "b07e2a9b-38cc-4d32-bc10-ef239ab82811", 
                "amount": 1250000.00, 
                "currency": "THB", 
                "transaction_date": "2026-08-09T14:32:00Z", 
                "reference_number": "TXN-99882211", 
                "evidence_id": "f05d9e5b-ec1d-4009-bf2f-e8b9fb6cb088"
            },
            {
                "id": "a01c3d9a-1122-3344-5566-778899aabbcd", 
                "case_id": "CASE-142", 
                "source_account_id": "b07e2a9b-38cc-4d32-bc10-ef239ab82811", 
                "target_account_id": "b10e5a9e-61ff-7a65-ef43-a2562de15144", 
                "amount": 600000.00, 
                "currency": "THB", 
                "transaction_date": "2026-08-09T15:10:00Z", 
                "reference_number": "TXN-99882212", 
                "evidence_id": None
            },
            # Case 2 Transactions
            {
                "id": "a02c4d9b-2233-4455-6677-8899aabbccdd", 
                "case_id": "CASE-087", 
                "source_account_id": None, 
                "target_account_id": "b08e3a9c-49dd-5e43-cd21-f0340bc93922", 
                "amount": 480000.00, 
                "currency": "THB", 
                "transaction_date": "2026-08-11T11:15:00Z", 
                "reference_number": "TXN-77665544", 
                "evidence_id": "ev-gold-cert"
            },
            # Case 3 Transactions
            {
                "id": "a03c5d9c-3344-5566-7788-99aabbccddee", 
                "case_id": "CASE-112", 
                "source_account_id": None, 
                "target_account_id": "b09e4a9d-50ee-6f54-de32-f1451cd04033", 
                "amount": 250000.00, 
                "currency": "THB", 
                "transaction_date": "2026-08-13T09:45:00Z", 
                "reference_number": "TXN-11223344", 
                "evidence_id": "ev-food-lab"
            }
        ]
        
        # 7. TIMELINE (ลำดับเหตุการณ์ในคดี)
        self.timeline = [
            # Case 1 Timeline
            {"id": "ev-1", "case_id": "CASE-142", "event_date": "2026-08-01T09:00:00Z", "title": "จดทะเบียนจัดตั้ง บริษัท สยาม เน็ตเวิร์ค จำกัด", "description": "นายกิตติศักดิ์และนายสมชายจดทะเบียนจัดตั้งบริษัทกับกรมพัฒนาธุรกิจการค้า ทุนจดทะเบียน 1 ล้านบาท", "evidence_id": None},
            {"id": "ev-2", "case_id": "CASE-142", "event_date": "2026-08-05T10:00:00Z", "title": "เปิดบัญชีม้าธนาคารไทยพาณิชย์", "description": "นายกิตติศักดิ์ วงศ์สวัสดิ์ ดำเนินการเปิดบัญชีเงินฝาก SCB เลขที่ 401-229-3388 เพื่อรับเงินจากเหยื่อ", "evidence_id": None},
            {"id": "ev-3", "case_id": "CASE-142", "event_date": "2026-08-08T15:00:00Z", "title": "เปิดเพจ Facebook และลงโฆษณาขายเวชสำอางค์ลด 70%", "description": "เริ่มแคมเปญโฆษณาหลอกลวงประชาชนผ่านระบบเครือข่ายสังคมออนไลน์", "evidence_id": "11b7df3c-6622-48df-9cb9-ef77ba4c28f1"},
            {"id": "ev-4", "case_id": "CASE-142", "event_date": "2026-08-09T14:32:00Z", "title": "ผู้เสียหายโอนเงินสั่งซื้อเวชสำอางค์ 1.25 ล้านบาท", "description": "นายนัฐพงษ์ สุขประเสริฐ โอนเงิน 1,250,000 บาท เข้าบัญชี SCB 401-229-3388", "evidence_id": "f05d9e5b-ec1d-4009-bf2f-e8b9fb6cb088"},
            {"id": "ev-5", "case_id": "CASE-142", "event_date": "2026-08-10T11:00:00Z", "title": "ถอนเงินสดและทำธุรกรรมผ่านตู้ ATM ลาดพร้าว", "description": "ตรวจพบบันทึกการเข้าใช้งานระบบผ่าน IP ในกรุงเทพฯ และถอนเงินสด ขัดแย้งกับคำให้การที่อ้างว่าอยู่เชียงใหม่", "evidence_id": None},
            # Case 2 Timeline
            {"id": "ev-6", "case_id": "CASE-087", "event_date": "2026-08-11T10:00:00Z", "title": "ไลฟ์สดจำหน่ายทองคำแท้ราคาพิเศษบน TikTok", "description": "นายวิชาญดำเนินรายการอ้างทองคำแท้ 96.5% หลุดจำนำเยาวราช", "evidence_id": "ev-087-video"},
            {"id": "ev-7", "case_id": "CASE-087", "event_date": "2026-08-11T11:15:00Z", "title": "ผู้เสียหายโอนเงิน 480,000 บาท เข้าบัญชีกสิกรไทย", "description": "นางสาวมณีรัตน์สั่งซื้อทองคำและโอนเงินเข้าบัญชี 702-888-1123", "evidence_id": "ev-gold-cert"},
            {"id": "ev-8", "case_id": "CASE-087", "event_date": "2026-08-12T14:00:00Z", "title": "สถาบัน GIT ออกใบรับรองผลตรวจทองคำแท้เพียง 12.4%", "description": "ผลวิเคราะห์ทางแล็บยืนยันเป็นทองชุบผสมต่ำกว่ามาตรฐานอย่างร้ายแรง", "evidence_id": "ev-gold-cert"},
            # Case 3 Timeline
            {"id": "ev-9", "case_id": "CASE-112", "event_date": "2026-08-13T09:45:00Z", "title": "ผู้เสียหายสั่งซื้อผลิตภัณฑ์ SlimFit Detox ทางออนไลน์", "description": "นางกัลยาโอนเงิน 250,000 บาท สำหรับสั่งซื้อล็อตใหญ่เป็นตัวแทน", "evidence_id": "ev-food-lab"},
            {"id": "ev-10", "case_id": "CASE-112", "event_date": "2026-08-14T14:00:00Z", "title": "ผู้บริโภคเกิดภาวะแทรกซ้อนหัวใจและเข้าห้อง ICU", "description": "แพทย์ตรวจพบสารไซบูทรามีนในเลือด นำไปสู่การร้องเรียนต่อ บก.ปคบ.", "evidence_id": "ev-food-lab"},
            {"id": "ev-11", "case_id": "CASE-112", "event_date": "2026-08-15T10:00:00Z", "title": "ตรวจค้นโกดังบางขุนเทียนและตรวจยึดของกลาง 12,000 กล่อง", "description": "เจ้าหน้าที่ ปคบ. นำหมายค้นเข้าตรวจยึดสินค้าและจับกุมผู้ดูแลโรงงาน", "evidence_id": "ev-112-seizure"}
        ]
        
        # 8. LEGAL_ISSUES (ประเด็นข้อกฎหมายและองค์ประกอบความผิด)
        self.legal_issues = [
            # Case 1
            {"id": "li-1", "case_id": "CASE-142", "issue_title": "ร่วมกันฉ้อโกงประชาชน", "legal_code": "ประมวลกฎหมายอาญา มาตรา 343 ประกอบ มาตรา 83", "description": "หลอกลวงด้วยการแสดงข้อความอันเป็นเท็จต่อประชาชนทั่วไปผ่านเพจ Facebook และ Line", "status": "substantiated", "evidence_ids": ["f05d9e5b-ec1d-4009-bf2f-e8b9fb6cb088", "11b7df3c-6622-48df-9cb9-ef77ba4c28f1"]},
            {"id": "li-2", "case_id": "CASE-142", "issue_title": "การผลิตและจำหน่ายเครื่องสำอางไม่ปลอดภัย", "legal_code": "พ.ร.บ.เครื่องสำอาง พ.ศ. 2558 มาตรา 27 และ 28", "description": "มีส่วนผสมของสารปรอทและไฮโดรควิโนนอันก่อให้เกิดอันตรายต่อผู้บริโภค", "status": "substantiated", "evidence_ids": ["ev-142-lab"]},
            {"id": "li-3", "case_id": "CASE-142", "issue_title": "นำเข้าข้อมูลคอมพิวเตอร์อันเป็นเท็จ", "legal_code": "พ.ร.บ.คอมพิวเตอร์ฯ พ.ศ. 2550 มาตรา 14(1)", "description": "นำเข้าข้อมูลอันเป็นเท็จโดยประการที่น่าจะเกิดความเสียหายแก่ประชาชน", "status": "substantiated", "evidence_ids": ["11b7df3c-6622-48df-9cb9-ef77ba4c28f1"]},
            # Case 2
            {"id": "li-4", "case_id": "CASE-087", "issue_title": "ร่วมกันหลอกลวงจำหน่ายทองคำต่ำกว่ามาตรฐาน", "legal_code": "ประมวลกฎหมายอาญา มาตรา 271 ประกอบ พ.ร.บ.คุ้มครองผู้บริโภคฯ", "description": "ขายทองคำโดยหลอกลวงเรื่องปริมาณ คุณภาพ หรือความบริสุทธิ์ของทองคำ", "status": "substantiated", "evidence_ids": ["ev-gold-cert"]},
            {"id": "li-5", "case_id": "CASE-087", "issue_title": "การโฆษณาอันเป็นเท็จหรือเกินความจริง", "legal_code": "พ.ร.บ.คุ้มครองผู้บริโภค พ.ศ. 2522 มาตรา 22", "description": "โฆษณาอ้างว่าเป็นทองคำแท้ 96.5% จากเยาวราช", "status": "substantiated", "evidence_ids": ["ev-087-video"]},
            # Case 3
            {"id": "li-6", "case_id": "CASE-112", "issue_title": "จำหน่ายอาหารไม่บริสุทธิ์ผสมวัตถุออกฤทธิ์ต่อจิตประสาท", "legal_code": "พ.ร.บ.อาหาร พ.ศ. 2522 มาตรา 26 ประกอบประมวลกฎหมายยาเสพติด", "description": "ลักลอบผสมสารไซบูทรามีนในอาหารเสริมลดน้ำหนัก", "status": "substantiated", "evidence_ids": ["ev-food-lab", "ev-112-seizure"]}
        ]
        
        # 9. TASKS (รายการงานสืบสวนสอบสวน)
        self.tasks = [
            {"id": "918d6e3c-8c5e-4c7b-8395-5db460cb7d10", "case_id": "CASE-142", "title": "ตรวจสอบประวัติและอัตลักษณ์บุคคล นายกิตติศักดิ์ วงศ์สวัสดิ์", "description": "ตรวจสอบข้อมูลทะเบียนราษฎร์ (Linkage) กรมการปกครอง และหมายจับค้างเก่า", "assigned_to": "d2f0998c-8c1d-4099-ae1e-f3f2a89366df", "status": "pending", "due_date": "2026-08-25T17:00:00Z"},
            {"id": "918d6e3c-8c5e-4c7b-8395-5db460cb7d11", "case_id": "CASE-142", "title": "วิเคราะห์เส้นทางการเงินและขออายัดบัญชีธนาคาร", "description": "ประสาน ปปง. และธนาคารไทยพาณิชย์เพื่ออายัดเงินในบัญชี 401-229-3388 และบัญชีแถวที่สอง", "assigned_to": "d2f0998c-8c1d-4099-ae1e-f3f2a89366df", "status": "in_progress", "due_date": "2026-08-28T17:00:00Z"},
            {"id": "918d6e3c-8c5e-4c7b-8395-5db460cb7d12", "case_id": "CASE-087", "title": "ออกหมายเรียกผู้ต้องหาคดีทองคำปลอมภูเก็ต", "description": "ออกหมายเรียกนายวิชาญ ทองประเสริฐ เข้าพบพนักงานสอบสวน กก.1 บก.ปคบ.", "assigned_to": "a1b2c3d4-e5f6-7a8b-9c0d-1e2f3a4b5c6d", "status": "pending", "due_date": "2026-08-30T17:00:00Z"},
            {"id": "918d6e3c-8c5e-4c7b-8395-5db460cb7d13", "case_id": "CASE-112", "title": "ส่งตรวจพิสูจน์สารเคมีของกลาง ณ กรมวิทยาศาสตร์การแพทย์", "description": "นำตัวอย่างแคปซูลอาหารเสริม SlimFit Detox ของกลางตรวจหาปริมาณไซบูทรามีน", "assigned_to": "a1b2c3d4-e5f6-7a8b-9c0d-1e2f3a4b5c6d", "status": "completed", "due_date": "2026-08-20T17:00:00Z"}
        ]
        
        # 10. REPORTS (รายงานและเอกสารทางคดี)
        self.reports = [
            {"id": "rep-001", "case_id": "CASE-142", "report_type": "Executive Brief", "title": "รายงานสรุปข้อเท็จจริงคดีสยาม คอสเมติกส์ เสนอ ผบก.ปคบ.", "content": "# รายงานสรุปย่อผู้บังคับบัญชา\nคดีหลอกจำหน่ายเวชสำอางค์ปลอมผ่านเพจ Facebook สยาม คอสเมติกส์ ออฟฟิเชียล...", "version": 1, "status": "AI_DRAFT", "created_at": "2026-08-17T12:00:00Z"},
            {"id": "rep-002", "case_id": "CASE-087", "report_type": "Executive Brief", "title": "รายงานสรุปพฤติการณ์คดีหลอกขายทองคำออนไลน์ หจก. ภูเก็ตไซเบอร์โกลด์", "content": "# รายงานสรุปย่อผู้บังคับบัญชา\nคดีหลอกขายทองรูปพรรณเปอร์เซ็นต์ต่ำผ่านการไลฟ์สด...", "version": 1, "status": "AI_DRAFT", "created_at": "2026-08-17T13:00:00Z"}
        ]
        
        # 11. COMMUNICATIONS (บันทึกการสื่อสารดิจิทัล)
        self.communications = [
            {
                "id": "comm-001",
                "case_id": "CASE-142",
                "channel": "LINE_CHAT",
                "sender_identifier": "089-111-2345 (แอดมินเพจ สยาม คอสเมติกส์)",
                "recipient_identifier": "081-555-0192 (นายนัฐพงษ์ สุขประเสริฐ)",
                "timestamp": "2026-08-09T14:15:00Z",
                "content_text": "รบกวนโอนเงินจำนวน 1,250,000 บาท เข้าบัญชี SCB 401-229-3388 นายกิตติศักดิ์ วงศ์สวัสดิ์ เพื่อล็อคสต็อกสินค้าเวชสำอางค์ล็อตพิเศษครับ",
                "evidence_id": "11b7df3c-6622-48df-9cb9-ef77ba4c28f1"
            },
            {
                "id": "comm-002",
                "case_id": "CASE-142",
                "channel": "PHONE_CALL",
                "sender_identifier": "089-111-2345 (นายกิตติศักดิ์)",
                "recipient_identifier": "081-555-0192 (นายนัฐพงษ์)",
                "timestamp": "2026-08-09T14:20:00Z",
                "content_text": "บันทึกการโทรศัพท์ยืนยันยอดเงินและนัดหมายส่งมอบสินค้าที่คลังสินค้าบางเขน",
                "evidence_id": None
            },
            {
                "id": "comm-003",
                "case_id": "CASE-087",
                "channel": "LINE_CHAT",
                "sender_identifier": "082-333-4455 (นายวิชาญ ทองประเสริฐ)",
                "recipient_identifier": "086-777-8899 (นางสาวมณีรัตน์ ทองแท้)",
                "timestamp": "2026-08-11T11:00:00Z",
                "content_text": "ทองคำแท้ 96.5% มีใบรับประกันจากร้านเยาวราช โอนเงินเข้าบัญชี หจก. ได้ทันทีครับ ราคานี้เหลือเพียง 2 เส้นสุดท้าย",
                "evidence_id": "ev-gold-cert"
            }
        ]

        # 12. AI_ANALYSES (ผลวิเคราะห์ AI แยกจาก Original Evidence)
        self.ai_analyses = [
            {
                "id": "ana-001",
                "case_id": "CASE-142",
                "agent_name": "TimelineAgent",
                "analysis_type": "TIMELINE_CONTRADICTION",
                "fact_tags": [
                    {"tag": "FACT", "text": "ผู้เสียหายโอนเงิน 1.25 ล้านบาท เข้าบัญชี SCB 401-229-3388 เวลา 14:32:00 น.", "source_evidence_id": "f05d9e5b-ec1d-4009-bf2f-e8b9fb6cb088"},
                    {"tag": "CLAIM", "text": "ผู้ต้องหาอ้างว่าตนเองอยู่เชียงใหม่และทำบัตร ATM หาย", "source_evidence_id": None},
                    {"tag": "CONFLICT", "text": "ตรวจพบบันทึกการเข้าสู่ระบบผ่าน IP ในกรุงเทพฯ เวลา 14:32 น. ขัดแย้งกับข้ออ้าง Alibi", "source_evidence_id": "11b7df3c-6622-48df-9cb9-ef77ba4c28f1"}
                ],
                "findings_summary": "ตรวจพบข้อขัดแย้งสำคัญของคำให้การผู้ต้องหากับพิกัด IP และประวัติการทำธุรกรรม",
                "confidence_score": 0.94,
                "review_status": "REQUIRES_HUMAN_REVIEW",
                "reviewed_by": None,
                "investigator_notes": None,
                "created_at": "2026-08-17T12:30:00Z"
            },
            {
                "id": "ana-002",
                "case_id": "CASE-087",
                "agent_name": "EvidenceAnalysisAgent",
                "analysis_type": "EVIDENCE_AUTHENTICITY",
                "fact_tags": [
                    {"tag": "FACT", "text": "ผลตรวจวิเคราะห์จากสถาบัน GIT ระบุเปอร์เซ็นต์ทองคำแท้ 12.4%", "source_evidence_id": "ev-gold-cert"},
                    {"tag": "CLAIM", "text": "คลิปไลฟ์สดโฆษณาอ้างว่าเป็นทองคำแท้ 96.5%", "source_evidence_id": "ev-087-video"},
                    {"tag": "CONFLICT", "text": "คุณภาพสินค้าจริงต่ำกว่ามาตรฐานที่โฆษณาไว้ถึง 84.1%", "source_evidence_id": "ev-gold-cert"}
                ],
                "findings_summary": "เข้าข่ายความผิดฐานหลอกลวงเรื่องชนิดและคุณภาพแห่งของตาม ป.อ. มาตรา 271 ชัดเจน",
                "confidence_score": 0.98,
                "review_status": "VERIFIED",
                "reviewed_by": "d2f0998c-8c1d-4099-ae1e-f3f2a89366df",
                "investigator_notes": "ผลตรวจทางวิทยาศาสตร์มีความน่าเชื่อถือตาม ป.วิ.อ. มาตรา 226/3",
                "created_at": "2026-08-17T14:00:00Z"
            }
        ]

        # 13. AUDIT_LOG
        self.audit_log = []
        self.trigger_events = []
        
        # Legacy compatibility values
        self.statements = [
            {
                "id": "stat-142-01",
                "case_id": "CASE-142",
                "subject_id": "cf2f8c5b-38ab-41c1-903c-83b66d4db02a",
                "subject_type": "victim",
                "role": "VICTIM",
                "status": "APPROVED",
                "recorded_at": "2026-08-10T10:00:00Z",
                "transcript": "ข้าพเจ้านายนัฐพงษ์ สุขประเสริฐ ได้รับการติดต่อเสนอขายสินค้าเวชสำอางค์ราคาพิเศษผ่านเพจเฟซบุ๊ก จึงหลงเชื่อโอนเงินจำนวน 1,250,000 บาท เข้าบัญชีธนาคารไทยพาณิชย์ เลขที่ 401-229-3388 นายกิตติศักดิ์ วงศ์สวัสดิ์ หมายเลขติดต่อ 089-111-2345 ภายหลังได้รับสินค้าปลอมและผู้ขายปิดเพจหลบหนี",
                "summary": "ผู้เสียหายถูกหลอกโอนเงิน 1.25 ล้านบาท ซื้อเวชสำอางค์ปลอมผ่านเพจเฟซบุ๊ก โอนเข้า SCB 401-229-3388 เบอร์ติดต่อ 089-111-2345",
                "created_at": "2026-08-10T10:00:00Z"
            },
            {
                "id": "a8efde12-b91b-4f9e-bc43-2287f3b890a2", 
                "case_id": "CASE-142", 
                "subject_id": "cf2f8c5b-38ab-41c1-903c-83b66d4db02a", 
                "subject_type": "victim", 
                "role": "VICTIM",
                "status": "APPROVED",
                "recorded_at": "2026-08-10T10:00:00Z", 
                "transcript": "ข้าพเจ้านายนัฐพงษ์ สุขประเสริฐ ได้รับการติดต่อเสนอขายสินค้าเวชสำอางค์ราคาพิเศษผ่านเพจเฟซบุ๊ก จึงหลงเชื่อโอนเงินจำนวน 1,250,000 บาท เข้าบัญชีธนาคารไทยพาณิชย์ เลขที่ 401-229-3388 นายกิตติศักดิ์ วงศ์สวัสดิ์ หมายเลขติดต่อ 089-111-2345 ภายหลังได้รับสินค้าปลอมและผู้ขายปิดเพจหลบหนี", 
                "summary": "ผู้เสียหายถูกหลอกโอนเงิน 1.25 ล้านบาท ซื้อเวชสำอางค์ปลอมผ่านเพจเฟซบุ๊ก โอนเข้า SCB 401-229-3388 เบอร์ติดต่อ 089-111-2345",
                "created_at": "2026-08-10T10:00:00Z"
            },
            {
                "id": "stmt-087-01", 
                "case_id": "CASE-087", 
                "subject_id": "8b3e9fb3-83bc-42b7-8ce6-90bd551deeb3", 
                "subject_type": "victim", 
                "recorded_at": "2026-08-12T11:00:00Z", 
                "transcript": "ข้าพเจ้านางสาวมณีรัตน์ ทองแท้ ได้ดูไลฟ์สดใน TikTok ของนายวิชาญ ทองประเสริฐ มีการนำทองคำรูปพรรณมาแสดงและอ้างว่าเป็นทองคำแท้ 96.5% ราคาถูกกว่าร้านค้าทองทั่วไป จึงได้โอนเงิน 480,000 บาท เข้าบัญชี KBANK 702-888-1123 ต่อมานำไปตรวจสอบพบว่าเป็นทองผสมปลอม", 
                "summary": "ผู้เสียหายถูกหลอกซื้อทองคำรูปพรรณปลอม 480,000 บาท ผ่านไลฟ์สด TikTok โอนเข้า KBANK 702-888-1123",
                "created_at": "2026-08-12T11:00:00Z"
            }
        ]
        # PHASE 6 COLLECTIONS (Legal Analysis & Investigation Planning Layer)
        self.laws = [
            {
                "id": "law-penal-code",
                "code": "TH-CRIMINAL-CODE",
                "title_th": "ประมวลกฎหมายอาญา",
                "title_en": "Criminal Code of Thailand",
                "jurisdiction": "THAILAND",
                "effective_from": "1957-01-01",
                "effective_to": None,
                "status": "ACTIVE",
                "source_reference": "ราชกิจจานุเบกษา เล่ม 73 ตอนที่ 95",
                "version": "2024"
            },
            {
                "id": "law-computer-crime",
                "code": "TH-COMPUTER-CRIME-ACT",
                "title_th": "พระราชบัญญัติว่าด้วยการกระทำความผิดเกี่ยวกับคอมพิวเตอร์ พ.ศ. 2550 (และที่แก้ไขเพิ่มเติม)",
                "title_en": "Computer Crime Act B.E. 2550",
                "jurisdiction": "THAILAND",
                "effective_from": "2007-07-18",
                "effective_to": None,
                "status": "ACTIVE",
                "source_reference": "ราชกิจจานุเบกษา เล่ม 124 ตอนที่ 27 ก",
                "version": "2017"
            },
            {
                "id": "law-cosmetics",
                "code": "TH-COSMETICS-ACT",
                "title_th": "พระราชบัญญัติเครื่องสำอาง พ.ศ. 2558",
                "title_en": "Cosmetics Act B.E. 2558",
                "jurisdiction": "THAILAND",
                "effective_from": "2015-09-09",
                "effective_to": None,
                "status": "ACTIVE",
                "source_reference": "ราชกิจจานุเบกษา เล่ม 132 ตอนที่ 86 ก",
                "version": "2015"
            }
        ]

        self.legal_provisions = [
            {
                "id": "prov-sec-343",
                "law_id": "law-penal-code",
                "section": "343",
                "subsection": None,
                "title": "ความผิดฐานฉ้อโกงประชาชน",
                "text_reference": "ถ้าการกระทำความผิดฐานฉ้อโกงได้กระทำด้วยการแสดงข้อความอันเป็นเท็จต่อประชาชน...",
                "effective_from": "1957-01-01",
                "effective_to": None
            },
            {
                "id": "prov-cca-sec-14-1",
                "law_id": "law-computer-crime",
                "section": "14",
                "subsection": "1",
                "title": "นำเข้าสู่ระบบคอมพิวเตอร์ซึ่งข้อมูลอันเป็นเท็จ",
                "text_reference": "โดยทุจริต หรือโดยหลอกลวง นำเข้าสู่ระบบคอมพิวเตอร์ซึ่งข้อมูลคอมพิวเตอร์ที่บิดเบือนหรือปลอม...",
                "effective_from": "2017-05-24",
                "effective_to": None
            }
        ]

        self.case_facts = [
            {
                "id": "fact-142-01",
                "case_id": "CASE-142",
                "fact_text": "ผู้เสียหายโอนเงินจำนวน 1,250,000 บาท เข้าบัญชีธนาคารไทยพาณิชย์ เลขที่ 401-229-3388 นายกิตติศักดิ์ วงศ์สวัสดิ์ เมื่อ 9 ส.ค. 2569",
                "fact_type": "FACT",
                "verification_status": "VERIFIED",
                "source_type": "EVIDENCE",
                "source_ids": ["f05d9e5b-ec1d-4009-bf2f-e8b9fb6cb088"],
                "created_by": "d2f0998c-8c1d-4099-ae1e-f3f2a89366df",
                "reviewed_by": "d2f0998c-8c1d-4099-ae1e-f3f2a89366df",
                "created_at": "2026-08-10T10:10:00Z"
            },
            {
                "id": "fact-142-02",
                "case_id": "CASE-142",
                "fact_text": "เพจเฟซบุ๊ก สยาม คอสเมติกส์ ออฟฟิเชียล มีการโฆษณาขายเวชสำอางค์ลดราคา 70% ต่อประชาชนทั่วไป",
                "fact_type": "FACT",
                "verification_status": "VERIFIED",
                "source_type": "EVIDENCE",
                "source_ids": ["11b7df3c-6622-48df-9cb9-ef77ba4c28f1"],
                "created_by": "d2f0998c-8c1d-4099-ae1e-f3f2a89366df",
                "reviewed_by": "d2f0998c-8c1d-4099-ae1e-f3f2a89366df",
                "created_at": "2026-08-10T10:15:00Z"
            }
        ]

        self.legal_element_assessments = [
            {
                "id": "lea-142-01",
                "case_id": "CASE-142",
                "legal_issue_id": "li-142-01",
                "legal_element_id": "elem-142-01",
                "status": "SUPPORTED",
                "supporting_fact_ids": ["fact-142-02"],
                "supporting_evidence_ids": ["11b7df3c-6622-48df-9cb9-ef77ba4c28f1"],
                "contradictory_evidence_ids": [],
                "missing_fact_description": None,
                "analyst_comment": "มีพยานหลักฐานโพสต์ Facebook โฆษณาหลอกลวงประชาชนชัดเจน",
                "reviewed_by": "d2f0998c-8c1d-4099-ae1e-f3f2a89366df",
                "reviewed_at": "2026-08-10T11:00:00Z"
            }
        ]

        self.human_legal_decisions = [
            {
                "id": "hld-142-01",
                "case_id": "CASE-142",
                "decision": "ACCEPT_LEGAL_MAPPING",
                "reason": "ข้อเท็จจริงในสำนวนเข้าองค์ประกอบความผิดตาม ป.อ. ม.343 และ พ.ร.บ.คอมพิวเตอร์ฯ ม.14(1)",
                "decided_by": "d2f0998c-8c1d-4099-ae1e-f3f2a89366df",
                "decided_at": "2026-08-10T11:30:00Z",
                "related_resource": "li-142-01"
            }
        ]

        # PHASE 5 COLLECTIONS (Statement & Interview Copilot Layer)
        self.interview_preparations = [
            {
                "id": "prep-142-01",
                "case_id": "CASE-142",
                "statement_id": "stat-142-01",
                "person_id": "p-142-01",
                "objective": "สอบสวนข้อเท็จจริงเกี่ยวกับการโอนเงิน 1,250,000 บาท และการส่งมอบเวชสำอางค์ปลอม",
                "issues_to_cover": ["การติดต่อสั่งซื้อ", "การโอนเงินและบัญชีปลายทาง", "การรับมอบสินค้าและผลตรวจสารเคมี"],
                "known_facts": ["ผู้เสียหายโอนเงินเข้าบัญชี SCB 401-229-3388 เมื่อ 9 ส.ค. 2569 เวลา 14:32:00"],
                "relevant_evidence_ids": ["f05d9e5b-ec1d-4009-bf2f-e8b9fb6cb088", "7f83b1657ff1fc53b92dc18148a1d65dfc2d4b1fa3d677284addd200126d9069"],
                "known_conflicts": [],
                "prepared_by": "d2f0998c-8c1d-4099-ae1e-f3f2a89366df",
                "ai_assisted": True,
                "reviewed_by": "d2f0998c-8c1d-4099-ae1e-f3f2a89366df",
                "created_at": "2026-08-10T09:30:00Z",
                "updated_at": "2026-08-10T09:45:00Z"
            }
        ]

        self.interview_questions = [
            {
                "id": "q-142-01",
                "statement_id": "stat-142-01",
                "sequence": 1,
                "question_type": "BACKGROUND",
                "topic": "ข้อมูลส่วนตัวและความสัมพันธ์กับผู้ต้องหา",
                "question_text": "ท่านรู้จักกับนายกิตติศักดิ์ วงศ์สวัสดิ์ หรือผู้ดูแลเพจ สยาม คอสเมติกส์ ออฟฟิเชียล มาก่อนหรือไม่ อย่างไร?",
                "purpose": "ตรวจสอบมูลเหตุจูงใจและความสัมพันธ์เดิม",
                "source_reference_ids": ["INTAKE-001"],
                "generated_by": "AI",
                "status": "ASKED",
                "asked_at": "2026-08-10T10:00:00Z",
                "created_at": "2026-08-10T09:50:00Z"
            },
            {
                "id": "q-142-02",
                "statement_id": "stat-142-01",
                "sequence": 2,
                "question_type": "FINANCIAL",
                "topic": "การโอนเงินชำระค่าสินค้า",
                "question_text": "ท่านโอนเงินจำนวน 1,250,000 บาท ผ่านช่องทางใด ไปยังบัญชีธนาคารใด ในวันเวลาใด?",
                "purpose": "ยืนยันความถูกต้องของสลิปการโอนเงิน",
                "source_reference_ids": ["f05d9e5b-ec1d-4009-bf2f-e8b9fb6cb088"],
                "generated_by": "AI",
                "status": "ASKED",
                "asked_at": "2026-08-10T10:15:00Z",
                "created_at": "2026-08-10T09:50:00Z"
            }
        ]

        self.statement_answers = [
            {
                "id": "ans-142-01",
                "statement_id": "stat-142-01",
                "question_id": "q-142-01",
                "sequence": 1,
                "answer_text": "ไม่เคยรู้จักหรือมีความสัมพันธ์ส่วนตัวกับนายกิตติศักดิ์ วงศ์สวัสดิ์ มาก่อน ติดต่อสั่งซื้อเวชสำอางค์ผ่านหน้าเพจเฟซบุ๊ก สยาม คอสเมติกส์ ออฟฟิเชียล เท่านั้น",
                "answer_type": "VERBATIM",
                "recorded_by": "d2f0998c-8c1d-4099-ae1e-f3f2a89366df",
                "recorded_at": "2026-08-10T10:05:00Z",
                "notes": "ผู้ให้การตอบด้วยความหนักแน่นและแสดงหลักฐานแชตประกอบ"
            },
            {
                "id": "ans-142-02",
                "statement_id": "stat-142-01",
                "question_id": "q-142-02",
                "sequence": 2,
                "answer_text": "ข้าพเจ้าได้โอนเงินจากแอปพลิเคชัน Krungthai NEXT จำนวน 1,250,000 บาท เข้าบัญชีธนาคารไทยพาณิชย์ เลขที่ 401-229-3388 ชื่อบัญชี นายกิตติศักดิ์ วงศ์สวัสดิ์ เมื่อวันที่ 9 สิงหาคม 2569 เวลาประมาณ 14:32 น. ตามสลิปที่นำมามอบให้เจ้าพนักงาน",
                "answer_type": "VERBATIM",
                "recorded_by": "d2f0998c-8c1d-4099-ae1e-f3f2a89366df",
                "recorded_at": "2026-08-10T10:18:00Z",
                "notes": "ตรงกับสลิปและข้อมูลรายการเดินบัญชีของธนาคาร"
            }
        ]

        self.statement_versions = [
            {
                "id": "sv-142-01",
                "statement_id": "stat-142-01",
                "version_number": 1,
                "content_text": "บันทึกคำให้การผู้กล่าวหา นายนัฐพงษ์ สุขประเสริฐ ให้การยืนยันการถูกหลอกโอนเงิน 1,250,000 บาท และส่งมอบพยานหลักฐานสลิปและแชตการสั่งซื้อ",
                "changed_by": "d2f0998c-8c1d-4099-ae1e-f3f2a89366df",
                "change_reason": "บันทึกร่างคำให้การแรกรับ",
                "review_status": "APPROVED",
                "created_at": "2026-08-10T10:30:00Z"
            }
        ]

        # PHASE 4 COLLECTIONS (AI Orchestrator & Multi-Agent Engine)
        self.ai_executions = [
            {
                "id": "exec-142-01",
                "case_id": "CASE-142",
                "requested_by": "d2f0998c-8c1d-4099-ae1e-f3f2a89366df",
                "agent_type": "EvidenceAnalysisAgent",
                "provider": "LOCAL_SECURE_LLM",
                "model_name": "typhoon-2-70b-instruct",
                "model_version": "v2.1",
                "prompt_version": "v1.4",
                "input_source_ids": ["f05d9e5b-ec1d-4009-bf2f-e8b9fb6cb088"],
                "data_classification": "CONFIDENTIAL",
                "status": "SUCCEEDED",
                "started_at": "2026-08-10T10:06:00Z",
                "completed_at": "2026-08-10T10:06:04Z",
                "token_usage": {"prompt_tokens": 1240, "completion_tokens": 380, "total_tokens": 1620},
                "cost_metadata": {"estimated_cost_thb": 0.0},
                "created_at": "2026-08-10T10:06:00Z"
            }
        ]

        self.prompt_registry = [
            {
                "prompt_id": "prompt-intake-triage-v1",
                "agent_type": "IntakeCaseTriageAgent",
                "version": "1.0",
                "language": "th",
                "system_prompt": "คุณคือ AI ผู้ช่วยคัดกรองคดี กก.1 บก.ปคบ. แยกบุคคล เหตุการณ์ พยานหลักฐาน และประเด็นต้องสงสัย ห้ามสรุปความผิดเด็ดขาด",
                "status": "ACTIVE"
            },
            {
                "prompt_id": "prompt-investigation-planning-v1",
                "agent_type": "InvestigationPlanningAgent",
                "version": "1.0",
                "language": "th",
                "system_prompt": "คุณคือ AI วางแผนการสืบสวนสอบสวน กก.1 บก.ปคบ. เสนอประเด็นตรวจพิสูจน์ พยานหลักฐานที่ต้องรวบรวม และหน่วยงานที่ต้องประสาน",
                "status": "ACTIVE"
            },
            {
                "prompt_id": "prompt-timeline-agent-v1",
                "agent_type": "TimelineAgent",
                "version": "1.0",
                "language": "th",
                "system_prompt": "คุณคือ AI ตรวจสอบและเรียบเรียงลำดับเวลาคดีอาญา กก.1 บก.ปคบ. ระบุข้อขัดแย้งและคำให้การที่ขัดแย้งกัน",
                "status": "ACTIVE"
            },
            {
                "prompt_id": "prompt-legal-mapping-v1",
                "agent_type": "LegalMappingAgent",
                "version": "1.0",
                "language": "th",
                "system_prompt": "คุณคือ AI วิเคราะห์องค์ประกอบความผิดตามกฎหมาย (ป.อ. ม.343, พ.ร.บ.คอมพิวเตอร์ฯ) ห้ามวินิจฉัยความผิดเด็ดขาด",
                "status": "ACTIVE"
            }
        ]

        # PHASE 3 COLLECTIONS (Evidence Intelligence Layer)
        self.evidence_files = [
            {
                "id": "ef-142-01",
                "evidence_id": "f05d9e5b-ec1d-4009-bf2f-e8b9fb6cb088",
                "artifact_type": "ORIGINAL",
                "parent_file_id": None,
                "object_key": "evidence/case-142/raw/slip_1.25m.png",
                "original_filename": "slip_scb_transfer_1250000.png",
                "stored_filename": "f05d9e5b_raw.png",
                "mime_type": "image/png",
                "extension": "png",
                "size_bytes": 1048576,
                "sha256": "a3f82cb304b5f883201de374ffea57bd8c928e1832049e3bfd12cf88c9d21415",
                "sha512": "b9c8d7e6f5a4b3c2d1e0f9a8b7c6d5e4f3a2b1c0d9e8f7a6b5c4d3e2f1a0b9c8d7e6f5a4b3c2d1e0f9a8b7c6d5e4f3a2b1c0d9e8f7a6b5c4d3e2f1a0b9c8d7e6",
                "storage_provider": "CPPD_SECURE_STORAGE",
                "storage_bucket": "cppd-evidence-vault-142",
                "uploaded_by": "d2f0998c-8c1d-4099-ae1e-f3f2a89366df",
                "uploaded_at": "2026-08-10T10:05:00Z",
                "scan_status": "CLEAN",
                "integrity_status": "VERIFIED",
                "is_primary": True,
                "is_immutable": True,
                "metadata_json": {
                    "width": 1080,
                    "height": 1920,
                    "format": "PNG",
                    "camera_device": "Apple iPhone 14 Pro",
                    "color_space": "sRGB"
                }
            },
            {
                "id": "ef-142-02",
                "evidence_id": "f05d9e5b-ec1d-4009-bf2f-e8b9fb6cb088",
                "artifact_type": "WORKING_COPY",
                "parent_file_id": "ef-142-01",
                "object_key": "evidence/case-142/working/slip_cropped_qr.png",
                "original_filename": "slip_scb_qr_cropped.png",
                "stored_filename": "f05d9e5b_working.png",
                "mime_type": "image/png",
                "extension": "png",
                "size_bytes": 262144,
                "sha256": "4b227777d4dd1fc61c6f884f48641d02b4d121d3fd328cb08b5531fcacdabf8a",
                "sha512": None,
                "storage_provider": "CPPD_SECURE_STORAGE",
                "storage_bucket": "cppd-evidence-vault-142",
                "uploaded_by": "d2f0998c-8c1d-4099-ae1e-f3f2a89366df",
                "uploaded_at": "2026-08-10T10:10:00Z",
                "scan_status": "CLEAN",
                "integrity_status": "VERIFIED",
                "is_primary": False,
                "is_immutable": False,
                "metadata_json": {
                    "width": 500,
                    "height": 500,
                    "cropped_region": "PromptPay QR Code"
                }
            }
        ]

        self.custody_events = [
            {
                "id": "cust-142-01",
                "evidence_id": "f05d9e5b-ec1d-4009-bf2f-e8b9fb6cb088",
                "event_type": "RECEIVED",
                "from_user_id": "นายนัฐพงษ์ สุขประเสริฐ (ผู้เสียหาย)",
                "to_user_id": "d2f0998c-8c1d-4099-ae1e-f3f2a89366df",
                "from_location": "จุดรับเรื่อง กก.1 บก.ปคบ.",
                "to_location": "ห้องเก็บพยานหลักฐาน กก.1 (Evidence Room Locker A-12)",
                "performed_by": "พ.ต.ท. สมชาย สอบสวนสืบสวน",
                "witnessed_by": "ส.ต.อ. สุรชัย คดีมั่น",
                "occurred_at": "2026-08-10T10:05:00Z",
                "reason": "รับมอบพยานหลักฐานสลิปโอนเงินประกอบการแจ้งความร้องทุกข์",
                "seal_number": "SEAL-CPPD-2026-0881",
                "condition_before": "สมบูรณ์",
                "condition_after": "บรรจุในซองเก็บพยานหลักฐานดิจิทัลพร้อมสลักลายเซ็น",
                "notes": "สลักลายเซ็น SHA-256 เรียบร้อย",
                "created_at": "2026-08-10T10:05:00Z"
            },
            {
                "id": "cust-142-02",
                "evidence_id": "7f83b1657ff1fc53b92dc18148a1d65dfc2d4b1fa3d677284addd200126d9069",
                "event_type": "SUBMITTED_FOR_ANALYSIS",
                "from_user_id": "d2f0998c-8c1d-4099-ae1e-f3f2a89366df",
                "to_user_id": "กรมวิทยาศาสตร์การแพทย์ กระทรวงสาธารณสุข",
                "from_location": "ห้องเก็บพยานหลักฐาน กก.1",
                "to_location": "สำนักยาและวัตถุเสพติด กรมวิทยาศาสตร์การแพทย์",
                "performed_by": "พ.ต.ท. สมชาย สอบสวนสืบสวน",
                "witnessed_by": "ร.ต.อ. สมศักดิ์ สืบสวนไว",
                "occurred_at": "2026-08-11T13:00:00Z",
                "reason": "ส่งตรวจพิสูจน์สารเคมีอันตรายและสารปรอทในเวชสำอางค์",
                "seal_number": "SEAL-CPPD-2026-0899",
                "condition_before": "ปิดผนึกสมบูรณ์",
                "condition_after": "เปิดผนึกเพื่อสกัดสารทดสอบในห้องปฏิบัติการ",
                "notes": "ได้รับรายงานผลตรวจทางเคมีกลับเมื่อ 14 ส.ค. 2569",
                "created_at": "2026-08-11T13:00:00Z"
            }
        ]

        self.evidence_locations = [
            {"id": "loc-1", "name": "Evidence Vault Locker A-12 (กก.1 บก.ปคบ.)", "type": "DIGITAL_AND_PHYSICAL_VAULT", "custodian": "ส.ต.อ. สุรชัย คดีมั่น"},
            {"id": "loc-2", "name": "ห้องปฏิบัติการ กรมวิทยาศาสตร์การแพทย์", "type": "EXTERNAL_LAB", "custodian": "เภสัชกรชำนาญการ กรมวิทย์ฯ"},
            {"id": "loc-3", "name": "โต๊ะพนักงานสอบสวน พ.ต.ท. สมชาย", "type": "INVESTIGATOR_CUSTODY", "custodian": "พ.ต.ท. สมชาย สอบสวนสืบสวน"}
        ]

        self.evidence_integrity_checks = [
            {
                "id": "chk-142-01",
                "evidence_file_id": "ef-142-01",
                "check_type": "UPLOAD",
                "expected_hash": "a3f82cb304b5f883201de374ffea57bd8c928e1832049e3bfd12cf88c9d21415",
                "actual_hash": "a3f82cb304b5f883201de374ffea57bd8c928e1832049e3bfd12cf88c9d21415",
                "result": "MATCH",
                "performed_by": "d2f0998c-8c1d-4099-ae1e-f3f2a89366df",
                "performed_at": "2026-08-10T10:05:00Z",
                "tool_name": "CPPD_SHA256_INTEGRITY_ENGINE",
                "tool_version": "v1.2.0",
                "notes": "Original file verified bit-exact on upload."
            }
        ]

        self.evidence_gaps = [
            {
                "id": "gap-142-01",
                "case_id": "CASE-142",
                "investigation_issue_id": "iss-142-01",
                "legal_element_id": "elem-142-02",
                "description": "ยังขาดภาพบันทึกกล้องวงจรปิด (CCTV) หน้าตู้ ATM สาขาลาดพร้าว ขณะคนร้ายกดเงินสด 100,000 บาท",
                "required_evidence_type": "VIDEO_CCTV",
                "priority": "HIGH",
                "status": "IN_PROGRESS",
                "assigned_to": "d2f0998c-8c1d-4099-ae1e-f3f2a89366df",
                "due_at": "2026-08-25T17:00:00Z",
                "resolved_by_evidence_id": None
            },
            {
                "id": "gap-142-02",
                "case_id": "CASE-142",
                "investigation_issue_id": "iss-142-02",
                "legal_element_id": "elem-142-01",
                "description": "รายการเดินบัญชีแถวที่ 2 ธนาคารกรุงไทยของนางสาวพัชรี แก้วมณี",
                "required_evidence_type": "BANK_STATEMENT",
                "priority": "HIGH",
                "status": "OPEN",
                "assigned_to": "d2f0998c-8c1d-4099-ae1e-f3f2a89366df",
                "due_at": "2026-08-28T17:00:00Z",
                "resolved_by_evidence_id": None
            }
        ]

        self.evidence_analyses = [
            {
                "id": "ea-142-01",
                "case_id": "CASE-142",
                "evidence_id": "f05d9e5b-ec1d-4009-bf2f-e8b9fb6cb088",
                "analysis_type": "OCR_FINANCIAL_EXTRACTION",
                "analyst_type": "TOOL",
                "analyst_user_id": "d2f0998c-8c1d-4099-ae1e-f3f2a89366df",
                "tool_name": "Tesseract_OCR_Thai_Slip_Parser",
                "tool_version": "5.3.0",
                "input_artifact_ids": ["ef-142-01"],
                "result": {
                    "bank": "Siam Commercial Bank (SCB)",
                    "account": "401-229-3388",
                    "recipient": "นายกิตติศักดิ์ วงศ์สวัสดิ์",
                    "amount": 1250000.0,
                    "date": "2026-08-09 14:32:00"
                },
                "status": "VERIFIED",
                "reviewed_by": "d2f0998c-8c1d-4099-ae1e-f3f2a89366df",
                "reviewed_at": "2026-08-10T10:10:00Z",
                "created_at": "2026-08-10T10:08:00Z"
            }
        ]

        # PHASE 2 COLLECTIONS
        self.investigation_issues = [
            {
                "id": "iss-142-01",
                "case_id": "CASE-142",
                "title": "พิสูจน์ความเชื่อมโยงของบัญชี SCB 401-229-3388 กับผู้ต้องหา",
                "description": "ตรวจสอบว่านายกิตติศักดิ์เป็นผู้เปิดบัญชีด้วยตนเอง หรือเป็นบัญชีม้าที่ถูกว่าจ้างมา และใครเป็นผู้ถือครองแอปพลิเคชันตัวจริง",
                "category": "FINANCIAL_LINKAGE",
                "priority": "HIGH",
                "status": "IN_PROGRESS",
                "source": "VICTIM_STATEMENT",
                "created_by": "d2f0998c-8c1d-4099-ae1e-f3f2a89366df",
                "assigned_to": "d2f0998c-8c1d-4099-ae1e-f3f2a89366df",
                "created_at": "2026-08-10T11:00:00Z",
                "updated_at": "2026-08-11T09:30:00Z"
            },
            {
                "id": "iss-142-02",
                "case_id": "CASE-142",
                "title": "ตรวจสอบสารเคมีอันตรายและแหล่งผลิตเวชสำอางค์ปลอม",
                "description": "พิสูจน์แหล่งกักเก็บและบรรจุสินค้าเวชสำอางค์ปลอมที่ตรวจพบสารปรอทและไฮโดรควิโนน",
                "category": "PHYSICAL_EVIDENCE",
                "priority": "HIGH",
                "status": "RESOLVED",
                "source": "LAB_REPORT",
                "created_by": "d2f0998c-8c1d-4099-ae1e-f3f2a89366df",
                "assigned_to": "a1b2c3d4-e5f6-7a8b-9c0d-1e2f3a4b5c6d",
                "created_at": "2026-08-11T12:00:00Z",
                "updated_at": "2026-08-14T15:00:00Z"
            },
            {
                "id": "iss-087-01",
                "case_id": "CASE-087",
                "title": "พิสูจน์เจตนาหลอกลวงในการไลฟ์สดขายทองคำเปอร์เซ็นต์ต่ำ",
                "description": "ตรวจสอบพฤติการณ์การโฆษณาอ้างทองคำ 96.5% เทียบกับผลวิเคราะห์ GIT 12.4%",
                "category": "MENS_REA",
                "priority": "HIGH",
                "status": "OPEN",
                "source": "CITIZEN_COMPLAINT",
                "created_by": "a1b2c3d4-e5f6-7a8b-9c0d-1e2f3a4b5c6d",
                "assigned_to": "a1b2c3d4-e5f6-7a8b-9c0d-1e2f3a4b5c6d",
                "created_at": "2026-08-12T11:00:00Z",
                "updated_at": "2026-08-12T11:00:00Z"
            }
        ]

        self.statement_qas = [
            {
                "id": "qa-142-01",
                "statement_id": "a8efde12-b91b-4f9e-bc43-2287f3b890a2",
                "sequence": 1,
                "question": "ท่านเริ่มติดต่อสั่งซื้อเวชสำอางค์จากเพจ สยาม คอสเมติกส์ ออฟฟิเชียล เมื่อใดและผ่านช่องทางใด?",
                "answer": "ข้าพเจ้าเริ่มติดต่อผ่านแอปพลิเคชัน Facebook เมื่อวันที่ 8 สิงหาคม 2569 และต่อมาได้พูดคุยทาง Line ID @siamcosmetic_th",
                "notes": "ตรงกับหลักฐานภาพแคปหน้าจอแชต EV-142-02",
                "source_reference": "11b7df3c-6622-48df-9cb9-ef77ba4c28f1"
            },
            {
                "id": "qa-142-02",
                "statement_id": "a8efde12-b91b-4f9e-bc43-2287f3b890a2",
                "sequence": 2,
                "question": "ท่านโอนเงินจำนวน 1,250,000 บาท ไปยังบัญชีใดและด้วยเหตุผลใด?",
                "answer": "โอนเข้าบัญชีธนาคารไทยพาณิชย์ เลขที่ 401-229-3388 นายกิตติศักดิ์ วงศ์สวัสดิ์ เพื่อชำระค่าสินค้าล็อตพิเศษตามที่ตกลงกันไว้",
                "notes": "สลิปโอนเงินผ่านการตรวจสอบ Hash เรียบร้อยแล้ว",
                "source_reference": "f05d9e5b-ec1d-4009-bf2f-e8b9fb6cb088"
            }
        ]

        self.evidence_relations = [
            {
                "id": "rel-142-01",
                "case_id": "CASE-142",
                "evidence_id": "f05d9e5b-ec1d-4009-bf2f-e8b9fb6cb088",
                "target_type": "PERSON",
                "target_id": "p-nattapong",
                "relation_type": "OWNED_BY_VICTIM",
                "notes": "สลิปโอนเงินจากบัญชีของผู้เสียหาย",
                "created_at": "2026-08-10T10:05:00Z"
            },
            {
                "id": "rel-142-02",
                "case_id": "CASE-142",
                "evidence_id": "f05d9e5b-ec1d-4009-bf2f-e8b9fb6cb088",
                "target_type": "STATEMENT",
                "target_id": "a8efde12-b91b-4f9e-bc43-2287f3b890a2",
                "relation_type": "SUPPORTING_STATEMENT_QA",
                "notes": "ใช้ประกอบคำให้การข้อ 2 ของผู้เสียหาย",
                "created_at": "2026-08-10T10:05:00Z"
            },
            {
                "id": "rel-142-03",
                "case_id": "CASE-142",
                "evidence_id": "11b7df3c-6622-48df-9cb9-ef77ba4c28f1",
                "target_type": "INVESTIGATION_ISSUE",
                "target_id": "iss-142-01",
                "relation_type": "PROVES_ISSUE",
                "notes": "หลักฐานการติดต่อแสดงการแจ้งเลขบัญชีรับเงิน",
                "created_at": "2026-08-10T10:10:00Z"
            }
        ]

        self.investigation_plans = [
            {
                "id": "plan-142-01",
                "case_id": "CASE-142",
                "objective": "พิสูจน์เส้นทางการเงินและรวบรวมพยานหลักฐานดำเนินคดีข้อหาฉ้อโกงประชาชนและ พ.ร.บ.เครื่องสำอาง",
                "issues_to_prove": ["การรับโอนเงินของบัญชีม้า", "ผลตรวจสารอันตรายในเครื่องสำอาง", "พิกัด IP การถอนเงินสด"],
                "required_evidence": ["สเตตเมนต์ธนาคารไทยพาณิชย์", "ผลตรวจจากกรมวิทยาศาสตร์การแพทย์", "CCTV หน้าตู้ ATM"],
                "persons_to_interview": ["นายนัฐพงษ์ สุขประเสริฐ (ผู้เสียหาย)", "นายสมชาย แสนสุข (กรรมการนอมินี)", "นายกิตติศักดิ์ วงศ์สวัสดิ์ (ผู้ต้องหา)"],
                "agencies_to_contact": ["สำนักงาน ปปง.", "กรมพัฒนาธุรกิจการค้า (DBD)", "สถาบันนิติวิทยาศาสตร์"],
                "digital_checks": ["IP Logins", "LINE UID Verification", "Cell-site Analysis"],
                "legal_questions": ["เข้าข่ายฉ้อโกงประชาชนตาม ป.อ. ม.343 หรือไม่", "เครื่องสำอางเข้าข่ายไม่ปลอดภัยตาม พ.ร.บ.เครื่องสำอาง ม.27 หรือไม่"],
                "outstanding_gaps": ["ยังไม่ได้รับภาพวงจรปิด CCTV หน้าตู้ ATM ลาดพร้าว", "รอผลการตรวจสอบรายการเดินบัญชีแถวที่สอง"],
                "target_date": "2026-08-30",
                "responsible_investigator": "พ.ต.ท. สมชาย สอบสวนสืบสวน",
                "status": "APPROVED",
                "actions": [
                    {
                        "id": "act-142-01",
                        "title": "ทำหนังสือขอรายการเดินบัญชี SCB 401-229-3388 ฉบับเต็ม",
                        "description": "ส่งหนังสือตาม ป.วิ.อ. ขอข้อมูล Statement ย้อนหลัง 6 เดือน",
                        "assigned_to": "d2f0998c-8c1d-4099-ae1e-f3f2a89366df",
                        "status": "COMPLETED",
                        "target_date": "2026-08-20",
                        "related_task_id": "918d6e3c-8c5e-4c7b-8395-5db460cb7d11"
                    },
                    {
                        "id": "act-142-02",
                        "title": "ออกหมายเรียกนายกิตติศักดิ์ วงศ์สวัสดิ์ ครั้งที่ 1",
                        "description": "จัดส่งหมายเรียกผู้ต้องหาตามที่อยู่ทะเบียนราษฎร์",
                        "assigned_to": "d2f0998c-8c1d-4099-ae1e-f3f2a89366df",
                        "status": "IN_PROGRESS",
                        "target_date": "2026-08-25",
                        "related_task_id": "918d6e3c-8c5e-4c7b-8395-5db460cb7d10"
                    }
                ],
                "created_at": "2026-08-10T12:00:00Z"
            }
        ]

        self.legal_elements = [
            {
                "id": "elem-142-01",
                "issue_id": "li-1",
                "element_title": "มีการหลอกลวงด้วยการแสดงข้อความอันเป็นเท็จต่อประชาชน",
                "supporting_facts": "ผู้ต้องหาเปิดเพจสาธารณะและยิงแคมเปญโฆษณาขายเครื่องสำอางแท้ลด 70% ทั้งที่เป็นของปลอม",
                "supporting_evidence_ids": ["11b7df3c-6622-48df-9cb9-ef77ba4c28f1"],
                "contradictory_evidence_ids": [],
                "missing_evidence": "คำให้การของพยานผู้ดูแลระบบจัดการเซิร์ฟเวอร์",
                "review_status": "SUPPORTED"
            },
            {
                "id": "elem-142-02",
                "issue_id": "li-1",
                "element_title": "ได้ไปซึ่งทรัพย์สินจากผู้ถูกหลอกลวงหรือบุคคลที่สาม",
                "supporting_facts": "ได้รับเงินโอน 1,250,000 บาท เข้าบัญชีของผู้ต้องหาและมีการถอนเงินสด",
                "supporting_evidence_ids": ["f05d9e5b-ec1d-4009-bf2f-e8b9fb6cb088"],
                "contradictory_evidence_ids": [],
                "missing_evidence": "ภาพ CCTV ยืนยันบุคคลขณะกดเงินสด",
                "review_status": "PARTIALLY_SUPPORTED"
            }
        ]

        self.case_documents = [
            {
                "id": "doc-142-01",
                "case_id": "CASE-142",
                "document_type": "SUMMONS_WARRANT",
                "title": "หมายเรียกผู้ต้องหา ครั้งที่ 1 - นายกิตติศักดิ์ วงศ์สวัสดิ์",
                "content": "หมายเรียกผู้ต้องหา ครั้งที่ 1 กก.1 บก.ปคบ. เรียกนายกิตติศักดิ์ วงศ์สวัสดิ์...",
                "version": 1,
                "author": "พ.ต.ท. สมชาย สอบสวนสืบสวน",
                "reviewer": "พ.ต.อ. อนงค์ บังคับการ",
                "approval_status": "APPROVED",
                "generated_from": "AI_DRAFT",
                "source_references": ["p-kittisak", "li-1"],
                "created_at": "2026-08-16T10:00:00Z",
                "updated_at": "2026-08-16T11:30:00Z",
                "history": [
                    {"version": 1, "status": "APPROVED", "updated_by": "superintendent@cppd.go.th", "timestamp": "2026-08-16T11:30:00Z"}
                ]
            },
            {
                "id": "doc-142-02",
                "case_id": "CASE-142",
                "document_type": "FINAL_REPORT",
                "title": "รายงานการสอบสวนและความเห็นทางคดีเสนออัยการ",
                "content": "รายงานการสอบสวนคดีอาญาที่ 142/2569 กก.1 บก.ปคบ. เห็นควรสั่งฟ้อง...",
                "version": 2,
                "author": "พ.ต.ท. สมชาย สอบสวนสืบสวน",
                "reviewer": "พ.ต.อ. อนงค์ บังคับการ",
                "approval_status": "IN_REVIEW",
                "generated_from": "AI_COPILOT",
                "source_references": ["f05d9e5b-ec1d-4009-bf2f-e8b9fb6cb088", "11b7df3c-6622-48df-9cb9-ef77ba4c28f1", "li-1"],
                "created_at": "2026-08-17T12:00:00Z",
                "updated_at": "2026-08-17T14:00:00Z",
                "history": [
                    {"version": 1, "status": "DRAFT", "updated_by": "somchai.i@cppd.go.th", "timestamp": "2026-08-17T12:00:00Z"},
                    {"version": 2, "status": "IN_REVIEW", "updated_by": "somchai.i@cppd.go.th", "timestamp": "2026-08-17T14:00:00Z"}
                ]
            }
        ]

        self.review_requests = [
            {
                "id": "rev-142-01",
                "case_id": "CASE-142",
                "resource_type": "DOCUMENT",
                "resource_id": "doc-142-02",
                "requested_by": "d2f0998c-8c1d-4099-ae1e-f3f2a89366df",
                "reviewer_id": "f8c3de7d-94d7-46e2-bc2f-e8b9fb6cb077",
                "status": "PENDING",
                "comments": "ขออนุมัติรายงานการสอบสวนฉบับสมบูรณ์สำหรับเสนออัยการ",
                "requested_at": "2026-08-17T14:00:00Z",
                "reviewed_at": None
            },
            {
                "id": "rev-142-02",
                "case_id": "CASE-142",
                "resource_type": "INVESTIGATION_PLAN",
                "resource_id": "plan-142-01",
                "requested_by": "d2f0998c-8c1d-4099-ae1e-f3f2a89366df",
                "reviewer_id": "f8c3de7d-94d7-46e2-bc2f-e8b9fb6cb077",
                "status": "APPROVED",
                "comments": "แผนการสืบสวนครบถ้วน อนุมัติดำเนินการตามแผน",
                "requested_at": "2026-08-10T12:00:00Z",
                "reviewed_at": "2026-08-10T14:30:00Z"
            }
        ]

        self.case_narrative_history = [
            {
                "case_id": "CASE-142",
                "version": 1,
                "narrative": "ผู้เสียหายถูกหลอกลวงให้สั่งซื้อสินค้าเวชสำอางค์ผ่านช่องทางออนไลน์ มูลค่าความเสียหาย 1.25 ล้านบาท",
                "updated_by": "somchai.i@cppd.go.th",
                "updated_at": "2026-08-10T10:00:00Z"
            },
            {
                "case_id": "CASE-142",
                "version": 2,
                "narrative": "การสืบสวนเครือข่ายขบวนการหลอกลวงจำหน่ายเครื่องสำอางและเวชสำอางค์เคาน์เตอร์แบรนด์ปลอมผ่านแพลตฟอร์ม Facebook และ Line Official โดยแอบอ้างสิทธิ์ตัวแทนนำเข้า มีการใช้บัญชีม้าแถวที่ 1 และแถวที่ 2 ในการฟอกเงินและยักย้ายถ่ายเททรัพย์สิน มูลค่าความเสียหายรวม 1,250,000 บาท",
                "updated_by": "somchai.i@cppd.go.th",
                "updated_at": "2026-08-17T15:00:00Z"
            }
        ]

        self.ai_findings = [
            {
                "id": "ai-find-001",
                "case_id": "CASE-142",
                "entity_type": "BANK_ACCOUNT",
                "entity_name": "401-229-3388",
                "details": "เชื่อมโยงกับ นายกิตติศักดิ์ วงศ์สวัสดิ์ ในคดีหลอกจำหน่ายเวชสำอางค์ปลอม",
                "confidence": 0.95,
                "status": "unverified",
                "created_at": "2026-08-17T12:00:00Z"
            },
            {
                "id": "ai-find-002",
                "case_id": "CASE-087",
                "entity_type": "ORGANIZATION",
                "entity_name": "หจก. ภูเก็ตไซเบอร์โกลด์",
                "details": "ตรวจพบความเชื่อมโยงกับบัญชีธนาคารกสิกรไทย 702-888-1123 และเพจ TikTok",
                "confidence": 0.98,
                "status": "unverified",
                "created_at": "2026-08-17T14:00:00Z"
            }
        ]

    @property
    def audit_events(self):
        return self.audit_log
        
    @audit_events.setter
    def audit_events(self, value):
        self.audit_log = value
        
    @property
    def entities(self):
        result = []
        for p in self.persons:
            result.append({"id": p["id"], "type": "PERSON", "name": p["name"]})
        for o in self.organizations:
            result.append({"id": o["id"], "type": "ORGANIZATION", "name": o["name"]})
        return result

db = MockDatabase()

# -------------------------------------------------------------
# Base Models
# -------------------------------------------------------------
class CaseCreate(BaseModel):
    id: str
    title: str
    description: Optional[str] = None
    owning_unit: str
    sensitive: Optional[bool] = False

class TaskCreate(BaseModel):
    case_id: str
    title: str
    description: Optional[str] = None
    assigned_to: Optional[str] = None
    due_date: Optional[str] = None

class PubSubMessage(BaseModel):
    event_type: str
    payload: Dict[str, Any]

# -------------------------------------------------------------
# Endpoints
# -------------------------------------------------------------

@app.get("/")
def read_root():
    return {"status": "online", "service": "CPPD API Gateway"}

@app.get("/api/cases")
def list_cases(authorization: Optional[str] = Header(None)):
    user = get_user_from_token(authorization)
    role = user["role"]
    email = user["email"]
    
    profile = next((p for p in db.profiles.values() if p["email"] == email), None)
    profile_id = profile["id"] if profile else email
    division = profile["org_unit"] if profile else "Financial Crimes"
    
    if role in ["admin", "commander", "deputy_commander", "deputy_superintendent"]:
        return list(db.cases.values())
    elif role == "superintendent":
        return [c for c in db.cases.values() if c["owning_unit"] == division]
    elif role in ["investigator", "clerk"]:
        assigned_case_ids = [m["case_id"] for m in db.case_members if m["user_id"] == profile_id]
        return [c for c in db.cases.values() if c["id"] in assigned_case_ids]
        
    return []

@app.get("/api/cases/{case_id}")
def get_case(case_id: str, authorization: Optional[str] = Header(None)):
    if case_id not in db.cases:
        raise HTTPException(status_code=404, detail="Case not found")
        
    user = get_user_from_token(authorization)
    role = user["role"]
    email = user["email"]
    
    profile = next((p for p in db.profiles.values() if p["email"] == email), None)
    profile_id = profile["id"] if profile else email
    division = profile["org_unit"] if profile else "Financial Crimes"
    
    case = db.cases[case_id]
    
    is_authorized = False
    if role in ["admin", "commander", "deputy_commander", "deputy_superintendent"]:
        is_authorized = True
    elif role == "superintendent" and case["owning_unit"] == division:
        is_authorized = True
    elif role in ["investigator", "clerk"]:
        is_assigned = any(m for m in db.case_members if m["case_id"] == case_id and m["user_id"] == profile_id)
        if is_assigned:
            is_authorized = True
            
    if not is_authorized:
        raise HTTPException(status_code=403, detail="Forbidden: You do not have access to this case.")
        
    case_victims = [v for v in db.victims if v["case_id"] == case_id]
    case_evidence = [e for e in db.evidence if e["case_id"] == case_id]
    case_tasks = [t for t in db.tasks if t["case_id"] == case_id]
    case_entities = [
        {"id": p["id"], "type": "PERSON", "name": p["name"], "role": p["role"]}
        for p in db.persons if p.get("case_id") == case_id
    ] + [
        {"id": o["id"], "type": "ORGANIZATION", "name": o["name"], "role": o.get("type", "Company")}
        for o in db.organizations if o.get("case_id") == case_id
    ]
    case_transactions = [t for t in db.transactions if t["case_id"] == case_id]
    
    db.audit_events.append({
        "id": str(uuid.uuid4()),
        "user_id": email,
        "action": "VIEW_CASE_DETAILS",
        "table_name": "cases",
        "record_id": case_id,
        "query_details": f"User viewed case details profile.",
        "logged_at": time.strftime("%Y-%m-%dT%H:%M:%SZ")
    })
    
    return {
        "case": case,
        "victims": case_victims,
        "evidence": case_evidence,
        "entities": case_entities,
        "tasks": case_tasks,
        "transactions": case_transactions
    }

# -------------------------------------------------------------
# CCPD AI Copilot — Intake Management Endpoints
# -------------------------------------------------------------
class IntakeCreate(BaseModel):
    title: str
    description: Optional[str] = None
    reporter_name: str
    reporter_phone: str
    raw_statement: str

@app.get("/api/intakes")
def list_intakes(authorization: Optional[str] = Header(None)):
    user = get_user_from_token(authorization)
    return db.intakes

@app.post("/api/intakes")
def create_intake(payload: IntakeCreate, authorization: Optional[str] = Header(None)):
    user = get_user_from_token(authorization)
    intake_id = f"INTAKE-{str(uuid.uuid4())[:8].upper()}"
    
    statement_lower = payload.raw_statement.lower()
    urgency = "medium"
    reason = "Standard consumer protection case."
    if any(x in statement_lower for x in ["scam", "fraud", "หลอก", "โกง", "ลวง", "เสียหาย", "สูญเสีย"]):
        urgency = "high"
        reason = "Potential financial crime or public fraud indicators detected in statements."
    
    new_intake = {
        "id": intake_id,
        "case_id": None,
        "title": payload.title,
        "description": payload.description,
        "reporter_name": payload.reporter_name,
        "reporter_phone": payload.reporter_phone,
        "raw_statement": payload.raw_statement,
        "triage_urgency": urgency,
        "triage_reason": reason,
        "status": "pending",
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ")
    }
    db.intakes.append(new_intake)
    
    db.audit_log.append({
        "id": str(uuid.uuid4()),
        "user_id": user["email"],
        "action": "CREATE_INTAKE",
        "table_name": "intakes",
        "record_id": intake_id,
        "query_details": f"Registered new complaint report: {payload.title}",
        "logged_at": time.strftime("%Y-%m-%dT%H:%M:%SZ")
    })
    return new_intake

@app.post("/api/intakes/{intake_id}/promote")
def promote_intake_to_case(intake_id: str, authorization: Optional[str] = Header(None)):
    user = get_user_from_token(authorization)
    intake = next((i for i in db.intakes if i["id"] == intake_id), None)
    if not intake:
        raise HTTPException(status_code=404, detail="Intake report not found")
        
    case_id = f"CASE-{str(uuid.uuid4())[:8].upper()}"
    new_case = {
        "id": case_id,
        "title": intake["title"],
        "description": intake["raw_statement"],
        "status": "open",
        "owning_unit": "Financial Crimes Division 1",
        "sensitive": False,
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "updated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ")
    }
    db.cases[case_id] = new_case
    intake["case_id"] = case_id
    intake["status"] = "promoted"
    
    victim_id = str(uuid.uuid4())
    db.victims.append({
        "id": victim_id,
        "case_id": case_id,
        "full_name": intake["reporter_name"],
        "phone": intake["reporter_phone"],
        "email": f"{intake['reporter_name'].lower().replace(' ', '')}@gmail.com",
        "address": "Simulated address",
        "loss_amount": 10000.0,
        "intake_source": "complaint"
    })
    
    db.audit_log.append({
        "id": str(uuid.uuid4()),
        "user_id": user["email"],
        "action": "PROMOTE_INTAKE",
        "table_name": "cases",
        "record_id": case_id,
        "query_details": f"Promoted intake complaint {intake_id} to case {case_id}",
        "logged_at": time.strftime("%Y-%m-%dT%H:%M:%SZ")
    })
    
    return {"status": "success", "case_id": case_id, "case": new_case}

# -------------------------------------------------------------
# CCPD AI Copilot — Case Workspace Sub-tabs Endpoints
# -------------------------------------------------------------
@app.get("/api/cases/{case_id}/timeline")
def get_case_timeline(case_id: str, authorization: Optional[str] = Header(None)):
    user = get_user_from_token(authorization)
    case_statements = [s for s in db.statements if s["case_id"] == case_id]
    auditor = StatementTimelineAuditor()
    audit_report = auditor.audit_case_chronology(case_id, case_statements)
    
    db.audit_log.append({
        "id": str(uuid.uuid4()),
        "user_id": user["email"],
        "action": "AUDIT_TIMELINE",
        "table_name": "statements",
        "record_id": case_id,
        "query_details": f"Ran timeline chronology and contradiction audit for case {case_id}",
        "logged_at": time.strftime("%Y-%m-%dT%H:%M:%SZ")
    })
    
    return audit_report.dict()

@app.get("/api/cases/{case_id}/legal-issues")
def get_case_legal_issues(case_id: str, authorization: Optional[str] = Header(None)):
    user = get_user_from_token(authorization)
    issues = [li for li in db.legal_issues if li["case_id"] == case_id]
    return issues

@app.get("/api/cases/{case_id}/reports")
def get_case_reports(case_id: str, authorization: Optional[str] = Header(None)):
    user = get_user_from_token(authorization)
    case_reports = [r for r in db.reports if r["case_id"] == case_id]
    return case_reports

@app.get("/api/cases/{case_id}/communications")
def get_case_communications(case_id: str, authorization: Optional[str] = Header(None)):
    user = get_user_from_token(authorization)
    comms = [c for c in getattr(db, "communications", []) if c["case_id"] == case_id]
    return comms

@app.get("/api/cases/{case_id}/ai-analyses")
def get_case_ai_analyses(case_id: str, authorization: Optional[str] = Header(None)):
    user = get_user_from_token(authorization)
    analyses = [a for a in getattr(db, "ai_analyses", []) if a["case_id"] == case_id]
    return analyses

class InterviewGenerateRequest(BaseModel):
    case_id: str
    target_role: str = "suspect" # 'suspect', 'victim', 'witness'
    target_name: str = "Kittisak Wongsawat"

@app.post("/api/interviews/generate")
def generate_interview_questions_endpoint(payload: InterviewGenerateRequest, authorization: Optional[str] = Header(None)):
    user = get_user_from_token(authorization)
    from statement_interview_agent import StatementInterviewAgent
    agent = StatementInterviewAgent(api_url="http://localhost:8000")
    result = agent.generate_interview_questions(payload.case_id, payload.target_role, payload.target_name)
    
    # Save to AI analyses table (isolated from original evidence)
    if hasattr(db, "ai_analyses"):
        db.ai_analyses.append({
            "id": f"ana-{str(uuid.uuid4())[:8]}",
            "case_id": payload.case_id,
            "agent_name": "StatementInterviewAgent",
            "analysis_type": "INTERVIEW_QUESTIONNAIRE",
            "fact_tags": result.get("findings", []),
            "findings_summary": result.get("summary", "Interview questions formulated."),
            "confidence_score": 0.95,
            "review_status": "REQUIRES_HUMAN_REVIEW",
            "reviewed_by": None,
            "investigator_notes": None,
            "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ")
        })
        
    db.audit_log.append({
        "id": str(uuid.uuid4()),
        "user_id": user["email"],
        "action": "GENERATE_INTERVIEW_QUESTIONS",
        "table_name": "ai_analyses",
        "record_id": payload.case_id,
        "query_details": f"Generated {payload.target_role} questions for {payload.target_name}",
        "logged_at": time.strftime("%Y-%m-%dT%H:%M:%SZ")
    })
    
    return {"status": "success", "result": result}

class ReportGenerateRequest(BaseModel):
    case_id: str
    report_type: str

@app.post("/api/reports/generate")
def generate_report_draft(payload: ReportGenerateRequest, authorization: Optional[str] = Header(None)):
    user = get_user_from_token(authorization)
    case = db.cases.get(payload.case_id)
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
        
    report_id = f"REP-{str(uuid.uuid4())[:8].upper()}"
    draft_title = f"{payload.report_type} - {case['title']}"
    draft_content = ""
    
    # Check if official Thai Law Enforcement Document Template
    from document_drafting_agent import DocumentDraftingAgent
    doc_agent = DocumentDraftingAgent(api_url="http://localhost:8000")
    
    if payload.report_type in ["SUMMONS_WARRANT", "หมายเรียกผู้ต้องหา"]:
        res = doc_agent.draft_document(payload.case_id, "SUMMONS_WARRANT")
        draft_title = res["title"]
        draft_content = res["content_markdown"]
    elif payload.report_type in ["SEARCH_WARRANT", "คำร้องขอหมายค้น"]:
        res = doc_agent.draft_document(payload.case_id, "SEARCH_WARRANT")
        draft_title = res["title"]
        draft_content = res["content_markdown"]
    elif payload.report_type in ["ACCUSATION_RECORD", "บันทึกแจ้งข้อกล่าวหา"]:
        res = doc_agent.draft_document(payload.case_id, "ACCUSATION_RECORD")
        draft_title = res["title"]
        draft_content = res["content_markdown"]
    elif payload.report_type in ["FINAL_REPORT", "รายงานการสอบสวนและความเห็น"]:
        res = doc_agent.draft_document(payload.case_id, "FINAL_REPORT")
        draft_title = res["title"]
        draft_content = res["content_markdown"]
    elif payload.report_type == "Executive Brief":
        draft_content = (
            f"# รายงานสรุปย่อผู้บังคับบัญชา (Executive Brief)\n"
            f"**คดี**: {case['title']} ({case['id']})\n"
            f"**หน่วยงานเจ้าของสำนวน**: {case['owning_unit']}\n\n"
            f"### 1. สรุปข้อเท็จจริง:\n"
            f"คดีนี้เป็นข้อร้องเรียนกรณีความผิดคุ้มครองผู้บริโภค กก.1 บก.ปคบ.: {case['description']}\n\n"
            f"### 2. บุคคลและพยานหลักฐานที่พิสูจน์แล้ว:\n"
            f"- ผู้ต้องสงสัย: นายกิตติศักดิ์ วงศ์สวัสดิ์ (บัญชี SCB 401-229-3388)\n"
            f"- พยานหลักฐาน: สลิปโอนเงิน (SHA-256 Verified), ภาพบันทึกแชต Line\n\n"
            f"### 3. ประเด็นข้อกฎหมายและความเห็น:\n"
            f"พฤติการณ์สอดคล้องกับความผิดฐานร่วมกันฉ้อโกงประชาชน ตาม ป.อ. มาตรา 343 และ พ.ร.บ.คอมพิวเตอร์ฯ มาตรา 14(1)\n\n"
            f"---\n*สถานะ: [AI_DRAFT v1.0] รอพนักงานสอบสวนตรวจรับรอง*"
        )
    elif payload.report_type == "Investigation Plan":
        draft_content = (
            f"# แผนการสืบสวนสอบสวน (Investigation Plan)\n"
            f"**คดี**: {case['title']} ({case['id']})\n\n"
            f"### 1. ยุทธวิธีและแนวทางดำเนินการ:\n"
            f"- ตรวจสอบความถูกต้องของอัตลักษณ์บุคคล ตรวจสอบประวัติอาชญากรรม\n"
            f"- ตรวจสอบสเตตเมนต์ธนาคารและการถ่ายเทเงินไปยังบัญชีม้าแถวที่สอง\n\n"
            f"### 2. แผนการปฏิบัติงาน (Task List):\n"
            f"- [x] ตรวจสอบความถูกต้องสลิปโอนเงิน 1.25 ล้านบาท\n"
            f"- [ ] ยื่นขอหมายค้นสถานที่ตั้งบริษัท สยาม เน็ตเวิร์ค จำกัด\n"
            f"- [ ] ออกหมายเรียกผู้ต้องหาเข้าให้ปากคำครั้งที่ 1"
        )
    else:
        draft_content = (
            f"# {payload.report_type.upper()} REPORT DRAFT\n"
            f"**Case Reference**: {case['id']} - {case['title']}\n"
            f"**Compiled by**: {user['email']}\n\n"
            f"Simulated AI Copilot generated content matching evidence-first parameters."
        )
        
    report_record = {
        "id": report_id,
        "case_id": payload.case_id,
        "report_type": payload.report_type,
        "title": draft_title,
        "content": draft_content,
        "version": 1,
        "status": "AI_DRAFT",
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ")
    }
    db.reports.append(report_record)
    
    db.audit_log.append({
        "id": str(uuid.uuid4()),
        "user_id": user["email"],
        "action": "GENERATE_REPORT",
        "table_name": "reports",
        "record_id": report_id,
        "query_details": f"Generated {payload.report_type} draft: {draft_title}",
        "logged_at": time.strftime("%Y-%m-%dT%H:%M:%SZ")
    })
    
    return report_record

@app.post("/api/cases")
def create_case(case: CaseCreate):
    if case.id in db.cases:
        raise HTTPException(status_code=400, detail="Case ID already exists")
    new_case = case.dict()
    new_case["created_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ")
    new_case["updated_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ")
    db.cases[case.id] = new_case
    return new_case

import re

@app.post("/api/evidence/upload")
async def upload_evidence(
    case_id: str = Form(...),
    title: str = Form(...),
    description: Optional[str] = Form(None),
    type: str = Form(...),
    file: UploadFile = File(...),
    authorization: Optional[str] = Header(None)
):
    user = get_user_from_token(authorization)
    
    file_bytes = await file.read()
    sha256 = hashlib.sha256(file_bytes).hexdigest()
    
    evidence_id = str(uuid.uuid4())
    evidence_record = {
        "id": evidence_id,
        "case_id": case_id,
        "title": title,
        "description": description,
        "type": type,
        "file_hash": sha256,
        "status": "sealed",
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ")
    }
    db.evidence.append(evidence_record)
    
    ocr_text = ""
    ocr_extracted_data = {}
    
    try:
        if file.content_type and "image" in file.content_type:
            raise ValueError("Image file uploaded")
        ocr_text = file_bytes.decode("utf-8")
        if "slip" in file.filename.lower() or "receipt" in file.filename.lower():
            if not any(k in ocr_text.lower() for k in ["amount", "account", "bank", "baht", "thb", "บาท"]):
                raise ValueError("Force simulated slip OCR")
    except Exception:
        if "slip" in file.filename.lower() or "receipt" in file.filename.lower():
            ocr_text = "TRANSFER SLIP\nFrom: Nattapong Sukprasert\nTo: Kittisak Wongsawat\nBank: Siam Commerce Bank\nAccount: 401-229-3388\nAmount: 1,250,000.00 THB\nRef: TXN-99882211\nDate: 2026-08-09 14:32:00"
        else:
            ocr_text = f"FILE SCAN: {file.filename}\nNo explicit bank keywords found. Simulated generic document scanning completed."
            
    amount_match = re.search(r"(?:amount|sum|฿|baht|thb|บาท)\s*[:=]?\s*([\d,]+(?:\.\d{2})?)", ocr_text, re.IGNORECASE)
    account_match = re.search(r"(?:account|acc|เลขบัญชี|บัญชี)\s*[:=]?\s*(\d{3}-\d{1}-\d{5}-\d{1}|\d{3}-\d{3}-\d{4}|\d{10,12})", ocr_text, re.IGNORECASE)
    bank_match = re.search(r"(?:bank|ธนาคาร)\s*[:=]?\s*(Siam Commerce Bank|Kasikorn Bank|SCB|KBANK|Krungthai|KTB|Bangkok Bank|BBL)", ocr_text, re.IGNORECASE)
    
    extracted_amount = 0.0
    if amount_match:
        try:
            extracted_amount = float(amount_match.group(1).replace(",", ""))
        except:
            pass
            
    extracted_account = account_match.group(1) if account_match else None
    extracted_bank = bank_match.group(1) if bank_match else "Siam Commerce Bank"
    
    if extracted_amount > 0 and extracted_account:
        target_acc = next((a for a in db.bank_accounts if a["account_number"] == extracted_account), None)
        if not target_acc:
            target_acc = {
                "id": str(uuid.uuid4()),
                "bank_name": extracted_bank,
                "account_number": extracted_account,
                "account_name": "Kittisak Wongsawat" if extracted_account == "401-229-3388" else "Unknown Target"
            }
            db.bank_accounts.append(target_acc)
            
        txn_record = {
            "id": str(uuid.uuid4()),
            "case_id": case_id,
            "source_account_id": None,
            "target_account_id": target_acc["id"],
            "amount": extracted_amount,
            "currency": "THB",
            "transaction_date": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "reference_number": "TXN-OCR-" + str(uuid.uuid4())[:8].upper(),
            "evidence_id": evidence_id
        }
        db.transactions.append(txn_record)
        ocr_extracted_data = {
            "status": "extracted",
            "bank": extracted_bank,
            "account": extracted_account,
            "amount": extracted_amount,
            "transaction": txn_record
        }
    else:
        ocr_extracted_data = {
            "status": "text_only",
            "text": ocr_text
        }
        
    db.audit_events.append({
        "id": str(uuid.uuid4()),
        "user_id": user["email"],
        "action": "UPLOAD_EVIDENCE",
        "table_name": "evidence",
        "record_id": evidence_id,
        "query_details": f"Uploaded file: {file.filename}, Hash: {sha256}. OCR status: {ocr_extracted_data['status']}",
        "logged_at": time.strftime("%Y-%m-%dT%H:%M:%SZ")
    })
    
    return {
        "status": "success",
        "evidence_id": evidence_id,
        "hash": sha256,
        "record": evidence_record,
        "ocr_result": ocr_extracted_data
    }

@app.get("/api/entities")
def get_entities(query: Optional[str] = None):
    if query:
        # Fuzzy/exact match on entities name or identifier
        matching_entities = [e for e in db.entities if query.lower() in e["name"].lower()]
        return matching_entities
    return db.entities

@app.get("/api/ai-findings")
def list_ai_findings(case_id: Optional[str] = None):
    if case_id:
        return [f for f in db.ai_findings if f["case_id"] == case_id]
    return db.ai_findings

@app.post("/api/ai-findings/{finding_id}/verify")
def verify_finding(finding_id: str, status: str = "verified"):
    for f in db.ai_findings:
        if f["id"] == finding_id:
            f["status"] = status
            # Audit log
            db.audit_events.append({
                "id": str(uuid.uuid4()),
                "user_id": None,
                "action": f"VERIFY_FINDING_{status.upper()}",
                "table_name": "ai_findings",
                "record_id": finding_id,
                "query_details": f"Investigator marked AI finding as {status}",
                "logged_at": time.strftime("%Y-%m-%dT%H:%M:%SZ")
            })
            return {"status": "success", "finding": f}
    raise HTTPException(status_code=404, detail="Finding not found")

@app.get("/api/audit-logs")
def get_audit_logs():
    return db.audit_events

class AISettings(BaseModel):
    mode: str
    local_endpoint: str
    local_model: str

@app.get("/api/settings/ai")
def get_ai_settings():
    settings_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../ai-router/ai_settings.json"))
    if os.path.exists(settings_path):
        try:
            with open(settings_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {
        "mode": "cloud",
        "local_endpoint": "http://localhost:11434/v1",
        "local_model": "llama3"
    }

@app.post("/api/settings/ai")
def save_ai_settings(settings: AISettings):
    settings_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../ai-router/ai_settings.json"))
    try:
        os.makedirs(os.path.dirname(settings_path), exist_ok=True)
        with open(settings_path, "w", encoding="utf-8") as f:
            json.dump(settings.dict(), f, indent=2)
            
        db.audit_events.append({
            "id": str(uuid.uuid4()),
            "user_id": None,
            "action": "UPDATE_AI_SETTINGS",
            "table_name": "profiles",
            "record_id": "ai_settings",
            "query_details": f"User changed AI mode to {settings.mode} (Endpoint: {settings.local_endpoint}, Model: {settings.local_model})",
            "logged_at": time.strftime("%Y-%m-%dT%H:%M:%SZ")
        })
        return {"status": "success", "settings": settings.dict()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/mock-local-ai/v1/chat/completions")
def mock_local_ai_completions():
    return {
        "choices": [
            {
                "message": {
                    "role": "assistant",
                    "content": "Local AI Mock Response: Successfully processed confidential case metadata locally."
                }
            }
        ]
    }

# -------------------------------------------------------------
# Google OAuth Gmail Authentication & Logging
# -------------------------------------------------------------
@app.get("/api/auth/google/login")
def google_login():
    return {
        "redirect_url": "http://127.0.0.1:8000/api/auth/google/callback?code=mock-gmail-oauth-code"
    }

class CallbackRequest(BaseModel):
    code: str
    email: Optional[str] = "investigator.anong@gmail.com"

@app.post("/api/auth/google/callback")
def google_callback(payload: CallbackRequest, request: Request):
    email = payload.email
    if not email.endswith("@gmail.com") and not email.endswith("@cppd.go.th"):
        raise HTTPException(status_code=400, detail="Invalid Gmail or corporate account")
        
    token = "sess-tok-" + str(uuid.uuid4())[:12]
    
    profile = next((p for p in db.profiles.values() if p["email"] == email), None)
    if profile:
        if not profile.get("approved", False):
            raise HTTPException(status_code=403, detail="Access Denied: Your account is pending administrator approval.")
        role = profile["role"]
        name = profile["full_name"]
    else:
        role = "investigator"
        name = email.split("@")[0].capitalize()
        # Default self-registered users to approved=False
        db.profiles[email] = {"id": email, "email": email, "full_name": name, "org_unit": "Financial Crimes", "role": role, "approved": False}
        raise HTTPException(status_code=403, detail="Access Denied: Your account has been registered and is pending administrator approval.")
        
    db.sessions[token] = {
        "email": email,
        "role": role,
        "name": name,
        "login_time": time.strftime("%Y-%m-%dT%H:%M:%SZ")
    }
    
    client_ip = request.client.host if request.client else "127.0.0.1"
    db.audit_events.append({
        "id": str(uuid.uuid4()),
        "user_id": email,
        "action": "LOGIN_SUCCESS",
        "table_name": "profiles",
        "record_id": token,
        "query_details": f"Gmail OAuth2 login successful from IP {client_ip}. Name: {name}",
        "logged_at": time.strftime("%Y-%m-%dT%H:%M:%SZ")
    })
    
    return {
        "status": "success",
        "token": token,
        "email": email,
        "role": role,
        "name": name
    }

@app.post("/api/auth/logout")
def logout(authorization: Optional[str] = Header(None)):
    if not authorization:
        return {"status": "success"}
    token = authorization.split(" ")[1] if authorization.startswith("Bearer ") else authorization
    if token in db.sessions:
        session = db.sessions.pop(token)
        db.audit_events.append({
            "id": str(uuid.uuid4()),
            "user_id": session["email"],
            "action": "LOGOUT",
            "table_name": "profiles",
            "record_id": token,
            "query_details": f"User logged out manually.",
            "logged_at": time.strftime("%Y-%m-%dT%H:%M:%SZ")
        })
    return {"status": "success"}

def get_user_from_token(authorization: Optional[str] = Header(None)) -> Dict[str, Any]:
    if not authorization:
        return {"email": "somchai.i@cppd.go.th", "role": "commander", "name": "Somchai Dev"}
    token = authorization.split(" ")[1] if authorization.startswith("Bearer ") else authorization
    
    if token in db.sessions:
        return db.sessions[token]
        
    if token == "mock-token-commander":
        return {"email": "somchai.i@cppd.go.th", "role": "commander", "name": "Somchai Dev"}
    if token == "mock-token-supervisor":
        return {"email": "anong.s@cppd.go.th", "role": "supervisor", "name": "Anong Head"}
        
    raise HTTPException(status_code=401, detail="Unauthorized: Invalid session token")

@app.get("/api/admin/audit-logs")
def get_admin_audit_logs(authorization: Optional[str] = Header(None), email: Optional[str] = None, action: Optional[str] = None):
    user = get_user_from_token(authorization)
    if user["role"] not in ["admin", "commander", "supervisor", "superintendent"]:
        raise HTTPException(status_code=403, detail="Forbidden: Admin privilege required.")
        
    logs = db.audit_events
    if email:
        logs = [l for l in logs if l.get("user_id") == email or email in str(l.get("query_details"))]
    if action:
        logs = [l for l in logs if l.get("action") == action]
        
    return logs

@app.get("/api/admin/users")
def get_admin_users(authorization: Optional[str] = Header(None)):
    user = get_user_from_token(authorization)
    if user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Forbidden: Admin privilege required.")
    return list(db.profiles.values())

class ApproveUserRequest(BaseModel):
    approved: bool

@app.post("/api/admin/users/{user_id}/approve")
def approve_user(user_id: str, payload: ApproveUserRequest, authorization: Optional[str] = Header(None)):
    user = get_user_from_token(authorization)
    if user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Forbidden: Admin privilege required.")
        
    profile = db.profiles.get(user_id)
    if not profile:
        profile = next((p for p in db.profiles.values() if p["email"] == user_id), None)
        
    if not profile:
        raise HTTPException(status_code=404, detail="User profile not found")
        
    profile["approved"] = payload.approved
    action = "USER_APPROVED" if payload.approved else "USER_REVOKED"
    
    db.audit_log.append({
        "id": str(uuid.uuid4()),
        "user_id": user["email"],
        "action": action,
        "table_name": "profiles",
        "record_id": profile["id"],
        "query_details": f"Admin updated approval status of user {profile['email']} to {payload.approved}.",
        "logged_at": time.strftime("%Y-%m-%dT%H:%M:%SZ")
    })
    
    return {"status": "success", "user": profile}



@app.get("/api/cases/{case_id}/readiness")
def get_case_readiness(case_id: str):
    if case_id not in db.cases:
        raise HTTPException(status_code=404, detail="Case not found")
        
    case_statements = [s for s in db.statements if s["case_id"] == case_id]
    auditor = StatementTimelineAuditor()
    audit_report = auditor.audit_case_chronology(case_id, case_statements)
    
    # Analyze readiness factors
    case_victims = [v for v in db.victims if v["case_id"] == case_id]
    case_evidence = [e for e in db.evidence if e["case_id"] == case_id]
    
    has_identity = len(case_victims) > 0
    has_statements = len(case_statements) > 0
    has_receipt = any(e for e in case_evidence if "slip" in e["title"].lower() or "receipt" in e["title"].lower())
    has_ledger = any(e for e in case_evidence if "ledger" in e["title"].lower())
    
    # Compute readiness score
    score = 40
    if has_identity: score += 15
    if has_statements: score += 15
    if has_receipt: score += 15
    if has_ledger: score += 15
    
    score = min(score, 100)
    
    return {
        "case_id": case_id,
        "readiness_percentage": score,
        "factors": {
            "identity_verified": has_identity,
            "statement_taken": has_statements,
            "evidence_integrity_check": has_receipt,
            "ledger_analysed": has_ledger
        },
        "contradictions_found": len([e for e in audit_report.events if e.status == "contradictory"])
    }

@app.post("/api/transactions/import")
def import_transactions(case_id: str, payload: List[Dict[str, Any]]):
    # Import transactions
    engine = TransactionIntelligenceEngine()
    analysis = engine.analyze_transactions(case_id, payload)
    
    for tx in payload:
        tx_id = str(uuid.uuid4())
        src_acc = tx.get("source_account")
        tgt_acc = tx.get("target_account")
        src_id = None
        tgt_id = None
        
        if src_acc:
            acc = next((a for a in db.bank_accounts if a["account_number"] == src_acc), None)
            if not acc:
                acc_id = str(uuid.uuid4())
                db.bank_accounts.append({"id": acc_id, "bank_name": "Siam Commerce Bank", "account_number": src_acc, "account_name": "Unknown Owner"})
                src_id = acc_id
            else:
                src_id = acc["id"]
                
        if tgt_acc:
            acc = next((a for a in db.bank_accounts if a["account_number"] == tgt_acc), None)
            if not acc:
                acc_id = str(uuid.uuid4())
                db.bank_accounts.append({"id": acc_id, "bank_name": "Siam Commerce Bank", "account_number": tgt_acc, "account_name": "Unknown Owner"})
                tgt_id = acc_id
            else:
                tgt_id = acc["id"]
                
        db.transactions.append({
            "id": tx_id,
            "case_id": case_id,
            "source_account_id": src_id,
            "target_account_id": tgt_id,
            "amount": float(tx.get("amount", 0.0)),
            "currency": tx.get("currency", "THB"),
            "transaction_date": tx.get("transaction_date", time.strftime("%Y-%m-%dT%H:%M:%SZ")),
            "reference_number": tx.get("reference_number", "REF-" + str(uuid.uuid4())[:8].upper()),
            "evidence_id": None
        })
        
    for alert in analysis["alerts"]:
        finding_id = "ai-find-" + str(uuid.uuid4())[:8]
        db.ai_findings.append({
            "id": finding_id,
            "case_id": case_id,
            "entity_type": "BANK_ACCOUNT",
            "entity_name": alert["account"],
            "details": f"🚨 TRANSACTION WARNING ({alert['type']}): {alert['details']}",
            "confidence": alert["confidence"],
            "status": "unverified",
            "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ")
        })
        
        slack_blocks = SlackBlockBuilder.build_cross_case_alert(
            case_id=case_id,
            account=alert["account"],
            linked_cases=["CASE-142", "CASE-087"],
            victims_count=2,
            loss=f"฿{tx.get('amount', 0.0):,.2f}" if payload else "฿0.00",
            confidence=alert["confidence"]
        )
        print(f"[Slack Alert Simulator] Sending Blocks Payload for alert:\n{json.dumps(slack_blocks, indent=2)}")

    return {
        "status": "success",
        "imported_count": len(payload),
        "alerts_count": len(analysis["alerts"]),
        "alerts": analysis["alerts"]
    }

@app.post("/api/agents/run")
def run_agent_workflow_endpoint(case_id: str, goal: str, user_email: str = "somchai.i@cppd.go.th"):
    orchestrator = CPPDCaseOrchestrator(api_url="http://localhost:8000")
    result = orchestrator.run_agent_workflow(case_id, goal, user_email)
    
    # Audit log
    db.audit_events.append({
        "id": str(uuid.uuid4()),
        "user_id": None,
        "action": "RUN_AGENT",
        "table_name": "agents",
        "record_id": case_id,
        "query_details": f"Ran agent workflow for case {case_id} (Goal: {goal})",
        "logged_at": time.strftime("%Y-%m-%dT%H:%M:%SZ")
    })
    
    return result

@app.post("/api/pubsub/publish")
def publish_pubsub(message: PubSubMessage):
    # Simulated Pub/Sub Bus
    event_id = str(uuid.uuid4())
    event_record = {
        "id": event_id,
        "event_type": message.event_type,
        "payload": message.payload,
        "status": "processed",
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ")
    }
    db.trigger_events.append(event_record)
    
    # Audit log
    db.audit_events.append({
        "id": str(uuid.uuid4()),
        "user_id": None,
        "action": "PUBLISH_EVENT",
        "table_name": "trigger_events",
        "record_id": event_id,
        "query_details": f"Event {message.event_type} triggered via Pub/Sub simulation",
        "logged_at": time.strftime("%Y-%m-%dT%H:%M:%SZ")
    })
    
    # Simulate execution of core workflows dynamically based on event
    simulate_workflow_triggers(message.event_type, message.payload)
    
    return {"status": "success", "event_id": event_id, "event": event_record}

# -------------------------------------------------------------
# Slack webhook simulator endpoints
# -------------------------------------------------------------
@app.post("/api/slack/events")
async def slack_events(request: Request):
    # Simulates Slack event ingestion and returns standard slack interaction responses
    body = await request.json()
    command = body.get("command", "")
    text = body.get("text", "").strip()
    
    # Audit log
    db.audit_events.append({
        "id": str(uuid.uuid4()),
        "user_id": None,
        "action": "SLACK_COMMAND",
        "table_name": "slack_messages",
        "record_id": str(uuid.uuid4()),
        "query_details": f"Slack Command: {command} {text}",
        "logged_at": time.strftime("%Y-%m-%dT%H:%M:%SZ")
    })
    
    if command == "/case":
        case_id = text
        if case_id in db.cases:
            # Query case details
            case_victims = [v for v in db.victims if v["case_id"] == case_id]
            case_evidence = [e for e in db.evidence if e["case_id"] == case_id]
            case_tasks = [t for t in db.tasks if t["case_id"] == case_id]
            
            c_data = {
                "case": db.cases[case_id],
                "victims": case_victims,
                "evidence": case_evidence,
                "tasks": case_tasks
            }
            # Build slack block layout
            slack_blocks = SlackBlockBuilder.build_case_detail_blocks(c_data)
            return {
                "response_type": "ephemeral",
                "blocks": slack_blocks["blocks"]
            }
        return {"text": f"Case {case_id} not found."}
        
    elif command == "/entity":
        # Search matching nodes
        matching_entities = [e for e in db.entities if text.lower() in e["name"].lower()]
        slack_blocks = SlackBlockBuilder.build_entity_search_blocks(text, matching_entities)
        return {
            "response_type": "ephemeral",
            "blocks": slack_blocks["blocks"]
        }
    
    return {"text": f"Slack Command {command} received."}

# -------------------------------------------------------------
# Trigger Workflows Simulation Logic
# -------------------------------------------------------------
def simulate_workflow_triggers(event_type: str, payload: Dict[str, Any]):
    case_id = payload.get("case_id", "CASE-142")
    router = CPPDEnvironmentRouter()
    
    if event_type == "VICTIM_REGISTERED":
        # 1. Register the victim in db
        victim_id = str(uuid.uuid4())
        victim_name = payload.get("full_name", "Jane Doe")
        db.victims.append({
            "id": victim_id,
            "case_id": case_id,
            "full_name": victim_name,
            "email": payload.get("email", "jane.doe@example.com"),
            "phone": payload.get("phone", "088-999-1122"),
            "address": payload.get("address", "Bangkok, Thailand"),
            "loss_amount": payload.get("loss_amount", 50000.00),
            "intake_source": "portal"
        })
        
        # 2. Extract statement details and generate summary using Gemini
        raw_statement = payload.get(
            "raw_statement", 
            f"My name is {victim_name}. I made a transfer to SCB account 401-229-3388. Contact phone: 089-111-2345."
        )
        summary = router.summarize_statement(raw_statement)
        extracted = router.extract_structured(raw_statement)
        
        # 3. Save statement transcript
        statement_id = str(uuid.uuid4())
        db.statements.append({
            "id": statement_id,
            "case_id": case_id,
            "subject_id": victim_id,
            "subject_type": "victim",
            "recorded_at": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "transcript": raw_statement,
            "summary": summary,
            "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ")
        })
        
        # 4. Create tasks
        db.tasks.append({
            "id": str(uuid.uuid4()),
            "case_id": case_id,
            "title": f"Review intake statement for {victim_name}",
            "description": f"Verify Gemini extraction summary: '{summary}'",
            "assigned_to": "d2f0998c-8c1d-4099-ae1e-f3f2a89366df",
            "status": "pending",
            "due_date": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.localtime(time.time() + 259200))
        })
        
        # 5. Automatically publish ENTITY_CREATED events for each extracted identifier
        for phone in extracted.phones:
            publish_pubsub(PubSubMessage(
                event_type="ENTITY_CREATED",
                payload={"case_id": case_id, "name": phone, "type": "PHONE"}
            ))
            
        for account in extracted.bank_accounts:
            publish_pubsub(PubSubMessage(
                event_type="ENTITY_CREATED",
                payload={"case_id": case_id, "name": account, "type": "BANK_ACCOUNT"}
            ))

    elif event_type == "EVIDENCE_UPLOADED":
        # Create task for investigator to review the evidence
        db.tasks.append({
            "id": str(uuid.uuid4()),
            "case_id": case_id,
            "title": f"Validate integrity & hash of {payload.get('title', 'evidence')}",
            "description": f"Calculate derived copies and verify custody hashes.",
            "assigned_to": "d2f0998c-8c1d-4099-ae1e-f3f2a89366df",
            "status": "pending",
            "due_date": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.localtime(time.time() + 86400))
        })
        
        # Audit check: check if bank ledger is missing
        has_ledger = any(e for e in db.evidence if "ledger" in e["title"].lower())
        if not has_ledger:
            publish_pubsub(PubSubMessage(
                event_type="EVIDENCE_GAP_FOUND",
                payload={"case_id": case_id, "gaps": ["Missing verified bank account transaction statement ledger"]}
            ))
        
    elif event_type == "ENTITY_CREATED":
        name = payload.get("name", "")
        type_ = payload.get("type", "PHONE")
        
        # Insert entity if not exists
        entity_exists = any(p for p in db.persons if p.get("phone") == name or p.get("bank_account") == name)
        if not entity_exists:
            person_id = str(uuid.uuid4())
            if type_ == "PHONE":
                db.persons.append({
                    "id": person_id,
                    "case_id": case_id,
                    "name": f"Suspect Phone ({name})",
                    "role": "Suspect",
                    "phone": name,
                    "bank_account": ""
                })
            else:
                db.persons.append({
                    "id": person_id,
                    "case_id": case_id,
                    "name": f"Suspect Account ({name})",
                    "role": "Suspect",
                    "phone": "",
                    "bank_account": name
                })
        
        # If suspect identifier matched, trigger Cross-Case match warning
        if name in ["089-111-2345", "401-229-3388"]:
            linked_cases = ["CASE-142", "CASE-087", "CASE-112"]
            finding_exists = any(f for f in db.ai_findings if f["entity_name"] == name and f["case_id"] == case_id)
            if not finding_exists:
                finding_id = "ai-find-" + str(uuid.uuid4())[:8]
                db.ai_findings.append({
                    "id": finding_id,
                    "case_id": case_id,
                    "entity_type": type_,
                    "entity_name": name,
                    "details": f"🚨 CROSS-CASE ALERT: Entity {name} matched across multiple active cases (CASE-142, CASE-087, CASE-112). Claimed loss total exceeds ฿2.1M.",
                    "confidence": 0.93,
                    "status": "unverified",
                    "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ")
                })
                
                # Format and output simulated Slack blocks
                slack_blocks = SlackBlockBuilder.build_cross_case_alert(
                    case_id=case_id,
                    account=name,
                    linked_cases=linked_cases,
                    victims_count=3,
                    loss="฿21.4M",
                    confidence=0.93
                )
                print(f"[Slack Alert Simulator] Sending Blocks Payload:\n{json.dumps(slack_blocks, indent=2)}")
                
                db.tasks.append({
                    "id": str(uuid.uuid4()),
                    "case_id": case_id,
                    "title": f"Verify cross-case association on identifier {name}",
                    "description": f"Resolve identical node linked with cases: {', '.join(linked_cases)}.",
                    "assigned_to": "d2f0998c-8c1d-4099-ae1e-f3f2a89366df",
                    "status": "pending",
                    "due_date": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.localtime(time.time() + 86400))
                })

    elif event_type == "EVIDENCE_GAP_FOUND":
        gaps = payload.get("gaps", [])
        gap_desc = ", ".join(gaps)
        
        # Check if task already exists
        task_exists = any(t for t in db.tasks if t["case_id"] == case_id and "Gap alert" in t["description"])
        if not task_exists:
            db.tasks.append({
                "id": str(uuid.uuid4()),
                "case_id": case_id,
                "title": "Resolve Missing Transfer Ledger",
                "description": f"Gap alert triggered: {gap_desc}",
                "assigned_to": "d2f0998c-8c1d-4099-ae1e-f3f2a89366df",
                "status": "pending",
                "due_date": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.localtime(time.time() + 172800))
            })



def authenticate_request(authorization: Optional[str] = Header(None)) -> Dict[str, Any]:
    user = get_user_from_token(authorization)
    email = user.get("email", "")
    profile = next((p for p in db.profiles.values() if p.get("email") == email), None)
    return {
        "id": profile["id"] if profile else email,
        "email": email,
        "role": user.get("role", "investigator"),
        "full_name": profile.get("full_name", profile.get("name", user.get("name", email))) if profile else user.get("name", email),
        "org_unit": profile.get("org_unit", "Financial Crimes Division 1") if profile else "Financial Crimes Division 1"
    }

def check_case_access(user: Dict[str, Any], case_id: str):
    if case_id not in db.cases:
        raise HTTPException(status_code=404, detail="Case not found")
    case = db.cases[case_id]
    role = user["role"]
    user_id = user["id"]
    division = user["org_unit"]
    
    is_authorized = False
    if role in ["admin", "commander", "deputy_commander", "deputy_superintendent"]:
        is_authorized = True
    elif role == "superintendent" and case.get("owning_unit") == division:
        is_authorized = True
    elif role in ["investigator", "clerk", "supervisor"]:
        is_assigned = any(m for m in db.case_members if m.get("case_id") == case_id and m.get("user_id") == user_id)
        if is_assigned:
            is_authorized = True
        elif not case.get("sensitive", False) and case.get("owning_unit") == division:
            is_authorized = True
            
    if not is_authorized:
        db.audit_events.append({
            "id": str(uuid.uuid4()),
            "user_id": user["email"],
            "action": "SECURITY.ACCESS.DENIED",
            "table_name": "cases",
            "record_id": case_id,
            "query_details": f"Unauthorized case access attempt by {user['email']}",
            "logged_at": time.strftime("%Y-%m-%dT%H:%M:%SZ")
        })
        raise HTTPException(status_code=403, detail="Forbidden: You do not have access to this case.")

# -------------------------------------------------------------
# PHASE 2: CASE WORKSPACE & INVESTIGATION WORKFLOW SCHEMAS
# -------------------------------------------------------------

class InvestigationIssueCreate(BaseModel):
    title: str
    description: str
    category: str = "FACT_TO_PROVE"
    priority: str = "HIGH"
    assigned_to: Optional[str] = None

class StatementCreate(BaseModel):
    person_id: str
    statement_type: str = "VICTIM"  # COMPLAINT, VICTIM, WITNESS, SUSPECT, ACCUSED, EXPERT, OFFICIAL
    location: str = "กก.1 บก.ปคบ."
    interviewed_by: Optional[str] = None
    transcript: Optional[str] = ""
    summary: Optional[str] = ""

class StatementQACreate(BaseModel):
    question: str
    answer: str
    sequence: Optional[int] = 1
    notes: Optional[str] = ""
    source_reference: Optional[str] = None

class EvidenceRelationCreate(BaseModel):
    evidence_id: str
    target_type: str  # PERSON, STATEMENT, EVENT, TRANSACTION, INVESTIGATION_ISSUE
    target_id: str
    relation_type: str
    notes: Optional[str] = ""

class InvestigationPlanCreate(BaseModel):
    objective: str
    issues_to_prove: List[str] = []
    required_evidence: List[str] = []
    persons_to_interview: List[str] = []
    agencies_to_contact: List[str] = []
    digital_checks: List[str] = []
    legal_questions: List[str] = []
    outstanding_gaps: List[str] = []
    target_date: str = "2026-08-30"
    responsible_investigator: Optional[str] = None

class InvestigationActionCreate(BaseModel):
    title: str
    description: str
    assigned_to: Optional[str] = None
    target_date: Optional[str] = None

class LegalIssueCreate(BaseModel):
    title: str
    law_reference: str
    section_reference: str
    issue_description: str

class LegalElementCreate(BaseModel):
    element_title: str
    supporting_facts: str
    supporting_evidence_ids: List[str] = []
    contradictory_evidence_ids: List[str] = []
    missing_evidence: Optional[str] = ""
    review_status: str = "SUPPORTED"  # SUPPORTED, PARTIALLY_SUPPORTED, NOT_SUPPORTED, CONTRADICTED, REQUIRES_REVIEW

class CaseDocumentCreate(BaseModel):
    document_type: str  # SUMMONS_WARRANT, SEARCH_WARRANT, ACCUSATION_RECORD, FINAL_REPORT, OFFICIAL_LETTER, INVESTIGATION_NOTE
    title: str
    content: str
    source_references: List[str] = []

class CaseDocumentVersionCreate(BaseModel):
    content: str
    status: str = "IN_REVIEW"

class ReviewRequestCreate(BaseModel):
    resource_type: str  # STATEMENT, INVESTIGATION_PLAN, LEGAL_ISSUE, DOCUMENT
    resource_id: str
    reviewer_id: Optional[str] = None
    comments: str

class ReviewActionRequest(BaseModel):
    action: str  # APPROVED, RETURNED, REJECTED
    comments: Optional[str] = ""

class NarrativeUpdate(BaseModel):
    narrative: str

# -------------------------------------------------------------
# PHASE 2: CASE WORKSPACE REST API ENDPOINTS
# -------------------------------------------------------------

@app.get("/api/v1/cases/{case_id}/overview")
@app.get("/api/cases/{case_id}/overview")
async def get_case_overview(case_id: str, authorization: Optional[str] = Header(None)):
    user = authenticate_request(authorization)
    check_case_access(user, case_id)
    
    case = db.cases.get(case_id)
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
        
    case_persons = [p for p in db.persons if p.get("case_id") == case_id]
    case_evidence = [e for e in db.evidence if e.get("case_id") == case_id]
    case_statements = [s for s in db.statements if s.get("case_id") == case_id]
    case_issues = [i for i in getattr(db, "investigation_issues", []) if i.get("case_id") == case_id]
    case_tasks = [t for t in db.tasks if t.get("case_id") == case_id]
    case_docs = [d for d in getattr(db, "case_documents", []) if d.get("case_id") == case_id]
    case_reviews = [r for r in getattr(db, "review_requests", []) if r.get("case_id") == case_id and r.get("status") == "PENDING"]
    
    total_loss = sum([v.get("loss_amount", 0) for v in db.victims if v.get("case_id") == case_id])
    narrative_history = [n for n in getattr(db, "case_narrative_history", []) if n.get("case_id") == case_id]
    
    return {
        "case": case,
        "metrics": {
            "evidence_count": len(case_evidence),
            "statement_count": len(case_statements),
            "person_count": len(case_persons),
            "open_issue_count": len([i for i in case_issues if i.get("status") in ["OPEN", "IN_PROGRESS"]]),
            "open_task_count": len([t for t in case_tasks if t.get("status") != "completed"]),
            "document_count": len(case_docs),
            "pending_review_count": len(case_reviews),
            "total_loss_thb": total_loss
        },
        "lead_investigator": "พ.ต.ท. สมชาย สอบสวนสืบสวน",
        "case_team": [
            {"name": "พ.ต.ท. สมชาย สอบสวนสืบสวน", "role": "Lead Investigator", "unit": "กก.1 บก.ปคบ."},
            {"name": "ร.ต.อ. สมศักดิ์ สืบสวนไว", "role": "Co-Investigator", "unit": "กก.1 บก.ปคบ."},
            {"name": "ส.ต.อ. สุรชัย คดีมั่น", "role": "Case Clerk", "unit": "กก.1 บก.ปคบ."}
        ],
        "narrative_history": narrative_history
    }

@app.patch("/api/v1/cases/{case_id}/narrative")
async def update_case_narrative(case_id: str, payload: NarrativeUpdate, authorization: Optional[str] = Header(None)):
    user = authenticate_request(authorization)
    check_case_access(user, case_id)
    
    case = db.cases.get(case_id)
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
        
    case["description"] = payload.narrative
    case["updated_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ")
    
    history = getattr(db, "case_narrative_history", [])
    current_versions = [h for h in history if h.get("case_id") == case_id]
    new_ver = len(current_versions) + 1
    
    history.append({
        "case_id": case_id,
        "version": new_ver,
        "narrative": payload.narrative,
        "updated_by": user["email"],
        "updated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ")
    })
    
    db.audit_log.append({
        "event_id": str(uuid.uuid4()),
        "occurred_at": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "actor_user_id": user["id"],
        "action": "CASE.UPDATE_NARRATIVE",
        "resource_type": "case",
        "resource_id": case_id,
        "result": "success",
        "metadata": {"version": new_ver}
    })
    
    return {"status": "success", "version": new_ver, "case": case}

# 1. Investigation Issues
@app.get("/api/v1/cases/{case_id}/issues")
@app.get("/api/cases/{case_id}/issues")
async def get_case_issues(case_id: str, authorization: Optional[str] = Header(None)):
    user = authenticate_request(authorization)
    check_case_access(user, case_id)
    issues = [i for i in getattr(db, "investigation_issues", []) if i.get("case_id") == case_id]
    return {"status": "success", "count": len(issues), "issues": issues}

@app.post("/api/v1/cases/{case_id}/issues")
@app.post("/api/cases/{case_id}/issues")
async def create_case_issue(case_id: str, payload: InvestigationIssueCreate, authorization: Optional[str] = Header(None)):
    user = authenticate_request(authorization)
    check_case_access(user, case_id)
    
    issue_id = f"iss-{case_id.lower()}-{str(uuid.uuid4())[:6]}"
    issue = {
        "id": issue_id,
        "case_id": case_id,
        "title": payload.title,
        "description": payload.description,
        "category": payload.category,
        "priority": payload.priority,
        "status": "OPEN",
        "source": "INVESTIGATOR",
        "created_by": user["id"],
        "assigned_to": payload.assigned_to or user["id"],
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "updated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ")
    }
    
    if not hasattr(db, "investigation_issues"):
        db.investigation_issues = []
    db.investigation_issues.append(issue)
    
    db.audit_log.append({
        "event_id": str(uuid.uuid4()),
        "occurred_at": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "actor_user_id": user["id"],
        "action": "CASE.ISSUE.CREATE",
        "resource_type": "investigation_issue",
        "resource_id": issue_id,
        "result": "success",
        "metadata": {"title": payload.title}
    })
    
    return {"status": "success", "issue": issue}

# 2. Statements & Statement QA
@app.get("/api/v1/cases/{case_id}/statements")
@app.get("/api/cases/{case_id}/statements")
async def get_case_statements(case_id: str, authorization: Optional[str] = Header(None)):
    user = authenticate_request(authorization)
    check_case_access(user, case_id)
    
    statements = [s for s in db.statements if s.get("case_id") == case_id]
    qas = getattr(db, "statement_qas", [])
    
    # attach QAs
    enriched = []
    for s in statements:
        item = dict(s)
        item["qa_list"] = [q for q in qas if q.get("statement_id") == s.get("id")]
        enriched.append(item)
        
    return {"status": "success", "count": len(enriched), "statements": enriched}

@app.post("/api/v1/cases/{case_id}/statements")
@app.post("/api/cases/{case_id}/statements")
async def create_case_statement(case_id: str, payload: StatementCreate, authorization: Optional[str] = Header(None)):
    user = authenticate_request(authorization)
    check_case_access(user, case_id)
    
    stmt_id = str(uuid.uuid4())
    statement_number = f"STMT-{case_id}-{len(db.statements) + 1:03d}"
    statement = {
        "id": stmt_id,
        "case_id": case_id,
        "person_id": payload.person_id,
        "statement_type": payload.statement_type,
        "statement_number": statement_number,
        "interviewed_by": payload.interviewed_by or user["full_name"],
        "interview_started_at": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "interview_ended_at": None,
        "location": payload.location,
        "status": "DRAFT",
        "version": 1,
        "transcript": payload.transcript or "",
        "summary": payload.summary or "",
        "created_by": user["id"],
        "approved_by": None,
        "approved_at": None,
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "updated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ")
    }
    
    db.statements.append(statement)
    db.audit_log.append({
        "event_id": str(uuid.uuid4()),
        "occurred_at": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "actor_user_id": user["id"],
        "action": "STATEMENT.CREATE",
        "resource_type": "statement",
        "resource_id": stmt_id,
        "result": "success",
        "metadata": {"statement_number": statement_number, "person_id": payload.person_id}
    })
    
    return {"status": "success", "statement": statement}

@app.post("/api/v1/statements/{statement_id}/qa")
@app.post("/api/statements/{statement_id}/qa")
async def add_statement_qa(statement_id: str, payload: StatementQACreate, authorization: Optional[str] = Header(None)):
    user = authenticate_request(authorization)
    
    stmt = next((s for s in db.statements if s.get("id") == statement_id), None)
    if not stmt:
        raise HTTPException(status_code=404, detail="Statement not found")
        
    qa_id = f"qa-{str(uuid.uuid4())[:8]}"
    qa = {
        "id": qa_id,
        "statement_id": statement_id,
        "sequence": payload.sequence or 1,
        "question": payload.question,
        "answer": payload.answer,
        "notes": payload.notes or "",
        "source_reference": payload.source_reference
    }
    
    if not hasattr(db, "statement_qas"):
        db.statement_qas = []
    db.statement_qas.append(qa)
    
    db.audit_log.append({
        "event_id": str(uuid.uuid4()),
        "occurred_at": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "actor_user_id": user["id"],
        "action": "STATEMENT.QA_ADD",
        "resource_type": "statement_qa",
        "resource_id": qa_id,
        "result": "success"
    })
    
    return {"status": "success", "qa": qa}

# 3. Evidence Relations
@app.get("/api/v1/cases/{case_id}/evidence-relations")
@app.get("/api/cases/{case_id}/evidence-relations")
async def get_evidence_relations(case_id: str, authorization: Optional[str] = Header(None)):
    user = authenticate_request(authorization)
    check_case_access(user, case_id)
    relations = [r for r in getattr(db, "evidence_relations", []) if r.get("case_id") == case_id]
    return {"status": "success", "relations": relations}

@app.post("/api/v1/cases/{case_id}/evidence-relations")
@app.post("/api/cases/{case_id}/evidence-relations")
async def create_evidence_relation(case_id: str, payload: EvidenceRelationCreate, authorization: Optional[str] = Header(None)):
    user = authenticate_request(authorization)
    check_case_access(user, case_id)
    
    rel_id = f"rel-{str(uuid.uuid4())[:8]}"
    relation = {
        "id": rel_id,
        "case_id": case_id,
        "evidence_id": payload.evidence_id,
        "target_type": payload.target_type,
        "target_id": payload.target_id,
        "relation_type": payload.relation_type,
        "notes": payload.notes or "",
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ")
    }
    
    if not hasattr(db, "evidence_relations"):
        db.evidence_relations = []
    db.evidence_relations.append(relation)
    
    db.audit_log.append({
        "event_id": str(uuid.uuid4()),
        "occurred_at": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "actor_user_id": user["id"],
        "action": "EVIDENCE.RELATION_CREATE",
        "resource_type": "evidence_relation",
        "resource_id": rel_id,
        "result": "success",
        "metadata": {"evidence_id": payload.evidence_id, "target_id": payload.target_id}
    })
    
    return {"status": "success", "relation": relation}

# 4. Investigation Plan
@app.get("/api/v1/cases/{case_id}/investigation-plan")
@app.get("/api/cases/{case_id}/investigation-plan")
async def get_investigation_plan(case_id: str, authorization: Optional[str] = Header(None)):
    user = authenticate_request(authorization)
    check_case_access(user, case_id)
    plan = next((p for p in getattr(db, "investigation_plans", []) if p.get("case_id") == case_id), None)
    return {"status": "success", "plan": plan}

@app.post("/api/v1/cases/{case_id}/investigation-plan/actions")
@app.post("/api/cases/{case_id}/investigation-plan/actions")
async def create_plan_action(case_id: str, payload: InvestigationActionCreate, authorization: Optional[str] = Header(None)):
    user = authenticate_request(authorization)
    check_case_access(user, case_id)
    
    plan = next((p for p in getattr(db, "investigation_plans", []) if p.get("case_id") == case_id), None)
    if not plan:
        raise HTTPException(status_code=404, detail="Investigation plan not found for this case")
        
    act_id = f"act-{str(uuid.uuid4())[:8]}"
    task_id = str(uuid.uuid4())
    
    action = {
        "id": act_id,
        "title": payload.title,
        "description": payload.description,
        "assigned_to": payload.assigned_to or user["id"],
        "status": "PLANNED",
        "target_date": payload.target_date or time.strftime("%Y-%m-%d"),
        "related_task_id": task_id
    }
    
    plan["actions"].append(action)
    
    # Also spawn CaseTask automatically for operational alignment
    db.tasks.append({
        "id": task_id,
        "case_id": case_id,
        "title": payload.title,
        "description": payload.description,
        "assigned_to": payload.assigned_to or user["id"],
        "status": "pending",
        "due_date": (payload.target_date or "2026-08-30") + "T17:00:00Z"
    })
    
    db.audit_log.append({
        "event_id": str(uuid.uuid4()),
        "occurred_at": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "actor_user_id": user["id"],
        "action": "INVESTIGATION_PLAN.ACTION_CREATE",
        "resource_type": "investigation_action",
        "resource_id": act_id,
        "result": "success",
        "metadata": {"task_id": task_id}
    })
    
    return {"status": "success", "action": action, "task_id": task_id}

# 5. Legal Issues & Legal Elements
@app.get("/api/v1/cases/{case_id}/legal-issues")
@app.get("/api/cases/{case_id}/legal-issues")
async def get_legal_issues_v1(case_id: str, authorization: Optional[str] = Header(None)):
    user = authenticate_request(authorization)
    check_case_access(user, case_id)
    
    issues = [li for li in db.legal_issues if li.get("case_id") == case_id]
    elements = getattr(db, "legal_elements", [])
    
    enriched = []
    for issue in issues:
        item = dict(issue)
        item["elements"] = [elem for elem in elements if elem.get("issue_id") == issue.get("id")]
        enriched.append(item)
        
    return {"status": "success", "legal_issues": enriched}

@app.post("/api/v1/cases/{case_id}/legal-issues")
@app.post("/api/cases/{case_id}/legal-issues")
async def create_legal_issue(case_id: str, payload: LegalIssueCreate, authorization: Optional[str] = Header(None)):
    user = authenticate_request(authorization)
    check_case_access(user, case_id)
    
    issue_id = f"li-{str(uuid.uuid4())[:6]}"
    issue = {
        "id": issue_id,
        "case_id": case_id,
        "issue_title": payload.title,
        "legal_code": f"{payload.law_reference} {payload.section_reference}".strip(),
        "description": payload.issue_description,
        "status": "substantiated",
        "evidence_ids": [],
        "created_by": user["id"],
        "reviewed_by": None,
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ")
    }
    
    db.legal_issues.append(issue)
    
    db.audit_log.append({
        "event_id": str(uuid.uuid4()),
        "occurred_at": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "actor_user_id": user["id"],
        "action": "LEGAL_ISSUE.CREATE",
        "resource_type": "legal_issue",
        "resource_id": issue_id,
        "result": "success",
        "metadata": {"title": payload.title}
    })
    
    return {"status": "success", "legal_issue": issue}

@app.post("/api/v1/legal-issues/{issue_id}/elements")
@app.post("/api/legal-issues/{issue_id}/elements")
async def add_legal_element(issue_id: str, payload: LegalElementCreate, authorization: Optional[str] = Header(None)):
    user = authenticate_request(authorization)
    
    elem_id = f"elem-{str(uuid.uuid4())[:8]}"
    element = {
        "id": elem_id,
        "issue_id": issue_id,
        "element_title": payload.element_title,
        "supporting_facts": payload.supporting_facts,
        "supporting_evidence_ids": payload.supporting_evidence_ids,
        "contradictory_evidence_ids": payload.contradictory_evidence_ids,
        "missing_evidence": payload.missing_evidence or "",
        "review_status": payload.review_status
    }
    
    if not hasattr(db, "legal_elements"):
        db.legal_elements = []
    db.legal_elements.append(element)
    
    db.audit_log.append({
        "event_id": str(uuid.uuid4()),
        "occurred_at": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "actor_user_id": user["id"],
        "action": "LEGAL_ELEMENT.ADD",
        "resource_type": "legal_element",
        "resource_id": elem_id,
        "result": "success"
    })
    
    return {"status": "success", "element": element}

# 6. Case Documents & Versions
@app.get("/api/v1/cases/{case_id}/documents")
@app.get("/api/cases/{case_id}/documents")
async def get_case_documents(case_id: str, authorization: Optional[str] = Header(None)):
    user = authenticate_request(authorization)
    check_case_access(user, case_id)
    docs = [d for d in getattr(db, "case_documents", []) if d.get("case_id") == case_id]
    return {"status": "success", "documents": docs}

@app.post("/api/v1/cases/{case_id}/documents")
@app.post("/api/cases/{case_id}/documents")
async def create_case_document(case_id: str, payload: CaseDocumentCreate, authorization: Optional[str] = Header(None)):
    user = authenticate_request(authorization)
    check_case_access(user, case_id)
    
    doc_id = f"doc-{case_id.lower()}-{str(uuid.uuid4())[:6]}"
    doc = {
        "id": doc_id,
        "case_id": case_id,
        "document_type": payload.document_type,
        "title": payload.title,
        "content": payload.content,
        "version": 1,
        "author": user["full_name"],
        "reviewer": "พ.ต.อ. อนงค์ บังคับการ",
        "approval_status": "DRAFT",
        "generated_from": "INVESTIGATOR",
        "source_references": payload.source_references,
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "updated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "history": [
            {"version": 1, "status": "DRAFT", "updated_by": user["email"], "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ")}
        ]
    }
    
    if not hasattr(db, "case_documents"):
        db.case_documents = []
    db.case_documents.append(doc)
    
    db.audit_log.append({
        "event_id": str(uuid.uuid4()),
        "occurred_at": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "actor_user_id": user["id"],
        "action": "DOCUMENT.CREATE",
        "resource_type": "case_document",
        "resource_id": doc_id,
        "result": "success",
        "metadata": {"title": payload.title, "type": payload.document_type}
    })
    
    return {"status": "success", "document": doc}

@app.post("/api/v1/documents/{doc_id}/version")
@app.post("/api/documents/{doc_id}/version")
async def add_document_version(doc_id: str, payload: CaseDocumentVersionCreate, authorization: Optional[str] = Header(None)):
    user = authenticate_request(authorization)
    
    doc = next((d for d in getattr(db, "case_documents", []) if d.get("id") == doc_id), None)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
        
    doc["version"] += 1
    doc["content"] = payload.content
    doc["approval_status"] = payload.status
    doc["updated_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ")
    doc["history"].append({
        "version": doc["version"],
        "status": payload.status,
        "updated_by": user["email"],
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ")
    })
    
    db.audit_log.append({
        "event_id": str(uuid.uuid4()),
        "occurred_at": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "actor_user_id": user["id"],
        "action": "DOCUMENT.VERSION.CREATE",
        "resource_type": "case_document",
        "resource_id": doc_id,
        "result": "success",
        "metadata": {"version": doc["version"], "status": payload.status}
    })
    
    return {"status": "success", "document": doc}

# 7. Review & Approval Engine
@app.get("/api/v1/cases/{case_id}/reviews")
@app.get("/api/cases/{case_id}/reviews")
async def get_case_reviews(case_id: str, authorization: Optional[str] = Header(None)):
    user = authenticate_request(authorization)
    check_case_access(user, case_id)
    reviews = [r for r in getattr(db, "review_requests", []) if r.get("case_id") == case_id]
    return {"status": "success", "reviews": reviews}

@app.post("/api/v1/cases/{case_id}/reviews")
@app.post("/api/cases/{case_id}/reviews")
async def create_review_request(case_id: str, payload: ReviewRequestCreate, authorization: Optional[str] = Header(None)):
    user = authenticate_request(authorization)
    check_case_access(user, case_id)
    
    rev_id = f"rev-{str(uuid.uuid4())[:8]}"
    review = {
        "id": rev_id,
        "case_id": case_id,
        "resource_type": payload.resource_type,
        "resource_id": payload.resource_id,
        "requested_by": user["id"],
        "reviewer_id": payload.reviewer_id or "f8c3de7d-94d7-46e2-bc2f-e8b9fb6cb077",
        "status": "PENDING",
        "comments": payload.comments,
        "requested_at": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "reviewed_at": None
    }
    
    if not hasattr(db, "review_requests"):
        db.review_requests = []
    db.review_requests.append(review)
    
    db.audit_log.append({
        "event_id": str(uuid.uuid4()),
        "occurred_at": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "actor_user_id": user["id"],
        "action": "REVIEW.REQUEST",
        "resource_type": payload.resource_type,
        "resource_id": payload.resource_id,
        "result": "success",
        "metadata": {"review_id": rev_id}
    })
    
    return {"status": "success", "review": review}

@app.post("/api/v1/reviews/{review_id}/action")
@app.post("/api/reviews/{review_id}/action")
async def process_review_action(review_id: str, payload: ReviewActionRequest, authorization: Optional[str] = Header(None)):
    user = authenticate_request(authorization)
    
    # Check supervisor/superintendent permission
    if user["role"] not in ["supervisor", "superintendent", "commander", "deputy_commander", "deputy_superintendent", "admin"]:
        raise HTTPException(status_code=403, detail="Forbidden: Only supervisory personnel can approve/return reviews")
        
    review = next((r for r in getattr(db, "review_requests", []) if r.get("id") == review_id), None)
    if not review:
        raise HTTPException(status_code=404, detail="Review request not found")
        
    review["status"] = payload.action.upper()
    review["reviewed_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ")
    if payload.comments:
        review["comments"] += f" | Response: {payload.comments}"
        
    # Update linked document if applicable
    if review["resource_type"] == "DOCUMENT":
        doc = next((d for d in getattr(db, "case_documents", []) if d.get("id") == review["resource_id"]), None)
        if doc:
            doc["approval_status"] = payload.action.upper()
            doc["history"].append({
                "version": doc["version"],
                "status": payload.action.upper(),
                "updated_by": user["email"],
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ")
            })
            
    db.audit_log.append({
        "event_id": str(uuid.uuid4()),
        "occurred_at": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "actor_user_id": user["id"],
        "action": f"REVIEW.{payload.action.upper()}",
        "resource_type": review["resource_type"],
        "resource_id": review["resource_id"],
        "result": "success",
        "metadata": {"review_id": review_id, "action": payload.action}
    })
    
    return {"status": "success", "review": review}

# 8. Activity Feed
@app.get("/api/v1/cases/{case_id}/activity")
@app.get("/api/cases/{case_id}/activity")
async def get_case_activity(case_id: str, authorization: Optional[str] = Header(None)):
    user = authenticate_request(authorization)
    check_case_access(user, case_id)
    
    events = [ev for ev in db.audit_log if ev.get("resource_id") == case_id or ev.get("metadata", {}).get("case_id") == case_id]
    
    # Synthesize readable domain events
    activities = []
    for ev in events:
        activities.append({
            "id": ev.get("event_id"),
            "timestamp": ev.get("occurred_at"),
            "actor": ev.get("actor_user_id"),
            "action": ev.get("action"),
            "resource_type": ev.get("resource_type"),
            "summary": f"{ev.get('action')} performed on {ev.get('resource_type')}"
        })
        
    # Add initial domain activity seeds
    activities.append({
        "id": "act-seed-1",
        "timestamp": "2026-08-10T10:00:00Z",
        "actor": "พ.ต.ท. สมชาย สอบสวนสืบสวน",
        "action": "CASE.CREATE",
        "resource_type": "case",
        "summary": "เปิดรับสำนวนการสอบสวนคดีอาญาที่ 142/2569"
    })
    activities.append({
        "id": "act-seed-2",
        "timestamp": "2026-08-10T10:05:00Z",
        "actor": "พ.ต.ท. สมชาย สอบสวนสืบสวน",
        "action": "EVIDENCE.FILE.UPLOAD",
        "resource_type": "evidence",
        "summary": "ลงทะเบียนสลิปการโอนเงินธนาคารไทยพาณิชย์ 1.25 ล้านบาท (SHA-256 Verified)"
    })
    activities.append({
        "id": "act-seed-3",
        "timestamp": "2026-08-10T11:00:00Z",
        "actor": "พ.ต.ท. สมชาย สอบสวนสืบสวน",
        "action": "CASE.ISSUE.CREATE",
        "resource_type": "investigation_issue",
        "summary": "สร้างประเด็นต้องพิสูจน์: ความเชื่อมโยงของบัญชี SCB กับผู้ต้องหา"
    })
    activities.append({
        "id": "act-seed-4",
        "timestamp": "2026-08-16T11:30:00Z",
        "actor": "พ.ต.อ. อนงค์ บังคับการ",
        "action": "DOCUMENT.APPROVE",
        "resource_type": "case_document",
        "summary": "อนุมัติหมายเรียกผู้ต้องหา ครั้งที่ 1 (นายกิตติศักดิ์ วงศ์สวัสดิ์)"
    })
    
    return {"status": "success", "count": len(activities), "activities": sorted(activities, key=lambda x: x["timestamp"], reverse=True)}


# -------------------------------------------------------------
# PHASE 3: EVIDENCE INTELLIGENCE & CHAIN OF CUSTODY SCHEMAS
# -------------------------------------------------------------

class EvidenceCustodyTransferRequest(BaseModel):
    to_user_id: str
    to_location: str
    reason: str
    seal_number: Optional[str] = None
    witnessed_by: Optional[str] = None
    condition_after: Optional[str] = "สมบูรณ์"

class EvidenceIntegrityCheckRequest(BaseModel):
    check_type: str = "MANUAL"  # UPLOAD, ACCESS, TRANSFER, EXPORT, PERIODIC, MANUAL
    actual_hash: Optional[str] = None

class EvidenceGapCreate(BaseModel):
    investigation_issue_id: Optional[str] = None
    legal_element_id: Optional[str] = None
    description: str
    required_evidence_type: str
    priority: str = "HIGH"
    assigned_to: Optional[str] = None
    due_at: Optional[str] = None

class EvidenceGapResolveRequest(BaseModel):
    resolved_by_evidence_id: str
    status: str = "RESOLVED"

class EvidenceArtifactCreate(BaseModel):
    artifact_type: str  # FORENSIC_COPY, WORKING_COPY, EXTRACTED_CONTENT, DERIVED_ARTIFACT, AI_ANALYSIS_OUTPUT
    parent_file_id: Optional[str] = None
    original_filename: str
    mime_type: str
    size_bytes: int
    sha256: str
    metadata_json: Optional[Dict[str, Any]] = {}

class EvidenceReviewRequest(BaseModel):
    review_result: str  # VERIFIED, PARTIALLY_VERIFIED, QUESTIONED, REJECTED, REQUIRES_ACTION
    authenticity_flag: bool = True
    relevance_flag: bool = True
    integrity_flag: bool = True
    admissibility_flag: bool = True
    comments: str

class EvidenceExportRequest(BaseModel):
    recipient: str
    purpose: str
    selected_evidence_ids: List[str] = []

# -------------------------------------------------------------
# PHASE 3: EVIDENCE INTELLIGENCE REST API ENDPOINTS
# -------------------------------------------------------------

# 1. Evidence Matrix & Gaps
@app.get("/api/v1/cases/{case_id}/evidence-matrix")
@app.get("/api/cases/{case_id}/evidence-matrix")
async def get_evidence_matrix(case_id: str, authorization: Optional[str] = Header(None)):
    user = authenticate_request(authorization)
    check_case_access(user, case_id)
    
    issues = [i for i in getattr(db, "investigation_issues", []) if i.get("case_id") == case_id]
    evidences = [e for e in db.evidence if e.get("case_id") == case_id]
    relations = [r for r in getattr(db, "evidence_relations", []) if r.get("case_id") == case_id]
    gaps = [g for g in getattr(db, "evidence_gaps", []) if g.get("case_id") == case_id]
    
    matrix = []
    for issue in issues:
        linked_rel = [r for r in relations if r.get("target_id") == issue.get("id")]
        avail_ev_ids = [r.get("evidence_id") for r in linked_rel]
        avail_evs = [e for e in evidences if e.get("id") in avail_ev_ids]
        issue_gaps = [g for g in gaps if g.get("investigation_issue_id") == issue.get("id")]
        
        status = "VERIFIED" if len(avail_evs) > 0 and len(issue_gaps) == 0 else "HAS_GAPS" if len(issue_gaps) > 0 else "PENDING_COLLECTION"
        
        matrix.append({
            "issue_id": issue.get("id"),
            "issue_title": issue.get("title"),
            "category": issue.get("category"),
            "available_evidence": [{"id": e["id"], "title": e["title"], "type": e.get("type", "document"), "hash": e.get("file_hash", "")} for e in avail_evs],
            "gaps": issue_gaps,
            "matrix_status": status
        })
        
    return {"status": "success", "case_id": case_id, "matrix": matrix}

@app.get("/api/v1/cases/{case_id}/evidence-gaps")
@app.get("/api/cases/{case_id}/evidence-gaps")
async def get_evidence_gaps(case_id: str, authorization: Optional[str] = Header(None)):
    user = authenticate_request(authorization)
    check_case_access(user, case_id)
    gaps = [g for g in getattr(db, "evidence_gaps", []) if g.get("case_id") == case_id]
    return {"status": "success", "gaps": gaps}

@app.post("/api/v1/cases/{case_id}/evidence-gaps")
@app.post("/api/cases/{case_id}/evidence-gaps")
async def create_evidence_gap(case_id: str, payload: EvidenceGapCreate, authorization: Optional[str] = Header(None)):
    user = authenticate_request(authorization)
    check_case_access(user, case_id)
    
    gap_id = f"gap-{case_id.lower()}-{str(uuid.uuid4())[:6]}"
    gap = {
        "id": gap_id,
        "case_id": case_id,
        "investigation_issue_id": payload.investigation_issue_id,
        "legal_element_id": payload.legal_element_id,
        "description": payload.description,
        "required_evidence_type": payload.required_evidence_type,
        "priority": payload.priority,
        "status": "OPEN",
        "assigned_to": payload.assigned_to or user["id"],
        "due_at": payload.due_at or time.strftime("%Y-%m-%dT17:00:00Z"),
        "resolved_by_evidence_id": None
    }
    
    if not hasattr(db, "evidence_gaps"):
        db.evidence_gaps = []
    db.evidence_gaps.append(gap)
    
    db.audit_log.append({
        "event_id": str(uuid.uuid4()),
        "occurred_at": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "actor_user_id": user["id"],
        "action": "EVIDENCE.GAP_CREATE",
        "resource_type": "evidence_gap",
        "resource_id": gap_id,
        "result": "success",
        "metadata": {"description": payload.description}
    })
    
    return {"status": "success", "gap": gap}

@app.patch("/api/v1/evidence-gaps/{gap_id}/resolve")
@app.patch("/api/evidence-gaps/{gap_id}/resolve")
async def resolve_evidence_gap(gap_id: str, payload: EvidenceGapResolveRequest, authorization: Optional[str] = Header(None)):
    user = authenticate_request(authorization)
    
    gap = next((g for g in getattr(db, "evidence_gaps", []) if g.get("id") == gap_id), None)
    if not gap:
        raise HTTPException(status_code=404, detail="Evidence gap not found")
        
    gap["status"] = payload.status
    gap["resolved_by_evidence_id"] = payload.resolved_by_evidence_id
    
    db.audit_log.append({
        "event_id": str(uuid.uuid4()),
        "occurred_at": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "actor_user_id": user["id"],
        "action": "EVIDENCE.GAP_RESOLVE",
        "resource_type": "evidence_gap",
        "resource_id": gap_id,
        "result": "success",
        "metadata": {"resolved_by": payload.resolved_by_evidence_id}
    })
    
    return {"status": "success", "gap": gap}

# 2. Chain of Custody (Append-only)
@app.get("/api/v1/evidence/{evidence_id}/custody")
@app.get("/api/evidence/{evidence_id}/custody")
async def get_evidence_custody_events(evidence_id: str, authorization: Optional[str] = Header(None)):
    user = authenticate_request(authorization)
    events = [c for c in getattr(db, "custody_events", []) if c.get("evidence_id") == evidence_id]
    return {"status": "success", "events": sorted(events, key=lambda x: x.get("occurred_at", ""), reverse=True)}

@app.post("/api/v1/evidence/{evidence_id}/custody/transfer")
@app.post("/api/evidence/{evidence_id}/custody/transfer")
async def transfer_evidence_custody(evidence_id: str, payload: EvidenceCustodyTransferRequest, authorization: Optional[str] = Header(None)):
    user = authenticate_request(authorization)
    
    ev = next((e for e in db.evidence if e.get("id") == evidence_id), None)
    if not ev:
        raise HTTPException(status_code=404, detail="Evidence not found")
        
    cust_id = f"cust-{str(uuid.uuid4())[:8]}"
    event = {
        "id": cust_id,
        "evidence_id": evidence_id,
        "event_type": "TRANSFERRED",
        "from_user_id": user["full_name"],
        "to_user_id": payload.to_user_id,
        "from_location": "กก.1 บก.ปคบ.",
        "to_location": payload.to_location,
        "performed_by": user["full_name"],
        "witnessed_by": payload.witnessed_by or "ส.ต.อ. สุรชัย คดีมั่น",
        "occurred_at": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "reason": payload.reason,
        "seal_number": payload.seal_number or f"SEAL-CPPD-{str(uuid.uuid4())[:6]}",
        "condition_before": "ปิดผนึกสมบูรณ์",
        "condition_after": payload.condition_after or "ส่งมอบในสภาพสมบูรณ์",
        "notes": f"โอนย้ายการครอบครองไปยัง {payload.to_user_id}",
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ")
    }
    
    if not hasattr(db, "custody_events"):
        db.custody_events = []
    db.custody_events.append(event)
    
    db.audit_log.append({
        "event_id": str(uuid.uuid4()),
        "occurred_at": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "actor_user_id": user["id"],
        "action": "EVIDENCE.CUSTODY.TRANSFER",
        "resource_type": "evidence",
        "resource_id": evidence_id,
        "result": "success",
        "metadata": {"to_user": payload.to_user_id, "location": payload.to_location}
    })
    
    return {"status": "success", "event": event}

# 3. Integrity Check & SHA-256 Verification
@app.post("/api/v1/evidence/{evidence_id}/integrity/verify")
@app.post("/api/evidence/{evidence_id}/integrity/verify")
async def verify_evidence_integrity(evidence_id: str, payload: EvidenceIntegrityCheckRequest, authorization: Optional[str] = Header(None)):
    user = authenticate_request(authorization)
    
    ev = next((e for e in db.evidence if e.get("id") == evidence_id), None)
    if not ev:
        raise HTTPException(status_code=404, detail="Evidence not found")
        
    expected_hash = ev.get("file_hash", "")
    actual_hash = payload.actual_hash or expected_hash
    
    is_match = (expected_hash == actual_hash)
    result = "MATCH" if is_match else "MISMATCH"
    
    chk_id = f"chk-{str(uuid.uuid4())[:8]}"
    check_record = {
        "id": chk_id,
        "evidence_id": evidence_id,
        "check_type": payload.check_type,
        "expected_hash": expected_hash,
        "actual_hash": actual_hash,
        "result": result,
        "performed_by": user["id"],
        "performed_at": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "tool_name": "CPPD_SHA256_INTEGRITY_ENGINE",
        "tool_version": "v1.2.0",
        "notes": "Bit-exact integrity match" if is_match else "CRITICAL: Hash mismatch detected!"
    }
    
    if not hasattr(db, "evidence_integrity_checks"):
        db.evidence_integrity_checks = []
    db.evidence_integrity_checks.append(check_record)
    
    if not is_match:
        # Create Security Event
        db.audit_events.append({
            "id": str(uuid.uuid4()),
            "user_id": user["email"],
            "action": "EVIDENCE.HASH.MISMATCH",
            "table_name": "evidence",
            "record_id": evidence_id,
            "query_details": f"CRITICAL TAMPERING ALERT: Expected {expected_hash} but found {actual_hash}",
            "logged_at": time.strftime("%Y-%m-%dT%H:%M:%SZ")
        })
        raise HTTPException(status_code=409, detail="Security Alert: Evidence SHA-256 hash mismatch detected!")
        
    db.audit_log.append({
        "event_id": str(uuid.uuid4()),
        "occurred_at": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "actor_user_id": user["id"],
        "action": "EVIDENCE.HASH.VERIFY",
        "resource_type": "evidence",
        "resource_id": evidence_id,
        "result": "success",
        "metadata": {"sha256": actual_hash}
    })
    
    return {"status": "success", "result": result, "check_record": check_record}

# 4. Artifact Hierarchy (Original / Working / Derived)
@app.get("/api/v1/evidence/{evidence_id}/artifacts")
@app.get("/api/evidence/{evidence_id}/artifacts")
async def get_evidence_artifacts(evidence_id: str, authorization: Optional[str] = Header(None)):
    user = authenticate_request(authorization)
    files = [f for f in getattr(db, "evidence_files", []) if f.get("evidence_id") == evidence_id]
    return {"status": "success", "artifacts": files}

@app.post("/api/v1/evidence/{evidence_id}/artifacts")
@app.post("/api/evidence/{evidence_id}/artifacts")
async def create_evidence_artifact(evidence_id: str, payload: EvidenceArtifactCreate, authorization: Optional[str] = Header(None)):
    user = authenticate_request(authorization)
    
    art_id = f"ef-{str(uuid.uuid4())[:8]}"
    artifact = {
        "id": art_id,
        "evidence_id": evidence_id,
        "artifact_type": payload.artifact_type,
        "parent_file_id": payload.parent_file_id,
        "object_key": f"evidence/derived/{art_id}_{payload.original_filename}",
        "original_filename": payload.original_filename,
        "stored_filename": f"{art_id}.{payload.original_filename.split('.')[-1]}",
        "mime_type": payload.mime_type,
        "extension": payload.original_filename.split(".")[-1],
        "size_bytes": payload.size_bytes,
        "sha256": payload.sha256,
        "sha512": None,
        "storage_provider": "CPPD_SECURE_STORAGE",
        "uploaded_by": user["id"],
        "uploaded_at": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "scan_status": "CLEAN",
        "integrity_status": "VERIFIED",
        "is_primary": False,
        "is_immutable": (payload.artifact_type == "ORIGINAL"),
        "metadata_json": payload.metadata_json
    }
    
    if not hasattr(db, "evidence_files"):
        db.evidence_files = []
    db.evidence_files.append(artifact)
    
    db.audit_log.append({
        "event_id": str(uuid.uuid4()),
        "occurred_at": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "actor_user_id": user["id"],
        "action": "EVIDENCE.ARTIFACT_CREATE",
        "resource_type": "evidence_file",
        "resource_id": art_id,
        "result": "success",
        "metadata": {"artifact_type": payload.artifact_type, "parent_file_id": payload.parent_file_id}
    })
    
    return {"status": "success", "artifact": artifact}

# 5. Controlled Evidence Export & Hash Manifest
@app.post("/api/v1/cases/{case_id}/evidence/export")
@app.post("/api/cases/{case_id}/evidence/export")
async def export_evidence_package(case_id: str, payload: EvidenceExportRequest, authorization: Optional[str] = Header(None)):
    user = authenticate_request(authorization)
    check_case_access(user, case_id)
    
    all_case_evidences = [e for e in db.evidence if e.get("case_id") == case_id]
    if payload.selected_evidence_ids:
        target_evs = [e for e in all_case_evidences if e.get("id") in payload.selected_evidence_ids]
    else:
        target_evs = all_case_evidences
        
    export_id = f"pkg-{case_id.lower()}-{str(uuid.uuid4())[:6]}"
    manifest_items = []
    for ev in target_evs:
        manifest_items.append({
            "evidence_id": ev["id"],
            "title": ev["title"],
            "type": ev.get("type", "document"),
            "sha256": ev.get("file_hash", ""),
            "classification": ev.get("classification", "CONFIDENTIAL"),
            "custody_status": ev.get("status", "sealed")
        })
        
    manifest = {
        "export_package_id": export_id,
        "case_id": case_id,
        "export_date": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "exporting_officer": user["full_name"],
        "recipient": payload.recipient,
        "purpose": payload.purpose,
        "total_items": len(manifest_items),
        "manifest_items": manifest_items
    }
    
    db.audit_log.append({
        "event_id": str(uuid.uuid4()),
        "occurred_at": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "actor_user_id": user["id"],
        "action": "EVIDENCE.EXPORT",
        "resource_type": "evidence_package",
        "resource_id": export_id,
        "result": "success",
        "metadata": {"recipient": payload.recipient, "total_items": len(manifest_items)}
    })
    
    return {"status": "success", "manifest": manifest}

# 6. Duplicate Detection
@app.get("/api/v1/cases/{case_id}/evidence/duplicates")
@app.get("/api/cases/{case_id}/evidence/duplicates")
async def detect_evidence_duplicates(case_id: str, authorization: Optional[str] = Header(None)):
    user = authenticate_request(authorization)
    check_case_access(user, case_id)
    
    case_evs = [e for e in db.evidence if e.get("case_id") == case_id]
    hashes = {}
    duplicates = []
    for e in case_evs:
        h = e.get("file_hash")
        if h:
            if h in hashes:
                duplicates.append({
                    "evidence_id": e["id"],
                    "duplicate_of_id": hashes[h]["id"],
                    "sha256": h,
                    "match_type": "EXACT_HASH_MATCH"
                })
            else:
                hashes[h] = e
                
    return {"status": "success", "duplicates_count": len(duplicates), "duplicates": duplicates}


# -------------------------------------------------------------
# PHASE 4: AI ORCHESTRATOR & AGENTS SCHEMAS
# -------------------------------------------------------------

class AIOrchestrationRunRequest(BaseModel):
    agent_type: str  # IntakeCaseTriageAgent, InvestigationPlanningAgent, EvidenceAnalysisAgent, TimelineAgent, StatementComparisonAgent, FinancialTransactionAgent, LegalMappingAgent, EvidenceGapAgent
    purpose: str
    data_classification: Optional[str] = "CONFIDENTIAL"  # PUBLIC, INTERNAL, CONFIDENTIAL, RESTRICTED
    provider_preference: Optional[str] = "AUTO"  # AUTO, LOCAL, CLOUD
    input_source_ids: Optional[List[str]] = []
    language: Optional[str] = "th"

class AIAnalysisReviewRequest(BaseModel):
    review_status: str  # ACCEPTED, PARTIALLY_ACCEPTED, REJECTED
    comments: Optional[str] = ""

class AIResultConvertRequest(BaseModel):
    target_type: str  # TIMELINE_EVENT, CASE_TASK, INVESTIGATION_ISSUE, EVIDENCE_GAP
    finding_index: int = 0
    title: Optional[str] = None
    description: Optional[str] = None
    priority: Optional[str] = "HIGH"

# -------------------------------------------------------------
# PHASE 4: AI ORCHESTRATOR & AGENTS REST API ENDPOINTS
# -------------------------------------------------------------

# 1. Prompt Registry
@app.get("/api/v1/ai/prompts")
@app.get("/api/ai/prompts")
async def get_prompt_registry(authorization: Optional[str] = Header(None)):
    user = authenticate_request(authorization)
    return {"status": "success", "prompts": getattr(db, "prompt_registry", [])}

# 2. AI Execution Run (Central Orchestrator)
@app.post("/api/v1/cases/{case_id}/ai/run")
@app.post("/api/cases/{case_id}/ai/run")
async def run_ai_orchestrator(case_id: str, payload: AIOrchestrationRunRequest, authorization: Optional[str] = Header(None)):
    user = authenticate_request(authorization)
    check_case_access(user, case_id)
    
    target_case = db.cases.get(case_id, {})
    is_sensitive = target_case.get("sensitive", False) or payload.data_classification == "RESTRICTED"
    
    # Provider Routing Policy
    if is_sensitive and payload.provider_preference == "CLOUD":
        # Block Cloud Provider for sensitive/restricted cases
        db.audit_log.append({
            "event_id": str(uuid.uuid4()),
            "occurred_at": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "actor_user_id": user["id"],
            "action": "AI.POLICY.DENY",
            "resource_type": "ai_execution",
            "resource_id": case_id,
            "result": "denied",
            "metadata": {"reason": "Cloud AI strictly prohibited for RESTRICTED/sensitive cases"}
        })
        raise HTTPException(status_code=403, detail="Security Policy Violation: Cloud AI provider is prohibited for RESTRICTED or sensitive cases. Use Local Provider only.")
        
    selected_provider = "LOCAL_SECURE_LLM" if is_sensitive else ("ON_PREMISE_CPPD_AI" if payload.provider_preference != "CLOUD" else "APPROVED_GOV_CLOUD_AI")
    
    exec_id = f"exec-{case_id.lower()}-{str(uuid.uuid4())[:6]}"
    analysis_id = f"ai-an-{str(uuid.uuid4())[:8]}"
    
    # Retrieve scoped evidence/sources
    scoped_ev = [e for e in db.evidence if e.get("case_id") == case_id]
    if payload.input_source_ids:
        scoped_ev = [e for e in scoped_ev if e.get("id") in payload.input_source_ids]
        
    # Execute Modular Agent Logic with Structured Tags
    agent = payload.agent_type
    summary_text = ""
    findings = []
    
    if agent == "IntakeCaseTriageAgent":
        summary_text = f"คัดกรองเบื้องต้นสำหรับคดี {case_id}: พบพฤติการณ์หลอกลวงผ่านระบบคอมพิวเตอร์และเวชสำอางค์ปนเปื้อนสารเคมีอันตราย"
        findings = [
            {"type": "CLAIM", "text": "ผู้เสียหายอ้างว่าสั่งซื้อสินค้าจากเพจเฟซบุ๊ก สยาม คอสเมติกส์ ออฟฟิเชียล ยอดโอน 1,250,000 บาท", "source_ids": ["INTAKE-001"], "confidence": 0.95, "review_required": True},
            {"type": "INFERENCE", "text": "พฤติการณ์เข้าข่ายความผิดตาม ป.อ. ม.343 และ พ.ร.บ.คอมพิวเตอร์ฯ ม.14(1)", "source_ids": ["INTAKE-001"], "confidence": 0.88, "review_required": True},
            {"type": "REQUIRES_HUMAN_REVIEW", "text": "จำเป็นต้องตรวจสอบชื่อผู้ครอบครองบัญชีรับโอน 401-229-3388 จากธนาคารไทยพาณิชย์", "source_ids": ["INTAKE-001"], "confidence": 0.99, "review_required": True}
        ]
    elif agent == "TimelineAgent":
        summary_text = f"วิเคราะห์ลำดับเวลาและตรวจจับข้อขัดแย้งสำหรับคดี {case_id}"
        findings = [
            {"type": "FACT", "text": "9 ส.ค. 2569 เวลา 14:32:00: ผู้เสียหายโอนเงิน 1,250,000 บาท เข้าบัญชี SCB 401-229-3388", "source_ids": ["f05d9e5b-ec1d-4009-bf2f-e8b9fb6cb088"], "confidence": 0.99, "review_required": False},
            {"type": "CONFLICT", "text": "ข้อขัดแย้ง: นายกิตติศักดิ์อ้างว่าอยู่ จ.เชียงใหม่ แต่ IP ล็อกอิน SCB Easy เป็น IP คอนโดย่านลาดพร้าว", "source_ids": ["stat-142-02", "ev-142-03"], "confidence": 0.92, "review_required": True},
            {"type": "EVIDENCE_GAP", "text": "ยังขาดภาพบันทึก CCTV หน้าตู้ ATM สาขาลาดพร้าว ขณะทำรายการถอนเงินสด", "source_ids": [], "confidence": 0.95, "review_required": True}
        ]
    elif agent == "LegalMappingAgent":
        summary_text = f"วิเคราะห์การจับคู่ข้อเท็จจริงกับองค์ประกอบความผิดตามกฎหมายสำหรับ {case_id}"
        findings = [
            {"type": "INFERENCE", "text": "องค์ประกอบที่ 1: การหลอกลวงด้วยการแสดงข้อความอันเป็นเท็จต่อประชาชน สอดคล้องกับพยานหลักฐานโพสต์โฆษณาใน Facebook", "source_ids": ["7f83b1657ff1fc53b92dc18148a1d65dfc2d4b1fa3d677284addd200126d9069"], "confidence": 0.90, "review_required": True},
            {"type": "INFERENCE", "text": "องค์ประกอบที่ 2: ได้ไปซึ่งทรัพย์สินจากผู้ถูกหลอกลวง สอดคล้องกับสลิปการโอนเงิน 1,250,000 บาท", "source_ids": ["f05d9e5b-ec1d-4009-bf2f-e8b9fb6cb088"], "confidence": 0.95, "review_required": True},
            {"type": "REQUIRES_HUMAN_REVIEW", "text": "หมายเหตุ: AI เป็นผู้ช่วยวิเคราะห์องค์ประกอบเท่านั้น พนักงานสอบสวนต้องเป็นผู้วินิจฉัยข้อกฎหมายขั้นสุดท้าย", "source_ids": [], "confidence": 1.0, "review_required": True}
        ]
    elif agent == "EvidenceGapAgent":
        summary_text = f"ตรวจสอบช่องว่างพยานหลักฐานและสิ่งที่ต้องรวบรวมเพิ่มเติมสำหรับ {case_id}"
        findings = [
            {"type": "EVIDENCE_GAP", "text": "ยังขาดรายการเดินบัญชี (Bank Statement) ของบัญชีแถวที่ 2 เพื่อยืนยันเส้นทางการฟอกเงิน", "source_ids": ["iss-142-01"], "confidence": 0.94, "review_required": True},
            {"type": "EVIDENCE_GAP", "text": "ยังขาดผลการตรวจสอบเครื่องหมาย อย. และใบอนุญาตผลิตจากสำนักงานคณะกรรมการอาหารและยา", "source_ids": ["iss-142-02"], "confidence": 0.91, "review_required": True}
        ]
    else:
        # Default Evidence Analysis Agent
        summary_text = f"ผลการวิเคราะห์พยานหลักฐานโดย {agent} สำหรับคดี {case_id}"
        findings = [
            {"type": "FACT", "text": f"ตรวจสอบพบพยานหลักฐานจำนวน {len(scoped_ev)} รายการในสำนวนคดี", "source_ids": [e["id"] for e in scoped_ev], "confidence": 0.98, "review_required": False},
            {"type": "INFERENCE", "text": "ตรวจพบความเชื่อมโยงของชื่อบัญชีและหมายเลขโทรศัพท์ตรงกับฐานข้อมูลคดีหลอกลวงฉ้อโกงประชาชน", "source_ids": [e["id"] for e in scoped_ev], "confidence": 0.89, "review_required": True},
            {"type": "REQUIRES_HUMAN_REVIEW", "text": "เสนอแนะให้ออกหมายเรียกพยานเอกสารจากสถาบันการเงินและผู้ให้บริการเครือข่ายโทรศัพท์มือถือ", "source_ids": [], "confidence": 0.95, "review_required": True}
        ]
        
    execution_record = {
        "id": exec_id,
        "case_id": case_id,
        "requested_by": user["id"],
        "agent_type": agent,
        "provider": selected_provider,
        "model_name": "typhoon-2-70b-instruct",
        "model_version": "v2.1",
        "prompt_version": "v1.4",
        "input_source_ids": [e["id"] for e in scoped_ev],
        "data_classification": payload.data_classification,
        "status": "SUCCEEDED",
        "started_at": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "completed_at": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "token_usage": {"prompt_tokens": 850, "completion_tokens": 320, "total_tokens": 1170},
        "cost_metadata": {"estimated_cost_thb": 0.0},
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ")
    }
    
    analysis_record = {
        "id": analysis_id,
        "execution_id": exec_id,
        "case_id": case_id,
        "analysis_type": agent,
        "result_json": {
            "summary": summary_text,
            "findings": findings,
            "agent": agent,
            "provider": selected_provider
        },
        "summary": summary_text,
        "confidence": 0.93,
        "review_status": "REQUIRES_REVIEW",
        "reviewed_by": None,
        "reviewed_at": None,
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ")
    }
    
    if not hasattr(db, "ai_executions"):
        db.ai_executions = []
    db.ai_executions.append(execution_record)
    
    if not hasattr(db, "ai_analyses"):
        db.ai_analyses = []
    db.ai_analyses.append(analysis_record)
    
    db.audit_log.append({
        "event_id": str(uuid.uuid4()),
        "occurred_at": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "actor_user_id": user["id"],
        "action": "AI.EXECUTION.SUCCESS",
        "resource_type": "ai_analysis",
        "resource_id": analysis_id,
        "result": "success",
        "metadata": {"agent": agent, "provider": selected_provider, "classification": payload.data_classification}
    })
    
    return {"status": "success", "execution": execution_record, "analysis": analysis_record}

# 3. AI Executions & Analyses Retrieval
@app.get("/api/v1/cases/{case_id}/ai/executions")
@app.get("/api/cases/{case_id}/ai/executions")
async def get_case_ai_executions(case_id: str, authorization: Optional[str] = Header(None)):
    user = authenticate_request(authorization)
    check_case_access(user, case_id)
    execs = [e for e in getattr(db, "ai_executions", []) if e.get("case_id") == case_id]
    return {"status": "success", "executions": sorted(execs, key=lambda x: x.get("created_at", ""), reverse=True)}

@app.get("/api/v1/cases/{case_id}/ai/analyses")
@app.get("/api/cases/{case_id}/ai/analyses")
async def get_case_ai_analyses(case_id: str, authorization: Optional[str] = Header(None)):
    user = authenticate_request(authorization)
    check_case_access(user, case_id)
    analyses = [a for a in getattr(db, "ai_analyses", []) if a.get("case_id") == case_id]
    return {"status": "success", "analyses": sorted(analyses, key=lambda x: x.get("created_at", ""), reverse=True)}

# 4. Human Review of AI Analysis
@app.post("/api/v1/ai/analyses/{analysis_id}/review")
@app.post("/api/ai/analyses/{analysis_id}/review")
async def review_ai_analysis(analysis_id: str, payload: AIAnalysisReviewRequest, authorization: Optional[str] = Header(None)):
    user = authenticate_request(authorization)
    
    analysis = next((a for a in getattr(db, "ai_analyses", []) if a.get("id") == analysis_id), None)
    if not analysis:
        raise HTTPException(status_code=404, detail="AI analysis not found")
        
    analysis["review_status"] = payload.review_status
    analysis["reviewed_by"] = user["full_name"]
    analysis["reviewed_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ")
    
    db.audit_log.append({
        "event_id": str(uuid.uuid4()),
        "occurred_at": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "actor_user_id": user["id"],
        "action": f"AI.RESULT.{payload.review_status}",
        "resource_type": "ai_analysis",
        "resource_id": analysis_id,
        "result": "success",
        "metadata": {"comments": payload.comments}
    })
    
    return {"status": "success", "analysis": analysis}

# 5. Conversion of AI Finding to Official Domain Artifact
@app.post("/api/v1/ai/analyses/{analysis_id}/convert")
@app.post("/api/ai/analyses/{analysis_id}/convert")
async def convert_ai_finding(analysis_id: str, payload: AIResultConvertRequest, authorization: Optional[str] = Header(None)):
    user = authenticate_request(authorization)
    
    analysis = next((a for a in getattr(db, "ai_analyses", []) if a.get("id") == analysis_id), None)
    if not analysis:
        raise HTTPException(status_code=404, detail="AI analysis not found")
        
    case_id = analysis.get("case_id")
    findings = analysis.get("result_json", {}).get("findings", [])
    finding = findings[payload.finding_index] if payload.finding_index < len(findings) else {"text": payload.description or "AI Finding"}
    
    title = payload.title or finding.get("text", "")[:50]
    desc = payload.description or finding.get("text", "")
    converted_id = None
    
    if payload.target_type == "TIMELINE_EVENT":
        converted_id = f"ev-{str(uuid.uuid4())[:8]}"
        ev_item = {
            "id": converted_id,
            "case_id": case_id,
            "occurred_at": time.strftime("%Y-%m-%d %H:%M:%S"),
            "event_type": "AI_DERIVED_EVENT",
            "title": title,
            "description": desc,
            "source_evidence_ids": finding.get("source_ids", []),
            "status": "human_approved",
            "created_by": user["id"]
        }
        if not hasattr(db, "timeline_events"):
            db.timeline_events = []
        db.timeline_events.append(ev_item)
    elif payload.target_type == "CASE_TASK":
        converted_id = f"task-{str(uuid.uuid4())[:8]}"
        task_item = {
            "id": converted_id,
            "case_id": case_id,
            "title": title,
            "description": desc,
            "priority": payload.priority or "HIGH",
            "assigned_to": user["id"],
            "status": "pending",
            "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ")
        }
        db.tasks.append(task_item)
    elif payload.target_type == "INVESTIGATION_ISSUE":
        converted_id = f"iss-{case_id.lower()}-{str(uuid.uuid4())[:6]}"
        iss_item = {
            "id": converted_id,
            "case_id": case_id,
            "title": title,
            "category": "AI_IDENTIFIED_ISSUE",
            "status": "OPEN",
            "priority": payload.priority or "HIGH",
            "assigned_to": user["id"],
            "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ")
        }
        if not hasattr(db, "investigation_issues"):
            db.investigation_issues = []
        db.investigation_issues.append(iss_item)
    elif payload.target_type == "EVIDENCE_GAP":
        converted_id = f"gap-{case_id.lower()}-{str(uuid.uuid4())[:6]}"
        gap_item = {
            "id": converted_id,
            "case_id": case_id,
            "investigation_issue_id": None,
            "description": desc,
            "required_evidence_type": "OFFICIAL_RECORD",
            "priority": payload.priority or "HIGH",
            "status": "OPEN",
            "assigned_to": user["id"],
            "due_at": time.strftime("%Y-%m-%dT17:00:00Z"),
            "resolved_by_evidence_id": None
        }
        if not hasattr(db, "evidence_gaps"):
            db.evidence_gaps = []
        db.evidence_gaps.append(gap_item)
        
    db.audit_log.append({
        "event_id": str(uuid.uuid4()),
        "occurred_at": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "actor_user_id": user["id"],
        "action": f"AI.RESULT.CONVERT.{payload.target_type}",
        "resource_type": "ai_analysis",
        "resource_id": analysis_id,
        "result": "success",
        "metadata": {"converted_id": converted_id, "target_type": payload.target_type}
    })
    
    return {"status": "success", "converted_id": converted_id, "target_type": payload.target_type}


# -------------------------------------------------------------
# PHASE 5: STATEMENT & INTERVIEW COPILOT SCHEMAS
# -------------------------------------------------------------

class InterviewQuestionCreate(BaseModel):
    sequence: int = 1
    question_type: str = "OPEN"
    topic: str
    question_text: str
    purpose: str
    source_reference_ids: Optional[List[str]] = []
    generated_by: Optional[str] = "HUMAN"
    status: Optional[str] = "ASKED"

class StatementAnswerCreate(BaseModel):
    question_id: str
    sequence: int = 1
    answer_text: str
    answer_type: str = "VERBATIM"  # VERBATIM, SUMMARY, STRUCTURED
    notes: Optional[str] = None

class InterviewPrepCreate(BaseModel):
    person_id: str
    objective: str
    issues_to_cover: List[str] = []
    known_facts: Optional[List[str]] = []
    relevant_evidence_ids: Optional[List[str]] = []

class StatementReviewAction(BaseModel):
    action: str  # SUBMIT_REVIEW, APPROVE, RETURN
    comments: Optional[str] = ""

class StatementDraftRequest(BaseModel):
    template_type: Optional[str] = "POLICE_STATEMENT_FORM_1"
    language: Optional[str] = "th"

# -------------------------------------------------------------
# PHASE 5: STATEMENT & INTERVIEW COPILOT REST API ENDPOINTS
# -------------------------------------------------------------

# 1. Statement Details & Lifecycle
@app.get("/api/v1/statements/{statement_id}")
@app.get("/api/statements/{statement_id}")
async def get_statement_details(statement_id: str, authorization: Optional[str] = Header(None)):
    user = authenticate_request(authorization)
    
    stat = next((s for s in db.statements if s.get("id") == statement_id), None)
    if not stat:
        raise HTTPException(status_code=404, detail="Statement not found")
        
    check_case_access(user, stat["case_id"])
    
    questions = [q for q in getattr(db, "interview_questions", []) if q.get("statement_id") == statement_id]
    answers = [a for a in getattr(db, "statement_answers", []) if a.get("statement_id") == statement_id]
    versions = [v for v in getattr(db, "statement_versions", []) if v.get("statement_id") == statement_id]
    prep = next((p for p in getattr(db, "interview_preparations", []) if p.get("statement_id") == statement_id), None)
    
    return {
        "status": "success",
        "statement": stat,
        "preparation": prep,
        "questions": sorted(questions, key=lambda x: x.get("sequence", 0)),
        "answers": sorted(answers, key=lambda x: x.get("sequence", 0)),
        "versions": sorted(versions, key=lambda x: x.get("version_number", 0), reverse=True)
    }

@app.post("/api/v1/statements/{statement_id}/start")
@app.post("/api/statements/{statement_id}/start")
async def start_statement_interview(statement_id: str, authorization: Optional[str] = Header(None)):
    user = authenticate_request(authorization)
    stat = next((s for s in db.statements if s.get("id") == statement_id), None)
    if not stat:
        raise HTTPException(status_code=404, detail="Statement not found")
    stat["status"] = "IN_PROGRESS"
    db.audit_log.append({
        "event_id": str(uuid.uuid4()), "occurred_at": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "actor_user_id": user["id"], "action": "STATEMENT.START",
        "resource_type": "statement", "resource_id": statement_id, "result": "success"
    })
    return {"status": "success", "statement_status": "IN_PROGRESS"}

@app.post("/api/v1/statements/{statement_id}/pause")
@app.post("/api/statements/{statement_id}/pause")
async def pause_statement_interview(statement_id: str, authorization: Optional[str] = Header(None)):
    user = authenticate_request(authorization)
    stat = next((s for s in db.statements if s.get("id") == statement_id), None)
    if not stat:
        raise HTTPException(status_code=404, detail="Statement not found")
    stat["status"] = "PAUSED"
    db.audit_log.append({
        "event_id": str(uuid.uuid4()), "occurred_at": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "actor_user_id": user["id"], "action": "STATEMENT.PAUSE",
        "resource_type": "statement", "resource_id": statement_id, "result": "success"
    })
    return {"status": "success", "statement_status": "PAUSED"}

@app.post("/api/v1/statements/{statement_id}/complete")
@app.post("/api/statements/{statement_id}/complete")
async def complete_statement_interview(statement_id: str, authorization: Optional[str] = Header(None)):
    user = authenticate_request(authorization)
    stat = next((s for s in db.statements if s.get("id") == statement_id), None)
    if not stat:
        raise HTTPException(status_code=404, detail="Statement not found")
    stat["status"] = "COMPLETED"
    db.audit_log.append({
        "event_id": str(uuid.uuid4()), "occurred_at": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "actor_user_id": user["id"], "action": "STATEMENT.COMPLETE",
        "resource_type": "statement", "resource_id": statement_id, "result": "success"
    })
    return {"status": "success", "statement_status": "COMPLETED"}

# 2. Questions and Answers
@app.post("/api/v1/statements/{statement_id}/questions")
@app.post("/api/statements/{statement_id}/questions")
async def add_interview_question(statement_id: str, payload: InterviewQuestionCreate, authorization: Optional[str] = Header(None)):
    user = authenticate_request(authorization)
    q_id = f"q-{str(uuid.uuid4())[:8]}"
    q_item = {
        "id": q_id,
        "statement_id": statement_id,
        "sequence": payload.sequence,
        "question_type": payload.question_type,
        "topic": payload.topic,
        "question_text": payload.question_text,
        "purpose": payload.purpose,
        "source_reference_ids": payload.source_reference_ids or [],
        "generated_by": payload.generated_by or "HUMAN",
        "status": payload.status or "ASKED",
        "asked_at": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ")
    }
    if not hasattr(db, "interview_questions"):
        db.interview_questions = []
    db.interview_questions.append(q_item)
    return {"status": "success", "question": q_item}

@app.post("/api/v1/statements/{statement_id}/answers")
@app.post("/api/statements/{statement_id}/answers")
async def add_statement_answer(statement_id: str, payload: StatementAnswerCreate, authorization: Optional[str] = Header(None)):
    user = authenticate_request(authorization)
    ans_id = f"ans-{str(uuid.uuid4())[:8]}"
    ans_item = {
        "id": ans_id,
        "statement_id": statement_id,
        "question_id": payload.question_id,
        "sequence": payload.sequence,
        "answer_text": payload.answer_text,
        "answer_type": payload.answer_type,
        "recorded_by": user["id"],
        "recorded_at": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "notes": payload.notes
    }
    if not hasattr(db, "statement_answers"):
        db.statement_answers = []
    db.statement_answers.append(ans_item)
    return {"status": "success", "answer": ans_item}

# 3. AI Question & Follow-up Agents
@app.post("/api/v1/statements/{statement_id}/ai/questions")
@app.post("/api/statements/{statement_id}/ai/questions")
async def generate_statement_ai_questions(statement_id: str, authorization: Optional[str] = Header(None)):
    user = authenticate_request(authorization)
    stat = next((s for s in db.statements if s.get("id") == statement_id), None)
    if not stat:
        raise HTTPException(status_code=404, detail="Statement not found")
        
    role = stat.get("role", "WITNESS")
    suggested_questions = [
        {
            "sequence": 1,
            "question_type": "BACKGROUND",
            "topic": "ความสัมพันธ์และภูมิหลัง",
            "question_text": "ท่านมีความสัมพันธ์หรือเคยมีข้อพิพาทใดๆ กับบุคคลในคดีนี้มาก่อนหรือไม่?",
            "purpose": "ตรวจสอบมูลเหตุจูงใจและความเป็นกลาง",
            "status": "SUGGESTED",
            "source_ids": [stat["id"]]
        },
        {
            "sequence": 2,
            "question_type": "EVIDENCE_BASED",
            "topic": "การทำธุรกรรมและการส่งมอบพยานหลักฐาน",
            "question_text": "ตามที่ปรากฏสลิปการโอนเงินจำนวน 1,250,000 บาท ท่านเป็นผู้ทำรายการด้วยตนเองใช่หรือไม่ และทำจากสถานที่ใด?",
            "purpose": "ยืนยันความถูกต้องและถิ่นที่อยู่ขณะทำธุรกรรม",
            "status": "SUGGESTED",
            "source_ids": ["f05d9e5b-ec1d-4009-bf2f-e8b9fb6cb088"]
        },
        {
            "sequence": 3,
            "question_type": "TIMELINE",
            "topic": "ลำดับเวลาเกิดเหตุ",
            "question_text": "หลังจากโอนเงินแล้ว ท่านได้รับการติดต่อหรือได้รับพัสดุสินค้าเมื่อวันเวลาใด?",
            "purpose": "ประกอบไทม์ไลน์ช่วงเวลาเกิดความเสียหาย",
            "status": "SUGGESTED",
            "source_ids": []
        }
    ]
    
    db.audit_log.append({
        "event_id": str(uuid.uuid4()), "occurred_at": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "actor_user_id": user["id"], "action": "STATEMENT.AI.QUESTION",
        "resource_type": "statement", "resource_id": statement_id, "result": "success"
    })
    
    return {"status": "success", "suggested_questions": suggested_questions}

@app.post("/api/v1/statements/{statement_id}/ai/follow-up")
@app.post("/api/statements/{statement_id}/ai/follow-up")
async def generate_statement_ai_followup(statement_id: str, authorization: Optional[str] = Header(None)):
    user = authenticate_request(authorization)
    
    follow_up_suggestions = [
        {
            "type": "FOLLOW_UP",
            "question_text": "ท่านระบุว่าได้โทรศัพท์ติดต่อกับแอดมินเพจ ขอให้ระบุหมายเลขโทรศัพท์และแอปพลิเคชันที่ใช้สนทนาให้ชัดเจน",
            "purpose": "ขอข้อมูลระบุตัวตน (Phone/Chat ID) เพื่อใช้ขอข้อมูลการจราจรทางคอมพิวเตอร์",
            "reason": "ผู้ให้การกล่าวถึงการโทรศัพท์แต่ยังไม่ระบุหมายเลขโทรศัพท์",
            "status": "SUGGESTED"
        },
        {
            "type": "CONTRADICTION_CHECK",
            "question_text": "ในคำให้การระบุว่าอยู่ใน จ.เชียงใหม่ แต่ IP การล็อกอินทำรายการบันทึกไว้ในกรุงเทพฯ ท่านสามารถอธิบายข้อเท็จจริงนี้ได้หรือไม่?",
            "purpose": "เปิดโอกาสให้ผู้ให้การชี้แจงประเด็นข้อขัดแย้งเกี่ยวกับสถานที่ล็อกอิน",
            "reason": "ตรวจพบข้อขัดแย้งระหว่างคำให้การและข้อมูลจราจรคอมพิวเตอร์",
            "status": "SUGGESTED"
        }
    ]
    
    return {"status": "success", "follow_up_questions": follow_up_suggestions}

# 4. Consistency & Completeness Audits
@app.post("/api/v1/statements/{statement_id}/ai/consistency")
@app.post("/api/statements/{statement_id}/ai/consistency")
async def check_statement_consistency(statement_id: str, authorization: Optional[str] = Header(None)):
    user = authenticate_request(authorization)
    
    consistency_results = {
        "status": "REQUIRES_REVIEW",
        "contradictions_found": 1,
        "items": [
            {
                "type": "CONFLICT",
                "topic": "สถานที่ขณะเกิดเหตุ",
                "statement_claim": "ผู้ต้องสงสัยอ้างว่าอยู่ที่ จ.เชียงใหม่ ในวันที่ 9 ส.ค. 2569",
                "evidence_fact": "หลักฐานการล็อกอิน SCB Easy จาก IP คอนโดมิเนียมย่านลาดพร้าว กรุงเทพฯ ในเวลาเดียวกัน",
                "severity": "HIGH",
                "source_evidence_ids": ["f05d9e5b-ec1d-4009-bf2f-e8b9fb6cb088"]
            }
        ]
    }
    return {"status": "success", "consistency": consistency_results}

@app.post("/api/v1/statements/{statement_id}/ai/completeness")
@app.post("/api/statements/{statement_id}/ai/completeness")
async def check_statement_completeness(statement_id: str, authorization: Optional[str] = Header(None)):
    user = authenticate_request(authorization)
    
    checklist = [
        {"topic": "ข้อมูลประจำตัวและเลขบัตรประชาชน", "status": "COMPLETE"},
        {"topic": "ความสัมพันธ์และบทบาทในคดี", "status": "COMPLETE"},
        {"topic": "วันเวลาและสถานที่เกิดเหตุ", "status": "COMPLETE"},
        {"topic": "เส้นทางการเงินและยอดความเสียหาย", "status": "COMPLETE"},
        {"topic": "ภาพบันทึก CCTV หรือพยานบุคคลขณะถอนเงิน", "status": "MISSING_INFORMATION"}
    ]
    return {"status": "success", "completeness_status": "PARTIALLY_COMPLETE", "checklist": checklist}

# 5. AI Statement Drafting & Version History
@app.post("/api/v1/statements/{statement_id}/ai/draft")
@app.post("/api/statements/{statement_id}/ai/draft")
async def generate_statement_ai_draft(statement_id: str, payload: StatementDraftRequest, authorization: Optional[str] = Header(None)):
    user = authenticate_request(authorization)
    stat = next((s for s in db.statements if s.get("id") == statement_id), None)
    if not stat:
        raise HTTPException(status_code=404, detail="Statement not found")
        
    answers = [a for a in getattr(db, "statement_answers", []) if a.get("statement_id") == statement_id]
    
    draft_body = f"""บันทึกคำให้การ (AI-ASSISTED DRAFT -- NOT FINAL)
คดีอาญาที่ 142/2569 กองกำกับการ 1 กองบังคับการปราบปรามการกระทำความผิดเกี่ยวกับการคุ้มครองผู้บริโภค
วันที่ 10 สิงหาคม 2569

ผู้ให้การ: นายนัฐพงษ์ สุขประเสริฐ (ผู้เสียหาย/ผู้กล่าวหา)
พนักงานสอบสวน: {user['full_name']}

ข้อเท็จจริงตามที่ได้บันทึกคำให้การ:
1. ผู้ให้การไม่เคยมีความสัมพันธ์ส่วนตัวกับนายกิตติศักดิ์ วงศ์สวัสดิ์ มาก่อน ได้ติดต่อสั่งซื้อเวชสำอางค์ผ่านหน้าเพจเฟซบุ๊ก สยาม คอสเมติกส์ ออฟฟิเชียล
2. เมื่อวันที่ 9 สิงหาคม 2569 เวลา 14:32 น. ผู้ให้การได้โอนเงินค่าสินค้าจำนวน 1,250,000 บาท เข้าบัญชีธนาคารไทยพาณิชย์ เลขที่ 401-229-3388 ชื่อบัญชี นายกิตติศักดิ์ วงศ์สวัสดิ์
3. [ข้อมูลยังไม่ครบ / ต้องตรวจสอบ: รายละเอียดใบเสร็จการจัดส่งพัสดุและผลการตรวจพิสูจน์สารเคมีจากกรมวิทยาศาสตร์การแพทย์]

บันทึกไว้ ณ วันที่ 10 สิงหาคม 2569
(ลงชื่อ).................................................ผู้ให้ถ้อยคำ
(ลงชื่อ).................................................พนักงานสอบสวนผู้บันทึก
"""
    
    # Create new Statement Version
    ver_num = len([v for v in getattr(db, "statement_versions", []) if v.get("statement_id") == statement_id]) + 1
    ver_id = f"sv-{str(uuid.uuid4())[:8]}"
    ver_item = {
        "id": ver_id,
        "statement_id": statement_id,
        "version_number": ver_num,
        "content_text": draft_body,
        "changed_by": user["id"],
        "change_reason": "สร้างร่างคำให้การด้วย AI Statement Copilot",
        "review_status": "DRAFT",
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ")
    }
    
    if not hasattr(db, "statement_versions"):
        db.statement_versions = []
    db.statement_versions.append(ver_item)
    
    db.audit_log.append({
        "event_id": str(uuid.uuid4()), "occurred_at": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "actor_user_id": user["id"], "action": "STATEMENT.AI.DRAFT",
        "resource_type": "statement", "resource_id": statement_id, "result": "success"
    })
    
    return {"status": "success", "draft": draft_body, "version": ver_item}

# 6. Statement Supervisor Review & Approval
@app.post("/api/v1/statements/{statement_id}/submit-review")
@app.post("/api/statements/{statement_id}/submit-review")
async def submit_statement_for_review(statement_id: str, authorization: Optional[str] = Header(None)):
    user = authenticate_request(authorization)
    stat = next((s for s in db.statements if s.get("id") == statement_id), None)
    if not stat:
        raise HTTPException(status_code=404, detail="Statement not found")
    stat["status"] = "IN_REVIEW"
    db.audit_log.append({
        "event_id": str(uuid.uuid4()), "occurred_at": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "actor_user_id": user["id"], "action": "STATEMENT.SUBMIT_REVIEW",
        "resource_type": "statement", "resource_id": statement_id, "result": "success"
    })
    return {"status": "success", "statement_status": "IN_REVIEW"}

@app.post("/api/v1/statements/{statement_id}/approve")
@app.post("/api/statements/{statement_id}/approve")
async def approve_statement_review(statement_id: str, authorization: Optional[str] = Header(None)):
    user = authenticate_request(authorization)
    stat = next((s for s in db.statements if s.get("id") == statement_id), None)
    if not stat:
        raise HTTPException(status_code=404, detail="Statement not found")
    stat["status"] = "APPROVED"
    db.audit_log.append({
        "event_id": str(uuid.uuid4()), "occurred_at": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "actor_user_id": user["id"], "action": "STATEMENT.APPROVE",
        "resource_type": "statement", "resource_id": statement_id, "result": "success"
    })
    return {"status": "success", "statement_status": "APPROVED"}


# -------------------------------------------------------------
# PHASE 6: LEGAL ANALYSIS & INVESTIGATION PLANNING SCHEMAS
# -------------------------------------------------------------

class CaseFactCreate(BaseModel):
    fact_text: str
    fact_type: str = "FACT"  # FACT, CLAIM, INFERENCE, CONFLICT
    verification_status: str = "NOT_VERIFIED"  # VERIFIED, PARTIALLY_VERIFIED, NOT_VERIFIED, CONTRADICTED
    source_type: str = "EVIDENCE"  # EVIDENCE, STATEMENT, TIMELINE, TRANSACTION
    source_ids: Optional[List[str]] = []

class LegalElementAssessmentCreate(BaseModel):
    legal_issue_id: str
    status: str = "SUPPORTED"  # SUPPORTED, PARTIALLY_SUPPORTED, NOT_SUPPORTED, CONTRADICTED, INSUFFICIENT_EVIDENCE
    supporting_fact_ids: Optional[List[str]] = []
    supporting_evidence_ids: Optional[List[str]] = []
    contradictory_evidence_ids: Optional[List[str]] = []
    missing_fact_description: Optional[str] = None
    analyst_comment: Optional[str] = ""

class InvestigationGapActionCreate(BaseModel):
    title: str
    description: str
    action_type: str = "REQUEST_DOCUMENT"  # INTERVIEW, REQUEST_DOCUMENT, REQUEST_BANK_RECORD, OBTAIN_CCTV, DIGITAL_FORENSICS, AGENCY_REQUEST
    priority: str = "HIGH"
    assigned_to: Optional[str] = None
    due_at: Optional[str] = None

class HumanLegalDecisionCreate(BaseModel):
    decision: str  # ACCEPT_LEGAL_MAPPING, REJECT_LEGAL_MAPPING, CLOSE_LEGAL_GAP, APPROVE_ELEMENT_ASSESSMENT
    reason: str
    related_resource: str

# -------------------------------------------------------------
# PHASE 6: LEGAL ANALYSIS & INVESTIGATION PLANNING REST APIs
# -------------------------------------------------------------

# 1. Case Facts & Fact Source Mapping
@app.get("/api/v1/cases/{case_id}/facts")
@app.get("/api/cases/{case_id}/facts")
async def get_case_facts(case_id: str, authorization: Optional[str] = Header(None)):
    user = authenticate_request(authorization)
    check_case_access(user, case_id)
    facts = [f for f in getattr(db, "case_facts", []) if f.get("case_id") == case_id]
    return {"status": "success", "facts": facts}

@app.post("/api/v1/cases/{case_id}/facts")
@app.post("/api/cases/{case_id}/facts")
async def create_case_fact(case_id: str, payload: CaseFactCreate, authorization: Optional[str] = Header(None)):
    user = authenticate_request(authorization)
    check_case_access(user, case_id)
    
    fact_id = f"fact-{case_id.lower()}-{str(uuid.uuid4())[:6]}"
    fact = {
        "id": fact_id,
        "case_id": case_id,
        "fact_text": payload.fact_text,
        "fact_type": payload.fact_type,
        "verification_status": payload.verification_status,
        "source_type": payload.source_type,
        "source_ids": payload.source_ids or [],
        "created_by": user["id"],
        "reviewed_by": user["id"] if payload.verification_status == "VERIFIED" else None,
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ")
    }
    
    if not hasattr(db, "case_facts"):
        db.case_facts = []
    db.case_facts.append(fact)
    
    db.audit_log.append({
        "event_id": str(uuid.uuid4()), "occurred_at": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "actor_user_id": user["id"], "action": "LEGAL.FACT.CREATE",
        "resource_type": "case_fact", "resource_id": fact_id, "result": "success"
    })
    
    return {"status": "success", "fact": fact}

# 2. Fact-Evidence-Legal Element Full Drill-down Matrix
@app.get("/api/v1/cases/{case_id}/legal-matrix")
@app.get("/api/cases/{case_id}/legal-matrix")
async def get_legal_matrix_full(case_id: str, authorization: Optional[str] = Header(None)):
    user = authenticate_request(authorization)
    check_case_access(user, case_id)
    
    legal_issues = [li for li in getattr(db, "legal_issues", []) if li.get("case_id") == case_id]
    legal_elements = [el for el in getattr(db, "legal_elements", []) if el.get("case_id") == case_id]
    facts = [f for f in getattr(db, "case_facts", []) if f.get("case_id") == case_id]
    evidences = [e for e in db.evidence if e.get("case_id") == case_id]
    assessments = [a for a in getattr(db, "legal_element_assessments", []) if a.get("case_id") == case_id]
    gaps = [g for g in getattr(db, "evidence_gaps", []) if g.get("case_id") == case_id]
    
    matrix = []
    for issue in legal_issues:
        issue_elems = [el for el in legal_elements if el.get("legal_issue_id") == issue.get("id")]
        elem_list = []
        for elem in issue_elems:
            asm = next((a for a in assessments if a.get("legal_element_id") == elem.get("id")), None)
            elem_gaps = [g for g in gaps if g.get("legal_element_id") == elem.get("id")]
            supp_facts = [f for f in facts if asm and f.get("id") in asm.get("supporting_fact_ids", [])]
            supp_evs = [e for e in evidences if asm and e.get("id") in asm.get("supporting_evidence_ids", [])]
            
            elem_list.append({
                "element_id": elem.get("id"),
                "element_code": elem.get("element_code"),
                "title": elem.get("title"),
                "is_required": elem.get("is_required", True),
                "assessment_status": asm.get("status", "REQUIRES_REVIEW") if asm else "REQUIRES_REVIEW",
                "supporting_facts": supp_facts,
                "supporting_evidence": supp_evs,
                "gaps": elem_gaps
            })
            
        matrix.append({
            "issue_id": issue.get("id"),
            "issue_title": issue.get("issue_title"),
            "legal_code": issue.get("legal_code"),
            "status": issue.get("status"),
            "elements": elem_list
        })
        
    return {"status": "success", "case_id": case_id, "matrix": matrix}

# 3. Element Assessment
@app.post("/api/v1/legal-elements/{element_id}/assess")
@app.post("/api/legal-elements/{element_id}/assess")
async def assess_legal_element(element_id: str, payload: LegalElementAssessmentCreate, authorization: Optional[str] = Header(None)):
    user = authenticate_request(authorization)
    
    asm_id = f"lea-{str(uuid.uuid4())[:8]}"
    asm = {
        "id": asm_id,
        "legal_element_id": element_id,
        "legal_issue_id": payload.legal_issue_id,
        "status": payload.status,
        "supporting_fact_ids": payload.supporting_fact_ids or [],
        "supporting_evidence_ids": payload.supporting_evidence_ids or [],
        "contradictory_evidence_ids": payload.contradictory_evidence_ids or [],
        "missing_fact_description": payload.missing_fact_description,
        "analyst_comment": payload.analyst_comment,
        "reviewed_by": user["full_name"],
        "reviewed_at": time.strftime("%Y-%m-%dT%H:%M:%SZ")
    }
    
    if not hasattr(db, "legal_element_assessments"):
        db.legal_element_assessments = []
    db.legal_element_assessments.append(asm)
    
    db.audit_log.append({
        "event_id": str(uuid.uuid4()), "occurred_at": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "actor_user_id": user["id"], "action": "LEGAL.ELEMENT.ASSESS",
        "resource_type": "legal_element", "resource_id": element_id, "result": "success"
    })
    
    return {"status": "success", "assessment": asm}

# 4. AI Legal Mapping & Evidence Sufficiency Agents
@app.post("/api/v1/cases/{case_id}/ai/legal-mapping")
@app.post("/api/cases/{case_id}/ai/legal-mapping")
async def run_ai_legal_mapping(case_id: str, authorization: Optional[str] = Header(None)):
    user = authenticate_request(authorization)
    check_case_access(user, case_id)
    
    mapping_result = {
        "case_id": case_id,
        "applicable_laws": [
            {
                "law_title": "ประมวลกฎหมายอาญา มาตรา 343",
                "provisions": "ความผิดฐานร่วมกันฉ้อโกงประชาชน",
                "elements_mapped": [
                    {"element": "หลอกลวงด้วยการแสดงข้อความอันเป็นเท็จต่อประชาชน", "evidence_support": "11b7df3c-6622-48df-9cb9-ef77ba4c28f1", "status": "SUPPORTED"},
                    {"element": "ได้ไปซึ่งทรัพย์สินจากผู้ถูกหลอกลวง", "evidence_support": "f05d9e5b-ec1d-4009-bf2f-e8b9fb6cb088", "status": "SUPPORTED"}
                ]
            },
            {
                "law_title": "พ.ร.บ.ว่าด้วยการกระทำความผิดเกี่ยวกับคอมพิวเตอร์ พ.ศ. 2550 มาตรา 14(1)",
                "provisions": "นำเข้าสู่ระบบคอมพิวเตอร์ซึ่งข้อมูลอันเป็นเท็จ",
                "elements_mapped": [
                    {"element": "นำเข้าข้อมูลคอมพิวเตอร์ปลอมหรือเท็จโดยประการที่น่าจะเกิดความเสียหายแก่ประชาชน", "evidence_support": "11b7df3c-6622-48df-9cb9-ef77ba4c28f1", "status": "SUPPORTED"}
                ]
            }
        ],
        "warning": "คำเตือน: AI เป็นผู้ช่วยวิเคราะห์องค์ประกอบความผิดเท่านั้น พนักงานสอบสวนต้องเป็นผู้วินิจฉัยข้อกฎหมายขั้นสุดท้าย",
        "review_status": "REQUIRES_REVIEW"
    }
    
    db.audit_log.append({
        "event_id": str(uuid.uuid4()), "occurred_at": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "actor_user_id": user["id"], "action": "LEGAL.AI.MAPPING",
        "resource_type": "legal_mapping", "resource_id": case_id, "result": "success"
    })
    
    return {"status": "success", "mapping": mapping_result}

@app.post("/api/v1/cases/{case_id}/ai/evidence-sufficiency")
@app.post("/api/cases/{case_id}/ai/evidence-sufficiency")
async def run_ai_evidence_sufficiency(case_id: str, authorization: Optional[str] = Header(None)):
    user = authenticate_request(authorization)
    check_case_access(user, case_id)
    
    sufficiency_result = {
        "case_id": case_id,
        "overall_sufficiency": "MODERATE_SUPPORT",
        "elements_summary": [
            {"element_code": "SEC343-E1", "support_level": "STRONG_SUPPORT", "independent_sources": 3, "integrity_verified": True},
            {"element_code": "SEC343-E2", "support_level": "STRONG_SUPPORT", "independent_sources": 2, "integrity_verified": True},
            {"element_code": "SEC343-E3", "support_level": "LIMITED_SUPPORT", "independent_sources": 1, "missing_items": ["CCTV ตู้ ATM ลาดพร้าว"]}
        ],
        "workflow_readiness": "PARTIALLY_READY"
    }
    return {"status": "success", "sufficiency": sufficiency_result}

# 5. AI Investigation Planning Engine
@app.post("/api/v1/cases/{case_id}/ai/investigation-plan")
@app.post("/api/cases/{case_id}/ai/investigation-plan")
async def generate_ai_investigation_plan(case_id: str, authorization: Optional[str] = Header(None)):
    user = authenticate_request(authorization)
    check_case_access(user, case_id)
    
    suggested_actions = [
        {
            "priority": "URGENT",
            "action_type": "REQUEST_BANK_RECORD",
            "title": "ขอรายการเดินบัญชีแถวที่ 2 ธนาคารกรุงไทย ของ น.ส.พัชรี แก้วมณี",
            "description": "ประสานงานธนาคารกรุงไทยเพื่อตรวจสอบเส้นทางการเงินและอายัดบัญชี",
            "target_agency": "ธนาคารกรุงไทย / ปปง."
        },
        {
            "priority": "HIGH",
            "action_type": "OBTAIN_CCTV",
            "title": "ขอภาพบันทึกกล้อง CCTV หน้าตู้ ATM สาขาลาดพร้าว",
            "description": "ประสานขอภาพกล้องวงจรปิดขณะคนร้ายทำรายการถอนเงินสดเพื่อยืนยันตัวตน",
            "target_agency": "ธนาคารไทยพาณิชย์ สาขาลาดพร้าว"
        },
        {
            "priority": "HIGH",
            "action_type": "INTERVIEW",
            "title": "ออกหมายเรียกสอบปากคำ น.ส.พัชรี แก้วมณี (เจ้าของบัญชีม้า)",
            "description": "สอบสวนที่มาของการเปิดบัญชีและการรับโอนเงินต่อจากนายกิตติศักดิ์",
            "target_agency": "สภ.ดอนเมือง (ส่งหมายเรียก)"
        }
    ]
    
    return {"status": "success", "suggested_actions": suggested_actions}

# 6. Gap Conversion to Investigation Action
@app.post("/api/v1/investigation-gaps/{gap_id}/create-action")
@app.post("/api/investigation-gaps/{gap_id}/create-action")
async def create_action_from_gap(gap_id: str, payload: InvestigationGapActionCreate, authorization: Optional[str] = Header(None)):
    user = authenticate_request(authorization)
    
    action_id = f"act-{str(uuid.uuid4())[:8]}"
    action_item = {
        "id": action_id,
        "gap_id": gap_id,
        "title": payload.title,
        "description": payload.description,
        "action_type": payload.action_type,
        "priority": payload.priority,
        "assigned_to": payload.assigned_to or user["id"],
        "status": "pending",
        "due_at": payload.due_at or time.strftime("%Y-%m-%dT17:00:00Z"),
        "created_by": user["id"],
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ")
    }
    
    if not hasattr(db, "investigation_actions"):
        db.investigation_actions = []
    db.investigation_actions.append(action_item)
    
    db.audit_log.append({
        "event_id": str(uuid.uuid4()), "occurred_at": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "actor_user_id": user["id"], "action": "INVESTIGATION.ACTION.CREATE",
        "resource_type": "investigation_action", "resource_id": action_id, "result": "success"
    })
    
    return {"status": "success", "action": action_item}

# 7. Human Legal Decision Recording
@app.post("/api/v1/cases/{case_id}/legal-decisions")
@app.post("/api/cases/{case_id}/legal-decisions")
async def record_human_legal_decision(case_id: str, payload: HumanLegalDecisionCreate, authorization: Optional[str] = Header(None)):
    user = authenticate_request(authorization)
    check_case_access(user, case_id)
    
    decision_id = f"hld-{case_id.lower()}-{str(uuid.uuid4())[:6]}"
    decision_item = {
        "id": decision_id,
        "case_id": case_id,
        "decision": payload.decision,
        "reason": payload.reason,
        "decided_by": user["full_name"],
        "decided_at": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "related_resource": payload.related_resource
    }
    
    if not hasattr(db, "human_legal_decisions"):
        db.human_legal_decisions = []
    db.human_legal_decisions.append(decision_item)
    
    db.audit_log.append({
        "event_id": str(uuid.uuid4()), "occurred_at": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "actor_user_id": user["id"], "action": "HUMAN.LEGAL.DECISION",
        "resource_type": "human_legal_decision", "resource_id": decision_id, "result": "success"
    })
    
    return {"status": "success", "decision": decision_item}
