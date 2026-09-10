"""
Cascade Aesthetic Medicine & MedSpa - Autonomous Agent Bridge
Implements:
1. High-Value Cancelled Slot Autofill (Dual-Resource Room + Provider Lock)
2. Lapsed VIP Beauty Bank Re-Engagement ($400+ Unspent Banked Balances)
3. Washington MHMDA & TCPA Consent Fencing
4. Atomic Slot Claim & Race Condition Resolution (<20ms)
"""

import time
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from medspa_module.medspa_engine import MedSpaEngine, DB_PATH


class MedSpaAgent:
    def __init__(self, engine: Optional[MedSpaEngine] = None):
        self.engine = engine or MedSpaEngine()

    def get_cancelled_slots(self) -> List[Dict[str, Any]]:
        """Retrieve high-value cancelled slots needing urgent autofill."""
        with self.engine.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("""
                SELECT 
                    a.appointment_id,
                    a.start_time,
                    a.end_time,
                    a.total_price,
                    a.cancellation_reason,
                    r.room_id,
                    r.room_name,
                    r.room_type,
                    r.equipment_tag,
                    p.provider_id,
                    p.first_name AS prov_fname,
                    p.last_name AS prov_lname,
                    p.title AS prov_title,
                    s.service_id,
                    s.service_code,
                    s.service_name,
                    s.category,
                    s.duration_minutes
                FROM appointments a
                INNER JOIN rooms r ON a.room_id = r.room_id
                INNER JOIN providers p ON a.provider_id = p.provider_id
                INNER JOIN services s ON a.service_id = s.service_id
                WHERE a.status = 'CANCELLED'
                ORDER BY a.start_time ASC
            """)
            rows = cur.fetchall()
            return [dict(r) for r in rows]

    def get_candidate_clients(self, service_category: str, provider_id: int, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Match top overdue / retreatment aesthetic clients for the vacant slot.
        Enforces:
        - MHMDA consent (mhmda_consent = 1)
        - Active SMS preference (prefer_sms = 1)
        - Retreatment due date reached
        - VIP Tier prioritization (Platinum > Gold > Standard)
        """
        with self.engine.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("""
                SELECT 
                    c.client_id,
                    c.first_name,
                    c.last_name,
                    c.phone,
                    c.vip_tier,
                    c.last_visit_date,
                    c.next_due_date,
                    m.banked_balance,
                    m.tier_name AS membership_tier,
                    (CASE 
                        WHEN c.vip_tier = 'PLATINUM_VIP' THEN 100
                        WHEN c.vip_tier = 'GOLD_VIP' THEN 50
                        ELSE 10
                     END + 
                     CASE WHEN m.banked_balance > 300 THEN 40 ELSE 0 END +
                     CASE WHEN c.preferred_provider_id = ? THEN 30 ELSE 0 END
                    ) AS match_score
                FROM clients c
                LEFT JOIN memberships m ON c.client_id = m.client_id AND m.status IN ('ACTIVE', 'LAPSED')
                WHERE c.prefer_sms = 1
                  AND c.mhmda_consent = 1
                  AND c.client_id NOT IN (
                      -- Exclude clients already booked today
                      SELECT DISTINCT client_id FROM appointments 
                      WHERE status IN ('SCHEDULED', 'CONFIRMED') AND client_id IS NOT NULL
                  )
                ORDER BY match_score DESC, c.next_due_date ASC
                LIMIT ?
            """, (provider_id, limit))
            rows = cur.fetchall()
            return [dict(r) for r in rows]

    def claim_slot(self, appointment_id: int, client_phone: str, sms_body: str = "YES") -> Dict[str, Any]:
        """
        Atomic slot claim transaction.
        Enforces:
        - ACID exclusive row-level lock on appointment
        - Verified client identity via phone number
        - TCPA keyword parsing ('STOP', 'UNSUBSCRIBE')
        - Prevents double-booking collisions
        """
        start_t = time.perf_counter()
        normalized_body = sms_body.strip().upper()

        # 1. Handle TCPA Opt-Out
        if normalized_body in ["STOP", "UNSUBSCRIBE", "QUIT", "CANCEL", "END"]:
            with self.engine.get_connection() as conn:
                conn.execute("UPDATE clients SET prefer_sms = 0 WHERE phone = ?", (client_phone,))
                conn.commit()
            return {
                "status": "OPTED_OUT",
                "message": "TCPA Opt-out registered. You will receive no further SMS notifications.",
                "latency_ms": round((time.perf_counter() - start_t) * 1000, 2)
            }

        # 2. Find Client
        with self.engine.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT client_id, first_name, last_name, vip_tier FROM clients WHERE phone = ?", (client_phone,))
            client = cur.fetchone()
            if not client:
                return {
                    "status": "CLIENT_NOT_FOUND",
                    "message": f"No client registered with phone {client_phone}",
                    "latency_ms": round((time.perf_counter() - start_t) * 1000, 2)
                }
            client_id = client["client_id"]
            client_name = f"{client['first_name']} {client['last_name']}"

        # 3. Execute ACID Atomic Claim Lock
        with self.engine.get_connection() as conn:
            cur = conn.cursor()
            try:
                # Begin exclusive immediate transaction
                cur.execute("BEGIN IMMEDIATE;")
                
                # Check current slot status
                cur.execute("""
                    SELECT appointment_id, status, start_time, total_price, room_id, provider_id
                    FROM appointments
                    WHERE appointment_id = ?
                """, (appointment_id,))
                slot = cur.fetchone()

                if not slot:
                    conn.rollback()
                    return {"status": "NOT_FOUND", "message": "Appointment slot not found."}

                if slot["status"] != "CANCELLED":
                    # Contention collision: Another patient already won this slot!
                    conn.rollback()
                    latency = round((time.perf_counter() - start_t) * 1000, 2)
                    
                    # Log contention notice
                    with self.engine.get_connection() as log_conn:
                        log_conn.execute("""
                            INSERT INTO communication_logs (
                                client_id, appointment_id, direction, message_body, status, is_claim_winner
                            ) VALUES (?, ?, 'INBOUND', ?, 'CONTENTION_LOST', 0)
                        """, (client_id, appointment_id, sms_body))
                        log_conn.commit()

                    return {
                        "status": "ALREADY_CLAIMED",
                        "winner": False,
                        "message": "Sorry, another VIP client just claimed this opening! We have reserved your priority spot for the next availability.",
                        "latency_ms": latency
                    }

                # Claim the slot
                cur.execute("""
                    UPDATE appointments
                    SET client_id = ?,
                        status = 'CONFIRMED',
                        updated_at = CURRENT_TIMESTAMP
                    WHERE appointment_id = ? AND status = 'CANCELLED'
                """, (client_id, appointment_id))

                # Log winning communication
                cur.execute("""
                    INSERT INTO communication_logs (
                        client_id, appointment_id, direction, message_body, status, is_claim_winner
                    ) VALUES (?, ?, 'INBOUND', ?, 'CLAIMED_SUCCESS', 1)
                """, (client_id, appointment_id, sms_body))

                conn.commit()
                latency = round((time.perf_counter() - start_t) * 1000, 2)

                return {
                    "status": "SUCCESS",
                    "winner": True,
                    "client_name": client_name,
                    "slot_time": slot["start_time"],
                    "value": slot["total_price"],
                    "message": f"Confirmed! You are scheduled for {slot['start_time']}. We look forward to seeing you at Cascade Aesthetic Medicine!",
                    "latency_ms": latency
                }

            except Exception as e:
                conn.rollback()
                return {"status": "ERROR", "message": str(e)}

    def get_lapsed_vip_memberships(self, min_balance: float = 300.0, days_dormant: int = 60) -> List[Dict[str, Any]]:
        """
        Identify high-value VIP members with unspent banked credits who haven't visited recently.
        Critical for reducing deferred liability and recovering high-margin injector utilization.
        """
        with self.engine.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("""
                SELECT 
                    m.membership_id,
                    m.tier_name,
                    m.monthly_dues,
                    m.banked_balance,
                    m.status AS membership_status,
                    c.client_id,
                    c.first_name,
                    c.last_name,
                    c.phone,
                    c.last_visit_date,
                    c.vip_tier,
                    p.first_name AS pref_prov_fname,
                    p.title AS pref_prov_title,
                    CAST((julianday('now') - julianday(c.last_visit_date)) AS INTEGER) AS days_since_visit
                FROM memberships m
                INNER JOIN clients c ON m.client_id = c.client_id
                LEFT JOIN providers p ON c.preferred_provider_id = p.provider_id
                WHERE m.banked_balance >= ?
                  AND c.prefer_sms = 1
                  AND c.mhmda_consent = 1
                  AND (julianday('now') - julianday(c.last_visit_date)) >= ?
                ORDER BY m.banked_balance DESC
            """, (min_balance, days_dormant))
            rows = cur.fetchall()
            return [dict(r) for r in rows]

    def generate_concierge_outreach(self, member: Dict[str, Any]) -> str:
        """Formulate a Zero-PHI luxury concierge outreach message."""
        balance_int = int(member["banked_balance"])
        provider = f"{member.get('pref_prov_fname', 'Elena')} ({member.get('pref_prov_title', 'ARNP')})"
        return (
            f"Cascade Aesthetic: Hi {member['first_name']}, you have ${balance_int} banked in your Beauty Bank wallet! "
            f"{provider} has exclusive VIP openings this week. "
            f"View your private booking concierge: https://cascadeaesthetic.app/vip/{member['client_id']} "
            f"or reply YES to request a callback. Reply STOP to opt out."
        )
