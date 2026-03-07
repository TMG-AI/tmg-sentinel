"""
Step 5: Corporate Filings / Business Registrations
===================================================
APIs: SEC EDGAR Company Search, GLEIF LEI Registry
Identifies corporate affiliations, officer roles, entity structures.
"""

import json
import sys
import os
import time
import requests
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config


def search_sec_edgar_company(name: str) -> dict:
    """Search SEC EDGAR for company filings by name."""
    try:
        resp = requests.get(
            config.ENDPOINTS["sec_edgar_company"],
            params={
                "q": f'"{name}"',
                "forms": "10-K,10-Q,8-K,DEF 14A,S-1,4",
                "from": 0,
                "size": 15,
            },
            headers={"User-Agent": config.SEC_EDGAR_USER_AGENT},
            timeout=config.REQUEST_TIMEOUT,
        )
        resp.raise_for_status()
        data = resp.json()

        total = data.get("hits", {}).get("total", {}).get("value", 0)
        hits = []
        for hit in data.get("hits", {}).get("hits", [])[:15]:
            src = hit.get("_source", {})
            hits.append({
                "company_name": ", ".join(src.get("display_names", [])),
                "form_type": src.get("form_type", ""),
                "file_date": src.get("file_date", ""),
                "file_description": src.get("file_description", ""),
                "file_url": f"https://www.sec.gov/Archives/edgar/data/{src.get('file_num', '')}" if src.get("file_num") else "",
                "display_date_dt": src.get("file_date", ""),
            })

        return {"source": "SEC EDGAR", "total": total, "filings": hits}
    except Exception as e:
        return {"source": "SEC EDGAR", "error": str(e), "total": 0, "filings": []}


def search_gleif(name: str) -> dict:
    """Search GLEIF LEI registry for legal entities."""
    try:
        resp = requests.get(
            config.ENDPOINTS["gleif_lei"],
            params={
                "filter[entity.legalName]": name,
                "page[size]": 10,
            },
            headers={"Accept": "application/vnd.api+json"},
            timeout=config.REQUEST_TIMEOUT,
        )
        resp.raise_for_status()
        data = resp.json()

        entities = []
        for rec in data.get("data", []):
            attrs = rec.get("attributes", {})
            entity = attrs.get("entity", {})
            entities.append({
                "lei": attrs.get("lei", ""),
                "legal_name": entity.get("legalName", {}).get("name", ""),
                "jurisdiction": entity.get("jurisdiction", ""),
                "status": entity.get("status", ""),
                "category": entity.get("category", ""),
                "legal_address": {
                    "city": entity.get("legalAddress", {}).get("city", ""),
                    "country": entity.get("legalAddress", {}).get("country", ""),
                },
                "registration_status": attrs.get("registration", {}).get("status", ""),
            })

        return {"source": "GLEIF LEI", "total": len(entities), "entities": entities}
    except Exception as e:
        return {"source": "GLEIF LEI", "error": str(e), "total": 0, "entities": []}


def run_corporate_search(intake: dict) -> dict:
    """Run corporate filings search."""

    name = intake["subject"]["name"]
    company = intake["subject"].get("company") or ""
    subject_id = intake["subject_id"]

    print(f"  🔍 Step 5: Searching corporate filings for '{name}'...")

    # Search SEC EDGAR for the person
    edgar_person = search_sec_edgar_company(name)
    time.sleep(config.REQUEST_DELAY)

    # If company provided, search that too
    edgar_company = {"source": "SEC EDGAR (company)", "total": 0, "filings": []}
    if company:
        edgar_company = search_sec_edgar_company(company)
        edgar_company["source"] = "SEC EDGAR (company)"
        time.sleep(config.REQUEST_DELAY)

    # Search GLEIF for company
    gleif_result = {"source": "GLEIF LEI", "total": 0, "entities": []}
    if company:
        gleif_result = search_gleif(company)

    result = {
        "step": 5,
        "step_name": "Corporate Filings / Business Registrations",
        "subject_id": subject_id,
        "subject_name": name,
        "company_searched": company,
        "summary": {
            "edgar_person_filings": edgar_person.get("total", 0),
            "edgar_company_filings": edgar_company.get("total", 0),
            "gleif_entities": gleif_result.get("total", 0),
        },
        "sec_edgar_person": edgar_person,
        "sec_edgar_company": edgar_company,
        "gleif": gleif_result,
        "metadata": {
            "checked_at": datetime.now(timezone.utc).isoformat(),
            "sources": ["SEC EDGAR EFTS", "GLEIF LEI Registry"],
            "note": "State SOS business registrations not included (no unified free API).",
        },
    }

    output_path = config.CORPORATE_DIR / f"{subject_id}.json"
    with open(output_path, "w") as f:
        json.dump(result, f, indent=2)

    total = edgar_person.get("total", 0) + edgar_company.get("total", 0)
    print(f"  ✅ Step 5: {total} EDGAR filings, {gleif_result.get('total', 0)} GLEIF entities → {output_path.name}")

    return result


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Step 5: Corporate Filings Search")
    parser.add_argument("--subject-id", required=True)
    args = parser.parse_args()

    intake_path = config.INTAKE_DIR / f"{args.subject_id}.json"
    with open(intake_path) as f:
        intake = json.load(f)

    run_corporate_search(intake)
