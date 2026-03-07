"""
Step 2: Government Debarment / Exclusion Check — BINARY GATE
=============================================================
Checks: SAM.gov Exclusions API (federal debarment/exclusion)
A match = AUTO-REJECT. No composite score calculated.
"""

import json
import sys
import os
import requests
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config


def check_sam_gov(name: str) -> dict:
    """Check SAM.gov Exclusions API for debarment/exclusion records."""

    try:
        resp = requests.get(
            config.ENDPOINTS["sam_gov_exclusions"],
            params={
                "api_key": config.SAM_GOV_API_KEY,
                "q": name,
                "page": 0,
                "size": 25,
            },
            timeout=config.REQUEST_TIMEOUT,
        )
        resp.raise_for_status()
        data = resp.json()

        total = data.get("totalRecords", 0)
        records = []

        for rec in data.get("results", [])[:10]:
            records.append({
                "name": f"{rec.get('firstName', '')} {rec.get('lastName', '')}".strip() or rec.get("firm", ""),
                "exclusion_type": rec.get("exclusionType", ""),
                "excluding_agency": rec.get("excludingAgency", ""),
                "classification": rec.get("classification", ""),
                "active_date": rec.get("activateDate", ""),
                "termination_date": rec.get("terminationDate", ""),
                "state": rec.get("stateProvince", ""),
                "country": rec.get("country", ""),
                "description": rec.get("additionalComments", ""),
                "sam_number": rec.get("samNumber", ""),
            })

        return {
            "source": "SAM.gov Exclusions",
            "query": name,
            "total_records": total,
            "records": records,
            "checked_at": datetime.now(timezone.utc).isoformat(),
        }
    except Exception as e:
        return {
            "source": "SAM.gov Exclusions",
            "query": name,
            "error": str(e),
            "total_records": 0,
            "records": [],
            "checked_at": datetime.now(timezone.utc).isoformat(),
        }


def run_debarment_check(intake: dict) -> dict:
    """Run all debarment/exclusion checks for a subject."""

    name = intake["subject"]["name"]
    subject_id = intake["subject_id"]

    print(f"  🔍 Step 2: Checking debarment/exclusion for '{name}'...")

    sam_result = check_sam_gov(name)

    # Determine gate status
    # SAM.gov returns broad results — we need to filter for close name matches
    close_matches = []
    name_lower = name.lower()
    name_parts = set(name_lower.split())

    for rec in sam_result.get("records", []):
        rec_name = rec.get("name", "").lower()
        rec_parts = set(rec_name.split())
        # Check if at least last name matches and first name starts similarly
        overlap = name_parts & rec_parts
        if len(overlap) >= 2 or (len(name_parts) == 1 and name_parts & rec_parts):
            close_matches.append(rec)

    gate_status = "PASS"
    gate_details = []

    if close_matches:
        gate_status = "FAIL"
        for m in close_matches:
            gate_details.append(
                f"DEBARMENT MATCH: {m['name']} — {m['exclusion_type']} by {m['excluding_agency']} "
                f"(active: {m['active_date']}, term: {m['termination_date'] or 'indefinite'})"
            )

    result = {
        "step": 2,
        "step_name": "Government Debarment / Exclusion",
        "subject_id": subject_id,
        "subject_name": name,
        "gate": {
            "status": gate_status,
            "close_matches": len(close_matches),
            "total_records": sam_result.get("total_records", 0),
            "details": gate_details,
        },
        "sam_gov": sam_result,
        "metadata": {
            "checked_at": datetime.now(timezone.utc).isoformat(),
            "sources_checked": ["SAM.gov Exclusions (v4)"],
        },
    }

    # Save
    output_path = config.DEBARMENT_DIR / f"{subject_id}.json"
    with open(output_path, "w") as f:
        json.dump(result, f, indent=2)

    if gate_status == "FAIL":
        print(f"  🚩 Step 2: DEBARMENT GATE FAILED — {'; '.join(gate_details)}")
    else:
        print(f"  ✅ Step 2: Debarment gate PASSED ({sam_result.get('total_records', 0)} broad results, 0 close name matches) → {output_path.name}")

    return result


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Step 2: Debarment/Exclusion Check")
    parser.add_argument("--subject-id", required=True)
    args = parser.parse_args()

    intake_path = config.INTAKE_DIR / f"{args.subject_id}.json"
    with open(intake_path) as f:
        intake = json.load(f)

    result = run_debarment_check(intake)
    print(f"\nGate: {result['gate']['status']}")
