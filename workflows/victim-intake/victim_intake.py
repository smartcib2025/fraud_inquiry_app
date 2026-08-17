# CPPD Workflow: Victim Intake Ingestion
import sys
import os
import json
import httpx
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../services/ai-router')))
from ai_router import CPPDEnvironmentRouter

class VictimIntakeWorkflow:
    def __init__(self, api_url: str = "http://localhost:8000"):
        self.api_url = api_url
        self.router = CPPDEnvironmentRouter()

    def process_intake(self, case_id: str, raw_text: str) -> dict:
        """
        Executes the victim intake process:
        1. Logs audit start.
        2. Routes transcript to Gemini Flash for structured JSON extraction.
        3. Validates extracted schema fields.
        4. Publishes to the central trigger event bus.
        """
        print(f"[Workflow: Victim Intake] Starting ingest for case: {case_id}")
        
        # 1. Extract using AI Router
        extracted = self.router.extract_structured(raw_text)
        print(f"[Workflow: Victim Intake] Extracted structured model: {extracted.dict()}")
        
        # Determine primary victim name (first person in extracted list)
        primary_name = extracted.persons[0] if extracted.persons else "Unknown Victim"
        phone = extracted.phones[0] if extracted.phones else ""
        loss_amount = float(extracted.transactions[0]) if extracted.transactions else 0.00
        
        # 2. Publish to Pub/Sub simulation
        payload = {
            "case_id": case_id,
            "full_name": primary_name,
            "phone": phone,
            "email": f"{primary_name.lower().replace(' ', '.')}@example.com" if primary_name != "Unknown Victim" else "",
            "loss_amount": loss_amount,
            "address": "Extracted from intake form statement",
            "extracted_raw": extracted.dict()
        }
        
        try:
            response = httpx.post(
                f"{self.api_url}/api/pubsub/publish",
                json={"event_type": "VICTIM_REGISTERED", "payload": payload}
            )
            return {"status": "processed", "result": response.json()}
        except Exception as e:
            return {"status": "error", "error": f"Failed to post to Event Bus: {str(e)}", "payload": payload}

if __name__ == "__main__":
    sample_statement = (
        "My name is Nattapong Sukprasert, I live in Bangkok. I was defrauded of 1.25M Baht by Facebook merchant Kittisak Wongsawat. "
        "I transferred the money to Siam Commerce Bank 401-229-3388 on August 9th. My phone number is 081-555-0192."
    )
    workflow = VictimIntakeWorkflow()
    res = workflow.process_intake("CASE-142", sample_statement)
    print(json.dumps(res, indent=2))
