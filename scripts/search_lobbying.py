"""
Step 8: Lobbying Disclosures — Senate LDA API
==============================================
Searches lobbying disclosure filings for the subject or their company.
"""

import json
import sys
import os
import time
import requests
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config


def search_lda_filings(query: str) -> dict:
    """Search Senate LDA for lobbying filings."""
    try:
        resp = requests.get(
            config.ENDPOINTS["senate_lda_filings"],
            params={
                "search": query,
                "page_size": 20,
                "ordering": "-dt_posted",
            },
            headers={
                "Authorization": f"Token {config.LDA_API_KEY}",
                "Accept": "application/json",
            },
            timeout=config.REQUEST_TIMEOUT,
        )
        resp.raise_for_status()
        data = resp.json()

        total = data.get("count", 0)
        filings = []
        for f in data.get("results", [])[:20]:
            filing = {
                "filing_type": f.get("filing_type_display", ""),
                "registrant_name": f.get("registrant", {}).get("name", "") if isinstance(f.get("registrant"), dict) else str(f.get("registrant", "")),
                "client_name": f.get("client", {}).get("name", "") if isinstance(f.get("client"), dict) else str(f.get("client", "")),
                "income": f.get("income", ""),
                "expenses": f.get("expenses", ""),
                "filing_year": f.get("filing_year", ""),
                "filing_period": f.get("filing_period_display", ""),
                "posted_date": f.get("dt_posted", ""),
                "lobbying_activities": [],
            }

            # Extract lobbying activities/issues
            for activity in f.get("lobbying_activities", [])[:5]:
                filing["lobbying_activities"].append({
                    "general_issue": activity.get("general_issue_code_display", ""),
                    "description": (activity.get("description") or "")[:200],
                    "lobbyists": [
                        lb.get("lobbyist", {}).get("name", "") if isinstance(lb.get("lobbyist"), dict) else ""
                        for lb in activity.get("lobbyists", [])[:3]
                    ],
                })

            filings.append(filing)

        return {"source": "Senate LDA", "total": total, "filings": filings}
    except Exception as e:
        return {"source": "Senate LDA", "error": str(e), "total": 0, "filings": []}


def run_lobbying_search(intake: dict) -> dict:
    """Run lobbying disclosure search."""

    name = intake["subject"]["name"]
    company = intake["subject"].get("company") or ""
    subject_id = intake["subject_id"]

    print(f"  🔍 Step 8: Searching lobbying disclosures for '{name}'...")

    # Search by person name
    person_results = search_lda_filings(name)
    time.sleep(config.REQUEST_DELAY)

    # Search by company if provided
    company_results = {"source": "Senate LDA (company)", "total": 0, "filings": []}
    if company:
        company_results = search_lda_filings(company)
        company_results["source"] = "Senate LDA (company)"

    # Combine unique filings
    all_filings = person_results.get("filings", []) + company_results.get("filings", [])

    # Extract unique registrants and clients
    registrants = set()
    clients = set()
    for f in all_filings:
        if f.get("registrant_name"):
            registrants.add(f["registrant_name"])
        if f.get("client_name"):
            clients.add(f["client_name"])

    result = {
        "step": 8,
        "step_name": "Lobbying Disclosures",
        "subject_id": subject_id,
        "subject_name": name,
        "summary": {
            "person_filings": person_results.get("total", 0),
            "company_filings": company_results.get("total", 0),
            "unique_registrants": len(registrants),
            "unique_clients": len(clients),
        },
        "person_results": person_results,
        "company_results": company_results,
        "unique_registrants": sorted(list(registrants)),
        "unique_clients": sorted(list(clients)),
        "metadata": {
            "checked_at": datetime.now(timezone.utc).isoformat(),
            "source": "Senate LDA API (lda.senate.gov)",
            "note": "LDA API migrating to LDA.gov after June 30, 2026.",
        },
    }

    output_path = config.LOBBYING_DIR / f"{subject_id}.json"
    with open(output_path, "w") as f:
        json.dump(result, f, indent=2)

    total = person_results.get("total", 0) + company_results.get("total", 0)
    print(f"  ✅ Step 8: {total} lobbying filings, {len(registrants)} registrants, {len(clients)} clients → {output_path.name}")

    return result


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Step 8: Lobbying Disclosures Search")
    parser.add_argument("--subject-id", required=True)
    args = parser.parse_args()

    intake_path = config.INTAKE_DIR / f"{args.subject_id}.json"
    with open(intake_path) as f:
        intake = json.load(f)

    run_lobbying_search(intake)
