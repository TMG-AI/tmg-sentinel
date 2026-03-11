"""
Step 9: Bankruptcy Filings Search — CourtListener API
=====================================================
Searches federal bankruptcy court records via CourtListener.
Uses the same API/token as Step 4 (litigation), different search type.

Debtor vs creditor classification:
- Caption heuristic: "In re [Subject]" → debtor (risk)
- /parties/ endpoint: checks party role for debtor/creditor distinction
- Only debtor cases flagged as risk; creditor/other = not a red flag
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

# Max party endpoint checks per run (API cost control)
MAX_PARTY_CHECKS = 20


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


def _name_in_caption(subject_name: str, case_name: str) -> bool:
    """Check if subject name appears in bankruptcy caption."""
    if not case_name or not subject_name:
        return False
    case_lower = case_name.lower()
    skip_words = {"inc", "llc", "ltd", "corp", "co", "the", "and", "of", "a",
                  "corporation", "company", "technologies", "group", "holdings"}
    name_words = [w for w in subject_name.lower().split() if len(w) >= 2 and w not in skip_words]
    if not name_words:
        return False
    matched = sum(1 for w in name_words if w in case_lower)
    return matched >= max(1, len(name_words) * 0.5)


def check_bankruptcy_parties(docket_id: str, subject_name: str) -> dict:
    """Call CourtListener /parties/ endpoint to determine bankruptcy role.
    Returns {"role": "debtor"|"creditor"|"other"|"unknown", "party_name": str}."""
    try:
        resp = requests.get(
            config.ENDPOINTS["courtlistener_parties"],
            params={"docket": docket_id},
            headers={"Authorization": f"Token {config.COURTLISTENER_API_TOKEN}"},
            timeout=config.REQUEST_TIMEOUT,
        )
        resp.raise_for_status()
        data = resp.json()
        results = data.get("results", [])

        skip_words = {"inc", "llc", "ltd", "corp", "co", "the", "and", "of",
                      "corporation", "company", "technologies", "group"}
        name_words = [w for w in subject_name.lower().split() if len(w) >= 2 and w not in skip_words]

        for party in results:
            party_name = (party.get("name") or "").lower()
            if not party_name:
                continue
            matched = sum(1 for w in name_words if w in party_name)
            if matched >= max(1, len(name_words) * 0.5):
                ptype = (party.get("type") or party.get("party_type") or "").lower()
                if "debtor" in ptype:
                    return {"role": "debtor", "party_name": party.get("name", "")}
                elif "creditor" in ptype or "claimant" in ptype:
                    return {"role": "creditor", "party_name": party.get("name", "")}
                else:
                    return {"role": "other", "party_name": party.get("name", "")}

        return {"role": "unknown", "party_name": None}
    except Exception:
        return {"role": "unknown", "party_name": None}


def classify_bankruptcy(case: dict, subject_name: str = "") -> dict:
    """Classify bankruptcy case with debtor/creditor distinction.

    Three-tier role detection:
    1. Caption heuristic: "In re [Subject]" → debtor (red flag)
    2. Caption shows "v." → creditor/claimant (not a red flag)
    3. Ambiguous → check /parties/ endpoint (done in run_bankruptcy_search)
    """
    case_name = (case.get("caseName") or case.get("case_name") or "").lower()
    docket_number = (case.get("docketNumber") or case.get("docket_number") or "").lower()
    snippet = (case.get("snippet") or "").lower()
    combined = f"{case_name} {docket_number} {snippet}"

    chapter = "Unknown"
    for keyword, label in CHAPTER_KEYWORDS.items():
        if keyword in combined:
            chapter = label
            break

    # Debtor/creditor classification via caption heuristics
    role = "unknown"
    role_source = "unclassified"

    # Check 1: "In re [Subject Name]" → subject is the debtor (red flag)
    if subject_name:
        # "In re" or "In the matter of" followed by subject name
        in_re_patterns = ["in re:", "in re ", "in the matter of"]
        for pattern in in_re_patterns:
            if pattern in case_name:
                # Extract what comes after "In re"
                after_re = case_name.split(pattern, 1)[1].strip() if pattern in case_name else ""
                if _name_in_caption(subject_name, after_re):
                    role = "debtor"
                    role_source = "caption_in_re"
                    break

    # Check 2: Subject in case_name but NOT after "In re" → likely creditor or other party
    if role == "unknown" and subject_name and _name_in_caption(subject_name, case_name):
        if "v." in case_name:
            role = "creditor"
            role_source = "caption_adversary"
        else:
            role = "other"
            role_source = "caption_other"

    # Check 3: Text-level hints (lower confidence)
    # IMPORTANT: Only flag as possible_debtor if the subject name also appears
    # in the case_name. Otherwise "Desktop Metal, Inc., Debtor" would falsely
    # tag Anduril as a debtor when Anduril is just mentioned in docket text.
    if role == "unknown":
        subject_in_caption = _name_in_caption(subject_name, case_name) if subject_name else False
        if "debtor" in combined and subject_in_caption:
            role = "possible_debtor"
            role_source = "text_hint"
        elif ("creditor" in combined or "claim" in combined) and subject_in_caption:
            role = "creditor"
            role_source = "text_hint"
        elif not subject_in_caption:
            # Subject only appears in docket text, not caption — treat as mention-only noise
            role = "mention_only"
            role_source = "text_search_only"

    # is_risk: only debtor/possible_debtor is a risk signal
    is_risk = role in ("debtor", "possible_debtor")

    return {
        "chapter": chapter,
        "role": role,
        "role_source": role_source,
        "is_risk": is_risk,
    }


def run_bankruptcy_search(intake: dict) -> dict:
    """Run bankruptcy search for a subject."""

    name = intake["subject"]["name"]
    subject_id = intake["subject_id"]

    print(f"  🔍 Step 9: Searching bankruptcy filings for '{name}'...")

    # Search bankruptcy courts
    results = search_bankruptcy(name)

    total_count = results.get("count", 0)

    # Process results with debtor/creditor classification
    filings = []
    party_checks_done = 0

    for case in results.get("results", []):
        classification = classify_bankruptcy(case, subject_name=name)

        # For ambiguous roles ("unknown"), try /parties/ endpoint
        if classification["role"] == "unknown" and party_checks_done < MAX_PARTY_CHECKS:
            docket_id = case.get("docket_id") or case.get("id")
            if docket_id:
                time.sleep(config.REQUEST_DELAY)
                party_info = check_bankruptcy_parties(str(docket_id), name)
                party_checks_done += 1
                if party_info["role"] != "unknown":
                    classification["role"] = party_info["role"]
                    classification["role_source"] = "parties_endpoint"
                    classification["is_risk"] = classification["role"] in ("debtor", "possible_debtor")

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
            "role_source": classification["role_source"],
            "is_risk": classification["is_risk"],
        }
        filings.append(filing)

    if party_checks_done > 0:
        print(f"    Party endpoint checks: {party_checks_done} dockets verified")

    # Separate risk filings (debtor) from non-risk (creditor/other)
    debtor_filings = [f for f in filings if f["is_risk"]]
    creditor_filings = [f for f in filings if f["role"] == "creditor"]
    other_filings = [f for f in filings if not f["is_risk"] and f["role"] != "creditor"]

    result = {
        "step": 9,
        "step_name": "Bankruptcy Filings",
        "subject_id": subject_id,
        "subject_name": name,
        "summary": {
            "total_results": total_count,
            "filings_reviewed": len(filings),
            "debtor_filings": len(debtor_filings),
            "creditor_filings": len(creditor_filings),
            "other_filings": len(other_filings),
            "party_checks_performed": party_checks_done,
        },
        "debtor_filings": debtor_filings,
        "creditor_filings": creditor_filings,
        "filings": filings,
        "metadata": {
            "checked_at": datetime.now(timezone.utc).isoformat(),
            "source": "CourtListener RECAP (Bankruptcy Courts)",
            "note": "Debtor/creditor classified: only debtor filings (subject filed for bankruptcy) flagged as risk. Creditor filings (someone owes subject money) are not a risk signal.",
        },
    }

    # Save
    output_path = config.BANKRUPTCY_DIR / f"{subject_id}.json"
    with open(output_path, "w") as f:
        json.dump(result, f, indent=2)

    role_text = f" ({len(debtor_filings)} debtor=RISK, {len(creditor_filings)} creditor=OK, {len(other_filings)} other)"
    print(f"  ✅ Step 9: {total_count} bankruptcy results, {len(filings)} reviewed{role_text} → {output_path.name}")

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
