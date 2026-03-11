"""
Step 4: Court Records / Litigation Search — CourtListener RECAP API
===================================================================
Searches federal court records for litigation involving the subject.
Flags: criminal cases, fraud/corruption, repeated civil litigation.

Party-level filtering: Uses case_name as first-pass filter, then
CourtListener /parties/ endpoint to verify subject is a named party
(plaintiff/defendant) — not just mentioned in docket text.
"""

import json
import sys
import os
import time
import re
import requests
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config

# Keywords that indicate high-risk litigation
CRIMINAL_KEYWORDS = ["criminal", "indictment", "united states v.", "people v."]
FRAUD_KEYWORDS = ["fraud", "corrupt", "embezzl", "money launder", "brib", "racketeer", "rico"]
REGULATORY_KEYWORDS = ["sec v.", "ftc v.", "enforcement", "securities", "violation"]


# Max pages to paginate through (safety cap)
MAX_PAGES = 25  # 25 pages × 20 results = up to 500 results

# Max dockets to verify via /parties/ endpoint (API cost control)
MAX_PARTY_CHECKS = 30


def search_courtlistener(name: str, search_type: str = "r") -> dict:
    """
    Search CourtListener RECAP archive with full pagination.
    search_type: 'r' = RECAP (dockets), 'o' = opinions, 'p' = people
    """
    all_results = []
    total_count = 0
    page = 1

    try:
        while page <= MAX_PAGES:
            resp = requests.get(
                config.ENDPOINTS["courtlistener_search"],
                params={
                    "q": f'"{name}"',
                    "type": search_type,
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


def _name_in_case_name(subject_name: str, case_name: str) -> bool:
    """Check if subject appears in the case caption (e.g. 'X v. Anduril Industries').
    Uses fuzzy word matching — requires at least half of the significant words to match."""
    if not case_name or not subject_name:
        return False
    case_lower = case_name.lower()
    # Split subject name into significant words (skip short/common words)
    skip_words = {"inc", "llc", "ltd", "corp", "co", "the", "and", "of", "a", "an",
                  "corporation", "company", "technologies", "group", "holdings", "lp"}
    name_words = [w for w in subject_name.lower().split() if len(w) >= 2 and w not in skip_words]
    if not name_words:
        return False
    matched = sum(1 for w in name_words if w in case_lower)
    return matched >= max(1, len(name_words) * 0.5)


def check_parties_endpoint(docket_id: str, subject_name: str) -> dict:
    """Call CourtListener /parties/ endpoint to check if subject is a named party.
    Returns {"is_party": bool, "party_type": str or None, "party_name": str or None}."""
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
                party_type = party.get("type") or party.get("party_type") or ""
                return {
                    "is_party": True,
                    "party_type": party_type,
                    "party_name": party.get("name", ""),
                }
        return {"is_party": False, "party_type": None, "party_name": None}
    except Exception as e:
        # If parties endpoint fails, don't block — return unknown
        return {"is_party": None, "party_type": None, "party_name": None, "error": str(e)}


def classify_party_match(case: dict, subject_name: str) -> str:
    """Determine if subject is a named party vs just mentioned in docket text.
    Returns: 'named_party' (in case_name), 'party_verified' (confirmed via /parties/),
             'mention_only' (only in full-text), 'unknown' (couldn't determine)."""
    case_name = case.get("caseName") or case.get("case_name") or ""

    # First pass: check case_name (caption)
    if _name_in_case_name(subject_name, case_name):
        return "named_party"

    # If not in caption, it's either in docket text only (mention) or
    # we need the /parties/ endpoint to confirm.
    # We return "mention_only" here — the caller can optionally upgrade
    # to "party_verified" via check_parties_endpoint for ambiguous high-risk cases.
    return "mention_only"


def classify_case(case: dict) -> dict:
    """Classify a case by risk level based on keywords."""
    case_name = (case.get("caseName") or case.get("case_name") or "").lower()
    docket_number = (case.get("docketNumber") or case.get("docket_number") or "").lower()
    court = (case.get("court") or case.get("court_id") or "").lower()
    snippet = (case.get("snippet") or "").lower()
    combined = f"{case_name} {docket_number} {court} {snippet}"

    flags = []
    risk_level = "low"

    # Check criminal
    if any(kw in combined for kw in CRIMINAL_KEYWORDS):
        flags.append("criminal")
        risk_level = "critical"

    # Check fraud/corruption
    if any(kw in combined for kw in FRAUD_KEYWORDS):
        flags.append("fraud_corruption")
        risk_level = "high" if risk_level != "critical" else risk_level

    # Check regulatory enforcement
    if any(kw in combined for kw in REGULATORY_KEYWORDS):
        flags.append("regulatory_enforcement")
        risk_level = "high" if risk_level not in ["critical", "high"] else risk_level

    # If named as defendant
    if " v. " in case_name:
        parts = case_name.split(" v. ")
        if len(parts) == 2:
            # Subject is likely defendant if their name appears after "v."
            defendant_side = parts[1]
            name_parts = case.get("_search_name", "").lower().split()
            if any(p in defendant_side for p in name_parts if len(p) > 2):
                flags.append("named_defendant")

    return {
        "flags": flags,
        "risk_level": risk_level,
    }


def run_litigation_search(intake: dict) -> dict:
    """Run litigation search for a subject."""

    name = intake["subject"]["name"]
    subject_id = intake["subject_id"]

    print(f"  🔍 Step 4: Searching court records for '{name}'...")

    # Search RECAP dockets
    docket_results = search_courtlistener(name, search_type="r")
    time.sleep(config.REQUEST_DELAY)

    # Search opinions
    opinion_results = search_courtlistener(name, search_type="o")

    docket_count = docket_results.get("count", 0)
    opinion_count = opinion_results.get("count", 0)

    # Process and classify docket results with party-level filtering
    cases = []
    party_cases = []      # Cases where subject is a named party
    mention_cases = []    # Cases where subject is only mentioned in text
    red_flags = []
    yellow_flags = []
    party_checks_done = 0

    for case in docket_results.get("results", []):
        case["_search_name"] = name
        classification = classify_case(case)
        party_match = classify_party_match(case, name)

        # For high-risk "mention_only" cases, try the /parties/ endpoint
        # to see if subject is actually a named party
        if party_match == "mention_only" and classification["risk_level"] in ["critical", "high"]:
            if party_checks_done < MAX_PARTY_CHECKS:
                docket_id = case.get("docket_id") or case.get("id")
                if docket_id:
                    time.sleep(config.REQUEST_DELAY)
                    party_info = check_parties_endpoint(str(docket_id), name)
                    party_checks_done += 1
                    if party_info.get("is_party"):
                        party_match = "party_verified"
                        if party_info.get("party_type"):
                            classification["flags"].append(f"party_role:{party_info['party_type']}")

        case_record = {
            "case_name": case.get("caseName") or case.get("case_name", ""),
            "docket_number": case.get("docketNumber") or case.get("docket_number", ""),
            "court": case.get("court") or case.get("court_id", ""),
            "date_filed": case.get("dateFiled") or case.get("date_filed", ""),
            "date_terminated": case.get("dateTerminated") or case.get("date_terminated", ""),
            "snippet": (case.get("snippet") or "")[:300],
            "url": f"https://www.courtlistener.com{case.get('absolute_url', '')}",
            "classification": classification,
            "party_match": party_match,
        }
        cases.append(case_record)

        if party_match in ("named_party", "party_verified"):
            party_cases.append(case_record)
        else:
            mention_cases.append(case_record)

        # Only count as red/yellow flags if subject is a named party
        if party_match in ("named_party", "party_verified"):
            if classification["risk_level"] in ["critical", "high"]:
                red_flags.append({
                    "case_name": case_record["case_name"],
                    "risk_level": classification["risk_level"],
                    "flags": classification["flags"],
                    "court": case_record["court"],
                    "date_filed": case_record["date_filed"],
                    "party_match": party_match,
                })
            elif classification["flags"]:
                yellow_flags.append({
                    "case_name": case_record["case_name"],
                    "risk_level": classification["risk_level"],
                    "flags": classification["flags"],
                    "party_match": party_match,
                })

    if party_checks_done > 0:
        print(f"    Party endpoint checks: {party_checks_done} dockets verified")

    # Process opinions (all paginated results)
    opinions = []
    for op in opinion_results.get("results", []):
        opinions.append({
            "case_name": op.get("caseName") or op.get("case_name", ""),
            "court": op.get("court") or op.get("court_id", ""),
            "date_filed": op.get("dateFiled") or op.get("date_filed", ""),
            "snippet": (op.get("snippet") or "")[:300],
            "url": f"https://www.courtlistener.com{op.get('absolute_url', '')}",
        })

    result = {
        "step": 4,
        "step_name": "Court Records / Litigation",
        "subject_id": subject_id,
        "subject_name": name,
        "summary": {
            "total_dockets": docket_count,
            "total_opinions": opinion_count,
            "cases_reviewed": len(cases),
            "party_cases": len(party_cases),
            "mention_only_cases": len(mention_cases),
            "red_flags": len(red_flags),
            "yellow_flags": len(yellow_flags),
            "party_checks_performed": party_checks_done,
        },
        "red_flags": red_flags,
        "yellow_flags": yellow_flags,
        "party_cases": party_cases,
        "mention_only_cases": mention_cases,
        "cases": cases,
        "opinions": opinions,
        "metadata": {
            "checked_at": datetime.now(timezone.utc).isoformat(),
            "source": "CourtListener RECAP",
            "note": "Party-filtered: only cases where subject is a named party (plaintiff/defendant) are flagged. Mention-only cases preserved but not scored.",
        },
    }

    # Save
    output_path = config.LITIGATION_DIR / f"{subject_id}.json"
    with open(output_path, "w") as f:
        json.dump(result, f, indent=2)

    flag_text = ""
    if red_flags:
        flag_text = f" 🚩 {len(red_flags)} RED FLAG(S): {', '.join(rf['flags'][0] for rf in red_flags[:3])}"
    elif yellow_flags:
        flag_text = f" ⚠️ {len(yellow_flags)} yellow flag(s)"

    party_text = f" ({len(party_cases)} as party, {len(mention_cases)} mention-only)"
    print(f"  ✅ Step 4: {docket_count} dockets{party_text}, {opinion_count} opinions{flag_text} → {output_path.name}")

    return result


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Step 4: Litigation Search")
    parser.add_argument("--subject-id", required=True)
    args = parser.parse_args()

    intake_path = config.INTAKE_DIR / f"{args.subject_id}.json"
    with open(intake_path) as f:
        intake = json.load(f)

    result = run_litigation_search(intake)
    print(f"\nDockets: {result['summary']['total_dockets']}, Red flags: {result['summary']['red_flags']}")
