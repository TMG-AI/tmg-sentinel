"""
Step 6: FEC / Campaign Finance Search
======================================
API: OpenFEC (api.open.fec.gov)
Searches campaign contributions by name.
"""

import json
import sys
import os
import time
import requests
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config


def search_individual_contributions(name: str, state: str = None) -> dict:
    """Search FEC for individual contributions by name."""
    try:
        params = {
            "api_key": config.FEC_API_KEY,
            "contributor_name": name,
            "sort": "-contribution_receipt_date",
            "per_page": 20,
            "is_individual": True,
        }
        if state:
            params["contributor_state"] = state

        resp = requests.get(
            config.ENDPOINTS["openfec_receipts"],
            params=params,
            timeout=config.REQUEST_TIMEOUT,
        )
        resp.raise_for_status()
        data = resp.json()

        total = data.get("pagination", {}).get("count", 0)
        contributions = []
        for rec in data.get("results", []):
            contributions.append({
                "contributor_name": rec.get("contributor_name", ""),
                "contributor_state": rec.get("contributor_state", ""),
                "contributor_city": rec.get("contributor_city", ""),
                "contributor_employer": rec.get("contributor_employer", ""),
                "contributor_occupation": rec.get("contributor_occupation", ""),
                "committee_name": rec.get("committee", {}).get("name", "") if isinstance(rec.get("committee"), dict) else rec.get("committee_name", ""),
                "candidate_name": rec.get("candidate_name", ""),
                "amount": rec.get("contribution_receipt_amount", 0),
                "date": rec.get("contribution_receipt_date", ""),
                "receipt_type_description": rec.get("receipt_type_description", ""),
            })

        # Aggregate stats
        total_amount = sum(c["amount"] for c in contributions if c["amount"])
        recipients = {}
        for c in contributions:
            recip = c.get("committee_name") or c.get("candidate_name") or "Unknown"
            if recip not in recipients:
                recipients[recip] = {"total": 0, "count": 0}
            recipients[recip]["total"] += c.get("amount", 0)
            recipients[recip]["count"] += 1

        top_recipients = sorted(recipients.items(), key=lambda x: x[1]["total"], reverse=True)[:10]

        return {
            "source": "OpenFEC",
            "total_results": total,
            "total_amount": total_amount,
            "top_recipients": [{"name": r[0], "total": r[1]["total"], "count": r[1]["count"]} for r in top_recipients],
            "contributions": contributions[:20],
        }
    except Exception as e:
        return {"source": "OpenFEC", "error": str(e), "total_results": 0, "contributions": []}


def search_candidate(name: str) -> dict:
    """Check if the subject themselves is a candidate."""
    try:
        resp = requests.get(
            config.ENDPOINTS["openfec_candidates"],
            params={
                "api_key": config.FEC_API_KEY,
                "q": name,
                "per_page": 5,
            },
            timeout=config.REQUEST_TIMEOUT,
        )
        resp.raise_for_status()
        data = resp.json()

        candidates = []
        for c in data.get("results", []):
            candidates.append({
                "name": c.get("name", ""),
                "party": c.get("party_full", ""),
                "office": c.get("office_full", ""),
                "state": c.get("state", ""),
                "district": c.get("district", ""),
                "candidate_id": c.get("candidate_id", ""),
                "cycles": c.get("cycles", []),
                "active": c.get("candidate_status", "") == "C",
            })

        return {"source": "OpenFEC Candidates", "total": len(candidates), "candidates": candidates}
    except Exception as e:
        return {"source": "OpenFEC Candidates", "error": str(e), "total": 0, "candidates": []}


def run_fec_search(intake: dict) -> dict:
    """Run FEC campaign finance search."""

    name = intake["subject"]["name"]
    subject_id = intake["subject_id"]

    print(f"  🔍 Step 6: Searching FEC campaign finance for '{name}'...")

    contributions = search_individual_contributions(name)
    time.sleep(config.REQUEST_DELAY)
    candidate_check = search_candidate(name)

    result = {
        "step": 6,
        "step_name": "FEC / Campaign Finance",
        "subject_id": subject_id,
        "subject_name": name,
        "summary": {
            "total_contributions": contributions.get("total_results", 0),
            "total_amount": contributions.get("total_amount", 0),
            "top_recipients_count": len(contributions.get("top_recipients", [])),
            "is_candidate": len(candidate_check.get("candidates", [])) > 0,
        },
        "contributions": contributions,
        "candidate_check": candidate_check,
        "metadata": {
            "checked_at": datetime.now(timezone.utc).isoformat(),
            "source": "OpenFEC API",
        },
    }

    output_path = config.FEC_DIR / f"{subject_id}.json"
    with open(output_path, "w") as f:
        json.dump(result, f, indent=2)

    amt = contributions.get("total_amount", 0)
    print(f"  ✅ Step 6: {contributions.get('total_results', 0)} contributions (${amt:,.0f} total) → {output_path.name}")

    return result


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Step 6: FEC Campaign Finance Search")
    parser.add_argument("--subject-id", required=True)
    args = parser.parse_args()

    intake_path = config.INTAKE_DIR / f"{args.subject_id}.json"
    with open(intake_path) as f:
        intake = json.load(f)

    run_fec_search(intake)
