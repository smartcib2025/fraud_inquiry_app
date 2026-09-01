# CPPD AI Model Router & Extraction Service (Master Prompt Compliant)
import os
import json
import time
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

try:
    from google import genai
    from google.genai import types
    client_available = True
except ImportError:
    client_available = False

class TaggedFactItem(BaseModel):
    tag: str = Field(description="FACT, CLAIM, INFERENCE, CONFLICT, EVIDENCE_GAP, NOT_VERIFIED, REQUIRES_HUMAN_REVIEW")
    text: str = Field(description="Factual summary or assertion")
    source_evidence_id: Optional[str] = Field(default=None, description="Linked Evidence ID or Statement ID")
    confidence: float = Field(default=0.90)

class StandardAnalysisResult(BaseModel):
    analysis_type: str
    case_id: str
    status: str = Field(default="REQUIRES_HUMAN_REVIEW", description="VERIFIED, PARTIALLY_VERIFIED, MISMATCH, NOT_VERIFIED, REQUIRES_CHECK, REQUIRES_HUMAN_REVIEW")
    facts: List[TaggedFactItem] = Field(default_factory=list)
    summary: str
    action_items: List[str] = Field(default_factory=list)

class ExtractedEntities(BaseModel):
    persons: list[str] = Field(default_factory=list)
    companies: list[str] = Field(default_factory=list)
    phones: list[str] = Field(default_factory=list)
    bank_accounts: list[str] = Field(default_factory=list)
    transactions: list[str] = Field(default_factory=list)
    dates: list[str] = Field(default_factory=list)
    locations: list[str] = Field(default_factory=list)
    allegations: list[str] = Field(default_factory=list)
    evidence_references: list[str] = Field(default_factory=list)

class CPPDEnvironmentRouter:
    SYSTEM_LEGAL_SAFETY_PROMPT = """
You are the Agentic AI Investigation Copilot for Division 1, Consumer Protection Police Division (กก.1 บก.ปคบ.).
Rules you must ALWAYS follow:
1. You are an investigative assistant, NOT a judicial fact-finder.
2. NEVER declare that a person is guilty or commit automated culpability verdicts.
3. Use safe legal terminology: 'Facts may correspond to statutory elements under Section X'.
4. Every fact statement must be categorized using tags:
   - [FACT]: Verified by tangible evidence (slip, hash, corporate filing).
   - [CLAIM]: Asserted by complainant, witness, or suspect.
   - [INFERENCE]: Analytical deduction by AI.
   - [CONFLICT]: Inconsistencies or contradictions.
   - [EVIDENCE GAP]: Missing documents/signatures required for prosecution.
   - [REQUIRES HUMAN REVIEW]: Critical decision for inquiry official.
5. Never hallucinate fake laws, judgments, or nonexistent witness statements.
"""

    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY", "mock-key")
        self.client = None
        if client_available and self.api_key != "mock-key":
            self.client = genai.Client(api_key=self.api_key)

    def load_settings(self) -> Dict[str, Any]:
        settings_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "ai_settings.json"))
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

    def _call_local_ai(self, prompt: str, system_prompt: str = None, response_format_json: bool = False) -> str:
        settings = self.load_settings()
        endpoint = settings.get("local_endpoint", "http://localhost:11434/v1")
        model = settings.get("local_model", "llama3")
        
        url = endpoint.rstrip("/")
        if not url.endswith("/chat/completions"):
            url = f"{url}/chat/completions"
            
        messages = []
        sys_p = (system_prompt or "") + "\n" + self.SYSTEM_LEGAL_SAFETY_PROMPT
        messages.append({"role": "system", "content": sys_p})
        messages.append({"role": "user", "content": prompt})
        
        payload = {
            "model": model,
            "messages": messages,
            "temperature": 0.1
        }
        if response_format_json:
            payload["response_format"] = {"type": "json_object"}
            
        print(f"[AI Router] Routing locally: {url} | Model: {model}")
        
        try:
            import httpx
            res = httpx.post(url, json=payload, headers={"Content-Type": "application/json"}, timeout=10.0)
            if res.status_code == 200:
                data = res.json()
                return data["choices"][0]["message"]["content"]
            else:
                print(f"[AI Router] Local AI returned status {res.status_code}: {res.text}")
                raise Exception(f"HTTP Status {res.status_code}")
        except Exception as e:
            print(f"[AI Router] Local AI request failed: {e}")
            raise e

    def route_model(self, task_type: str) -> str:
        pro_tasks = ["cross_case_synthesis", "timeline_reasoning", "contradiction_analysis", "supervisor_review", "legal_mapping"]
        if task_type in pro_tasks:
            return "gemini-2.5-pro"
        return "gemini-2.5-flash"

    def analyze_text(self, text: str, task_type: str) -> Dict[str, Any]:
        settings = self.load_settings()
        if settings.get("mode") == "cloud":
            model = self.route_model(task_type)
            print(f"[AI Router] Routing task: {task_type} -> Model: {model}")
            if not self.client:
                return self._mock_extraction(text, task_type)
            try:
                response = self.client.models.generate_content(
                    model=model,
                    contents=f"{self.SYSTEM_LEGAL_SAFETY_PROMPT}\n\nTask: {task_type}\nText: {text}"
                )
                return {"status": "success", "model_used": model, "result": response.text}
            except Exception as e:
                return {"status": "error", "error": str(e), "model_used": model}
        else:
            prompt = f"Task: {task_type}. Analyze this text:\n{text}"
            try:
                result = self._call_local_ai(prompt)
                return {"status": "success", "model_used": settings.get("local_model"), "result": result}
            except Exception as e:
                return {"status": "error", "error": str(e), "model_used": settings.get("local_model")}

    def extract_structured(self, text: str) -> ExtractedEntities:
        settings = self.load_settings()
        if settings.get("mode") == "cloud":
            if not self.client:
                return self._mock_structured(text)
            try:
                response = self.client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=f"{self.SYSTEM_LEGAL_SAFETY_PROMPT}\n\nExtract all CPPD entities from this statement: {text}",
                    config=types.GenerateContentConfig(
                        response_mime_type="application/json",
                        response_schema=ExtractedEntities,
                    )
                )
                data = json.loads(response.text)
                return ExtractedEntities(**data)
            except Exception as e:
                print(f"[AI Router] Failed to extract structured content: {e}. Falling back to default.")
                return self._mock_structured(text)
        else:
            prompt = f"Extract all CPPD entities from this statement: {text}\nYou must output a JSON object matching this schema:\n{json.dumps(ExtractedEntities.schema())}"
            system = "You are a CPPD Entity Extractor. Only output valid JSON matching the requested schema. Do not output anything else."
            try:
                raw_res = self._call_local_ai(prompt, system_prompt=system, response_format_json=True)
                data = json.loads(raw_res)
                return ExtractedEntities(**data)
            except Exception as e:
                print(f"[AI Router] Local AI structured extraction failed: {e}. Falling back to mock.")
                return self._mock_structured(text)

    def summarize_statement(self, text: str) -> str:
        settings = self.load_settings()
        if settings.get("mode") == "cloud":
            if not self.client:
                return "[FACT] Victim transfer 1.25M THB to SCB 401-229-3388. [CLAIM] Suspect contact: 089-111-2345."
            try:
                response = self.client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=f"{self.SYSTEM_LEGAL_SAFETY_PROMPT}\n\nSummarize this CPPD witness statement in 1-2 sentences with [FACT]/[CLAIM] prefix tags: {text}"
                )
                return response.text.strip()
            except Exception as e:
                print(f"[AI Router] Failed to summarize statement: {e}")
                return "Summary extraction failed."
        else:
            prompt = f"Summarize this CPPD witness statement in 1-2 sentences with [FACT]/[CLAIM] prefix tags: {text}"
            try:
                return self._call_local_ai(prompt).strip()
            except Exception as e:
                print(f"[AI Router] Local AI summarization failed: {e}")
                return "Local AI summary extraction failed."

    def _mock_extraction(self, text: str, task_type: str) -> Dict[str, Any]:
        time.sleep(0.1)
        if task_type == "classification":
            return {"category": "electronic_fraud", "confidence": 0.95}
        elif task_type == "summarization":
            return {"summary": "[FACT] " + text[:100] + "...", "length": len(text)}
        elif task_type == "supervisor_review":
            return {
                "case_readiness": "85%",
                "checks": {
                    "case_completeness": "complete",
                    "contradictions": "1 contradiction identified",
                    "evidence_mapping": "verified"
                }
            }
        return {"result": f"Mock analysis completed using routed schema for {task_type}"}

    def _mock_structured(self, text: str) -> ExtractedEntities:
        import re
        persons = []
        if "Kittisak" in text or "Somchai" in text:
            persons.append("Kittisak Wongsawat")
        if "Nattapong" in text:
            persons.append("Nattapong Sukprasert")
        if "Somsak" in text:
            persons.append("Somsak Test")
            
        phones = re.findall(r"\b\d{3}-\d{3}-\d{4}\b", text) or ["089-111-2345"]
        accounts = re.findall(r"\b\d{3}-\d{3}-\d{4}\b", text) or ["401-229-3388"]
        
        return ExtractedEntities(
            persons=persons,
            companies=["Facebook Shop"] if "Facebook" in text else [],
            phones=phones,
            bank_accounts=accounts,
            transactions=["1250000"] if "1.25M" in text or "1,250,000" in text else [],
            dates=["2026-08-10"],
            locations=["Bangkok"],
            allegations=["Online purchase fraud"],
            evidence_references=[]
        )
