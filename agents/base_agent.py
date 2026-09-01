# CPPD Investigation OS — Base Agent Interface
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
import uuid
import time

class FactTag(BaseModel):
    tag: str = Field(description="FACT, CLAIM, INFERENCE, CONFLICT, EVIDENCE_GAP, NOT_VERIFIED, REQUIRES_HUMAN_REVIEW")
    text: str = Field(description="Statement text or analytical assertion")
    source_evidence_id: Optional[str] = Field(default=None, description="Traceable Evidence ID or Statement ID")
    confidence: float = Field(default=0.90, description="Confidence score 0.0 to 1.0")

class AgentOutput(BaseModel):
    agent_name: str
    case_id: str
    status: str = Field(default="REQUIRES_HUMAN_REVIEW", description="VERIFIED, PARTIALLY_VERIFIED, MISMATCH, NOT_VERIFIED, REQUIRES_CHECK, REQUIRES_HUMAN_REVIEW")
    findings: List[FactTag] = Field(default_factory=list)
    summary: str
    action_items: List[str] = Field(default_factory=list)
    timestamp: str = Field(default_factory=lambda: time.strftime("%Y-%m-%dT%H:%M:%SZ"))

class CPPDBaseAgent:
    def __init__(self, agent_name: str, api_url: str = "http://localhost:8000"):
        self.agent_name = agent_name
        self.api_url = api_url

    def format_safe_output(self, case_id: str, summary: str, findings: List[Dict[str, Any]], actions: List[str] = None, status: str = "REQUIRES_HUMAN_REVIEW") -> Dict[str, Any]:
        tags = [FactTag(**f) if isinstance(f, dict) else f for f in findings]
        output = AgentOutput(
            agent_name=self.agent_name,
            case_id=case_id,
            status=status,
            findings=tags,
            summary=summary,
            action_items=actions or []
        )
        return output.dict()
