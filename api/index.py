"""
Vercel Serverless Function Handler (FastAPI) for:
1. Cascade Dental Arts (Dental Practice PMS)
2. Cascade Aesthetic Medicine & MedSpa (Aesthetic / MedSpa PMS)
Uses /tmp/ for serverless persistence.
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import sqlite3
import os
import random
from datetime import datetime, timedelta

app = FastAPI(title="Cascade Healthcare AI - Dual Practice Staging API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DENTAL_DB = "/tmp/cascade_dental.db"
MEDSPA_DB = "/tmp/cascade_medspa.db"

# ==============================================================================
# DENTAL MODULE HELPERS
# ==============================================================================
def get_dental_conn():
    conn = sqlite3.connect(DENTAL_DB, timeout=10.0)
    conn.row_factory = sqlite3.Row
    return conn

def init_dental_db():
    if not os.path.exists(DENTAL_DB):
        conn = get_dental_conn()
        cur = conn.cursor()
        cur.executescript("""
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

        ops = [
            (1, "Hygiene 1 (East)", 1),
            (2, "Hygiene 2 (West)", 1),
            (3, "Hygiene 3 (Pediatric)", 1),
            (4, "Doctor 1 (Restorative)", 0),
            (5, "Doctor 2 (Surgical/Implant)", 0),
            (6, "Doctor 3 (Endodontics)", 0)
        ]
        cur.executemany("INSERT INTO operatory VALUES (?, ?, ?)", ops)

        patients = [
            (101, "Miller", "Sarah", "+14255550201", 1, "smiller@email.com"),
            (102, "Anderson", "Henry", "+14255550203", 1, "handerson@email.com"),
            (103, "Kovacs", "Amelia", "+14255550220", 1, "akovacs@email.com"),
            (104, "Chen", "David", "+14255550205", 1, "dchen@email.com"),
            (105, "Davis", "Jessica", "+14255550214", 1, "jdavis@email.com"),
            (106, "Wright", "William", "+14255550209", 1, "wwright@email.com")
        ]
        cur.executemany("INSERT INTO patient VALUES (?, ?, ?, ?, ?, ?)", patients)

        today_str = datetime.now().strftime("%Y-%m-%d")
        appts = [
            (36, 101, f"{today_str} 09:00:00", 1, 3, 1, "//XXXX//", "Prophy & Exam", 1, 1),
            (37, 102, f"{today_str} 10:00:00", 1, 3, 1, "//XXXX//", "Perio Maintenance", 1, 1),
            (38, 104, f"{today_str} 11:00:00", 1, 3, 1, "//XXXX//", "Adult Prophy", 1, 1),
            (45, 105, f"{today_str} 09:30:00", 4, 1, 1, "///XXXX///", "Crown Prep #19", 0, 1),
            (46, 106, f"{today_str} 11:00:00", 4, 1, 1, "//XXXX//", "Composite #14-MOD", 0, 1)
        ]
        cur.executemany("INSERT INTO appointment VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", appts)
        conn.commit()

# ==============================================================================
# MED SPA MODULE HELPERS
# ==============================================================================
def get_medspa_conn():
    conn = sqlite3.connect(MEDSPA_DB, timeout=10.0)
    conn.row_factory = sqlite3.Row
    return conn

def init_medspa_db():
    if not os.path.exists(MEDSPA_DB):
        conn = get_medspa_conn()
        cur = conn.cursor()
        cur.executescript("""
        CREATE TABLE IF NOT EXISTS rooms (
            room_id INTEGER PRIMARY KEY,
            room_name TEXT NOT NULL,
            room_type TEXT NOT NULL,
            equipment_tag TEXT
        );

        CREATE TABLE IF NOT EXISTS providers (
            provider_id INTEGER PRIMARY KEY,
            first_name TEXT NOT NULL,
            last_name TEXT NOT NULL,
            title TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS clients (
            client_id INTEGER PRIMARY KEY,
            first_name TEXT NOT NULL,
            last_name TEXT NOT NULL,
            phone TEXT NOT NULL UNIQUE,
            vip_tier TEXT DEFAULT 'STANDARD',
            banked_balance REAL DEFAULT 0.0,
            prefer_sms INTEGER DEFAULT 1,
            mhmda_consent INTEGER DEFAULT 1
        );

        CREATE TABLE IF NOT EXISTS appointments (
            appointment_id INTEGER PRIMARY KEY,
            client_id INTEGER,
            provider_id INTEGER NOT NULL,
            room_id INTEGER NOT NULL,
            service_name TEXT NOT NULL,
            start_time TEXT NOT NULL,
            end_time TEXT NOT NULL,
            status TEXT NOT NULL,
            total_price REAL NOT NULL,
            cancellation_reason TEXT
        );

        CREATE TABLE IF NOT EXISTS comm_logs (
            log_id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_id INTEGER,
            message TEXT NOT NULL,
            direction TEXT NOT NULL,
            status TEXT NOT NULL,
            timestamp TEXT NOT NULL
        );
        """)

        # Rooms
        rooms = [
            (1, "Suite 1 (Master Injectables)", "INJECTABLE", "Allergan Facial Aesthetic Station"),
            (2, "Suite 2 (Laser & RF)", "LASER", "InMode Morpheus8 & Sciton BBL HERO"),
            (3, "Suite 3 (Clinical Skincare)", "SKINCARE", "HydraFacial Elite MD")
        ]
        cur.executemany("INSERT INTO rooms VALUES (?, ?, ?, ?)", rooms)

        # Providers
        providers = [
            (1, "Marcus", "Vance", "MD (Plastic Surgeon)"),
            (2, "Elena", "Rostova", "ARNP (Master Injector)"),
            (3, "Chloe", "Lin", "LMA (Lead Aesthetician)")
        ]
        cur.executemany("INSERT INTO providers VALUES (?, ?, ?, ?)", providers)

        # Clients
        clients = [
            (201, "Harper", "Rothschild", "+14255551002", "PLATINUM_VIP", 443.57, 1, 1),
            (202, "Emma", "Fontaine", "+14255551062", "PLATINUM_VIP", 631.88, 1, 1),
            (203, "Leah", "Kensington", "+14255551051", "GOLD_VIP", 598.73, 1, 1),
            (204, "Camila", "Sterling", "+14255551194", "GOLD_VIP", 510.23, 1, 1),
            (205, "Aria", "Pembroke", "+14255551171", "PLATINUM_VIP", 1190.99, 1, 1)
        ]
        cur.executemany("INSERT INTO clients VALUES (?, ?, ?, ?, ?, ?, ?, ?)", clients)

        # Appointments
        today_str = datetime.now().strftime("%Y-%m-%d")
        appts = [
            (1, 201, 2, 1, "Botox Cosmetic (30 Units)", f"{today_str} 09:00:00", f"{today_str} 09:45:00", "CONFIRMED", 450.0, None),
            (2, 203, 2, 1, "Juvederm Lip Volbella", f"{today_str} 10:00:00", f"{today_str} 11:00:00", "CONFIRMED", 750.0, None),
            (3, 204, 2, 1, "Juvederm Cheek Contour (2 Syringes)", f"{today_str} 13:30:00", f"{today_str} 14:45:00", "CANCELLED", 1500.0, "Client travel emergency"),
            (4, 202, 1, 2, "Sciton BBL HERO Photofacial", f"{today_str} 09:30:00", f"{today_str} 10:30:00", "CONFIRMED", 650.0, None),
            (5, 205, 1, 2, "Morpheus8 RF Microneedling", f"{today_str} 11:00:00", f"{today_str} 12:30:00", "CANCELLED", 1200.0, "Child care conflict"),
            (6, 201, 3, 3, "HydraFacial Deluxe", f"{today_str} 10:00:00", f"{today_str} 11:00:00", "CONFIRMED", 275.0, None)
        ]
        cur.executemany("INSERT INTO appointments VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", appts)
        conn.commit()


# ==============================================================================
# DENTAL ENDPOINTS
# ==============================================================================
@app.get("/api/state")
def get_dental_state():
    init_dental_db()
    conn = get_dental_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM operatory ORDER BY OperatoryNum")
    ops = [dict(r) for r in cur.fetchall()]
    cur.execute("SELECT a.*, p.FName, p.LName, p.WirelessPhone FROM appointment a LEFT JOIN patient p ON a.PatNum = p.PatNum ORDER BY a.AptDateTime")
    appts = [dict(r) for r in cur.fetchall()]
    cur.execute("SELECT * FROM custom_agent_log ORDER BY LogNum DESC LIMIT 20")
    logs = [dict(r) for r in cur.fetchall()]
    return {"operatories": ops, "appointments": appts, "logs": logs}

class CancelRequest(BaseModel):
    apt_num: int
    reason: Optional[str] = "Patient sudden cancellation"

@app.post("/api/cancel")
def cancel_dental_appointment(req: CancelRequest):
    init_dental_db()
    conn = get_dental_conn()
    cur = conn.cursor()
    cur.execute("UPDATE appointment SET AptStatus = 5 WHERE AptNum = ?", (req.apt_num,))
    cur.execute("INSERT INTO custom_agent_log (AptNum, ActionType, Details, Timestamp) VALUES (?, 'CANCELLED', ?, ?)",
                (req.apt_num, req.reason, datetime.now().isoformat()))
    conn.commit()
    return {"status": "SUCCESS", "apt_num": req.apt_num}

class InboundSMSRequest(BaseModel):
    phone: str
    body: str
    apt_num: int

@app.post("/api/inbound-sms")
def dental_inbound_sms(req: InboundSMSRequest):
    init_dental_db()
    conn = get_dental_conn()
    cur = conn.cursor()
    body_upper = req.body.strip().upper()
    if body_upper == "STOP":
        cur.execute("UPDATE patient SET PreferSMS = 0 WHERE WirelessPhone = ?", (req.phone,))
        conn.commit()
        return {"status": "OPTED_OUT", "message": "TCPA Opt-out registered."}
    
    cur.execute("SELECT AptStatus FROM appointment WHERE AptNum = ?", (req.apt_num,))
    row = cur.fetchone()
    if not row or row["AptStatus"] != 5:
        return {"status": "ALREADY_CLAIMED", "winner": False, "message": "Sorry, another patient just confirmed this slot!"}

    cur.execute("SELECT PatNum, FName, LName FROM patient WHERE WirelessPhone = ?", (req.phone,))
    pat = cur.fetchone()
    pat_num = pat["PatNum"] if pat else 102
    pat_name = f"{pat['FName']} {pat['LName']}" if pat else "Henry Anderson"

    cur.execute("UPDATE appointment SET PatNum = ?, AptStatus = 1, Confirmed = 1 WHERE AptNum = ?", (pat_num, req.apt_num))
    cur.execute("INSERT INTO custom_agent_log (AptNum, ActionType, Details, Timestamp) VALUES (?, 'CLAIMED', ?, ?)",
                (req.apt_num, f"Slot claimed via SMS by {pat_name} ({req.phone})", datetime.now().isoformat()))
    conn.commit()
    return {"status": "SUCCESS", "winner": True, "patient_name": pat_name, "message": "Confirmed! See you at 10:00 AM."}

# ==============================================================================
# MED SPA ENDPOINTS
# ==============================================================================
@app.get("/api/medspa/state")
def get_medspa_state():
    init_medspa_db()
    conn = get_medspa_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM rooms ORDER BY room_id")
    rooms = [dict(r) for r in cur.fetchall()]
    cur.execute("""
        SELECT a.*, c.first_name, c.last_name, c.phone, c.vip_tier, c.banked_balance, p.first_name AS prov_fname, p.title AS prov_title
        FROM appointments a
        LEFT JOIN clients c ON a.client_id = c.client_id
        LEFT JOIN providers p ON a.provider_id = p.provider_id
        ORDER BY a.start_time
    """)
    appts = [dict(r) for r in cur.fetchall()]
    cur.execute("SELECT * FROM clients WHERE banked_balance >= 400.0 ORDER BY banked_balance DESC")
    lapsed_vips = [dict(r) for r in cur.fetchall()]
    cur.execute("SELECT * FROM comm_logs ORDER BY log_id DESC LIMIT 20")
    logs = [dict(r) for r in cur.fetchall()]
    return {"rooms": rooms, "appointments": appts, "lapsed_vips": lapsed_vips, "logs": logs}

class MedSpaCancelRequest(BaseModel):
    appointment_id: int
    reason: Optional[str] = "Aesthetic client emergency"

@app.post("/api/medspa/cancel")
def cancel_medspa_appointment(req: MedSpaCancelRequest):
    init_medspa_db()
    conn = get_medspa_conn()
    cur = conn.cursor()
    cur.execute("UPDATE appointments SET status = 'CANCELLED', cancellation_reason = ? WHERE appointment_id = ?",
                (req.reason, req.appointment_id))
    cur.execute("INSERT INTO comm_logs (message, direction, status, timestamp) VALUES (?, 'OUTBOUND', 'CANCELLED', ?)",
                (f"Cancelled Appointment #{req.appointment_id}: {req.reason}", datetime.now().isoformat()))
    conn.commit()
    return {"status": "SUCCESS", "appointment_id": req.appointment_id}

class MedSpaInboundSMS(BaseModel):
    appointment_id: int
    phone: str
    body: str

@app.post("/api/medspa/inbound-sms")
def medspa_inbound_sms(req: MedSpaInboundSMS):
    init_medspa_db()
    conn = get_medspa_conn()
    cur = conn.cursor()
    if req.body.strip().upper() == "STOP":
        cur.execute("UPDATE clients SET prefer_sms = 0 WHERE phone = ?", (req.phone,))
        conn.commit()
        return {"status": "OPTED_OUT", "message": "TCPA Opt-out registered."}

    cur.execute("SELECT status, total_price, start_time FROM appointments WHERE appointment_id = ?", (req.appointment_id,))
    slot = cur.fetchone()
    if not slot or slot["status"] != "CANCELLED":
        return {"status": "ALREADY_CLAIMED", "winner": False, "message": "Sorry, another VIP client just claimed this opening!"}

    cur.execute("SELECT client_id, first_name, last_name, vip_tier FROM clients WHERE phone = ?", (req.phone,))
    client = cur.fetchone()
    client_id = client["client_id"] if client else 201
    client_name = f"{client['first_name']} {client['last_name']}" if client else "Harper Rothschild"

    cur.execute("UPDATE appointments SET client_id = ?, status = 'CONFIRMED' WHERE appointment_id = ?",
                (client_id, req.appointment_id))
    cur.execute("INSERT INTO comm_logs (client_id, message, direction, status, timestamp) VALUES (?, ?, 'INBOUND', 'CLAIMED', ?)",
                (client_id, f"VIP Slot claimed by {client_name} via SMS ({req.phone})", datetime.now().isoformat()))
    conn.commit()
    return {
        "status": "SUCCESS",
        "winner": True,
        "client_name": client_name,
        "slot_time": slot["start_time"],
        "value": slot["total_price"],
        "message": f"Confirmed! You are scheduled for {slot['start_time']} at Cascade Aesthetic Medicine."
    }

@app.post("/api/medspa/reengage-vips")
def reengage_vips():
    init_medspa_db()
    conn = get_medspa_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM clients WHERE banked_balance >= 400.0 AND prefer_sms = 1 LIMIT 5")
    vips = cur.fetchall()
    dispatched = []
    for v in vips:
        msg = f"Cascade Aesthetic: Hi {v['first_name']}, you have ${int(v['banked_balance'])} banked in your Beauty Bank! Elena has an opening this week. Reply YES to reserve or STOP to opt out."
        cur.execute("INSERT INTO comm_logs (client_id, message, direction, status, timestamp) VALUES (?, ?, 'OUTBOUND', 'SENT', ?)",
                    (v["client_id"], msg, datetime.now().isoformat()))
        dispatched.append({"client_name": f"{v['first_name']} {v['last_name']}", "balance": v["banked_balance"]})
    conn.commit()
    return {"status": "SUCCESS", "dispatched_count": len(dispatched), "recipients": dispatched}
