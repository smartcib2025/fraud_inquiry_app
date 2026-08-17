# CPPD Workflow: Entity Resolution and Deduplication
import sys
import os
import json
import httpx

class EntityResolutionWorkflow:
    def __init__(self, api_url: str = "http://localhost:8000"):
        self.api_url = api_url

    def resolve_entity(self, case_id: str, entity_type: str, entity_name: str, value: str) -> dict:
        """
        Executes CPPD Knowledge Graph Entity resolution:
        1. Checks for exact identifier matches (e.g. same phone, same bank account).
        2. Calculates fuzzy text matching on names.
        3. If a match is found on an active entity in another case, triggers cross-case alerts.
        """
        print(f"[Workflow: Entity Resolution] Evaluating entity: {entity_name} ({entity_type}) with value {value}")
        
        # In a real environment, we run fuzzy soundex/metaphone matching and query Supabase.
        # Here we simulate resolving the suspect Kittisak's details
        is_match = False
        linked_cases = []
        confidence = 1.0
        
        if value in ["089-111-2345", "401-229-3388", "1-1002-88832-11-2"]:
            is_match = True
            linked_cases = ["CASE-142", "CASE-087"]
            confidence = 0.93 if value == "089-111-2345" else 0.98
            
        if is_match:
            print(f"[Workflow: Entity Resolution] Match detected: {entity_name} linked to cases {linked_cases}")
            # Emit ENTITY_CREATED event to trigger Cross-Case warnings
            payload = {
                "case_id": case_id,
                "name": value,
                "type": entity_type,
                "linked_cases": linked_cases,
                "confidence": confidence
            }
            try:
                response = httpx.post(
                    f"{self.api_url}/api/pubsub/publish",
                    json={"event_type": "ENTITY_CREATED", "payload": payload}
                )
                return {"status": "resolved", "match_found": True, "details": response.json()}
            except Exception as e:
                return {"status": "error", "error": f"Failed to post resolution event: {str(e)}"}
                
        return {"status": "resolved", "match_found": False}

if __name__ == "__main__":
    workflow = EntityResolutionWorkflow()
    # Test suspect phone lookup
    res = workflow.resolve_entity("CASE-142", "PHONE", "Suspect Phone", "089-111-2345")
    print(json.dumps(res, indent=2))
