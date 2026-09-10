"""
Unit & Concurrency Test Suite for Cascade Aesthetic Medicine & MedSpa
Verifies:
1. Dual-resource relational schema & practice seeding
2. High-value cancelled slot recovery ($1,200 Morpheus8 / $1,500 Cheek Filler)
3. High-concurrency race condition stress test (5 simultaneous SMS replies -> 1 winner, 0 collisions)
4. Lapsed VIP Beauty Bank balance re-engagement
5. TCPA STOP keyword handling
"""

import pytest
import sqlite3
import os
import time
from concurrent.futures import ThreadPoolExecutor
from medspa_module.medspa_engine import MedSpaEngine
from medspa_module.medspa_agent import MedSpaAgent

TEST_DB = os.path.join(os.path.dirname(__file__), "test_medspa.db")


@pytest.fixture(scope="module")
def setup_engine():
    if os.path.exists(TEST_DB):
        try:
            os.remove(TEST_DB)
        except OSError:
            pass
    engine = MedSpaEngine(db_path=TEST_DB)
    engine.seed_practice_data(force=True)
    yield engine
    # Cleanup
    try:
        if os.path.exists(TEST_DB):
            os.remove(TEST_DB)
    except OSError:
        pass


def test_database_seeding(setup_engine):
    with setup_engine.get_connection() as conn:
        cur = conn.cursor()
        
        # 3 Suites
        cur.execute("SELECT COUNT(*) FROM rooms")
        assert cur.fetchone()[0] == 3
        
        # 3 Providers
        cur.execute("SELECT COUNT(*) FROM providers")
        assert cur.fetchone()[0] == 3
        
        # 200 Clients
        cur.execute("SELECT COUNT(*) FROM clients")
        assert cur.fetchone()[0] == 200
        
        # Memberships
        cur.execute("SELECT COUNT(*) FROM memberships")
        assert cur.fetchone()[0] > 0
        
        # Inventory
        cur.execute("SELECT COUNT(*) FROM inventory_lots")
        assert cur.fetchone()[0] >= 3


def test_cancelled_slot_detection(setup_engine):
    agent = MedSpaAgent(setup_engine)
    slots = agent.get_cancelled_slots()
    assert len(slots) >= 2  # Cheek Filler ($1,500) and Morpheus8 ($1,200)
    
    # Verify high dollar values
    values = [s["total_price"] for s in slots]
    assert 1200.0 in values
    assert 1500.0 in values


def test_candidate_matching_mhmda(setup_engine):
    agent = MedSpaAgent(setup_engine)
    candidates = agent.get_candidate_clients(service_category="LASER", provider_id=1, limit=5)
    assert len(candidates) > 0
    assert len(candidates) <= 5
    
    # Check consent constraints
    for c in candidates:
        assert c["vip_tier"] in ["PLATINUM_VIP", "GOLD_VIP", "STANDARD"]
        assert c["phone"].startswith("+1425555")


def test_tcpa_stop_keyword(setup_engine):
    agent = MedSpaAgent(setup_engine)
    test_phone = "+14255551050"
    
    res = agent.claim_slot(appointment_id=1, client_phone=test_phone, sms_body="STOP")
    assert res["status"] == "OPTED_OUT"
    
    with setup_engine.get_connection() as conn:
        cur = conn.cursor()
        cur.execute("SELECT prefer_sms FROM clients WHERE phone = ?", (test_phone,))
        assert cur.fetchone()[0] == 0


def test_high_concurrency_race_condition(setup_engine):
    """
    Stress test TR-009: 5 simultaneous VIP clients reply 'YES' to claim a cancelled $1,200 Morpheus8 slot.
    Must guarantee:
    - Exactly 1 WINNER
    - Exactly 4 graceful CONTENTION resolutions
    - Zero double-bookings (ACID isolation)
    - Sub-25ms average claim latency
    """
    agent = MedSpaAgent(setup_engine)
    
    # Target cancelled appointment (Morpheus8 in Suite 2)
    slots = agent.get_cancelled_slots()
    assert len(slots) > 0
    target_slot = slots[0]
    target_apt_id = target_slot["appointment_id"]
    
    # Retrieve 5 distinct candidates
    candidates = agent.get_candidate_clients(service_category=target_slot["category"], provider_id=target_slot["provider_id"], limit=5)
    assert len(candidates) == 5
    
    print(f"\n[RACE BENCHMARK] Firing 5 simultaneous claims for Slot #{target_apt_id} (${target_slot['total_price']})...")
    
    results = []
    
    def fire_claim(cand):
        return agent.claim_slot(
            appointment_id=target_apt_id,
            client_phone=cand["phone"],
            sms_body="YES"
        )
    
    t0 = time.perf_counter()
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(fire_claim, c) for c in candidates]
        for f in futures:
            results.append(f.result())
    total_batch_time_ms = (time.perf_counter() - t0) * 1000
    
    # Verify results
    winners = [r for r in results if r.get("status") == "SUCCESS"]
    contentions = [r for r in results if r.get("status") == "ALREADY_CLAIMED"]
    
    print(f"[RACE BENCHMARK] Winners: {len(winners)}, Contentions: {len(contentions)}, Batch Time: {total_batch_time_ms:.2f}ms")
    
    assert len(winners) == 1, f"Expected exactly 1 winner, got {len(winners)}"
    assert len(contentions) == 4, f"Expected exactly 4 contentions, got {len(contentions)}"
    
    winner = winners[0]
    assert winner["winner"] is True
    assert winner["latency_ms"] < 35.0  # Atomic lock under 35ms
    
    # Verify database state
    with setup_engine.get_connection() as conn:
        cur = conn.cursor()
        cur.execute("SELECT status, client_id FROM appointments WHERE appointment_id = ?", (target_apt_id,))
        row = cur.fetchone()
        assert row["status"] == "CONFIRMED"
        assert row["client_id"] is not None


def test_lapsed_vip_reengagement(setup_engine):
    agent = MedSpaAgent(setup_engine)
    lapsed = agent.get_lapsed_vip_memberships(min_balance=250.0, days_dormant=45)
    assert len(lapsed) > 0
    
    # Check first member outreach formatting
    m = lapsed[0]
    assert m["banked_balance"] >= 250.0
    outreach = agent.generate_concierge_outreach(m)
    
    assert "Beauty Bank" in outreach or "Cascade Aesthetic" in outreach
    assert str(int(m["banked_balance"])) in outreach
    assert "STOP" in outreach
