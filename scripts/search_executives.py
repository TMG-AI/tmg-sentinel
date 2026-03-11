"""
Step 11: Executive Identification & Mini-Vet (Organizations Only)
=================================================================
When vetting a company, identifies top executives via SEC EDGAR Form 3/4
filings, then runs mini due diligence on each: FEC donations, targeted
news search, and sanctions screening.

For private/non-SEC companies, falls back to Tavily web search + Claude
extraction of executive names from search results.

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

def lookup_cik(company_name: str) -> tuple:
    """Look up CIK number for a company using EDGAR full-text search.
    Returns (cik, matched_company_name) or (None, None)."""
    try:
        resp = requests.get(
            config.ENDPOINTS["sec_efts_search"],
            params={
                "q": f'"{company_name}"',
                "forms": "10-K",
                "from": 0,
                "size": 3,  # Get a few results to check for best match
            },
            headers={"User-Agent": config.SEC_EDGAR_USER_AGENT},
            timeout=config.REQUEST_TIMEOUT,
        )
        resp.raise_for_status()
        data = resp.json()

        hits = data.get("hits", {}).get("hits", [])
        if not hits:
            return None, None

        # Check each hit for a company name match
        search_lower = company_name.lower().strip()
        search_words = set(w for w in search_lower.split() if len(w) >= 3 and w not in ("inc", "llc", "ltd", "corp", "the", "and", "corporation", "company", "technologies"))

        for hit in hits:
            source = hit.get("_source", {})
            entity_name = (source.get("entity_name", "") or source.get("display_names", [""])[0]).lower().strip()
            entity_words = set(w for w in entity_name.split() if len(w) >= 3 and w not in ("inc", "llc", "ltd", "corp", "the", "and", "corporation", "company", "technologies"))

            # Require at least one significant word overlap
            overlap = search_words & entity_words
            if overlap and len(overlap) >= min(len(search_words), len(entity_words)) * 0.5:
                ciks = source.get("ciks", [])
                if ciks:
                    matched_name = source.get("entity_name", "") or source.get("display_names", [""])[0]
                    return str(ciks[0]), matched_name

        # No good match found
        first_name = hits[0].get("_source", {}).get("entity_name", "Unknown")
        print(f"    EDGAR match rejected: searched '{company_name}', best match was '{first_name}' — not similar enough")
        return None, None

    except Exception as e:
        print(f"    CIK lookup error: {e}")
    return None, None


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

    cik, matched_name = lookup_cik(company_name)
    if not cik:
        print(f"    No CIK found for '{company_name}' — will use Tavily fallback")
        return []

    print(f"    Found CIK: {cik} (matched: {matched_name})")
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


# ─── SEC Form D: Find Executives for Private Issuers ──────────

def identify_executives_form_d(company_name: str) -> list:
    """Search SEC EDGAR for Form D filings (Reg D exempt offerings).
    Private companies raising capital often file Form D, which lists
    executive officers, directors, and related persons."""
    print(f"    Searching SEC EDGAR Form D for '{company_name}'...")
    try:
        resp = requests.get(
            config.ENDPOINTS["sec_efts_search"],
            params={
                "q": f'"{company_name}"',
                "forms": "D",
                "from": 0,
                "size": 5,
            },
            headers={"User-Agent": config.SEC_EDGAR_USER_AGENT},
            timeout=config.REQUEST_TIMEOUT,
        )
        resp.raise_for_status()
        data = resp.json()

        hits = data.get("hits", {}).get("hits", [])
        if not hits:
            print(f"    No Form D filings found for '{company_name}'")
            return []

        # Verify company name match (same logic as lookup_cik)
        search_lower = company_name.lower().strip()
        skip = {"inc", "llc", "ltd", "corp", "the", "and", "corporation", "company", "technologies"}
        search_words = set(w for w in search_lower.split() if len(w) >= 3 and w not in skip)

        matched_hit = None
        for hit in hits:
            source = hit.get("_source", {})
            entity_name = (source.get("entity_name", "") or source.get("display_names", [""])[0]).lower().strip()
            entity_words = set(w for w in entity_name.split() if len(w) >= 3 and w not in skip)
            overlap = search_words & entity_words
            if overlap and len(overlap) >= min(len(search_words), len(entity_words)) * 0.5:
                matched_hit = hit
                break

        if not matched_hit:
            print(f"    Form D results don't match '{company_name}'")
            return []

        # Get the filing to parse for related persons
        source = matched_hit.get("_source", {})
        file_url = source.get("file_url", "")
        if not file_url:
            return []

        # Form D filings are XML — fetch and parse for related persons
        time.sleep(0.15)  # SEC rate limit
        xml_resp = requests.get(
            f"https://www.sec.gov{file_url}" if file_url.startswith("/") else file_url,
            headers={"User-Agent": config.SEC_EDGAR_USER_AGENT},
            timeout=config.REQUEST_TIMEOUT,
        )
        xml_resp.raise_for_status()

        # Parse Form D XML for relatedPersonsList
        root = ET.fromstring(xml_resp.text)
        ns = ""
        if root.tag.startswith("{"):
            ns = root.tag.split("}")[0] + "}"

        executives = []
        for person in root.findall(f".//{ns}relatedPersonInfo"):
            name_el = person.find(f"{ns}relatedPersonName")
            rel_el = person.find(f"{ns}relatedPersonRelationshipList")

            if name_el is None:
                continue

            first = (name_el.find(f"{ns}firstName") or name_el.find("firstName"))
            last = (name_el.find(f"{ns}lastName") or name_el.find("lastName"))
            first_text = (first.text or "").strip() if first is not None else ""
            last_text = (last.text or "").strip() if last is not None else ""

            if not last_text:
                continue

            full_name = f"{first_text} {last_text}".strip()

            # Parse relationships
            is_director = False
            is_officer = False
            is_promoter = False
            relationships = []
            if rel_el is not None:
                for rel in rel_el:
                    tag = rel.tag.replace(ns, "")
                    if rel.text and rel.text.strip():
                        relationships.append(tag)
                    if "Director" in tag:
                        is_director = True
                    elif "Officer" in tag or "Executive" in tag:
                        is_officer = True
                    elif "Promoter" in tag:
                        is_promoter = True

            executives.append({
                "name": full_name,
                "is_director": is_director,
                "is_officer": is_officer,
                "is_ten_percent_owner": is_promoter,
                "officer_title": ", ".join(relationships) if relationships else "Related Person",
                "source": "SEC Form D",
            })

        if executives:
            print(f"    Found {len(executives)} related persons from Form D filing")
        else:
            print(f"    Form D filing found but no related persons extracted")

        return executives

    except Exception as e:
        print(f"    Form D search error: {e}")
        return []


# ─── Tavily Fallback: Find Executives via Web Search ──────────

def identify_executives_tavily(company_name: str) -> list:
    """Identify executives via Tavily web search + Claude extraction.
    For private companies not in SEC EDGAR."""
    print(f"    Searching web for executives of '{company_name}'...")

    queries = [
        f'"{company_name}" CEO founder leadership team executives',
        f'"{company_name}" CFO CTO COO president board directors',
        f'"{company_name}" executive team Crunchbase OR LinkedIn OR Bloomberg',
        f'"{company_name}" co-founder chief officer general counsel VP',
        f'"{company_name}" leadership management team bios about',
    ]

    all_content = []
    raw_results = []
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
            results = data.get("results", [])
            raw_results.extend(results)
            for r in results:
                content = r.get("content", "") or ""
                title = r.get("title", "") or ""
                all_content.append(f"{title}\n{content}")
            time.sleep(config.REQUEST_DELAY)
        except Exception as e:
            print(f"    Tavily search error: {e}")

    if not all_content:
        print(f"    No web results found for executives")
        return []

    print(f"    Found {len(raw_results)} web results, extracting executive names with Claude...")

    # Use Claude to extract structured executive names from search results
    try:
        import anthropic
        client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)

        combined_text = "\n---\n".join(all_content[:10])  # Cap at 10 results

        extraction_prompt = f"""From the following web search results about {company_name}, extract ALL individuals who hold any of these roles:

- C-suite executives (CEO, CFO, CTO, COO, CMO, CRO, CISO, CLO, etc.)
- Founders and co-founders
- President and Vice Presidents (SVP, EVP)
- Board members and board chairman
- General Counsel
- General Partners (if a fund/partnership)
- Other named senior officers or key decision-makers

IMPORTANT: Do NOT limit to just the most prominent person. Extract EVERY person mentioned in any of these roles, even if they appear in only one search result. Aim for 5-10 people for a typical company.

Return ONLY a JSON array. Each element should have "name" (full name, natural order like "John Smith") and "title" (their most senior role). Maximum 15 executives. Most senior first.

If you cannot confidently identify any executives, return an empty array [].

Search results:
{combined_text}

Return ONLY the JSON array, no other text."""

        response = client.messages.create(
            model="claude-sonnet-4-20250514",  # Fast + cheap for extraction
            max_tokens=1000,
            messages=[{"role": "user", "content": extraction_prompt}],
        )

        response_text = response.content[0].text.strip()

        # Parse JSON from response (handle markdown code blocks)
        if "```" in response_text:
            json_match = re.search(r'```(?:json)?\s*(\[.*?\])\s*```', response_text, re.DOTALL)
            if json_match:
                response_text = json_match.group(1)

        extracted = json.loads(response_text)

        if not isinstance(extracted, list):
            extracted = []

        # Convert to standard exec format
        executives = []
        for item in extracted[:10]:
            name = item.get("name", "").strip()
            title = item.get("title", "").strip()
            if name:
                executives.append({
                    "name": name,
                    "is_director": any(w in title.lower() for w in ["director", "board", "chairman"]),
                    "is_officer": any(w in title.lower() for w in ["ceo", "cfo", "cto", "coo", "president", "chief", "officer", "founder"]),
                    "is_ten_percent_owner": "founder" in title.lower(),
                    "officer_title": title,
                    "source": "Tavily + Claude extraction",
                })

        print(f"    Extracted {len(executives)} executives from web results")
        return executives

    except Exception as e:
        print(f"    Claude extraction failed: {e}")
        # Return empty — synthesis will work without exec data
        return []


# ─── Mini-Vet: FEC + News + Sanctions for Each Executive ──────

def mini_vet_fec(name: str, company_name: str = None) -> dict:
    """Quick FEC search for an individual executive.
    When company_name is provided, filters by contributor_employer to avoid
    false positives from common names."""
    try:
        params = {
            "api_key": config.FEC_API_KEY,
            "contributor_name": name,
            "sort": "-contribution_receipt_amount",
            "per_page": 20,
            "is_individual": True,
        }
        if company_name:
            params["contributor_employer"] = company_name
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
    # Tavily-extracted names are already in natural order
    if executive.get("source") == "Tavily + Claude extraction":
        display_name = name  # Already in natural order
    elif "," in name:
        # "Cohen, Stephen Andrew" → "Stephen Andrew Cohen"
        last, rest = name.split(",", 1)
        display_name = f"{rest.strip()} {last.strip()}"
    else:
        parts = name.split()
        if len(parts) >= 2 and parts[0].isupper() and len(parts[0]) > 1:
            # "THIEL PETER" or "Cohen Stephen Andrew" → "Peter Thiel"
            display_name = " ".join(parts[1:]) + " " + parts[0]
            display_name = display_name.strip().title()
        else:
            display_name = name

    result = dict(executive)
    result["display_name"] = display_name

    # FEC donations (use company_name as employer filter to avoid false positives)
    fec = mini_vet_fec(name, company_name=company_name)
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

    # Try SEC EDGAR Form 3/4 first (public companies)
    executives = identify_executives_edgar(name)
    identification_source = "SEC EDGAR Form 3/4"

    if not executives:
        # Try SEC Form D (private companies that raised capital)
        executives = identify_executives_form_d(name)
        identification_source = "SEC Form D"

    if not executives:
        # Final fallback: Tavily + Claude for companies with no SEC filings
        executives = identify_executives_tavily(name)
        identification_source = "Tavily + Claude extraction"
        if executives:
            print(f"    Using Tavily + Claude extraction for executive identification")
        else:
            print(f"    WARNING: Could not identify executives via EDGAR, Form D, or Tavily")

    # Mini-vet the top executives (cap at 8 to manage API costs)
    MAX_EXEC_VET = 8
    vetted_executives = []

    if executives:
        to_vet = executives[:MAX_EXEC_VET]
        print(f"  🔍 Mini-vetting top {len(to_vet)} executives (FEC, news, sanctions)...")

        for i, exec_info in enumerate(to_vet):
            exec_name = exec_info.get("name", "Unknown")
            title = exec_info.get("officer_title", "")
            role = title or ("Director" if exec_info.get("is_director") else "Executive")
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
    print(f"  ✅ Step 11: {len(executives)} executives found ({identification_source}), {len(vetted_executives)} vetted, ${total_donations:,.0f} in FEC donations → {output_path.name}")

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
