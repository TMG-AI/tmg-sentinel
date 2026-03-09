"""
Step 11: Executive Identification & Mini-Vet (Organizations Only)
=================================================================
When vetting a company, identifies top executives via SEC EDGAR Form 3/4
filings, then runs mini due diligence on each: FEC donations, targeted
news search, and sanctions screening.

For private/non-SEC companies, falls back to Tavily web search.

Only runs when subject_type == "organization".
"""

import json
import sys
import os
import time
import re
import requests
import xml.etree.ElementTree as ET
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config
from config_tavily import get_tavily_params


# ─── SEC EDGAR: Find Executives via Form 3/4 ──────────────────

def lookup_cik(company_name: str) -> str:
    """Look up CIK number for a company using EDGAR full-text search."""
    try:
        resp = requests.get(
            config.ENDPOINTS["sec_efts_search"],
            params={
                "q": f'"{company_name}"',
                "forms": "10-K",
                "from": 0,
                "size": 1,
            },
            headers={"User-Agent": config.SEC_EDGAR_USER_AGENT},
            timeout=config.REQUEST_TIMEOUT,
        )
        resp.raise_for_status()
        data = resp.json()

        hits = data.get("hits", {}).get("hits", [])
        if hits:
            ciks = hits[0].get("_source", {}).get("ciks", [])
            if ciks:
                return str(ciks[0])
    except Exception as e:
        print(f"    CIK lookup error: {e}")
    return None


def get_form3_filings(cik: str, max_filings: int = 30) -> list:
    """Get recent Form 3 (initial ownership) and Form 4 filings from EDGAR submissions."""
    try:
        cik_padded = cik.zfill(10)
        resp = requests.get(
            f"{config.ENDPOINTS['sec_edgar_submissions']}CIK{cik_padded}.json",
            headers={"User-Agent": config.SEC_EDGAR_USER_AGENT},
            timeout=config.REQUEST_TIMEOUT,
        )
        resp.raise_for_status()
        data = resp.json()

        filings = data.get("filings", {}).get("recent", {})
        forms = filings.get("form", [])
        accessions = filings.get("accessionNumber", [])
        dates = filings.get("filingDate", [])
        primary_docs = filings.get("primaryDocument", [])

        # Collect Form 3 and Form 4 filings (ownership statements list officers/directors)
        form3_4 = []
        for i, form_type in enumerate(forms):
            if form_type in ("3", "4") and i < len(accessions):
                form3_4.append({
                    "form": form_type,
                    "accession": accessions[i],
                    "date": dates[i] if i < len(dates) else "",
                    "primary_doc": primary_docs[i] if i < len(primary_docs) else "",
                })
                if len(form3_4) >= max_filings:
                    break

        return form3_4
    except Exception as e:
        print(f"    Form 3/4 lookup error: {e}")
        return []


def parse_ownership_xml(cik: str, accession: str) -> dict:
    """Fetch and parse a Form 3/4 XML filing to extract officer info."""
    try:
        # Convert accession to path format (remove dashes for directory)
        acc_nodash = accession.replace("-", "")

        # Get the filing index to find the XML file
        index_url = f"https://www.sec.gov/Archives/edgar/data/{cik}/{acc_nodash}/{accession}-index.htm"
        resp = requests.get(
            index_url,
            headers={"User-Agent": config.SEC_EDGAR_USER_AGENT},
            timeout=config.REQUEST_TIMEOUT,
        )
        resp.raise_for_status()

        # Find XML link in the index page
        xml_pattern = r'href="(/Archives/edgar/data/[^"]+\.xml)"'
        matches = re.findall(xml_pattern, resp.text)

        # Filter out XSL-rendered versions (paths containing 'xsl')
        # and pick the raw ownership XML
        xml_paths = [m for m in matches if "xsl" not in m.lower()]
        if not xml_paths:
            return None

        # Fetch the actual XML
        xml_url = f"https://www.sec.gov{xml_paths[0]}"
        xml_resp = requests.get(
            xml_url,
            headers={"User-Agent": config.SEC_EDGAR_USER_AGENT},
            timeout=config.REQUEST_TIMEOUT,
        )
        xml_resp.raise_for_status()

        # Parse XML
        root = ET.fromstring(xml_resp.text)

        # Handle namespace
        ns = ""
        if root.tag.startswith("{"):
            ns = root.tag.split("}")[0] + "}"

        owner_el = root.find(f".//{ns}reportingOwner")
        if owner_el is None:
            return None

        name_el = owner_el.find(f".//{ns}rptOwnerName")
        rel_el = owner_el.find(f".//{ns}reportingOwnerRelationship")

        if name_el is None:
            return None

        owner_name = name_el.text or ""

        # Parse relationship flags
        is_director = False
        is_officer = False
        is_ten_pct = False
        officer_title = ""

        if rel_el is not None:
            dir_el = rel_el.find(f"{ns}isDirector")
            off_el = rel_el.find(f"{ns}isOfficer")
            ten_el = rel_el.find(f"{ns}isTenPercentOwner")
            title_el = rel_el.find(f"{ns}officerTitle")

            is_director = dir_el is not None and (dir_el.text or "").strip().lower() in ("1", "true")
            is_officer = off_el is not None and (off_el.text or "").strip().lower() in ("1", "true")
            is_ten_pct = ten_el is not None and (ten_el.text or "").strip().lower() in ("1", "true")
            officer_title = (title_el.text or "").strip() if title_el is not None else ""

        return {
            "name": owner_name,
            "is_director": is_director,
            "is_officer": is_officer,
            "is_ten_percent_owner": is_ten_pct,
            "officer_title": officer_title,
        }

    except Exception as e:
        # Silently skip problematic filings
        return None


def identify_executives_edgar(company_name: str) -> list:
    """Identify executives using SEC EDGAR Form 3/4 filings."""
    print(f"    Searching SEC EDGAR for executives of '{company_name}'...")

    cik = lookup_cik(company_name)
    if not cik:
        print(f"    No CIK found for '{company_name}' — will use Tavily fallback")
        return []

    print(f"    Found CIK: {cik}")
    time.sleep(0.15)  # SEC rate limit: 10 req/sec

    filings = get_form3_filings(cik, max_filings=30)
    if not filings:
        print(f"    No Form 3/4 filings found")
        return []

    print(f"    Found {len(filings)} Form 3/4 filings, parsing...")

    # Parse each filing for officer/director info
    executives = {}  # name -> best info
    for filing in filings:
        time.sleep(0.12)  # SEC rate limit
        info = parse_ownership_xml(cik, filing["accession"])
        if info and info["name"]:
            name = info["name"]
            # Skip the company itself appearing as a filer
            name_lower = name.lower()
            if any(skip in name_lower for skip in ["inc.", "inc", "llc", "corp", "ltd", "l.p.", "technologies"]):
                continue
            # Keep the most informative entry for each person
            if name not in executives or (info["officer_title"] and not executives[name].get("officer_title")):
                executives[name] = {
                    "name": name,
                    "is_director": info["is_director"],
                    "is_officer": info["is_officer"],
                    "is_ten_percent_owner": info["is_ten_percent_owner"],
                    "officer_title": info["officer_title"],
                    "source": "SEC EDGAR Form 3/4",
                    "filing_date": filing["date"],
                }
            else:
                # Merge flags (might be director in one filing, officer in another)
                if info["is_director"]:
                    executives[name]["is_director"] = True
                if info["is_officer"]:
                    executives[name]["is_officer"] = True
                if info["is_ten_percent_owner"]:
                    executives[name]["is_ten_percent_owner"] = True
                if info["officer_title"] and not executives[name]["officer_title"]:
                    executives[name]["officer_title"] = info["officer_title"]

    exec_list = list(executives.values())

    # Sort: officers first (by title importance), then directors, then 10% owners
    def sort_key(e):
        title = (e.get("officer_title") or "").lower()
        # Skip "see remarks" — treat as generic officer/director
        if title == "see remarks":
            title = ""
        if "chief executive" in title or "ceo" in title:
            return 0
        if "president" in title and "vice" not in title:
            return 1
        if "chief financial" in title or "cfo" in title:
            return 2
        if "chief operating" in title or "coo" in title:
            return 3
        if "chief technology" in title or "cto" in title:
            return 4
        if "general counsel" in title:
            return 5
        if title and e.get("is_officer"):
            return 6  # Named officer with a specific title
        if e.get("is_officer") and e.get("is_director"):
            return 7  # Officer+director but no title
        if e.get("is_officer"):
            return 8
        if e.get("is_director"):
            return 9
        if e.get("is_ten_percent_owner"):
            return 10
        return 11

    exec_list.sort(key=sort_key)
    print(f"    Identified {len(exec_list)} executives/directors from EDGAR")
    return exec_list


# ─── Tavily Fallback: Find Executives via Web Search ──────────

def identify_executives_tavily(company_name: str) -> list:
    """Identify executives via Tavily web search (fallback for private companies)."""
    print(f"    Searching web for executives of '{company_name}'...")

    queries = [
        f'"{company_name}" CEO CFO CTO executive leadership team',
        f'"{company_name}" board of directors officers',
    ]

    all_results = []
    for query in queries:
        try:
            params = get_tavily_params("news_basic", query)
            params["api_key"] = config.TAVILY_API_KEY
            resp = requests.post(
                config.ENDPOINTS["tavily_search"],
                json=params,
                timeout=30,
            )
            resp.raise_for_status()
            data = resp.json()
            all_results.extend(data.get("results", []))
            time.sleep(config.REQUEST_DELAY)
        except Exception as e:
            print(f"    Tavily search error: {e}")

    # We can't parse structured executive data from web results,
    # but we return the raw results for the synthesis prompt to interpret
    if all_results:
        print(f"    Found {len(all_results)} web results about executives")

    return [{
        "source": "Tavily web search",
        "results": [
            {
                "title": r.get("title", ""),
                "url": r.get("url", ""),
                "content": (r.get("content", "") or "")[:500],
            }
            for r in all_results[:10]
        ],
    }]


# ─── Mini-Vet: FEC + News + Sanctions for Each Executive ──────

def mini_vet_fec(name: str) -> dict:
    """Quick FEC search for an individual executive."""
    try:
        params = {
            "api_key": config.FEC_API_KEY,
            "contributor_name": name,
            "sort": "-contribution_receipt_date",
            "per_page": 20,
            "is_individual": True,
        }
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
                "committee_name": rec.get("committee", {}).get("name", "") if isinstance(rec.get("committee"), dict) else rec.get("committee_name", ""),
                "amount": rec.get("contribution_receipt_amount", 0),
                "date": rec.get("contribution_receipt_date", ""),
            })

        total_amount = sum(c["amount"] for c in contributions if c["amount"])
        # Aggregate by recipient
        recipients = {}
        for c in contributions:
            recip = c.get("committee_name", "Unknown")
            if recip not in recipients:
                recipients[recip] = {"total": 0, "count": 0}
            recipients[recip]["total"] += c.get("amount", 0)
            recipients[recip]["count"] += 1

        top = sorted(recipients.items(), key=lambda x: x[1]["total"], reverse=True)[:10]

        return {
            "total_results": total,
            "total_amount": total_amount,
            "top_recipients": [{"name": r[0], "total": r[1]["total"], "count": r[1]["count"]} for r in top],
            "contributions": contributions[:10],
        }
    except Exception as e:
        return {"error": str(e), "total_results": 0, "contributions": []}


def mini_vet_news(name: str, company_name: str) -> dict:
    """Quick news search for an executive. Filters results to only those mentioning the exec."""
    try:
        # Extract last name and first name for filtering
        name_parts = name.strip().split()
        last_name = name_parts[-1].lower() if name_parts else ""
        first_name = name_parts[0].lower() if name_parts else ""

        query = f'"{name}" {company_name} controversy OR scandal OR lawsuit OR investigation'
        params = get_tavily_params("news_basic", query)
        params["api_key"] = config.TAVILY_API_KEY
        resp = requests.post(
            config.ENDPOINTS["tavily_search"],
            json=params,
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()

        all_results = data.get("results", [])

        # Filter: only keep results where the exec's name actually appears
        # in the title or content (not just company-level news)
        filtered = []
        for r in all_results:
            text = (r.get("title", "") + " " + (r.get("content", "") or "")).lower()
            if last_name and first_name and (last_name in text and first_name in text):
                filtered.append(r)

        return {
            "total_results": len(filtered),
            "answer": data.get("answer", ""),
            "results": [
                {
                    "title": r.get("title", ""),
                    "url": r.get("url", ""),
                    "content": (r.get("content", "") or "")[:400],
                    "score": r.get("score", 0),
                }
                for r in filtered[:5]
            ],
        }
    except Exception as e:
        return {"error": str(e), "total_results": 0, "results": []}


def mini_vet_sanctions(name: str) -> dict:
    """Quick sanctions check for an executive."""
    try:
        resp = requests.post(
            config.ENDPOINTS["opensanctions_match"],
            json={
                "queries": {
                    "exec": {
                        "schema": "Person",
                        "properties": {
                            "name": [name],
                        },
                    }
                }
            },
            headers={
                "Authorization": f"ApiKey {config.OPENSANCTIONS_API_KEY}",
            },
            timeout=config.REQUEST_TIMEOUT,
        )
        resp.raise_for_status()
        data = resp.json()

        results = data.get("responses", {}).get("exec", {}).get("results", [])
        matches = [r for r in results if r.get("score", 0) >= 0.7]

        return {
            "matches_found": len(matches),
            "matches": [
                {
                    "name": m.get("caption", ""),
                    "score": m.get("score", 0),
                    "datasets": m.get("datasets", []),
                }
                for m in matches[:5]
            ],
        }
    except Exception as e:
        return {"error": str(e), "matches_found": 0, "matches": []}


def run_mini_vet(executive: dict, company_name: str) -> dict:
    """Run mini due diligence on a single executive."""
    name = executive.get("name", "")
    if not name:
        return executive

    # Normalize name from EDGAR format to natural order for news/sanctions queries
    # EDGAR uses "LAST FIRST MIDDLE" or "Last, First Middle"
    if "," in name:
        # "Cohen, Stephen Andrew" → "Stephen Andrew Cohen"
        last, rest = name.split(",", 1)
        display_name = f"{rest.strip()} {last.strip()}"
    else:
        parts = name.split()
        if len(parts) >= 2 and parts[0].isupper() and len(parts[0]) > 1:
            # "THIEL PETER" or "Cohen Stephen Andrew" → "Stephen Andrew Cohen" / "Peter Thiel"
            display_name = " ".join(parts[1:]) + " " + parts[0]
            display_name = display_name.strip().title()
        else:
            display_name = name

    result = dict(executive)
    result["display_name"] = display_name

    # FEC donations
    fec = mini_vet_fec(name)
    result["fec"] = fec
    time.sleep(config.REQUEST_DELAY)

    # News search
    news = mini_vet_news(display_name, company_name)
    result["news"] = news
    time.sleep(config.REQUEST_DELAY)

    # Sanctions
    sanctions = mini_vet_sanctions(display_name)
    result["sanctions"] = sanctions
    time.sleep(config.REQUEST_DELAY)

    return result


# ─── Main Step Runner ──────────────────────────────────────────

def run_executive_search(intake: dict) -> dict:
    """Step 11: Identify executives and run mini due diligence."""

    subject = intake["subject"]
    name = subject["name"]
    subject_id = intake["subject_id"]
    subject_type = subject.get("type", "individual")

    # Only run for organizations
    if subject_type != "organization":
        print(f"  ⏭️  Step 11: Skipping executive search (subject is {subject_type}, not organization)")
        result = {
            "step": 11,
            "step_name": "Executive Identification & Mini-Vet",
            "subject_id": subject_id,
            "skipped": True,
            "reason": f"Subject type is '{subject_type}', not 'organization'",
            "metadata": {"checked_at": datetime.now(timezone.utc).isoformat()},
        }
        output_path = config.EXECUTIVES_DIR / f"{subject_id}.json"
        with open(output_path, "w") as f:
            json.dump(result, f, indent=2)
        return result

    print(f"  🔍 Step 11: Identifying executives for '{name}'...")

    # Try SEC EDGAR first (public companies)
    executives = identify_executives_edgar(name)
    identification_source = "SEC EDGAR Form 3/4"
    tavily_fallback = None

    if not executives:
        # Fallback to Tavily for private companies
        tavily_fallback = identify_executives_tavily(name)
        identification_source = "Tavily web search"
        print(f"    Using Tavily fallback for executive identification")

    # Mini-vet the top executives (cap at 8 to manage API costs)
    MAX_EXEC_VET = 8
    vetted_executives = []

    if executives:
        to_vet = executives[:MAX_EXEC_VET]
        print(f"  🔍 Mini-vetting top {len(to_vet)} executives (FEC, news, sanctions)...")

        for i, exec_info in enumerate(to_vet):
            exec_name = exec_info.get("name", "Unknown")
            title = exec_info.get("officer_title", "")
            role = title or ("Director" if exec_info.get("is_director") else "10%+ Owner")
            print(f"    [{i+1}/{len(to_vet)}] {exec_name} — {role}")

            vetted = run_mini_vet(exec_info, name)
            vetted_executives.append(vetted)

    result = {
        "step": 11,
        "step_name": "Executive Identification & Mini-Vet",
        "subject_id": subject_id,
        "subject_name": name,
        "identification_source": identification_source,
        "summary": {
            "total_executives_found": len(executives),
            "executives_vetted": len(vetted_executives),
            "total_fec_contributions": sum(
                e.get("fec", {}).get("total_amount", 0) for e in vetted_executives
            ),
            "sanctions_flags": sum(
                1 for e in vetted_executives if e.get("sanctions", {}).get("matches_found", 0) > 0
            ),
            "news_flags": sum(
                1 for e in vetted_executives if e.get("news", {}).get("total_results", 0) > 0
            ),
        },
        "executives": vetted_executives,
        "all_identified": [
            {
                "name": e.get("name", ""),
                "officer_title": e.get("officer_title", ""),
                "is_director": e.get("is_director", False),
                "is_officer": e.get("is_officer", False),
            }
            for e in executives
        ],
        "tavily_fallback": tavily_fallback,
        "metadata": {
            "checked_at": datetime.now(timezone.utc).isoformat(),
            "source": identification_source,
            "max_executives_vetted": MAX_EXEC_VET,
        },
    }

    output_path = config.EXECUTIVES_DIR / f"{subject_id}.json"
    with open(output_path, "w") as f:
        json.dump(result, f, indent=2)

    total_donations = result["summary"]["total_fec_contributions"]
    print(f"  ✅ Step 11: {len(executives)} executives found, {len(vetted_executives)} vetted, ${total_donations:,.0f} in FEC donations → {output_path.name}")

    return result


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Step 11: Executive Identification & Mini-Vet")
    parser.add_argument("--subject-id", required=True)
    args = parser.parse_args()

    intake_path = config.INTAKE_DIR / f"{args.subject_id}.json"
    with open(intake_path) as f:
        intake = json.load(f)

    run_executive_search(intake)
