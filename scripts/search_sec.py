"""
Step 7: SEC Filings / Financial Disclosures
============================================
API: SEC EDGAR Full-Text Search (EFTS)
Searches all SEC filings since 2001 for mentions of the subject.
Focuses on enforcement actions, 8-K material events, insider trading (Form 4).
"""

import json
import sys
import os
import time
import requests
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config

# High-risk form types
ENFORCEMENT_FORMS = ["LIT-REL", "AAER"]  # Litigation releases, Accounting & Auditing Enforcement
INSIDER_FORMS = ["4", "3", "5"]  # Insider trading reports
MATERIAL_FORMS = ["8-K", "8-K/A"]  # Material event disclosures
REGISTRATION_FORMS = ["S-1", "S-1/A", "10-K", "10-Q", "DEF 14A"]


def search_sec_efts(name: str, forms: str = None, size: int = 15) -> dict:
    """Full-text search across all SEC filings."""
    try:
        params = {
            "q": f'"{name}"',
            "from": 0,
            "size": size,
        }
        if forms:
            params["forms"] = forms

        resp = requests.get(
            config.ENDPOINTS["sec_efts_search"],
            params=params,
            headers={"User-Agent": config.SEC_EDGAR_USER_AGENT},
            timeout=config.REQUEST_TIMEOUT,
        )
        resp.raise_for_status()
        data = resp.json()

        total = data.get("hits", {}).get("total", {}).get("value", 0)
        filings = []
        for hit in data.get("hits", {}).get("hits", []):
            src = hit.get("_source", {})
            filings.append({
                "company": ", ".join(src.get("display_names", [])),
                "form_type": src.get("form_type", ""),
                "file_date": src.get("file_date", ""),
                "description": src.get("file_description", ""),
                "period_of_report": src.get("period_of_report", ""),
            })

        return {"total": total, "filings": filings}
    except Exception as e:
        return {"error": str(e), "total": 0, "filings": []}


def run_sec_search(intake: dict) -> dict:
    """Run SEC filings search."""

    name = intake["subject"]["name"]
    company = intake["subject"].get("company") or ""
    subject_id = intake["subject_id"]

    print(f"  🔍 Step 7: Searching SEC filings for '{name}'...")

    # General search
    general = search_sec_efts(name)
    time.sleep(config.REQUEST_DELAY)

    # Enforcement-specific search
    enforcement = search_sec_efts(name, forms="LIT-REL,AAER", size=10)
    time.sleep(config.REQUEST_DELAY)

    # Insider trading (Form 4)
    insider = search_sec_efts(name, forms="4,3,5", size=10)

    # Company-specific if provided
    company_filings = {"total": 0, "filings": []}
    if company:
        time.sleep(config.REQUEST_DELAY)
        company_filings = search_sec_efts(company, forms="10-K,8-K,DEF 14A", size=10)

    # Flag enforcement actions
    red_flags = []
    if enforcement.get("total", 0) > 0:
        for f in enforcement.get("filings", []):
            red_flags.append({
                "type": "SEC Enforcement",
                "form": f["form_type"],
                "company": f["company"],
                "date": f["file_date"],
                "description": f["description"],
            })

    result = {
        "step": 7,
        "step_name": "SEC Filings / Financial Disclosures",
        "subject_id": subject_id,
        "subject_name": name,
        "summary": {
            "total_filings": general.get("total", 0),
            "enforcement_actions": enforcement.get("total", 0),
            "insider_trading_filings": insider.get("total", 0),
            "company_filings": company_filings.get("total", 0),
            "red_flags": len(red_flags),
        },
        "red_flags": red_flags,
        "general_filings": general,
        "enforcement": enforcement,
        "insider_trading": insider,
        "company_filings": company_filings,
        "metadata": {
            "checked_at": datetime.now(timezone.utc).isoformat(),
            "source": "SEC EDGAR EFTS (Full-Text Search)",
        },
    }

    output_path = config.SEC_DIR / f"{subject_id}.json"
    with open(output_path, "w") as f:
        json.dump(result, f, indent=2)

    flag_text = f" 🚩 {len(red_flags)} enforcement action(s)" if red_flags else ""
    print(f"  ✅ Step 7: {general.get('total', 0)} filings, {insider.get('total', 0)} insider forms{flag_text} → {output_path.name}")

    return result


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Step 7: SEC Filings Search")
    parser.add_argument("--subject-id", required=True)
    args = parser.parse_args()

    intake_path = config.INTAKE_DIR / f"{args.subject_id}.json"
    with open(intake_path) as f:
        intake = json.load(f)

    run_sec_search(intake)
