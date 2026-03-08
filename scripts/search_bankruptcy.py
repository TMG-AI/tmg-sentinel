"""
Step 9: Bankruptcy Filings Search — CourtListener API
=====================================================
Searches federal bankruptcy court records via CourtListener.
Uses the same API/token as Step 4 (litigation), different search type.
"""

import json
import sys
import os
import time
import requests
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config


# Bankruptcy chapter indicators
CHAPTER_KEYWORDS = {
    "chapter 7": "Chapter 7 (Liquidation)",
    "chapter 11": "Chapter 11 (Reorganization)",
    "chapter 13": "Chapter 13 (Individual Repayment Plan)",
    "chapter 15": "Chapter 15 (Cross-Border Insolvency)",
}


BANKRUPTCY_COURTS = "almb,almd,alnb,alnd,alsb,alsd,arb,are,arw,azb,azd,cab,cacd,caeb,caed,canb,cand,casb,casd,cob,cod,ctb,ctd,dcb,dcd,deb,ded,flmb,flmd,flnb,flnd,flsb,flsd,gamb,gamd,ganb,gand,gasb,gasd,gub,gud,hib,hid,iab,ian,ias,idb,idd,ilab,ilcd,ileb,iled,ilnb,ilnd,ilsb,ilsd,innb,innd,insb,insd,ksb,ksd,kyeb,kyed,kywb,kywd,laeb,laed,lamb,lamd,lawb,lawd,mab,mad,mdb,mdd,meab,med,mieb,mied,miwb,miwd,mnb,mnd,moeb,moed,mowb,mowd,msb,msnb,msnd,mssb,mssd,mtb,mtd,nceb,nced,ncmb,ncmd,ncwb,ncwd,ndb,ndd,neb,ned,nhb,nhd,njb,njd,nmb,nmd,nvb,nvd,nyeb,nyed,nynb,nynd,nysb,nysd,nywb,nywd,ohab,ohnd,ohnb,ohsb,ohsd,okeb,oked,oknb,oknd,okwb,okwd,orb,ord,paeb,paed,pamb,pamd,pawb,pawd,prib,prid,rib,rid,scb,scd,sdb,sdd,tneb,tned,tnmb,tnmd,tnwb,tnwd,txeb,txed,txnb,txnd,txsb,txsd,txwb,txwd,utb,utd,vab,vaed,vawb,vawd,vib,vid,vtb,vtd,waeb,waed,wawb,wawd,wvnb,wvnd,wvsb,wvsd,wieb,wied,wiwb,wiwd,wyb,wyd"

# Max pages to paginate through (safety cap)
MAX_PAGES = 25  # 25 pages × 20 results = up to 500 results


def search_bankruptcy(name: str) -> dict:
    """Search CourtListener for bankruptcy filings with full pagination."""
    all_results = []
    total_count = 0
    page = 1

    try:
        while page <= MAX_PAGES:
            resp = requests.get(
                config.ENDPOINTS["courtlistener_bankruptcy"],
                params={
                    "q": f'"{name}"',
                    "type": "r",  # RECAP dockets
                    "court": BANKRUPTCY_COURTS,
                    "page_size": 20,
                    "order_by": "score desc",
                    "page": page,
                },
                headers={
                    "Authorization": f"Token {config.COURTLISTENER_API_TOKEN}",
                },
                timeout=45,  # CourtListener pagination needs longer than default
            )
            resp.raise_for_status()
            data = resp.json()

            if page == 1:
                total_count = data.get("count", 0)

            results = data.get("results", [])
            if not results:
                break

            all_results.extend(results)

            # Check if there's a next page
            if not data.get("next"):
                break

            page += 1
            time.sleep(config.REQUEST_DELAY)

        print(f"    Paginated: {len(all_results)} results fetched across {page} page(s) (total in index: {total_count})")
        return {"count": total_count, "results": all_results}

    except Exception as e:
        # Return whatever we collected before the error
        if all_results:
            print(f"    Pagination stopped on page {page}: {e} (collected {len(all_results)} so far)")
            return {"count": total_count, "results": all_results}
        return {"error": str(e), "count": 0, "results": []}


def classify_bankruptcy(case: dict) -> dict:
    """Classify bankruptcy case details."""
    case_name = (case.get("caseName") or case.get("case_name") or "").lower()
    docket_number = (case.get("docketNumber") or case.get("docket_number") or "").lower()
    snippet = (case.get("snippet") or "").lower()
    combined = f"{case_name} {docket_number} {snippet}"

    chapter = "Unknown"
    for keyword, label in CHAPTER_KEYWORDS.items():
        if keyword in combined:
            chapter = label
            break

    # Check if subject is debtor (petitioner) vs creditor
    role = "unknown"
    if "debtor" in combined or "in re:" in case_name or "in the matter of" in case_name:
        role = "debtor"
    elif "creditor" in combined or "v." in case_name:
        role = "creditor"

    return {
        "chapter": chapter,
        "role": role,
    }


def run_bankruptcy_search(intake: dict) -> dict:
    """Run bankruptcy search for a subject."""

    name = intake["subject"]["name"]
    subject_id = intake["subject_id"]

    print(f"  🔍 Step 9: Searching bankruptcy filings for '{name}'...")

    # Search bankruptcy courts
    results = search_bankruptcy(name)

    total_count = results.get("count", 0)

    # Process results
    filings = []
    for case in results.get("results", []):
        classification = classify_bankruptcy(case)
        filing = {
            "case_name": case.get("caseName") or case.get("case_name", ""),
            "docket_number": case.get("docketNumber") or case.get("docket_number", ""),
            "court": case.get("court") or case.get("court_id", ""),
            "date_filed": case.get("dateFiled") or case.get("date_filed", ""),
            "date_terminated": case.get("dateTerminated") or case.get("date_terminated", ""),
            "snippet": (case.get("snippet") or "")[:300],
            "url": f"https://www.courtlistener.com{case.get('absolute_url', '')}",
            "chapter": classification["chapter"],
            "role": classification["role"],
        }
        filings.append(filing)

    # Identify debtor filings (higher risk)
    debtor_filings = [f for f in filings if f["role"] == "debtor"]

    result = {
        "step": 9,
        "step_name": "Bankruptcy Filings",
        "subject_id": subject_id,
        "subject_name": name,
        "summary": {
            "total_results": total_count,
            "filings_reviewed": len(filings),
            "debtor_filings": len(debtor_filings),
        },
        "filings": filings,
        "debtor_filings": debtor_filings,
        "metadata": {
            "checked_at": datetime.now(timezone.utc).isoformat(),
            "source": "CourtListener RECAP (Bankruptcy Courts)",
            "note": "Federal bankruptcy courts only.",
        },
    }

    # Save
    output_path = config.BANKRUPTCY_DIR / f"{subject_id}.json"
    with open(output_path, "w") as f:
        json.dump(result, f, indent=2)

    debtor_note = f" ({len(debtor_filings)} as debtor)" if debtor_filings else ""
    print(f"  ✅ Step 9: {total_count} bankruptcy results, {len(filings)} reviewed{debtor_note} → {output_path.name}")

    return result


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Step 9: Bankruptcy Filings Search")
    parser.add_argument("--subject-id", required=True)
    args = parser.parse_args()

    intake_path = config.INTAKE_DIR / f"{args.subject_id}.json"
    with open(intake_path) as f:
        intake = json.load(f)

    result = run_bankruptcy_search(intake)
    print(f"\nTotal results: {result['summary']['total_results']}, Debtor filings: {result['summary']['debtor_filings']}")
