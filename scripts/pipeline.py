"""
TMG Vetting Pipeline Runner
============================
Runs pipeline steps based on vetting level.
Each step is independent — can be run individually or as a pipeline.
Modeled after /Users/shannonwheatman/palantir/scripts/pipeline.py
"""

import json
import sys
import os
import time
import argparse
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config

# Import step scripts
from intake import create_intake
from check_sanctions import run_sanctions_check
from check_debarment import run_debarment_check
from search_news import run_news_search
from search_litigation import run_litigation_search
from search_corporate import run_corporate_search
from search_fec import run_fec_search
from search_sec import run_sec_search
from search_lobbying import run_lobbying_search
from search_bankruptcy import run_bankruptcy_search
from search_executives import run_executive_search
from search_international import run_international_search
from search_contracts import run_contracts_search
from search_network import run_network_search
from synthesize import run_synthesis


def run_pipeline(
    name: str,
    subject_type: str = "individual",
    company: str = None,
    country: str = None,
    city: str = None,
    brief_bio: str = None,
    referral_source: str = None,
    engagement_type: str = "domestic_corporate",
    vetting_level: str = "deep_dive",
    requested_by: str = "Shannon",
    from_step: int = None,
    force: bool = False,
    no_synthesis: bool = False,
) -> dict:
    """Run the full vetting pipeline for a subject."""

    steps_to_run = list(config.VETTING_LEVELS[vetting_level]["steps"])
    level_label = config.VETTING_LEVELS[vetting_level]["label"]

    # ─── Skip US-only steps for non-US subjects ─────────────
    is_us = (country or "US").upper() in ("US", "USA", "UNITED STATES")
    US_ONLY_STEPS = {
        2: "Debarment (SAM.gov — US only)",
        4: "Litigation (CourtListener — US courts only)",
        6: "FEC Campaign Finance (US only)",
        7: "SEC Filings (US only)",
        8: "Lobbying Disclosures (US Senate LDA only)",
        9: "Bankruptcy (US courts only)",
        14: "Government Contracts (USAspending — US only)",
    }
    skipped_steps = []
    if not is_us:
        for step_num, reason in US_ONLY_STEPS.items():
            if step_num in steps_to_run:
                steps_to_run.remove(step_num)
                skipped_steps.append(f"  Step {step_num}: {reason}")
        # Ensure Step 12 (International) is always included for non-US subjects
        if 12 not in steps_to_run and 13 in steps_to_run:
            # Insert before synthesis (step 13)
            idx = steps_to_run.index(13)
            steps_to_run.insert(idx, 12)

    print("=" * 60)
    print(f"TMG VETTING PIPELINE — {level_label.upper()}")
    print(f"Subject: {name}")
    if not is_us:
        print(f"Country: {country} (INTERNATIONAL — US-only steps will be skipped)")
    print(f"Level: {level_label} (Steps: {steps_to_run})")
    print(f"Engagement: {engagement_type} (multiplier: {config.ENGAGEMENT_MULTIPLIERS.get(engagement_type, 1.0)}x)")
    if skipped_steps:
        print(f"Skipped US-only steps:")
        for s in skipped_steps:
            print(s)
    print("=" * 60)

    start_time = time.time()

    # ─── STEP 0: Intake ────────────────────────────────
    print(f"\n{'─'*50}")
    print("STEP 0: INTAKE")
    print(f"{'─'*50}")
    intake = create_intake(
        name=name,
        subject_type=subject_type,
        company=company,
        country=country,
        city=city,
        brief_bio=brief_bio,
        referral_source=referral_source,
        engagement_type=engagement_type,
        vetting_level=vetting_level,
        requested_by=requested_by,
    )
    subject_id = intake["subject_id"]

    # ─── STEP 1: Sanctions Gate ────────────────────────
    if 1 in steps_to_run and (from_step is None or from_step <= 1):
        print(f"\n{'─'*50}")
        print("STEP 1: SANCTIONS / WATCHLIST GATE")
        print(f"{'─'*50}")
        sanctions = run_sanctions_check(intake)

        if sanctions["gate"]["status"] == "FAIL":
            print(f"\n{'='*60}")
            print("⛔ PIPELINE HALTED — SANCTIONS GATE FAILED")
            print(f"Subject '{name}' matched against sanctions/watchlist databases.")
            print("Result: AUTO-REJECT (CRITICAL tier)")
            print(f"Details: {'; '.join(sanctions['gate']['details'])}")
            print(f"{'='*60}")
            return _finalize(intake, "gates_failed", sanctions_gate="FAIL", debarment_gate="NOT_RUN",
                            start_time=start_time)

    # ─── STEP 2: Debarment Gate ────────────────────────
    if 2 in steps_to_run and (from_step is None or from_step <= 2):
        print(f"\n{'─'*50}")
        print("STEP 2: GOVERNMENT DEBARMENT / EXCLUSION GATE")
        print(f"{'─'*50}")
        debarment = run_debarment_check(intake)

        if debarment["gate"]["status"] == "FAIL":
            print(f"\n{'='*60}")
            print("⛔ PIPELINE HALTED — DEBARMENT GATE FAILED")
            print(f"Subject '{name}' found in government exclusion database.")
            print("Result: AUTO-REJECT (CRITICAL tier)")
            print(f"Details: {'; '.join(debarment['gate']['details'])}")
            print(f"{'='*60}")
            return _finalize(intake, "gates_failed", sanctions_gate="PASS", debarment_gate="FAIL",
                            start_time=start_time)

    # ─── STEP 3: Basic News ───────────────────────────
    if 3 in steps_to_run and (from_step is None or from_step <= 3):
        print(f"\n{'─'*50}")
        print("STEP 3: NEWS / MEDIA SCAN (Basic)")
        print(f"{'─'*50}")
        news = run_news_search(intake, deep=False)

    # ─── STEP 4: Litigation ──────────────────────────
    if 4 in steps_to_run and (from_step is None or from_step <= 4):
        print(f"\n{'─'*50}")
        print("STEP 4: COURT RECORDS / LITIGATION")
        print(f"{'─'*50}")
        litigation = run_litigation_search(intake)

    # ─── STEP 5: Corporate Filings ────────────────────
    if 5 in steps_to_run and (from_step is None or from_step <= 5):
        print(f"\n{'─'*50}")
        print("STEP 5: CORPORATE FILINGS / BUSINESS REGISTRATIONS")
        print(f"{'─'*50}")
        corporate = run_corporate_search(intake)

    # ─── STEP 15: Corporate Network Discovery ─────────
    if 15 in steps_to_run and (from_step is None or from_step <= 15):
        print(f"\n{'─'*50}")
        print("STEP 15: CORPORATE NETWORK DISCOVERY (OpenCorporates)")
        print(f"{'─'*50}")
        network = run_network_search(intake)

    # ─── STEP 6: FEC / Campaign Finance ───────────────
    if 6 in steps_to_run and (from_step is None or from_step <= 6):
        print(f"\n{'─'*50}")
        print("STEP 6: FEC / CAMPAIGN FINANCE")
        print(f"{'─'*50}")
        fec = run_fec_search(intake)

    # ─── STEP 7: SEC Filings ─────────────────────────
    if 7 in steps_to_run and (from_step is None or from_step <= 7):
        print(f"\n{'─'*50}")
        print("STEP 7: SEC FILINGS / FINANCIAL DISCLOSURES")
        print(f"{'─'*50}")
        sec = run_sec_search(intake)

    # ─── STEP 8: Lobbying ────────────────────────────
    if 8 in steps_to_run and (from_step is None or from_step <= 8):
        print(f"\n{'─'*50}")
        print("STEP 8: LOBBYING DISCLOSURES")
        print(f"{'─'*50}")
        lobbying = run_lobbying_search(intake)

    # ─── STEP 9: Bankruptcy ──────────────────────────
    if 9 in steps_to_run and (from_step is None or from_step <= 9):
        print(f"\n{'─'*50}")
        print("STEP 9: BANKRUPTCY FILINGS")
        print(f"{'─'*50}")
        bankruptcy = run_bankruptcy_search(intake)

    # ─── STEP 10: Expanded News (Deep) ───────────────
    if 10 in steps_to_run and (from_step is None or from_step <= 10):
        print(f"\n{'─'*50}")
        print("STEP 10: EXPANDED NEWS / MEDIA (Deep)")
        print(f"{'─'*50}")
        news_deep = run_news_search(intake, deep=True)

    # ─── STEP 11: Executive Identification ───────────
    if 11 in steps_to_run and (from_step is None or from_step <= 11):
        print(f"\n{'─'*50}")
        print("STEP 11: EXECUTIVE IDENTIFICATION & MINI-VET")
        print(f"{'─'*50}")
        executives = run_executive_search(intake)

    # ─── STEP 12: International Checks ───────────────
    if 12 in steps_to_run and (from_step is None or from_step <= 12):
        print(f"\n{'─'*50}")
        print("STEP 12: INTERNATIONAL CHECKS")
        print(f"{'─'*50}")
        international = run_international_search(intake)

    # ─── STEP 14: Government Contracts ─────────────────
    if 14 in steps_to_run and (from_step is None or from_step <= 14):
        print(f"\n{'─'*50}")
        print("STEP 14: GOVERNMENT CONTRACTS")
        print(f"{'─'*50}")
        contracts = run_contracts_search(intake)

    # ─── STOP BEFORE SYNTHESIS (if --no-synthesis) ───
    if no_synthesis:
        subject_id = intake["subject_id"]
        print(f"\n{'='*60}")
        print("PIPELINE PAUSED — SKIPPING SYNTHESIS")
        print(f"All research steps complete for '{name}'.")
        print(f"")
        print(f"To add manual findings before synthesis:")
        print(f"  1. Copy the template:  cp data/manual/_TEMPLATE.json data/manual/{subject_id}.json")
        print(f"  2. Edit with your findings:  open data/manual/{subject_id}.json")
        print(f"  3. Run synthesis:  python3 scripts/synthesize.py --subject-id {subject_id}")
        print(f"")
        print(f"Or run synthesis now without manual findings:")
        print(f"  python3 scripts/synthesize.py --subject-id {subject_id}")
        print(f"{'='*60}")
        return _finalize(intake, "paused", sanctions_gate="PASS", debarment_gate="PASS",
                        start_time=start_time)

    # ─── STEP 13: Claude Synthesis ───────────────────
    if 13 in steps_to_run and (from_step is None or from_step <= 13):
        print(f"\n{'─'*50}")
        print("STEP 13: CLAUDE SYNTHESIS")
        print(f"{'─'*50}")
        synthesis = run_synthesis(intake)

        if synthesis and synthesis.get("scoring"):
            return _finalize(intake, "completed", sanctions_gate="PASS", debarment_gate="PASS",
                            start_time=start_time, synthesis=synthesis)

    return _finalize(intake, "completed", sanctions_gate="PASS", debarment_gate="PASS",
                    start_time=start_time)


def _finalize(intake: dict, status: str, sanctions_gate: str, debarment_gate: str,
              start_time: float, synthesis: dict = None) -> dict:
    """Create final pipeline result summary."""
    elapsed = time.time() - start_time
    subject_id = intake["subject_id"]

    summary = {
        "subject_id": subject_id,
        "subject_name": intake["subject"]["name"],
        "vetting_level": intake["context"]["vetting_level"],
        "status": status,
        "gates": {
            "sanctions": sanctions_gate,
            "debarment": debarment_gate,
        },
        "elapsed_seconds": round(elapsed, 1),
        "completed_at": datetime.now(timezone.utc).isoformat(),
    }

    if synthesis and synthesis.get("scoring"):
        scoring = synthesis["scoring"]
        summary["composite_score"] = scoring.get("final_composite")
        summary["risk_tier"] = scoring.get("risk_tier")
        summary["recommendation"] = scoring.get("recommendation")
        summary["confidence"] = scoring.get("confidence_modifier", "HIGH")

    print(f"\n{'='*60}")
    print(f"PIPELINE {status.upper()}")
    print(f"Subject: {intake['subject']['name']}")
    print(f"Sanctions Gate: {sanctions_gate}")
    print(f"Debarment Gate: {debarment_gate}")
    if synthesis and synthesis.get("scoring"):
        scoring = synthesis["scoring"]
        print(f"Composite Score: {scoring.get('final_composite', 'N/A')}/10")
        print(f"Risk Tier: {scoring.get('risk_tier', 'N/A')}")
        print(f"Recommendation: {scoring.get('recommendation', 'N/A')}")
    print(f"Time: {elapsed:.1f}s")
    print(f"{'='*60}")

    return summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="TMG Vetting Pipeline Runner")
    parser.add_argument("--name", required=True, help="Subject name to vet")
    parser.add_argument("--type", default="individual", choices=["individual", "organization"])
    parser.add_argument("--company", default=None, help="Company affiliation")
    parser.add_argument("--country", default=None, help="Country of origin or operations")
    parser.add_argument("--city", default=None, help="City")
    parser.add_argument("--bio", default=None, help="Brief bio / background info")
    parser.add_argument("--referral", default=None, help="How they came to TMG / referral source")
    parser.add_argument("--engagement", default="domestic_corporate",
                        choices=list(config.ENGAGEMENT_MULTIPLIERS.keys()))
    parser.add_argument("--level", default="deep_dive",
                        choices=list(config.VETTING_LEVELS.keys()))
    parser.add_argument("--from-step", type=int, default=None, help="Start from this step")
    parser.add_argument("--no-synthesis", action="store_true",
                        help="Run research steps only, skip synthesis. Add manual findings then run synthesize.py separately.")
    parser.add_argument("--requested-by", default="Shannon")
    args = parser.parse_args()

    run_pipeline(
        name=args.name,
        subject_type=args.type,
        company=args.company,
        country=args.country,
        city=args.city,
        brief_bio=args.bio,
        referral_source=args.referral,
        engagement_type=args.engagement,
        vetting_level=args.level,
        from_step=args.from_step,
        no_synthesis=args.no_synthesis,
        requested_by=args.requested_by,
    )
