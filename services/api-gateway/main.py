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
                "title": "Siam Network Ledger Structuring",
                "description": "Investigation into structured cash transfers and suspected layering using fake online commerce entities.",
                "status": "open",
                "owning_unit": "Financial Crimes Division 1",
                "sensitive": False,
                "created_at": "2026-08-10T10:00:00Z",
                "updated_at": "2026-08-17T15:00:00Z"
            },
            "CASE-087": {
                "id": "CASE-087",
                "title": "Phuket Cyber Cash Layering",
                "description": "Tracking illegal offshore gambling proceeds routed through local proxy banking accounts.",
                "status": "open",
                "owning_unit": "Financial Crimes Division 1",
                "sensitive": False,
                "created_at": "2026-08-12T11:00:00Z",
                "updated_at": "2026-08-16T12:00:00Z"
            },
            "CASE-112": {
                "id": "CASE-112",
                "title": "Bangkok Shell Company Network",
                "description": "Network of interrelated shell companies sharing directors and bank accounts.",
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
            "d2f0998c-8c1d-4099-ae1e-f3f2a89366df": {"id": "d2f0998c-8c1d-4099-ae1e-f3f2a89366df", "email": "somchai.i@cppd.go.th", "full_name": "Somchai Dev (พนักงานสอบสวน กก.1)", "org_unit": "Financial Crimes Division 1", "role": "investigator", "approved": True},
            "a1b2c3d4-e5f6-7a8b-9c0d-1e2f3a4b5c6d": {"id": "a1b2c3d4-e5f6-7a8b-9c0d-1e2f3a4b5c6d", "email": "somsak.b@cppd.go.th", "full_name": "Somsak Code (พนักงานสอบสวน กก.1)", "org_unit": "Financial Crimes Division 1", "role": "investigator", "approved": True},
            "f8c3de7d-94d7-46e2-bc2f-e8b9fb6cb077": {"id": "f8c3de7d-94d7-46e2-bc2f-e8b9fb6cb077", "email": "superintendent@cppd.go.th", "full_name": "Anong Head (ผกก. กก.1 บก.ปคบ.)", "org_unit": "Financial Crimes Division 1", "role": "superintendent", "approved": True},
            "e37b98d2-430b-488f-9a73-982ee3f2112e": {"id": "e37b98d2-430b-488f-9a73-982ee3f2112e", "email": "commander@cppd.go.th", "full_name": "Prapas Chief (ผบก.ปคบ.)", "org_unit": "Division HQ", "role": "commander", "approved": True},
            "p-admin": {"id": "p-admin", "email": "admin@cppd.go.th", "full_name": "Admin Chief", "org_unit": "Division HQ", "role": "admin", "approved": True},
            "p-deputy-commander": {"id": "p-deputy-commander", "email": "deputy.commander@cppd.go.th", "full_name": "deputy.commander (รอง ผบก.ปคบ.)", "org_unit": "Division HQ", "role": "deputy_commander", "approved": True},
            "p-deputy-superintendent": {"id": "p-deputy-superintendent", "email": "deputy.superintendent@cppd.go.th", "full_name": "Anong Head (รอง ผกก. กก.1 บก.ปคบ.)", "org_unit": "Financial Crimes Division 1", "role": "deputy_superintendent", "approved": True},
            "p-clerk": {"id": "p-clerk", "email": "clerk.a@cppd.go.th", "full_name": "Clerk A (เสมียนคดี กก.1)", "org_unit": "Financial Crimes Division 1", "role": "clerk", "approved": False},
            "p-anong": {"id": "p-anong", "email": "investigator.anong@gmail.com", "full_name": "Anong Investigator", "org_unit": "Financial Crimes Division 1", "role": "supervisor", "approved": True}
        }
        self.sessions = {}
        
        # 1. INTAKES
        self.intakes = [
            {
                "id": "INTAKE-001",
                "case_id": None,
                "title": "Cosmetics Scam Complaint",
                "description": "Complaint regarding fake luxury lipsticks sold by 'Siam Network' on Facebook.",
                "reporter_name": "Sunisa Saelim",
                "reporter_phone": "082-111-9988",
                "raw_statement": "I ordered 5 luxury lipsticks from Siam Network page for 15,000 THB but received counterfeit ones. The seller refused refund and blocked me.",
                "triage_urgency": "high",
                "triage_reason": "Multiple similar complaints logged against this seller within 24 hours.",
                "status": "pending",
                "created_at": "2026-08-16T09:00:00Z"
            },
            {
                "id": "INTAKE-002",
                "case_id": None,
                "title": "Unauthorized Subscription Charge",
                "description": "Complaint regarding unauthorized health supplement subscription charges on credit card.",
                "reporter_name": "Piyabut Somdee",
                "reporter_phone": "085-333-2211",
                "raw_statement": "I bought a supplement trial bottle from Phuket supplements site. They charged my card 3,500 THB next month without my consent.",
                "triage_urgency": "medium",
                "triage_reason": "Single transaction dispute, needs consumer protection terms review.",
                "status": "pending",
                "created_at": "2026-08-17T11:00:00Z"
            }
        ]
        
        # 2. PERSONS
        self.persons = [
            {"id": "p-kittisak", "case_id": "CASE-142", "name": "Kittisak Wongsawat", "national_id": "1-1002-88832-11-2", "role": "Suspect", "phone": "089-111-2345", "address": "12/5 Ladprao Rd, Bangkok"},
            {"id": "p-sunisa", "case_id": "CASE-142", "name": "Sunisa Saelim", "national_id": "3-1209-99823-00-1", "role": "Witness/Victim", "phone": "082-111-9988", "address": "45 Vibhavadi Rd, Bangkok"},
            {"id": "p-somchai", "case_id": "CASE-142", "name": "Somchai Sukdee", "national_id": "1-1003-77723-11-0", "role": "Witness (Proxy Director)", "phone": "081-999-8888", "address": "77 Ratchada Rd, Bangkok"}
        ]
        
        # 3. ORGANIZATIONS
        self.organizations = [
            {"id": "org-siam-net", "case_id": "CASE-142", "name": "Siam Network Co., Ltd.", "registration_number": "0105563023145", "type": "Company", "address": "100/1 Sukhumvit Rd, Bangkok", "status": "active"},
            {"id": "org-phuket-supp", "case_id": "CASE-087", "name": "Phuket Supplements Co.", "registration_number": "0765561002231", "type": "Store/Manufacturer", "address": "55/9 Patong Beach Rd, Phuket", "status": "active"}
        ]
        
        # 4. VICTIMS
        self.victims = [
            {"id": "cf2f8c5b-38ab-41c1-903c-83b66d4db02a", "case_id": "CASE-142", "full_name": "Nattapong Sukprasert", "email": "nattapong.s@gmail.com", "phone": "081-555-0192", "address": "123/4 Sukhumvit Rd, Bangkok", "loss_amount": 1250000.00, "intake_source": "portal"},
            {"id": "8b3e9fb3-83bc-42b7-8ce6-90bd551deeb3", "case_id": "CASE-087", "full_name": "Chaiwat Mongkol", "email": "chaiwat.m@yahoo.com", "phone": "089-777-1234", "address": "56/9 Patong Beach Rd, Phuket", "loss_amount": 850000.00, "intake_source": "portal"}
        ]
        
        # 5. EVIDENCE
        self.evidence = [
            {"id": "f05d9e5b-ec1d-4009-bf2f-e8b9fb6cb088", "case_id": "CASE-142", "title": "Transfer slip receipt", "description": "Bank receipt slip showing 1.25M THB transfer to SCB account.", "type": "document", "file_hash": "a3f82cb304b5f883201de374ffea57bd8c928e1832049e3bfd12cf88c9d21415", "status": "sealed", "created_at": "2026-08-10T10:05:00Z"},
            {"id": "11b7df3c-6622-48df-9cb9-ef77ba4c28f1", "case_id": "CASE-142", "title": "Line Chat Logs screenshot", "description": "Screenshots showing contact between suspect and victim.", "type": "document", "file_hash": "e7b92f7a63bc1a2384a56c07221ee9f08cb18d9f10928e3bcfde204d80a1122a", "status": "sealed", "created_at": "2026-08-10T10:10:00Z"}
        ]
        
        # 6. TRANSACTIONS
        self.bank_accounts = [
            {"id": "b07e2a9b-38cc-4d32-bc10-ef239ab82811", "bank_name": "Siam Commerce Bank", "account_number": "401-229-3388", "account_name": "Kittisak Wongsawat"},
            {"id": "b08e3a9c-49dd-5e43-cd21-f0340bc93922", "bank_name": "Kasikorn Bank", "account_number": "702-888-1123", "account_name": "Siam Electronics Co. Ltd"}
        ]
        self.transactions = [
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
            }
        ]
        
        # 7. TIMELINE
        self.timeline = [
            {"id": "ev-1", "case_id": "CASE-142", "event_date": "2026-08-01T09:00:00Z", "title": "Siam Network Co. Registration", "description": "Siam Network Co., Ltd. registered with Department of Business Development.", "evidence_id": None},
            {"id": "ev-2", "case_id": "CASE-142", "event_date": "2026-08-05T10:00:00Z", "title": "Suspect Opens Mule Account", "description": "Kittisak Wongsawat opens Siam Commerce Bank account number 401-229-3388.", "evidence_id": None},
            {"id": "ev-3", "case_id": "CASE-142", "event_date": "2026-08-09T14:32:00Z", "title": "Victim Bank Transfer", "description": "Victim Nattapong Sukprasert transfers 1.25M Baht to Siam Commerce Bank account 401-229-3388.", "evidence_id": "f05d9e5b-ec1d-4009-bf2f-e8b9fb6cb088"},
            {"id": "ev-4", "case_id": "CASE-142", "event_date": "2026-08-10T11:00:00Z", "title": "Cash Withdrawal at Ladprao ATM", "description": "ATM records show 1.25M Baht cash withdrawal by Kittisak. (Alibi contradiction flag).", "evidence_id": None}
        ]
        
        # 8. LEGAL_ISSUES
        self.legal_issues = [
            {"id": "li-1", "case_id": "CASE-142", "issue_title": "Public Fraud (ฉ้อโกงประชาชน)", "legal_code": "Section 343 of Criminal Code", "description": "Fraudulent online listings targeting public consumer purchase.", "status": "substantiated", "evidence_ids": ["f05d9e5b-ec1d-4009-bf2f-e8b9fb6cb088"]},
            {"id": "li-2", "case_id": "CASE-142", "issue_title": "False Advertising (โฆษณาเป็นเท็จ)", "legal_code": "Section 22 of Consumer Protection Act B.E. 2522", "description": "Misrepresentation of cosmetic product quality and certifications.", "status": "under_review", "evidence_ids": ["11b7df3c-6622-48df-9cb9-ef77ba4c28f1"]},
            {"id": "li-3", "case_id": "CASE-142", "issue_title": "Computer Crimes", "legal_code": "Section 14(1) of Computer Crimes Act", "description": "Inputting false information into computer systems.", "status": "substantiated", "evidence_ids": ["11b7df3c-6622-48df-9cb9-ef77ba4c28f1"]}
        ]
        
        # 9. TASKS
        self.tasks = [
            {"id": "918d6e3c-8c5e-4c7b-8395-5db460cb7d10", "case_id": "CASE-142", "title": "Verify Kittisak Wongsawat identity", "description": "Cross-check suspect ID with Department of Provincial Administration registry.", "assigned_to": "d2f0998c-8c1d-4099-ae1e-f3f2a89366df", "status": "pending", "due_date": "2026-08-25T17:00:00Z"},
            {"id": "918d6e3c-8c5e-4c7b-8395-5db460cb7d11", "case_id": "CASE-142", "title": "Analyze bank transactions flow", "description": "Review layering indicators from transaction reports on SCB 401-229-3388.", "assigned_to": "d2f0998c-8c1d-4099-ae1e-f3f2a89366df", "status": "in_progress", "due_date": "2026-08-28T17:00:00Z"}
        ]
        
        # 10. REPORTS
        self.reports = [
            {"id": "rep-001", "case_id": "CASE-142", "report_type": "Executive Brief", "title": "Siam Network Triage Briefing", "content": "DRAFT REPORT\nSummary of Siam Network cosmetics scam...", "created_at": "2026-08-17T12:00:00Z"}
        ]
        
        # 11. COMMUNICATIONS
        self.communications = [
            {
                "id": "comm-001",
                "case_id": "CASE-142",
                "channel": "LINE_CHAT",
                "sender_identifier": "089-111-2345 (Seller)",
                "recipient_identifier": "081-555-0192 (Victim Nattapong)",
                "timestamp": "2026-08-09T14:15:00Z",
                "content_text": "Please transfer 1,250,000 THB to SCB account 401-229-3388 to secure discount cosmetics stock.",
                "evidence_id": "11b7df3c-6622-48df-9cb9-ef77ba4c28f1"
            },
            {
                "id": "comm-002",
                "case_id": "CASE-142",
                "channel": "PHONE_CALL",
                "sender_identifier": "089-111-2345 (Suspect)",
                "recipient_identifier": "081-555-0192 (Victim Nattapong)",
                "timestamp": "2026-08-09T14:20:00Z",
                "content_text": "Voice call confirming order details and delivery timetable.",
                "evidence_id": None
            }
        ]

        # 12. AI_ANALYSES (Isolated from Original Evidence)
        self.ai_analyses = [
            {
                "id": "ana-001",
                "case_id": "CASE-142",
                "agent_name": "TimelineAgent",
                "analysis_type": "TIMELINE_CONTRADICTION",
                "fact_tags": [
                    {"tag": "FACT", "text": "Victim transfer 1.25M to SCB 401-229-3388 at 14:32:00", "source_evidence_id": "f05d9e5b-ec1d-4009-bf2f-e8b9fb6cb088"},
                    {"tag": "CLAIM", "text": "Suspect claims he was in Chiang Mai and card was lost", "source_evidence_id": None},
                    {"tag": "CONFLICT", "text": "SCB online IP registers login in Bangkok at 14:32", "source_evidence_id": "11b7df3c-6622-48df-9cb9-ef77ba4c28f1"}
                ],
                "findings_summary": "Alibi contradiction detected between suspect claim and IP location.",
                "confidence_score": 0.92,
                "review_status": "REQUIRES_HUMAN_REVIEW",
                "reviewed_by": None,
                "investigator_notes": None,
                "created_at": "2026-08-17T12:30:00Z"
            }
        ]

        # 13. AUDIT_LOG
        self.audit_log = []
        self.trigger_events = []
        
        # Legacy compatibility values
        self.statements = [
            {
                "id": "a8efde12-b91b-4f9e-bc43-2287f3b890a2", 
                "case_id": "CASE-142", 
                "subject_id": "cf2f8c5b-38ab-41c1-903c-83b66d4db02a", 
                "subject_type": "victim", 
                "recorded_at": "2026-08-10T10:00:00Z", 
                "transcript": "I was contacted by a seller on Facebook offering bulk electronics at discount. I transferred 1.25M Baht to Siam Commerce Bank account number 401-229-3388. After payment, the seller deleted the Facebook page. The phone number they contacted me with was 089-111-2345.", 
                "summary": "Victim defrauded of 1.25M THB by fake Facebook seller. Funds transferred to SCB 401-229-3388. Contact phone: 089-111-2345.",
                "created_at": "2026-08-10T10:00:00Z"
            }
        ]
        self.ai_findings = [
            {
                "id": "ai-find-001",
                "case_id": "CASE-142",
                "entity_type": "BANK_ACCOUNT",
                "entity_name": "401-229-3388",
                "details": "Linked to Kittisak Wongsawat, active in Siam Network Ledger Structuring case",
                "confidence": 0.95,
                "status": "unverified",
                "created_at": "2026-08-17T12:00:00Z"
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
    if user["role"] not in ["commander", "supervisor"]:
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
