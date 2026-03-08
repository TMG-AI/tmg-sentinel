"""
Step 14: Government Contracts Search — USAspending.gov
=====================================================
Searches federal contract awards and IDVs (indefinite delivery vehicles)
for the subject company. No API key required.

Only meaningful for organizations, but will also check if an individual's
company has government contracts.
"""

import json
import sys
import os
import time
import requests
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config

USASPENDING_BASE = "https://api.usaspending.gov"
SPENDING_BY_AWARD = f"{USASPENDING_BASE}/api/v2/search/spending_by_award/"

# Award type code groups (cannot mix groups in a single request)
CONTRACT_CODES = ["A", "B", "C", "D"]
IDV_CODES = ["IDV_A", "IDV_B", "IDV_B_A", "IDV_B_B", "IDV_B_C", "IDV_C", "IDV_D", "IDV_E"]

FIELDS = [
    "Award ID",
    "Recipient Name",
    "Award Amount",
    "Total Outlays",
    "Description",
    "Start Date",
    "End Date",
    "Last Modified Date",
    "Awarding Agency",
    "Awarding Sub Agency",
    "Contract Award Type",
]

MAX_PAGES = 10  # Cap at 10 pages × 100 = 1000 results


def search_awards(company_name: str, award_type_codes: list, label: str) -> dict:
    """Search USAspending.gov for awards matching a company name."""
    all_results = []
    page = 1
    total_count = 0

    while page <= MAX_PAGES:
        try:
            payload = {
                "filters": {
                    "recipient_search_text": [company_name],
                    "award_type_codes": award_type_codes,
                    "time_period": [
                        {"start_date": "2007-10-01", "end_date": datetime.now().strftime("%Y-%m-%d")}
                    ],
                },
                "fields": FIELDS,
                "limit": 100,
                "page": page,
                "sort": "Award Amount",
                "order": "desc",
                "subawards": False,
            }

            resp = requests.post(
                SPENDING_BY_AWARD,
                json=payload,
                timeout=config.REQUEST_TIMEOUT,
            )
            resp.raise_for_status()
            data = resp.json()

            results = data.get("results", [])
            page_meta = data.get("page_metadata", {})

            for r in results:
                all_results.append({
                    "award_id": r.get("Award ID", ""),
                    "recipient_name": r.get("Recipient Name", ""),
                    "award_amount": r.get("Award Amount", 0),
                    "total_outlays": r.get("Total Outlays", 0),
                    "description": (r.get("Description", "") or "")[:300],
                    "start_date": r.get("Start Date", ""),
                    "end_date": r.get("End Date", ""),
                    "awarding_agency": r.get("Awarding Agency", ""),
                    "awarding_sub_agency": r.get("Awarding Sub Agency", ""),
                    "contract_type": r.get("Contract Award Type", ""),
                })

            if not page_meta.get("hasNext", False):
                break

            page += 1
            time.sleep(config.REQUEST_DELAY)

        except Exception as e:
            print(f"    {label} page {page} error: {e}")
            break

    # Aggregate by agency
    agencies = {}
    total_amount = 0
    for r in all_results:
        amt = r.get("award_amount", 0) or 0
        total_amount += amt
        agency = r.get("awarding_agency", "Unknown")
        if agency not in agencies:
            agencies[agency] = {"total": 0, "count": 0}
        agencies[agency]["total"] += amt
        agencies[agency]["count"] += 1

    top_agencies = sorted(agencies.items(), key=lambda x: x[1]["total"], reverse=True)

    return {
        "label": label,
        "total_results": len(all_results),
        "total_amount": total_amount,
        "top_agencies": [
            {"agency": a[0], "total": a[1]["total"], "count": a[1]["count"]}
            for a in top_agencies[:15]
        ],
        "awards": all_results,  # Full list, sorted by amount desc
    }


def run_contracts_search(intake: dict) -> dict:
    """Run government contracts search."""

    subject = intake["subject"]
    name = subject["name"]
    company = subject.get("company") or name
    subject_id = intake["subject_id"]
    subject_type = subject.get("type", "individual")

    # For individuals, search their company name
    search_name = company if subject_type == "individual" else name

    if not search_name or search_name == "N/A":
        print(f"  ⏭️  Step 14: Skipping contracts search (no company name)")
        result = {
            "step": 14,
            "step_name": "Government Contracts",
            "subject_id": subject_id,
            "skipped": True,
            "reason": "No company name to search",
            "metadata": {"checked_at": datetime.now(timezone.utc).isoformat()},
        }
        output_path = config.CONTRACTS_DIR / f"{subject_id}.json"
        with open(output_path, "w") as f:
            json.dump(result, f, indent=2)
        return result

    print(f"  🔍 Step 14: Searching government contracts for '{search_name}'...")

    # Search contracts (definitive contracts, delivery orders, etc.)
    contracts = search_awards(search_name, CONTRACT_CODES, "Contracts")
    time.sleep(config.REQUEST_DELAY)

    # Search IDVs (blanket purchase agreements, GWAC, etc.)
    idvs = search_awards(search_name, IDV_CODES, "IDVs")

    # Combined stats
    total_awards = contracts["total_results"] + idvs["total_results"]
    total_amount = contracts["total_amount"] + idvs["total_amount"]

    # Merge top agencies across both
    all_agency_map = {}
    for item in contracts.get("top_agencies", []) + idvs.get("top_agencies", []):
        agency = item["agency"]
        if agency not in all_agency_map:
            all_agency_map[agency] = {"total": 0, "count": 0}
        all_agency_map[agency]["total"] += item["total"]
        all_agency_map[agency]["count"] += item["count"]
    combined_agencies = sorted(all_agency_map.items(), key=lambda x: x[1]["total"], reverse=True)

    # Top 20 contracts by amount for the synthesis prompt
    all_awards = contracts.get("awards", []) + idvs.get("awards", [])
    all_awards.sort(key=lambda x: x.get("award_amount", 0) or 0, reverse=True)
    top_awards = all_awards[:20]

    result = {
        "step": 14,
        "step_name": "Government Contracts",
        "subject_id": subject_id,
        "subject_name": name,
        "search_name": search_name,
        "summary": {
            "total_awards": total_awards,
            "total_amount": total_amount,
            "total_contracts": contracts["total_results"],
            "total_idvs": idvs["total_results"],
            "contracts_amount": contracts["total_amount"],
            "idvs_amount": idvs["total_amount"],
            "agencies_count": len(all_agency_map),
        },
        "top_agencies": [
            {"agency": a[0], "total": a[1]["total"], "count": a[1]["count"]}
            for a in combined_agencies[:15]
        ],
        "top_awards": top_awards,
        "contracts": contracts,
        "idvs": idvs,
        "metadata": {
            "checked_at": datetime.now(timezone.utc).isoformat(),
            "source": "USAspending.gov API",
            "note": "No API key required. Data from 2007-10-01 to present.",
        },
    }

    output_path = config.CONTRACTS_DIR / f"{subject_id}.json"
    with open(output_path, "w") as f:
        json.dump(result, f, indent=2)

    print(f"  ✅ Step 14: {total_awards} awards, ${total_amount:,.0f} total across {len(all_agency_map)} agencies → {output_path.name}")

    return result


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Step 14: Government Contracts Search")
    parser.add_argument("--subject-id", required=True)
    args = parser.parse_args()

    intake_path = config.INTAKE_DIR / f"{args.subject_id}.json"
    with open(intake_path) as f:
        intake = json.load(f)

    run_contracts_search(intake)
