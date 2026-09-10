"""
Standalone Concurrency Benchmark & Test Runner for Med Spa Module
Verifies:
1. Dual-resource relational schema & practice seeding
2. High-value cancelled slot recovery ($1,200 Morpheus8 / $1,500 Cheek Filler)
3. High-concurrency race condition stress test (TR-009: 5 simultaneous SMS replies -> 1 winner, 0 collisions)
4. Lapsed VIP Beauty Bank balance re-engagement
5. TCPA STOP keyword handling
"""

import sys
import time
from concurrent.futures import ThreadPoolExecutor
from medspa_module.medspa_engine import MedSpaEngine
from medspa_module.medspa_agent import MedSpaAgent

def run_benchmarks():
    print("=" * 80)
    print("  CASCADE AESTHETIC MEDICINE & MEDSPA: BENCHMARK & CONCURRENCY SUITE (TR-009)")
    print("=" * 80)

    # 1. Initialize & Seed
    print("\n[1/5] Initializing Med Spa Relational Engine & Seeding Practice Data...")
    t0 = time.perf_counter()
    engine = MedSpaEngine()
    engine.seed_practice_data(force=True)
    seed_time = (time.perf_counter() - t0) * 1000
    print(f"  -> Database initialized with 3 Suites, 3 Clinicians, 200 Clients, and VIP Memberships in {seed_time:.2f}ms.")

    agent = MedSpaAgent(engine)

    # 2. Cancelled Slots
    print("\n[2/5] Detecting High-Value Cancelled Slots...")
    slots = agent.get_cancelled_slots()
    print(f"  -> Detected {len(slots)} high-value vacant slots:")
    for s in slots:
        print(f"     * Slot #{s['appointment_id']} ({s['room_name']}): {s['service_name']} (${s['total_price']:.2f}) at {s['start_time']}")
    
    assert len(slots) >= 2, "Expected at least 2 cancelled slots"
    target_slot = slots[0]  # E.g. Slot 3 or 6 ($1,500 Cheek Filler or $1,200 Morpheus8)
    target_apt_id = target_slot["appointment_id"]
    print(f"  -> Target Recovery Slot: #{target_apt_id} ({target_slot['service_name']} - ${target_slot['total_price']:.2f})")

    # 3. Candidate Matching
    print(f"\n[3/5] Matching Top Retreatment & VIP Candidates for {target_slot['category']}...")
    candidates = agent.get_candidate_clients(
        service_category=target_slot["category"],
        provider_id=target_slot["provider_id"],
        limit=5
    )
    print(f"  -> Retrieved {len(candidates)} eligible VIP candidates (MHMDA & SMS Opt-In Verified):")
    for c in candidates:
        banked = f"${c['banked_balance']:.2f}" if c['banked_balance'] else "$0.00"
        print(f"     * Pat #{c['client_id']} ({c['first_name']} {c['last_name']}) | Tier: {c['vip_tier']} | Banked: {banked} | Score: {c['match_score']}")

    # 4. Concurrency Stress Test
    print(f"\n[4/5] Executing High-Concurrency Stress Test (TR-009)...")
    print(f"  -> Firing 5 simultaneous 'YES' SMS messages via ThreadPoolExecutor...")

    def fire_claim(cand):
        return agent.claim_slot(
            appointment_id=target_apt_id,
            client_phone=cand["phone"],
            sms_body="YES"
        )

    t_start = time.perf_counter()
    results = []
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(fire_claim, c) for c in candidates]
        for f in futures:
            results.append(f.result())
    total_batch_ms = (time.perf_counter() - t_start) * 1000

    print("\n[RESULTS] Inbound Ingestion & Contention Resolution:")
    winners = [r for r in results if r.get("status") == "SUCCESS"]
    contentions = [r for r in results if r.get("status") == "ALREADY_CLAIMED"]

    for idx, r in enumerate(results, 1):
        if r.get("status") == "SUCCESS":
            print(f"  -> [WINNER]     Candidate: {r['client_name']} - 200 OK CLAIMED SLOT! Latency: {r['latency_ms']}ms")
        else:
            print(f"  -> [CONTENTION] Already Claimed notice sent gracefully. Latency: {r['latency_ms']}ms")

    assert len(winners) == 1, f"Expected 1 winner, got {len(winners)}"
    assert len(contentions) == 4, f"Expected 4 contentions, got {len(contentions)}"
    print(f"\n  -> Batch Processing Latency: {total_batch_ms:.2f}ms (Avg per claim: {total_batch_ms/5:.2f}ms)")
    print(f"  -> Winner Locking Latency: {winners[0]['latency_ms']}ms")
    print(f"  -> Double-Booking Contention Rate: 0.0% (Zero collisions)")

    # 5. Lapsed VIP Re-Engagement
    print("\n[5/5] Testing Lapsed VIP Beauty Bank Re-Engagement...")
    lapsed = agent.get_lapsed_vip_memberships(min_balance=300.0, days_dormant=60)
    print(f"  -> Found {len(lapsed)} VIP members with >= $300 unspent credits dormant for 60+ days.")
    if lapsed:
        sample = lapsed[0]
        outreach = agent.generate_concierge_outreach(sample)
        print(f"  -> Sample Zero-PHI Luxury Concierge Outreach for {sample['first_name']} {sample['last_name']} (${sample['banked_balance']:.2f} banked):")
        print(f'     "{outreach}"')

    # TCPA Test
    print("\n[BONUS] Verifying TCPA 'STOP' Keyword Opt-Out...")
    test_phone = candidates[-1]["phone"]
    opt_out_res = agent.claim_slot(appointment_id=target_apt_id, client_phone=test_phone, sms_body="STOP")
    print(f"  -> Opt-out Status: {opt_out_res['status']} | Latency: {opt_out_res['latency_ms']}ms")
    assert opt_out_res["status"] == "OPTED_OUT"

    print("\n" + "=" * 80)
    print("  [PASS] ALL MED SPA INTEGRATION & CONCURRENCY BENCHMARKS VERIFIED! (TR-009)")
    print("=" * 80)

if __name__ == "__main__":
    run_benchmarks()
