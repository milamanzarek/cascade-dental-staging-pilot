"""
Cascade Aesthetic Medicine & MedSpa - Relational Engine
Emulating Boulevard / Zenoti data models with dual-resource scheduling (Room + Provider),
neurotoxin/filler inventory lots, and recurring VIP beauty-bank memberships.
"""

import sqlite3
import os
import random
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

DB_PATH = os.path.join(os.path.dirname(__file__), "cascade_aesthetic_medspa.db")

SCHEMA_SQL = """
PRAGMA journal_mode = WAL;
PRAGMA synchronous = NORMAL;
PRAGMA foreign_keys = ON;

-- 1. Treatment Rooms & Laser Suites
CREATE TABLE IF NOT EXISTS rooms (
    room_id INTEGER PRIMARY KEY AUTOINCREMENT,
    room_name TEXT NOT NULL,
    room_type TEXT NOT NULL, -- 'INJECTABLE', 'LASER', 'SKINCARE'
    equipment_tag TEXT,      -- 'InMode Morpheus8', 'Sciton BBL HERO', 'HydraFacial Elite'
    is_active INTEGER DEFAULT 1
);

-- 2. Providers & Injector Credentials
CREATE TABLE IF NOT EXISTS providers (
    provider_id INTEGER PRIMARY KEY AUTOINCREMENT,
    first_name TEXT NOT NULL,
    last_name TEXT NOT NULL,
    title TEXT NOT NULL,       -- 'MD', 'ARNP', 'LMA'
    npi TEXT UNIQUE,
    can_inject INTEGER DEFAULT 0,
    can_laser INTEGER DEFAULT 0,
    can_skincare INTEGER DEFAULT 1,
    hourly_cost REAL DEFAULT 150.0
);

-- 3. Aesthetic Service Catalog
CREATE TABLE IF NOT EXISTS services (
    service_id INTEGER PRIMARY KEY AUTOINCREMENT,
    service_code TEXT UNIQUE NOT NULL, -- 'BTX-30', 'LIP-JUV', 'LASER-M8', 'HYDRA-DLX'
    service_name TEXT NOT NULL,
    category TEXT NOT NULL,            -- 'NEUROTOXIN', 'FILLER', 'LASER', 'FACIAL'
    duration_minutes INTEGER NOT NULL,
    retail_price REAL NOT NULL,
    cost_of_goods REAL NOT NULL,
    required_room_type TEXT NOT NULL,  -- 'INJECTABLE', 'LASER', 'SKINCARE'
    required_provider_tier TEXT NOT NULL -- 'INJECTOR', 'LASER_TECH', 'AESTHETICIAN'
);

-- 4. Clients & Patient Profiles
CREATE TABLE IF NOT EXISTS clients (
    client_id INTEGER PRIMARY KEY AUTOINCREMENT,
    first_name TEXT NOT NULL,
    last_name TEXT NOT NULL,
    phone TEXT UNIQUE NOT NULL,
    email TEXT UNIQUE NOT NULL,
    birthdate DATE,
    vip_tier TEXT DEFAULT 'STANDARD', -- 'STANDARD', 'GOLD_VIP', 'PLATINUM_VIP'
    preferred_provider_id INTEGER,
    prefer_sms INTEGER DEFAULT 1,
    mhmda_consent INTEGER DEFAULT 1,  -- Washington My Health My Data Act explicit consent
    photo_consent INTEGER DEFAULT 1,  -- HIPAA before/after marketing photo consent
    last_visit_date DATE,
    next_due_date DATE,               -- Next recommended Botox/Laser retreatment
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (preferred_provider_id) REFERENCES providers(provider_id)
);

-- 5. Memberships & Banked Wallet Ledgers
CREATE TABLE IF NOT EXISTS memberships (
    membership_id INTEGER PRIMARY KEY AUTOINCREMENT,
    client_id INTEGER UNIQUE NOT NULL,
    tier_name TEXT NOT NULL,          -- 'Beauty Bank VIP ($199/mo)'
    monthly_dues REAL NOT NULL,       -- 199.0
    banked_balance REAL NOT NULL,     -- Accrued wallet credits available for redemption
    status TEXT DEFAULT 'ACTIVE',     -- 'ACTIVE', 'PAUSED', 'LAPSED'
    last_billed_date DATE,
    joined_date DATE,
    FOREIGN KEY (client_id) REFERENCES clients(client_id)
);

-- 6. Dual-Resource Appointment Schedule
CREATE TABLE IF NOT EXISTS appointments (
    appointment_id INTEGER PRIMARY KEY AUTOINCREMENT,
    client_id INTEGER,
    provider_id INTEGER NOT NULL,
    room_id INTEGER NOT NULL,
    service_id INTEGER NOT NULL,
    start_time DATETIME NOT NULL,
    end_time DATETIME NOT NULL,
    status TEXT NOT NULL,             -- 'SCHEDULED', 'CONFIRMED', 'CANCELLED', 'COMPLETED'
    total_price REAL NOT NULL,
    deposit_collected REAL DEFAULT 0.0,
    cancellation_reason TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (client_id) REFERENCES clients(client_id),
    FOREIGN KEY (provider_id) REFERENCES providers(provider_id),
    FOREIGN KEY (room_id) REFERENCES rooms(room_id),
    FOREIGN KEY (service_id) REFERENCES services(service_id)
);

-- 7. Communication & Waitlist SMS Logs
CREATE TABLE IF NOT EXISTS communication_logs (
    log_id INTEGER PRIMARY KEY AUTOINCREMENT,
    client_id INTEGER NOT NULL,
    appointment_id INTEGER,
    direction TEXT NOT NULL,          -- 'OUTBOUND', 'INBOUND'
    channel TEXT DEFAULT 'SMS',
    message_body TEXT NOT NULL,
    status TEXT NOT NULL,             -- 'SENT', 'DELIVERED', 'RECEIVED'
    is_claim_winner INTEGER DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (client_id) REFERENCES clients(client_id)
);

-- 8. Injectable Inventory Lots (Botox/Filler Tracking)
CREATE TABLE IF NOT EXISTS inventory_lots (
    lot_id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_name TEXT NOT NULL,       -- 'Botox Cosmetic 100U', 'Juvederm Ultra XC'
    lot_number TEXT NOT NULL,
    units_on_hand REAL NOT NULL,
    expiration_date DATE NOT NULL,
    unit_cost REAL NOT NULL
);
"""

FIRST_NAMES = [
    "Sophia", "Olivia", "Emma", "Ava", "Mia", "Isabella", "Harper", "Camila",
    "Gianna", "Evelyn", "Aria", "Chloe", "Ella", "Victoria", "Aubrey", "Grace",
    "Zoey", "Penelope", "Layla", "Nora", "Lily", "Eleanor", "Hannah", "Lillian",
    "Addison", "Aubree", "Stella", "Natalie", "Zoe", "Leah", "Hazel", "Violet",
    "Aurora", "Savannah", "Audrey", "Brooklyn", "Bella", "Claire", "Skylar", "Lucy"
]

LAST_NAMES = [
    "Kovacs", "Vance", "Mercer", "Sterling", "Montague", "DuPont", "Sinclair",
    "Wellington", "Blackwood", "Fontaine", "Kensington", "Lancaster", "Ashford",
    "Holloway", "Carmichael", "St. James", "Winslow", "Gallagher", "Decker", "Prescott",
    "Vanderbilt", "Rothschild", "Pembroke", "Fairfax", "Hampton", "Carlisle", "Monroe"
]


class MedSpaEngine:
    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        self._init_database()

    def get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path, timeout=15.0)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON;")
        return conn

    def _init_database(self):
        with self.get_connection() as conn:
            conn.executescript(SCHEMA_SQL)
            conn.commit()

    def seed_practice_data(self, force: bool = False):
        with self.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT COUNT(*) FROM rooms")
            if cur.fetchone()[0] > 0 and not force:
                return  # Already seeded

            # Clear existing data if force
            if force:
                conn.executescript("""
                    DELETE FROM communication_logs;
                    DELETE FROM appointments;
                    DELETE FROM memberships;
                    DELETE FROM clients;
                    DELETE FROM services;
                    DELETE FROM providers;
                    DELETE FROM rooms;
                    DELETE FROM inventory_lots;
                    DELETE FROM sqlite_sequence WHERE name IN ('rooms', 'providers', 'services', 'clients', 'memberships', 'appointments', 'inventory_lots', 'communication_logs');
                """)

            # 1. Seed Rooms
            rooms_data = [
                ("Suite 1 - Master Injectable Suite", "INJECTABLE", "Allergan Facial Aesthetic Station"),
                ("Suite 2 - Advanced Laser & RF Suite", "LASER", "InMode Morpheus8 & Sciton BBL HERO"),
                ("Suite 3 - Clinical Skincare & Facial Bay", "SKINCARE", "HydraFacial Elite MD System")
            ]
            cur.executemany(
                "INSERT INTO rooms (room_name, room_type, equipment_tag) VALUES (?, ?, ?)",
                rooms_data
            )

            # 2. Seed Providers
            providers_data = [
                ("Marcus", "Vance", "MD", "1982736450", 1, 1, 1, 350.0),
                ("Elena", "Rostova", "ARNP", "1827364591", 1, 1, 0, 180.0),
                ("Chloe", "Lin", "LMA", "1726354892", 0, 0, 1, 65.0)
            ]
            cur.executemany(
                "INSERT INTO providers (first_name, last_name, title, npi, can_inject, can_laser, can_skincare, hourly_cost) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                providers_data
            )

            # 3. Seed Services
            services_data = [
                ("BTX-30", "Botox Cosmetic (30 Units)", "NEUROTOXIN", 45, 450.0, 150.0, "INJECTABLE", "INJECTOR"),
                ("BTX-50", "Full Face Neurotoxin (50 Units)", "NEUROTOXIN", 60, 750.0, 250.0, "INJECTABLE", "INJECTOR"),
                ("LIP-JUV", "Juvederm Volbella Lip Enhancement (1 Syringe)", "FILLER", 60, 750.0, 220.0, "INJECTABLE", "INJECTOR"),
                ("CHEEK-VOL", "Juvederm Voluma Cheek Contour (2 Syringes)", "FILLER", 75, 1500.0, 440.0, "INJECTABLE", "INJECTOR"),
                ("LASER-M8", "Morpheus8 RF Microneedling (Face & Neck)", "LASER", 90, 1200.0, 280.0, "LASER", "LASER_TECH"),
                ("LASER-BBL", "Sciton BBL HERO Photofacial", "LASER", 60, 650.0, 110.0, "LASER", "LASER_TECH"),
                ("HYDRA-DLX", "HydraFacial Deluxe with Booster", "FACIAL", 60, 275.0, 65.0, "SKINCARE", "AESTHETICIAN")
            ]
            cur.executemany(
                "INSERT INTO services (service_code, service_name, category, duration_minutes, retail_price, cost_of_goods, required_room_type, required_provider_tier) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                services_data
            )

            # 4. Seed Inventory Lots
            inventory_data = [
                ("Botox Cosmetic 100U", "LOT-BX8920", 280.0, "2027-08-31", 5.0),
                ("Juvederm Ultra Plus XC", "LOT-JV4412", 45.0, "2027-11-30", 220.0),
                ("Juvederm Voluma XC", "LOT-VM9921", 38.0, "2027-10-15", 240.0)
            ]
            cur.executemany(
                "INSERT INTO inventory_lots (product_name, lot_number, units_on_hand, expiration_date, unit_cost) VALUES (?, ?, ?, ?, ?)",
                inventory_data
            )

            # 5. Seed 200 Aesthetic Clients
            today = datetime.now().date()
            clients_to_insert = []
            random.seed(42)  # Deterministic seed

            for i in range(1, 201):
                fname = random.choice(FIRST_NAMES)
                lname = random.choice(LAST_NAMES)
                phone = f"+1425555{1000 + i:04d}"
                email = f"{fname.lower()}.{lname.lower()}{i}@luxurymail.com"
                bday = today - timedelta(days=random.randint(25 * 365, 62 * 365))
                tier = random.choices(["STANDARD", "GOLD_VIP", "PLATINUM_VIP"], weights=[0.60, 0.25, 0.15])[0]
                pref_prov = random.choice([1, 2, 3])

                # Last visit and next due date
                days_since_visit = random.randint(15, 180)
                last_visit = today - timedelta(days=days_since_visit)
                # Botox/Laser retreatment recommended every 90-120 days
                next_due = last_visit + timedelta(days=random.choice([90, 105, 120]))

                clients_to_insert.append((
                    fname, lname, phone, email, bday, tier, pref_prov, 1, 1, 1,
                    last_visit, next_due
                ))

            cur.executemany("""
                INSERT INTO clients (
                    first_name, last_name, phone, email, birthdate, vip_tier,
                    preferred_provider_id, prefer_sms, mhmda_consent, photo_consent,
                    last_visit_date, next_due_date
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, clients_to_insert)

            # 6. Seed Memberships for VIP clients
            cur.execute("SELECT client_id, vip_tier FROM clients WHERE vip_tier IN ('GOLD_VIP', 'PLATINUM_VIP')")
            vip_clients = cur.fetchall()
            memberships_data = []

            for row in vip_clients:
                c_id = row["client_id"]
                tier = row["vip_tier"]
                dues = 199.0 if tier == "GOLD_VIP" else 299.0
                tier_label = f"Beauty Bank Gold (${dues:.0f}/mo)" if tier == "GOLD_VIP" else f"Platinum Radiance VIP (${dues:.0f}/mo)"
                
                # Banked wallet balance: between $200 and $1,200
                banked = round(random.uniform(200.0, 1200.0), 2)
                # Some are lapsed (dormant > 75 days with high balance)
                status = "ACTIVE"
                if random.random() < 0.35:
                    status = "LAPSED"

                memberships_data.append((
                    c_id, tier_label, dues, banked, status,
                    today - timedelta(days=random.randint(5, 25)),
                    today - timedelta(days=random.randint(90, 450))
                ))

            cur.executemany("""
                INSERT INTO memberships (
                    client_id, tier_name, monthly_dues, banked_balance, status,
                    last_billed_date, joined_date
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """, memberships_data)

            # 7. Seed Today's Appointments across the 3 Suites
            base_date = today.strftime("%Y-%m-%d")
            appts = [
                # Suite 1 (Injectables) - Elena Rostova (ARNP)
                (12, 2, 1, 1, f"{base_date} 09:00:00", f"{base_date} 09:45:00", "CONFIRMED", 450.0, 100.0, None),
                (34, 2, 1, 3, f"{base_date} 10:00:00", f"{base_date} 11:00:00", "CONFIRMED", 750.0, 150.0, None),
                # CANCELLED SLOT: 1:30 PM Cheek Filler ($1,500 value)
                (55, 2, 1, 4, f"{base_date} 13:30:00", f"{base_date} 14:45:00", "CANCELLED", 1500.0, 200.0, "Client travel emergency"),
                (88, 2, 1, 2, f"{base_date} 15:30:00", f"{base_date} 16:30:00", "CONFIRMED", 750.0, 150.0, None),

                # Suite 2 (Laser) - Dr. Marcus Vance (MD)
                (21, 1, 2, 6, f"{base_date} 09:30:00", f"{base_date} 10:30:00", "CONFIRMED", 650.0, 100.0, None),
                # CANCELLED SLOT: 11:00 AM Morpheus8 ($1,200 value)
                (47, 1, 2, 5, f"{base_date} 11:00:00", f"{base_date} 12:30:00", "CANCELLED", 1200.0, 250.0, "Child care conflict"),
                (92, 1, 2, 5, f"{base_date} 14:00:00", f"{base_date} 15:30:00", "CONFIRMED", 1200.0, 250.0, None),

                # Suite 3 (Skincare) - Chloe Lin (LMA)
                (18, 3, 3, 7, f"{base_date} 09:00:00", f"{base_date} 10:00:00", "CONFIRMED", 275.0, 50.0, None),
                (64, 3, 3, 7, f"{base_date} 10:30:00", f"{base_date} 11:30:00", "CONFIRMED", 275.0, 50.0, None),
                (105, 3, 3, 7, f"{base_date} 13:00:00", f"{base_date} 14:00:00", "CONFIRMED", 275.0, 50.0, None),
                (142, 3, 3, 7, f"{base_date} 15:00:00", f"{base_date} 16:00:00", "CONFIRMED", 275.0, 50.0, None)
            ]

            cur.executemany("""
                INSERT INTO appointments (
                    client_id, provider_id, room_id, service_id, start_time, end_time,
                    status, total_price, deposit_collected, cancellation_reason
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, appts)

            conn.commit()
            print("Successfully seeded Cascade Aesthetic Medicine & MedSpa relational database!")


if __name__ == "__main__":
    engine = MedSpaEngine()
    engine.seed_practice_data(force=True)
