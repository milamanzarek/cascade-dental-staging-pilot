"""
Vercel Serverless Function Handler (FastAPI) for Cascade Dental Arts.
Uses /tmp/cascade_dental.db for serverless persistence.
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
import sqlite3
import os
import random
from datetime import datetime, timedelta

app = FastAPI(title="Cascade Dental Arts - Vercel Serverless Staging API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DB_FILE = "/tmp/cascade_dental.db"

def get_connection():
    conn = sqlite3.connect(DB_FILE, timeout=10.0)
    conn.row_factory = sqlite3.Row
    return conn

def init_db_if_needed():
    if not os.path.exists(DB_FILE):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.executescript("""
        CREATE TABLE IF NOT EXISTS appointment (
            AptNum INTEGER PRIMARY KEY,
            PatNum INTEGER NOT NULL,
            AptDateTime TEXT NOT NULL,
            Op INTEGER NOT NULL,
            ProvNum INTEGER NOT NULL,
            AptStatus INTEGER NOT NULL,
            Pattern TEXT,
            Note TEXT,
            IsHygiene INTEGER DEFAULT 0,
            Confirmed INTEGER DEFAULT 0
        );

        CREATE TABLE IF NOT EXISTS patient (
            PatNum INTEGER PRIMARY KEY,
            LName TEXT NOT NULL,
            FName TEXT NOT NULL,
            WirelessPhone TEXT NOT NULL UNIQUE,
            PreferSMS INTEGER DEFAULT 1,
            Email TEXT
        );

        CREATE TABLE IF NOT EXISTS recall (
            RecallNum INTEGER PRIMARY KEY,
            PatNum INTEGER NOT NULL,
            DateDueCalc TEXT NOT NULL,
            Note TEXT
        );

        CREATE TABLE IF NOT EXISTS operatory (
            OperatoryNum INTEGER PRIMARY KEY,
            OpName TEXT NOT NULL,
            IsHygiene INTEGER DEFAULT 0
        );

        CREATE TABLE IF NOT EXISTS waitlist_offers (
            OfferId INTEGER PRIMARY KEY AUTOINCREMENT,
            AptNum INTEGER NOT NULL,
            PatNum INTEGER NOT NULL,
            Phone TEXT NOT NULL,
            SentTimestamp TEXT NOT NULL,
            Status TEXT DEFAULT 'PENDING'
        );

        CREATE TABLE IF NOT EXISTS agent_staged_notes (
            StagedNoteNum INTEGER PRIMARY KEY AUTOINCREMENT,
            AptNum INTEGER NOT NULL,
            SOAPContent TEXT NOT NULL,
            SystemicAlerts TEXT,
            Status TEXT DEFAULT 'PENDING_REVIEW'
        );

        CREATE TABLE IF NOT EXISTS custom_agent_log (
            LogNum INTEGER PRIMARY KEY AUTOINCREMENT,
            AptNum INTEGER,
            ActionType TEXT NOT NULL,
            Details TEXT NOT NULL,
            Timestamp TEXT NOT NULL
        );
        """)

        # Operatories
        ops = [
            (1, "Hygiene 1 (East)", 1),
            (2, "Hygiene 2 (West)", 1),
            (3, "Op 1 (Restorative)", 0),
            (4, "Op 2 (Restorative)", 0),
            (5, "Op 3 (Surgical/Implants)", 0),
            (6, "Op 4 (Endodontics)", 0),
        ]
        cursor.executemany("INSERT OR IGNORE INTO operatory VALUES (?, ?, ?)", ops)

        # Patients
        patients = [
            (101, "Vance", "Marcus", "+14255550201", 1, "marcus.vance@example.com"),
            (102, "Anderson", "Henry", "+14255550203", 1, "henry.anderson@example.com"),
            (103, "Kovacs", "Amelia", "+14255550220", 1, "amelia.kovacs@example.com"),
            (108, "Wright", "William", "+14255550209", 1, "william.wright@example.com"),
            (113, "Davis", "Jessica", "+14255550214", 1, "jessica.davis@example.com"),
            (121, "Clark", "Jessica", "+14255550222", 1, "jessica.clark@example.com"),
            (122, "Chen", "Daniel", "+14255550223", 1, "daniel.chen@example.com"),
        ]
        cursor.executemany("INSERT OR IGNORE INTO patient VALUES (?, ?, ?, ?, ?, ?)", patients)

        # Recalls
        recalls = [
            (1, 102, "2026-06-18", "Overdue by 83 days"),
            (2, 113, "2026-06-22", "Overdue by 79 days"),
            (3, 108, "2026-06-23", "Overdue by 78 days"),
            (4, 121, "2026-06-24", "Overdue by 77 days"),
            (5, 122, "2026-06-28", "Overdue by 73 days"),
        ]
        cursor.executemany("INSERT OR IGNORE INTO recall VALUES (?, ?, ?, ?)", recalls)

        # Appointments
        tomorrow = (datetime.utcnow() + timedelta(days=1)).strftime("%Y-%m-%d")
        hours = ["08:00:00", "09:00:00", "11:00:00", "13:00:00", "14:00:00", "15:00:00"]
        apts = []
        aid = 1
        for op_id in range(1, 7):
            is_hyg = 1 if op_id in [1, 2] else 0
            for h in hours:
                apts.append((aid, 101, f"{tomorrow} {h}", op_id, 1, 1, "/XXXXXXXXXX/", "Routine appointment", is_hyg, 1))
                aid += 1
        cursor.executemany("INSERT OR IGNORE INTO appointment VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", apts)

        # Initial Staged Note
        cursor.execute("""
        INSERT INTO agent_staged_notes (AptNum, SOAPContent, SystemicAlerts, Status)
        VALUES (1, 'SUBJECTIVE: Tooth #19 cold sensitivity. Prescribed Eliquis 5mg BID.\nOBJECTIVE: Pocket depths 5-4-5mm.\nPLAN: Root planing & crown.', 'HIGH BLEEDING RISK: Anticoagulant therapy (Eliquis). Bleeding precaution for root planing.', 'PENDING_REVIEW')
        """)

        conn.commit()
        conn.close()

@app.get("/api/dashboard-data")
def dashboard_data():
    init_db_if_needed()
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM operatory ORDER BY OperatoryNum ASC")
    ops = [dict(r) for r in cursor.fetchall()]

    cursor.execute("""
    SELECT a.*, p.FName, p.LName, p.WirelessPhone
    FROM appointment a
    LEFT JOIN patient p ON a.PatNum = p.PatNum
    ORDER BY a.AptDateTime ASC
    """)
    apts = [dict(r) for r in cursor.fetchall()]

    cursor.execute("""
    SELECT o.*, p.FName, p.LName
    FROM waitlist_offers o JOIN patient p ON o.PatNum = p.PatNum
    ORDER BY o.OfferId DESC LIMIT 15
    """)
    offers = [dict(r) for r in cursor.fetchall()]

    cursor.execute("SELECT * FROM agent_staged_notes ORDER BY StagedNoteNum DESC LIMIT 5")
    notes = [dict(r) for r in cursor.fetchall()]

    cursor.execute("SELECT * FROM custom_agent_log ORDER BY LogNum DESC LIMIT 15")
    logs = [dict(r) for r in cursor.fetchall()]

    conn.close()
    return {
        "practice": "Cascade Dental Arts (Vercel Serverless)",
        "operatories": ops,
        "appointments": apts,
        "offers": offers,
        "notes": notes,
        "logs": logs
    }

@app.post("/api/simulate/cancel-appointment")
def cancel_appointment(apt_num: Optional[int] = None):
    init_db_if_needed()
    conn = get_connection()
    cursor = conn.cursor()

    if not apt_num:
        cursor.execute("SELECT AptNum FROM appointment WHERE AptStatus = 1 AND Op = 1 ORDER BY AptNum ASC LIMIT 1")
        row = cursor.fetchone()
        if not row:
            cursor.execute("SELECT AptNum FROM appointment WHERE AptStatus = 1 ORDER BY AptNum ASC LIMIT 1")
            row = cursor.fetchone()
        if row:
            apt_num = row["AptNum"]
        else:
            conn.close()
            return {"status": "NO_APPOINTMENTS", "message": "All appointments already cancelled!"}

    cursor.execute("UPDATE appointment SET AptStatus = 5, Note = coalesce(Note,'') || ' [Simulated Cancellation]' WHERE AptNum = ?", (apt_num,))
    cursor.execute("DELETE FROM waitlist_offers WHERE AptNum = ?", (apt_num,))
    
    # Get top recall candidates
    cursor.execute("""
    SELECT p.PatNum, p.FName, p.LName, p.WirelessPhone 
    FROM recall r JOIN patient p ON r.PatNum = p.PatNum 
    WHERE p.PreferSMS = 1 ORDER BY r.DateDueCalc ASC LIMIT 3
    """)
    candidates = [dict(r) for r in cursor.fetchall()]

    dispatched = []
    for c in candidates:
        cursor.execute("""
        INSERT INTO waitlist_offers (AptNum, PatNum, Phone, SentTimestamp, Status)
        VALUES (?, ?, ?, ?, 'PENDING')
        """, (apt_num, c["PatNum"], c["WirelessPhone"], datetime.utcnow().isoformat()))
        dispatched.append({
            "name": f"{c['FName']} {c['LName']}",
            "phone": c["WirelessPhone"]
        })

    cursor.execute("""
    INSERT INTO custom_agent_log (AptNum, ActionType, Details, Timestamp)
    VALUES (?, 'AUTOFILL_DISPATCHED', ?, ?)
    """, (apt_num, f"Dispatched offers to {len(dispatched)} candidates", datetime.utcnow().isoformat()))

    conn.commit()
    conn.close()
    return {
        "status": "SUCCESS",
        "cancelled_apt": apt_num,
        "dispatched_count": len(dispatched),
        "candidates": dispatched
    }

class TwilioPayload(BaseModel):
    From: str
    Body: str

@app.post("/webhooks/twilio/inbound-sms")
def twilio_webhook(payload: TwilioPayload):
    init_db_if_needed()
    conn = get_connection()
    cursor = conn.cursor()

    phone = payload.From.strip()
    body = payload.Body.strip().upper()

    if "STOP" in body:
        cursor.execute("UPDATE patient SET PreferSMS = 0 WHERE WirelessPhone = ?", (phone,))
        conn.commit()
        conn.close()
        return {"status": "OPTED_OUT", "message": "Unsubscribed from Cascade Dental Arts alerts."}

    if "YES" in body:
        cursor.execute("""
        SELECT o.OfferId, o.AptNum, o.PatNum, o.Status, p.FName, p.LName, a.AptDateTime, a.AptStatus
        FROM waitlist_offers o
        JOIN patient p ON o.PatNum = p.PatNum
        JOIN appointment a ON o.AptNum = a.AptNum
        WHERE o.Phone = ? AND o.Status IN ('PENDING', 'EXPIRED')
        ORDER BY o.OfferId DESC LIMIT 1
        """, (phone,))
        offer = cursor.fetchone()

        if not offer:
            conn.close()
            return {"status": "NO_OFFER", "message": "No active waitlist opening registered for this number."}

        if offer["AptStatus"] != 5 or offer["Status"] == "EXPIRED":
            conn.close()
            return {
                "status": "ALREADY_CLAIMED",
                "claimed": False,
                "message": "Sorry, another patient just confirmed this appointment! We have saved your spot on our priority waitlist."
            }

        # Atomically claim
        cursor.execute("""
        UPDATE appointment SET PatNum = ?, AptStatus = 1, Confirmed = 19
        WHERE AptNum = ?
        """, (offer["PatNum"], offer["AptNum"]))

        cursor.execute("UPDATE waitlist_offers SET Status = 'CLAIMED' WHERE OfferId = ?", (offer["OfferId"],))
        cursor.execute("UPDATE waitlist_offers SET Status = 'EXPIRED' WHERE AptNum = ? AND OfferId != ?", (offer["AptNum"], offer["OfferId"]))

        cursor.execute("""
        INSERT INTO custom_agent_log (AptNum, ActionType, Details, Timestamp)
        VALUES (?, 'AUTOFILL_CLAIMED', ?, ?)
        """, (offer["AptNum"], f"Claimed by {offer['FName']} {offer['LName']}", datetime.utcnow().isoformat()))

        conn.commit()
        conn.close()
        return {
            "status": "SUCCESS",
            "claimed": True,
            "apt_num": offer["AptNum"],
            "patient_name": f"{offer['FName']} {offer['LName']}",
            "message": f"Confirmed! Your cleaning appointment is reserved for {offer['AptDateTime']}."
        }

    conn.close()
    return {"status": "INFO", "message": "Reply YES to claim or STOP to unsubscribe."}

@app.post("/api/simulate/doctor-approve")
def doctor_approve(staged_id: int):
    init_db_if_needed()
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE agent_staged_notes SET Status = 'APPROVED' WHERE StagedNoteNum = ?", (staged_id,))
    cursor.execute("""
    INSERT INTO custom_agent_log (AptNum, ActionType, Details, Timestamp)
    VALUES (1, 'NOTE_SIGNED', 'Doctor Sarah Chen reviewed contraindications and signed chart note', ?)
    """, (datetime.utcnow().isoformat(),))
    conn.commit()
    conn.close()
    return {"status": "SUCCESS", "staged_id": staged_id}
