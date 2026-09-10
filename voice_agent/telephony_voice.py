"""
Telephony Voice Service & Emergency Clinical Triage Engine.

Supports Twilio Voice (TwiML XML) and Telnyx Voice (Call Control API),
enforcing DOC-AA-01 clinical safety boundaries and sub-second intent handling.
"""

import re
import json
import time
import sqlite3
from enum import Enum
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any


class TriageLevel(str, Enum):
    ROUTINE = "ROUTINE"
    URGENT = "URGENT"
    EMERGENCY = "EMERGENCY"


class CallIntent(str, Enum):
    GREETING = "GREETING"
    EMERGENCY = "EMERGENCY"
    CANCEL_APPOINTMENT = "CANCEL_APPOINTMENT"
    BOOK_CONSULTATION = "BOOK_CONSULTATION"
    PRACTICE_FAQ = "PRACTICE_FAQ"
    SPEAK_TO_STAFF = "SPEAK_TO_STAFF"
    UNKNOWN = "UNKNOWN"


@dataclass
class EmergencyTriageResult:
    is_emergency: bool
    triage_level: TriageLevel
    matched_red_flags: List[str]
    safety_message: str
    action: str  # "DISPATCH_911", "ESCALATE_ON_CALL", "CONTINUE"


@dataclass
class VoiceCallSession:
    call_sid: str
    caller_phone: str
    practice_id: str
    practice_name: str
    start_time: float = field(default_factory=time.time)
    intent: CallIntent = CallIntent.GREETING
    transcript_history: List[str] = field(default_factory=list)
    extracted_entities: Dict[str, Any] = field(default_factory=dict)
    is_completed: bool = False


class ClinicalSafetyTriager:
    """
    DOC-AA-01 Enforcer: Evaluates caller utterance for acute medical, dental,
    or aesthetic surgical emergencies. Never provides diagnostic assertions.
    """

    # Red-flag symptom patterns
    EMERGENCY_PATTERNS = {
        "uncontrolled_bleeding": r"\b(bleeding heavily|can't stop bleeding|hemorrhag|mouth full of blood|blood won't stop|gushing)\b",
        "airway_compromise": r"\b(can't breathe|trouble breathing|swallowing|throat closing|choking|airway)\b",
        "acute_infection_swelling": r"\b(swelling to eye|swollen shut|eye closed|neck swelling|fever.*10[2-5]|severe infection)\b",
        "vascular_occlusion": r"\b(skin turned white|blanching|gray skin|black spot|severe pain after filler|lost vision|blurry vision after injection)\b",
        "systemic_crisis": r"\b(chest pain|heart attack|stroke|passed out|unconscious|anaphylaxis|epipen)\b",
        "severe_trauma": r"\b(knocked out tooth|broken jaw|fractured face|severe facial trauma)\b"
    }

    URGENT_PATTERNS = {
        "moderate_pain": r"\b(throbbing|toothache|filling fell out|lost crown|moderate swelling|sore)\b",
        "medication_question": r"\b(antibiotic|prescription refill|tylenol|ibuprofen|narcotic)\b"
    }

    @classmethod
    def evaluate(cls, speech_text: str) -> EmergencyTriageResult:
        lowered = speech_text.lower()
        matched_flags = []

        for category, pattern in cls.EMERGENCY_PATTERNS.items():
            if re.search(pattern, lowered):
                matched_flags.append(category)

        if matched_flags:
            msg = (
                "Warning: If you are experiencing heavy bleeding, difficulty breathing, "
                "acute vision changes, or severe facial swelling, please hang up and call 911 "
                "immediately or proceed to the nearest emergency room. Our on-call clinical team "
                "has also been alerted."
            )
            return EmergencyTriageResult(
                is_emergency=True,
                triage_level=TriageLevel.EMERGENCY,
                matched_red_flags=matched_flags,
                safety_message=msg,
                action="DISPATCH_911"
            )

        for category, pattern in cls.URGENT_PATTERNS.items():
            if re.search(pattern, lowered):
                matched_flags.append(category)

        if matched_flags:
            msg = (
                "Thank you for letting us know. For urgent tooth pain or prescription questions, "
                "our clinical director reviews all messages at 7:00 AM. Let me record your details."
            )
            return EmergencyTriageResult(
                is_emergency=False,
                triage_level=TriageLevel.URGENT,
                matched_red_flags=matched_flags,
                safety_message=msg,
                action="ESCALATE_ON_CALL"
            )

        return EmergencyTriageResult(
            is_emergency=False,
            triage_level=TriageLevel.ROUTINE,
            matched_red_flags=[],
            safety_message="",
            action="CONTINUE"
        )


class VoiceAgentEngine:
    """
    Core conversational voice intake engine handling telephony hooks,
    cancellation processing, FAQ routing, and ambient appointment staging.
    """

    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path or ":memory:"
        self.active_sessions: Dict[str, VoiceCallSession] = {}
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self._init_db()

    def _init_db(self):
        cursor = self.conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS voice_call_logs (
                call_sid TEXT PRIMARY KEY,
                caller_phone TEXT,
                practice_id TEXT,
                intent TEXT,
                triage_level TEXT,
                transcript TEXT,
                entities_json TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS agent_staged_notes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                call_sid TEXT,
                caller_phone TEXT,
                patient_name TEXT,
                procedure_requested TEXT,
                preferred_window TEXT,
                notes TEXT,
                status TEXT DEFAULT 'PENDING_STAFF_REVIEW',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS appointment_cancellations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                call_sid TEXT,
                caller_phone TEXT,
                patient_name TEXT,
                appointment_date TEXT,
                procedure_type TEXT,
                reason TEXT,
                waitlist_triggered INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        self.conn.commit()

    def start_call(self, call_sid: str, caller_phone: str, practice_id: str, practice_name: str) -> str:
        """Initializes call session and returns greeting TwiML XML."""
        session = VoiceCallSession(
            call_sid=call_sid,
            caller_phone=caller_phone,
            practice_id=practice_id,
            practice_name=practice_name
        )
        self.active_sessions[call_sid] = session

        twiml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Gather input="speech dtmf" timeout="4" action="/voice/twilio/gather?call_sid={call_sid}" method="POST">
        <Say voice="Polly.Joanna-Neural">
            Thank you for calling {practice_name} after-hours concierge. 
            If this is a life-threatening medical emergency, please hang up and call 911 immediately. 
            Otherwise, you can say 'cancel an appointment', 'book a consultation', or ask a question about our procedures. 
            How may I assist you this evening?
        </Say>
    </Gather>
    <Say voice="Polly.Joanna-Neural">We did not receive any input. Please call back during normal business hours. Goodbye.</Say>
    <Hangup/>
</Response>"""
        return twiml.strip()

    def process_utterance(self, call_sid: str, speech_result: str) -> Tuple[CallIntent, str, str]:
        """
        Processes caller speech transcript, runs clinical safety triage,
        classifies intent, logs data, and returns (intent, spoken_response, twiml_xml).
        """
        session = self.active_sessions.get(call_sid)
        practice_name = session.practice_name if session else "our practice"
        caller_phone = session.caller_phone if session else "Unknown"

        if session:
            session.transcript_history.append(speech_result)

        # 1. Evaluate DOC-AA-01 Emergency Clinical Safety
        triage = ClinicalSafetyTriager.evaluate(speech_result)
        if triage.is_emergency:
            if session:
                session.intent = CallIntent.EMERGENCY
            self._log_call(call_sid, caller_phone, session.practice_id if session else "PR-GEN",
                           CallIntent.EMERGENCY, triage.triage_level, speech_result, {"red_flags": triage.matched_red_flags})
            
            twiml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="Polly.Joanna-Neural">
        {triage.safety_message}
    </Say>
    <Hangup/>
</Response>"""
            return CallIntent.EMERGENCY, triage.safety_message, twiml.strip()

        # 2. Intent Classification
        lowered = speech_result.lower()
        
        # Intent: Cancellation
        if any(w in lowered for w in ["cancel", "reschedule", "can't make it", "won't be able to come"]):
            intent = CallIntent.CANCEL_APPOINTMENT
            # Extract basic entities
            spoken = (
                f"I have registered your cancellation request for {practice_name}. "
                "Our front desk will confirm your release in the morning, and if you need to reschedule, "
                "you will receive a private booking link on your mobile phone. Have a wonderful evening."
            )
            self._stage_cancellation(call_sid, caller_phone, "Caller", "Next Available", "General Procedure", speech_result)
            twiml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="Polly.Joanna-Neural">{spoken}</Say>
    <Hangup/>
</Response>"""
            self._log_call(call_sid, caller_phone, session.practice_id if session else "PR-GEN",
                           intent, triage.triage_level, speech_result, {"raw_utterance": speech_result})
            return intent, spoken, twiml.strip()

        # Intent: Book Consultation
        elif any(w in lowered for w in ["book", "consultation", "appointment", "schedule", "morpheus", "botox", "filler", "implant", "cleaning"]):
            intent = CallIntent.BOOK_CONSULTATION
            spoken = (
                f"We would love to welcome you to {practice_name}. "
                "I have staged your consultation request for our patient coordinator. "
                "We will text a private, pixel-free scheduling link to this phone number at 8:00 AM tomorrow. "
                "Thank you for calling."
            )
            self._stage_consultation_note(call_sid, caller_phone, "New Patient", speech_result, "Morning Priority", speech_result)
            twiml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="Polly.Joanna-Neural">{spoken}</Say>
    <Hangup/>
</Response>"""
            self._log_call(call_sid, caller_phone, session.practice_id if session else "PR-GEN",
                           intent, triage.triage_level, speech_result, {"staged": True})
            return intent, spoken, twiml.strip()

        # Intent: Practice FAQ
        elif any(w in lowered for w in ["hours", "open", "address", "parking", "location", "cost", "price", "insurance"]):
            intent = CallIntent.PRACTICE_FAQ
            spoken = (
                f"{practice_name} is located downtown with validated parking available on-site. "
                "Our clinic hours are Monday through Friday, 8:00 AM to 5:00 PM. "
                "You can also explore our complete service menu and pricing securely on our website. "
                "Is there anything else I can assist you with?"
            )
            twiml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Gather input="speech dtmf" timeout="4" action="/voice/twilio/gather?call_sid={call_sid}" method="POST">
        <Say voice="Polly.Joanna-Neural">{spoken}</Say>
    </Gather>
    <Say voice="Polly.Joanna-Neural">Thank you for calling. Have a great night.</Say>
    <Hangup/>
</Response>"""
            self._log_call(call_sid, caller_phone, session.practice_id if session else "PR-GEN",
                           intent, triage.triage_level, speech_result, {"faq_category": "general"})
            return intent, spoken, twiml.strip()

        # Intent: Default / Speak to Staff
        else:
            intent = CallIntent.SPEAK_TO_STAFF
            spoken = (
                f"Thank you for your message. I have recorded your inquiry for {practice_name}'s "
                "reception team, who will return your call promptly at 8:00 AM when the office opens."
            )
            self._stage_consultation_note(call_sid, caller_phone, "Inquiry", "General Voice Message", "Next Business Day", speech_result)
            twiml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="Polly.Joanna-Neural">{spoken}</Say>
    <Hangup/>
</Response>"""
            self._log_call(call_sid, caller_phone, session.practice_id if session else "PR-GEN",
                           intent, triage.triage_level, speech_result, {"generic": True})
            return intent, spoken, twiml.strip()

    def _stage_cancellation(self, call_sid: str, phone: str, name: str, appt_date: str, procedure: str, reason: str):
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO appointment_cancellations 
            (call_sid, caller_phone, patient_name, appointment_date, procedure_type, reason, waitlist_triggered)
            VALUES (?, ?, ?, ?, ?, ?, 1)
        """, (call_sid, phone, name, appt_date, procedure, reason))
        self.conn.commit()

    def _stage_consultation_note(self, call_sid: str, phone: str, name: str, procedure: str, window: str, notes: str):
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO agent_staged_notes
            (call_sid, caller_phone, patient_name, procedure_requested, preferred_window, notes, status)
            VALUES (?, ?, ?, ?, ?, ?, 'PENDING_STAFF_REVIEW')
        """, (call_sid, phone, name, procedure, window, notes))
        self.conn.commit()

    def _log_call(self, call_sid: str, phone: str, practice_id: str, intent: CallIntent,
                  triage: TriageLevel, transcript: str, entities: Dict[str, Any]):
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO voice_call_logs 
            (call_sid, caller_phone, practice_id, intent, triage_level, transcript, entities_json)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (call_sid, phone, practice_id, intent.value, triage.value, transcript, json.dumps(entities)))
        self.conn.commit()


def create_voice_app(engine: Optional[VoiceAgentEngine] = None):
    """
    Creates a FastAPI ASGI application serving Twilio Voice and Telnyx webhooks.
    """
    try:
        from fastapi import FastAPI, Request, Response
        from fastapi.responses import PlainTextResponse, JSONResponse
    except ImportError:
        # Fallback dummy if fastapi is not installed in the environment
        return None

    engine = engine or VoiceAgentEngine()
    app = FastAPI(title="Lane 3 Voice Intake Agent", version="1.0.0")

    @app.post("/voice/twilio/inbound", response_class=PlainTextResponse)
    async def twilio_inbound(request: Request):
        form_data = await request.form()
        call_sid = form_data.get("CallSid", f"CA_{int(time.time()*1000)}")
        caller = form_data.get("From", "Unknown")
        practice_id = form_data.get("PracticeId", "PR-001")
        practice_name = form_data.get("PracticeName", "Bellevue Aesthetic Medicine")
        twiml = engine.start_call(call_sid, caller, practice_id, practice_name)
        return Response(content=twiml, media_type="application/xml")

    @app.post("/voice/twilio/gather", response_class=PlainTextResponse)
    async def twilio_gather(request: Request):
        form_data = await request.form()
        call_sid = request.query_params.get("call_sid") or form_data.get("CallSid", "CA_UNKNOWN")
        speech_result = form_data.get("SpeechResult") or form_data.get("Digits") or ""
        intent, spoken, twiml = engine.process_utterance(call_sid, speech_result)
        return Response(content=twiml, media_type="application/xml")

    @app.post("/voice/telnyx/inbound")
    async def telnyx_inbound(request: Request):
        body = await request.json()
        call_control_id = body.get("data", {}).get("payload", {}).get("call_control_id", "")
        # Telnyx speak command response
        return JSONResponse(content={
            "action": "speak",
            "call_control_id": call_control_id,
            "payload": "Thank you for calling after-hours. Please speak your request after the tone."
        })

    return app
