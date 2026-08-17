# CPPD Investigation OS - Event Triggers and Pub/Sub Routing

This document specifies the event-driven backbone.

## 1. Core Events
The platform utilizes a structured topic hierarchy on Google Cloud Pub/Sub:

| Event Type | Source Component | Key Action |
|---|---|---|
| `VICTIM_REGISTERED` | Supabase Webhook / Portal | Initiates intake flow, calls Gemini extract |
| `EVIDENCE_UPLOADED` | Evidence Gateway / Bucket | Runs hash verification, kicks off derived copies |
| `ENTITY_CREATED` | Entity Service | Triggers exact/fuzzy matching across graph |
| `ENTITY_MATCHED` | Entity Resolution Workflow | Publishes cross-case alert if linked to > 1 case |
| `TRANSACTION_IMPORTED` | Transaction Service | Triggers flow analysis & layer clustering |
| `EVIDENCE_GAP_FOUND` | Gap Workflow | Generates task assignments & Slack warning |
| `SUPERVISOR_REVIEW_REQUESTED` | Case Service | Generates supervisor checklist & approval cards |

## 2. Payload Schema Standard
All messages must include a standard wrapper containing:
```json
{
  "event_id": "UUID-v4",
  "event_type": "EVENT_TYPE",
  "timestamp": "ISO-8601",
  "sender_id": "service-identity-name",
  "payload": {
    "case_id": "CASE-142",
    "resource_id": "specific-record-id",
    "details": {}
  }
}
```
