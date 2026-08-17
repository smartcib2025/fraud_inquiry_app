# Model Context Protocol (MCP) Server - CPPD Investigation Interface
import sys
import json
from typing import Dict, Any, List

# Define the standard MCP Tool list
MCP_TOOLS = [
    {
        "name": "get_case",
        "description": "Retrieve the full profile details, victim lists, and task statuses for a specific case.",
        "input_schema": {
            "type": "object",
            "properties": {
                "case_id": {"type": "string", "description": "The case ID, e.g., CASE-142"}
            },
            "required": ["case_id"]
        }
    },
    {
        "name": "search_evidence",
        "description": "Query physical and digital evidence records associated with a case.",
        "input_schema": {
            "type": "object",
            "properties": {
                "case_id": {"type": "string", "description": "The case ID"},
                "query": {"type": "string", "description": "Keyword search across titles and descriptions"},
                "type": {"type": "string", "description": "Filter by evidence type (e.g. document, audio, video)"}
            },
            "required": ["case_id"]
        }
    },
    {
        "name": "search_entity",
        "description": "Lookup nodes in the CPPD Knowledge Graph such as phone numbers, bank accounts, or names.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search string value, e.g., phone number or account ID"}
            },
            "required": ["query"]
        }
    },
    {
        "name": "find_related_cases",
        "description": "Locate cross-case links where a specific entity appears in multiple investigations.",
        "input_schema": {
            "type": "object",
            "properties": {
                "entity_id": {"type": "string", "description": "The entity UUID"}
            },
            "required": ["entity_id"]
        }
    },
    {
        "name": "get_transactions",
        "description": "Retrieve financial ledger entries and flow linkages for a case or account.",
        "input_schema": {
            "type": "object",
            "properties": {
                "case_id": {"type": "string", "description": "Limit search to a case"},
                "account_id": {"type": "string", "description": "Limit search to a bank account ID"}
            }
        }
    },
    {
        "name": "create_task",
        "description": "Insert a new investigation check or task in the case ledger.",
        "input_schema": {
            "type": "object",
            "properties": {
                "case_id": {"type": "string", "description": "The case ID"},
                "title": {"type": "string", "description": "The task title"},
                "description": {"type": "string", "description": "Details of what is required"},
                "assigned_to": {"type": "string", "description": "The UUID of the investigator"},
                "due_date": {"type": "string", "description": "ISO timestamp for deadline"}
            },
            "required": ["case_id", "title"]
        }
    }
]

class CPPDMCPServer:
    def __init__(self, api_url: str = "http://localhost:8000"):
        self.api_url = api_url
        
    def list_tools(self) -> List[Dict[str, Any]]:
        return MCP_TOOLS

    def call_tool(self, name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        Routes the tool execution. In production, this verifies GCP IAM authorization,
        attributes resource usage, checks DLP policy, and executes queries against Supabase.
        """
        import httpx
        try:
            if name == "get_case":
                case_id = arguments.get("case_id")
                response = httpx.get(f"{self.api_url}/api/cases/{case_id}")
                return {"content": [{"type": "text", "text": json.dumps(response.json(), indent=2)}]}
                
            elif name == "search_evidence":
                case_id = arguments.get("case_id")
                response = httpx.get(f"{self.api_url}/api/cases/{case_id}")
                evidence = response.json().get("evidence", [])
                # Apply filter
                query = arguments.get("query")
                if query:
                    evidence = [e for e in evidence if query.lower() in e["title"].lower() or query.lower() in e.get("description", "").lower()]
                return {"content": [{"type": "text", "text": json.dumps(evidence, indent=2)}]}

            elif name == "search_entity":
                query = arguments.get("query")
                response = httpx.get(f"{self.api_url}/api/entities", params={"query": query})
                return {"content": [{"type": "text", "text": json.dumps(response.json(), indent=2)}]}

            elif name == "find_related_cases":
                entity_id = arguments.get("entity_id")
                # Simulated lookup mapping
                related = {
                    "c02f8c5b-38ab-41c1-903c-83b66d4db03b": ["CASE-142", "CASE-087"],
                    "c03f8c5b-38ab-41c1-903c-83b66d4db03c": ["CASE-142", "CASE-087"]
                }
                cases = related.get(entity_id, ["CASE-142"])
                return {"content": [{"type": "text", "text": json.dumps({"entity_id": entity_id, "related_cases": cases, "confidence": 0.93}, indent=2)}]}

            elif name == "get_transactions":
                # Returns seeded transaction mappings
                txn_data = [
                    {
                        "id": "a01c3d9a-1122-3344-5566-778899aabbcc",
                        "case_id": "CASE-142",
                        "amount": 1250000.00,
                        "currency": "THB",
                        "transaction_date": "2026-08-09T14:32:00Z",
                        "reference_number": "TXN-99882211"
                    }
                ]
                return {"content": [{"type": "text", "text": json.dumps(txn_data, indent=2)}]}

            elif name == "create_task":
                # Simulated POST insertion
                task_payload = {
                    "case_id": arguments.get("case_id"),
                    "title": arguments.get("title"),
                    "description": arguments.get("description"),
                    "assigned_to": arguments.get("assigned_to"),
                    "due_date": arguments.get("due_date")
                }
                return {"content": [{"type": "text", "text": json.dumps({"status": "created", "task": task_payload}, indent=2)}]}

            else:
                return {"is_error": True, "content": [{"type": "text", "text": f"Unknown tool: {name}"}]}

        except Exception as e:
            return {"is_error": True, "content": [{"type": "text", "text": f"Error running MCP tool: {str(e)}"}]}

if __name__ == "__main__":
    # Handlers for standard input/output MCP invocation
    server = CPPDMCPServer()
    if len(sys.argv) > 1 and sys.argv[1] == "list":
        print(json.dumps(server.list_tools(), indent=2))
    elif len(sys.argv) > 2 and sys.argv[1] == "call":
        tool_name = sys.argv[2]
        tool_args = json.loads(sys.argv[3]) if len(sys.argv) > 3 else {}
        print(json.dumps(server.call_tool(tool_name, tool_args), indent=2))
    else:
        print("CPPD MCP Server online. Usage: python mcp_server.py [list|call <tool_name> <arguments_json>]")
