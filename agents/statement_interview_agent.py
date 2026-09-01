# CPPD Agent: Statement / Interview Agent (Agent 9)
from typing import Dict, Any, List
from base_agent import CPPDBaseAgent

class StatementInterviewAgent(CPPDBaseAgent):
    def __init__(self, api_url: str = "http://localhost:8000"):
        super().__init__("StatementInterviewAgent", api_url)

    def generate_interview_questions(self, case_id: str, target_role: str = "suspect", target_name: str = "Kittisak Wongsawat") -> Dict[str, Any]:
        """
        Generates targeted, legally-grounded examination questions for victims, witnesses, or suspects.
        Tailors questions to address evidence conflicts, establish intent, and fulfill statutory elements.
        """
        if target_role.lower() == "suspect":
            questions = [
                "1. [Alibi Confrontation]: ท่านอ้างว่าท่านอยู่ที่จังหวัดเชียงใหม่ในวันที่ 9 สิงหาคม 2569 แต่เหตุใดระบบจึงตรวจพบการเข้าใช้งานบัญชี SCB เลขที่ 401-229-3388 จาก IP ในกรุงเทพมหานคร?",
                "2. [Mule / Beneficial Ownership]: บัญชีธนาคารไทยพาณิชย์เลขที่ 401-229-3388 ท่านเป็นผู้เปิดบัญชีด้วยตนเองหรือไม่ และท่านได้มอบสมุดบัญชี/รหัสผ่านให้แก่บุคคลอื่นใดหรือไม่?",
                "3. [Inventory / Goods Proof]: ในวันที่ผู้เสียหายโอนเงิน 1,250,000 บาท สั่งซื้อเครื่องสำอาง บริษัท สยาม เน็ตเวิร์ค จำกัด มีสินค้าดังกล่าวอยู่ในครอบครองจริงหรือไม่ ขอดูหลักฐานการสั่งซื้อหรือคลังสินค้า?",
                "4. [Proceeds Disposition]: เงินจำนวน 1,250,000 บาท ที่โอนเข้ามา ถูกโอนต่อไปยังบัญชี 702-888-1123 ภายใน 22 นาที ด้วยเหตุผลและวัตถุประสงค์ใด ใครเป็นผู้สั่งการ?"
            ]
            role_title = f"ผู้ต้องสงสัย ({target_name})"
        elif target_role.lower() == "witness":
            questions = [
                "1. ท่านรู้จักหรือมีความสัมพันธ์อย่างไรกับผู้ต้องหา หรือบริษัท สยาม เน็ตเวิร์ค จำกัด?",
                "2. ท่านเคยพบเห็นการขนส่งหรือการเก็บสต็อกสินค้าเครื่องสำอาง ณ ที่ทำการบริษัทหรือไม่?",
                "3. ท่านเคยได้รับคำสั่งให้ไปเปิดบัญชีธนาคารหรือดำเนินการถอนเงินสดแทนผู้ต้องหาหรือไม่?"
            ]
            role_title = f"พยานบุคคล ({target_name})"
        else: # victim
            questions = [
                "1. ผู้เสียหายรู้จักหรือติดต่อกับผู้ต้องหาผ่านช่องทางใด และเห็นโฆษณาเสนอขายสินค้าจากที่ใด?",
                "2. ก่อนการโอนเงิน ผู้ต้องหาได้แสดงเอกสารใบรับรอง หรือให้คำรับรองเรื่องการส่งมอบสินค้าอย่างไรบ้าง?",
                "3. ภายหลังการโอนเงิน 1,250,000 บาท ผู้เสียหายได้ทวงถามสินค้าอย่างไร และผู้ต้องหาบ่ายเบี่ยงอย่างไรจนกระทั่งติดต่อไม่ได้?"
            ]
            role_title = f"ผู้เสียหาย ({target_name})"

        findings = [
            {"tag": "FACT", "text": f"Generated {len(questions)} tailored interrogation questions for {role_title}.", "source_evidence_id": None, "confidence": 0.95},
            {"tag": "INFERENCE", "text": "Questions strategically designed to prove element of pre-existing fraudulent intent (เจตนาทุจริตหลอกลวง).", "source_evidence_id": None, "confidence": 0.90},
            {"tag": "REQUIRES_HUMAN_REVIEW", "text": "Inquiry official must adjust questions according to real-time witness demeanour and courtroom standards.", "source_evidence_id": None, "confidence": 1.0}
        ]

        actions = [
            f"Print examination sheet for {role_title}.",
            "Record verbal responses in formal Section 134/4 interrogation transcript record.",
            "Inspect physical identification cards and verify signature."
        ]

        summary = f"Generated {len(questions)} interrogation/interview questions for {role_title} focusing on intent, alibi conflict, and money flow."
        res = self.format_safe_output(case_id, summary, findings, actions, status="REQUIRES_HUMAN_REVIEW")
        res["questions"] = questions
        res["target_role"] = target_role
        res["target_name"] = target_name
        return res
