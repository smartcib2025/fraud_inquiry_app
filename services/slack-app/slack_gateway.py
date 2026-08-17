# CPPD Slack Integration Gateway
import hmac
import hashlib
import time
from typing import Dict, Any, List

class SlackBlockBuilder:
    @staticmethod
    def verify_signature(secret: str, timestamp: str, body: str, signature: str) -> bool:
        """
        Validates request origin. Uses HMAC-SHA256 signature matching.
        """
        if not secret or not signature:
            return False
        # Avoid replay attacks (5 minute threshold)
        if abs(time.time() - int(timestamp)) > 300:
            return False
            
        sig_basestring = f"v0:{timestamp}:{body}".encode('utf-8')
        computed_sig = 'v0=' + hmac.new(
            secret.encode('utf-8'),
            sig_basestring,
            hashlib.sha256
        ).hexdigest()
        
        return hmac.compare_digest(computed_sig, signature)

    @staticmethod
    def build_cross_case_alert(
        case_id: str, 
        account: str, 
        linked_cases: List[str], 
        victims_count: int, 
        loss: str, 
        confidence: float
    ) -> Dict[str, Any]:
        """
        Constructs a premium Slack interactive Block message layout for cross-case alerts.
        """
        return {
            "blocks": [
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": "🚨 CRITICAL CROSS-CASE ALERT",
                        "emoji": True
                    }
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*Case Reference*: `{case_id}`\n*Matched Entity*: 🏦 `Account: {account}`\n*Linked Cases*: {', '.join(f'`{c}`' for c in linked_cases)}"
                    }
                },
                {
                    "type": "section",
                    "fields": [
                        {
                            "type": "mrkdwn",
                            "text": f"*Linked Victims*:\n{victims_count}"
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*Claimed Loss*:\n{loss}"
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*AI Confidence*:\n`{confidence}`"
                        },
                        {
                            "type": "mrkdwn",
                            "text": "*Status*:\n🤖 `UNVERIFIED LEAD`"
                        }
                    ]
                },
                {
                    "type": "actions",
                    "elements": [
                        {
                            "type": "button",
                            "text": {
                                "type": "plain_text",
                                "text": "Open Graph 🔍"
                            },
                            "style": "primary",
                            "value": f"open_graph_{case_id}"
                        },
                        {
                            "type": "button",
                            "text": {
                                "type": "plain_text",
                                "text": "Verify Lead ✅"
                            },
                            "value": f"verify_lead_{account}"
                        },
                        {
                            "type": "button",
                            "text": {
                                "type": "plain_text",
                                "text": "Assign Investigator 👮"
                            },
                            "value": f"assign_{case_id}"
                        },
                        {
                            "type": "button",
                            "text": {
                                "type": "plain_text",
                                "text": "Dismiss ❌"
                            },
                            "style": "danger",
                            "value": f"dismiss_{account}"
                        }
                    ]
                }
            ]
        }

    @staticmethod
    def build_approval_request(case_id: str, requester: str, details: str) -> Dict[str, Any]:
        """
        Constructs a Slack message block for Supervisor/Commander approvals.
        """
        return {
            "blocks": [
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": "📋 SUPERVISOR APPROVAL REQUEST",
                        "emoji": True
                    }
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*Case Reference*: `{case_id}`\n*Requester*: `{requester}`\n*Action Details*: {details}"
                    }
                },
                {
                    "type": "actions",
                    "elements": [
                        {
                            "type": "button",
                            "text": {
                                "type": "plain_text",
                                "text": "Approve ✅"
                            },
                            "style": "primary",
                            "value": f"approve_{case_id}"
                        },
                        {
                            "type": "button",
                            "text": {
                                "type": "plain_text",
                                "text": "Reject ❌"
                            },
                            "style": "danger",
                            "value": f"reject_{case_id}"
                        }
                    ]
                }
            ]
        }

    @staticmethod
    def build_case_detail_blocks(c: Dict[str, Any]) -> Dict[str, Any]:
        """
        Formats case details into rich Slack blocks.
        """
        case = c.get("case", {})
        victims = c.get("victims", [])
        evidence = c.get("evidence", [])
        tasks = c.get("tasks", [])
        
        victim_names = ", ".join([v.get("full_name", "") for v in victims]) or "None"
        evidence_titles = ", ".join([e.get("title", "") for e in evidence]) or "None"
        task_titles = ", ".join([t.get("title", "") for t in tasks]) or "None"
        
        return {
            "blocks": [
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": f"👮 CPPD OS: Case {case.get('id')}",
                        "emoji": True
                    }
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*Title*: *{case.get('title')}*\n*Status*: `{case.get('status')}`\n*Owning Unit*: {case.get('owning_unit')}\n*Description*: {case.get('description')}"
                    }
                },
                {
                    "type": "section",
                    "fields": [
                        {
                            "type": "mrkdwn",
                            "text": f"*Victims*:\n{victim_names}"
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*Evidence*:\n{evidence_titles}"
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*Active Tasks*:\n{task_titles}"
                        }
                    ]
                }
            ]
        }

    @staticmethod
    def build_entity_search_blocks(query: str, entities: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Formats entity query search results into rich Slack blocks.
        """
        entity_rows = []
        for e in entities:
            entity_rows.append(f"• *{e.get('name')}* (`{e.get('type')}`)")
        
        entities_text = "\n".join(entity_rows) or "No entities matched."
        
        return {
            "blocks": [
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": f"🧩 CPPD OS: Entity Search Results",
                        "emoji": True
                    }
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*Query*: `{query}`\n\n*Matched Knowledge Graph Nodes*:\n{entities_text}"
                    }
                }
            ]
        }
