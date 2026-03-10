"""
Step 15: Corporate Network Discovery
======================================
Discovers companies and associates linked to the subject using:
1. OpenCorporates API (if API key available) — structured corporate registry data
2. Tavily fallback — web search for corporate associations, directorships, subsidiaries

This is the "expand the entity universe" strategy recommended by Perplexity
and used by professional due diligence firms (Kroll, Control Risks, Nardello).

The discovered entities are:
- Included in the synthesis prompt so Claude can cross-reference them
- Available for future use as additional search targets
"""

import json
import sys
import os
import time
import requests
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config
from config_tavily import get_tavily_params


# ─── OpenCorporates (when API key is available) ───────────────

def search_opencorporates_companies(name: str, country: str = "") -> list:
    """Search OpenCorporates for companies matching the subject name."""
    params = {"q": name, "per_page": 10}
    if config.OPENCORPORATES_API_KEY:
        params["api_token"] = config.OPENCORPORATES_API_KEY

    jurisdiction = _country_to_jurisdiction(country)
    if jurisdiction:
        params["country_code"] = jurisdiction

    try:
        resp = requests.get(
            config.ENDPOINTS["opencorporates_search"],
            params=params,
            timeout=config.REQUEST_TIMEOUT,
            headers={"User-Agent": "TMG-Vetting-Pipeline/1.0"},
        )
        resp.raise_for_status()
        data = resp.json()

        companies = []
        for item in data.get("results", {}).get("companies", []):
            c = item.get("company", {})
            companies.append({
                "name": c.get("name", ""),
                "company_number": c.get("company_number", ""),
                "jurisdiction_code": c.get("jurisdiction_code", ""),
                "incorporation_date": c.get("incorporation_date", ""),
                "dissolution_date": c.get("dissolution_date", ""),
                "company_type": c.get("company_type", ""),
                "registry_url": c.get("registry_url", ""),
                "opencorporates_url": c.get("opencorporates_url", ""),
                "current_status": c.get("current_status", ""),
                "registered_address": c.get("registered_address_in_full", ""),
            })
        return companies
    except Exception as e:
        print(f"    OpenCorporates company search error: {e}")
        return []


def search_opencorporates_officers(name: str, country: str = "") -> list:
    """Search OpenCorporates for officers/directors matching the subject name."""
    params = {"q": name, "per_page": 20}
    if config.OPENCORPORATES_API_KEY:
        params["api_token"] = config.OPENCORPORATES_API_KEY

    jurisdiction = _country_to_jurisdiction(country)
    if jurisdiction:
        params["country_code"] = jurisdiction

    try:
        resp = requests.get(
            config.ENDPOINTS["opencorporates_officers"],
            params=params,
            timeout=config.REQUEST_TIMEOUT,
            headers={"User-Agent": "TMG-Vetting-Pipeline/1.0"},
        )
        resp.raise_for_status()
        data = resp.json()

        officers = []
        for item in data.get("results", {}).get("officers", []):
            o = item.get("officer", {})
            company = o.get("company", {})
            officers.append({
                "name": o.get("name", ""),
                "position": o.get("position", ""),
                "start_date": o.get("start_date", ""),
                "end_date": o.get("end_date", ""),
                "opencorporates_url": o.get("opencorporates_url", ""),
                "company_name": company.get("name", ""),
                "company_number": company.get("company_number", ""),
                "company_jurisdiction": company.get("jurisdiction_code", ""),
                "company_opencorporates_url": company.get("opencorporates_url", ""),
            })
        return officers
    except Exception as e:
        print(f"    OpenCorporates officer search error: {e}")
        return []


def _country_to_jurisdiction(country: str) -> str:
    """Map country name/code to OpenCorporates jurisdiction code."""
    if not country:
        return ""
    mapping = {
        "US": "us", "USA": "us", "UNITED STATES": "us",
        "UK": "gb", "GB": "gb", "UNITED KINGDOM": "gb",
        "PAKISTAN": "pk", "PK": "pk",
        "INDIA": "in", "IN": "in",
        "UAE": "ae", "AE": "ae",
        "NIGERIA": "ng", "NG": "ng",
        "KENYA": "ke", "KE": "ke",
        "SOUTH AFRICA": "za", "ZA": "za",
        "BRAZIL": "br", "BR": "br",
        "MEXICO": "mx", "MX": "mx",
        "TURKEY": "tr", "TR": "tr",
        "PHILIPPINES": "ph", "PH": "ph",
        "SAUDI ARABIA": "sa", "SA": "sa",
        "COLOMBIA": "co", "CO": "co",
        "INDONESIA": "id", "ID": "id",
        "SOUTH KOREA": "kr", "KR": "kr",
        "EGYPT": "eg", "EG": "eg",
        "MALAYSIA": "my", "MY": "my",
    }
    return mapping.get(country.upper(), country.lower()[:2])


# ─── Tavily Fallback (no API key needed) ──────────────────────

def tavily_search(query: str, step: str = "corporate", **overrides) -> dict:
    """Run a single Tavily search for corporate network discovery."""
    try:
        params = get_tavily_params(step, query, **overrides)
        params["api_key"] = config.TAVILY_API_KEY
        resp = requests.post(
            config.ENDPOINTS["tavily_search"],
            json=params,
            timeout=30,
        )
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        return {"error": str(e), "results": [], "query": query}


def search_network_via_tavily(name: str, subject_type: str, company: str = "", country: str = "") -> dict:
    """
    Fallback: use Tavily to discover corporate associations, directorships,
    subsidiaries, and business partners when OpenCorporates is unavailable.
    """
    queries = []

    if subject_type == "individual":
        queries = [
            f"{name} director board member company",
            f"{name} business ventures companies founded",
            f"{name} corporate affiliations subsidiaries",
        ]
        if company:
            queries.append(f"{company} board of directors officers")
            queries.append(f"{company} subsidiaries affiliates related companies")
    else:
        queries = [
            f"{name} board of directors officers leadership",
            f"{name} subsidiaries affiliates related companies",
            f"{name} parent company ownership structure",
            f"{name} business partners joint ventures",
        ]

    all_results = []
    associated_entities = []
    seen_urls = set()

    for query in queries:
        data = tavily_search(query, step="corporate")
        results = data.get("results", [])

        search_record = {
            "query": query,
            "results": [],
        }

        for r in results:
            url = r.get("url", "")
            if url and url not in seen_urls:
                seen_urls.add(url)
                search_record["results"].append({
                    "title": r.get("title", ""),
                    "url": url,
                    "content": r.get("content", "")[:500],
                    "score": r.get("score", 0),
                })

        all_results.append(search_record)
        time.sleep(config.REQUEST_DELAY)

    total_sources = sum(len(s.get("results", [])) for s in all_results)

    return {
        "tavily_searches": all_results,
        "total_sources": total_sources,
    }


# ─── Main Entry Point ─────────────────────────────────────────

def run_network_search(intake: dict) -> dict:
    """
    Run corporate network discovery for a subject.
    Uses OpenCorporates API if key is available, otherwise falls back to Tavily.
    """
    name = intake["subject"]["name"]
    subject_type = intake["subject"]["type"]
    subject_id = intake["subject_id"]
    company = intake["subject"].get("company", "")
    country = intake["subject"].get("country", "")

    print(f"  🔍 Step 15: Corporate network discovery for '{name}'...")

    use_opencorporates = bool(config.OPENCORPORATES_API_KEY)
    associated_entities = []
    companies = []
    officers = []
    co_directors = []
    tavily_results = {}

    if use_opencorporates:
        print(f"    Using OpenCorporates API...")

        if subject_type == "individual":
            officers = search_opencorporates_officers(name, country)
            time.sleep(1)

            if company:
                companies = search_opencorporates_companies(company, country)
                time.sleep(1)

            for o in officers:
                co_name = o.get("company_name", "")
                if co_name and co_name.lower() != name.lower():
                    associated_entities.append({
                        "name": co_name,
                        "relationship": f"Subject is {o.get('position', 'officer')}",
                        "source": "OpenCorporates",
                    })

            # Get co-directors from top 5 companies
            for o in officers[:5]:
                co_url = o.get("company_opencorporates_url", "")
                if co_url:
                    try:
                        params = {}
                        if config.OPENCORPORATES_API_KEY:
                            params["api_token"] = config.OPENCORPORATES_API_KEY
                        resp = requests.get(
                            co_url + ".json",
                            params=params,
                            timeout=config.REQUEST_TIMEOUT,
                            headers={"User-Agent": "TMG-Vetting-Pipeline/1.0"},
                        )
                        resp.raise_for_status()
                        co_data = resp.json().get("results", {}).get("company", {})
                        for officer_data in co_data.get("officers", []):
                            off = officer_data.get("officer", {})
                            off_name = off.get("name", "")
                            if off_name and off_name.lower() != name.lower():
                                co_directors.append({
                                    "name": off_name,
                                    "position": off.get("position", ""),
                                    "company": o.get("company_name", ""),
                                })
                        time.sleep(1)
                    except Exception:
                        pass
        else:
            companies = search_opencorporates_companies(name, country)
            time.sleep(1)
            officers = search_opencorporates_officers(name, country)
            time.sleep(1)

            for o in officers:
                o_name = o.get("name", "")
                if o_name and o_name.lower() != name.lower():
                    associated_entities.append({
                        "name": o_name,
                        "relationship": f"{o.get('position', 'officer')} at {name}",
                        "source": "OpenCorporates",
                    })
    else:
        # Fallback to Tavily-based network discovery
        print(f"    No OpenCorporates API key — using Tavily fallback...")
        tavily_results = search_network_via_tavily(name, subject_type, company, country)

    # Deduplicate associated entities
    seen_names = set()
    unique_entities = []
    for e in associated_entities:
        key = e["name"].lower().strip()
        if key not in seen_names:
            seen_names.add(key)
            unique_entities.append(e)

    result = {
        "step": 15,
        "step_name": "Corporate Network Discovery",
        "subject_id": subject_id,
        "subject_name": name,
        "subject_type": subject_type,
        "summary": {
            "companies_found": len(companies),
            "officer_positions_found": len(officers),
            "associated_entities": len(unique_entities),
            "co_directors_found": len(co_directors),
            "tavily_sources": tavily_results.get("total_sources", 0),
        },
        "companies": companies,
        "officer_positions": officers,
        "associated_entities": unique_entities,
        "co_directors": co_directors,
        "tavily_network_searches": tavily_results.get("tavily_searches", []),
        "metadata": {
            "checked_at": datetime.now(timezone.utc).isoformat(),
            "source": "OpenCorporates" if use_opencorporates else "Tavily (fallback)",
            "opencorporates_available": use_opencorporates,
            "country_filter": country or "none",
        },
    }

    # Save
    output_path = config.NETWORK_DIR / f"{subject_id}.json"
    with open(output_path, "w") as f:
        json.dump(result, f, indent=2)

    if use_opencorporates:
        print(f"  ✅ Step 15: {len(companies)} companies, {len(officers)} officer positions, "
              f"{len(unique_entities)} associated entities → {output_path.name}")
    else:
        print(f"  ✅ Step 15: Tavily fallback — {tavily_results.get('total_sources', 0)} sources "
              f"→ {output_path.name}")
        print(f"    💡 Add OPENCORPORATES_API_KEY to .env for structured corporate data")

    return result


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Step 15: Corporate Network Discovery")
    parser.add_argument("--subject-id", required=True)
    args = parser.parse_args()

    intake_path = config.INTAKE_DIR / f"{args.subject_id}.json"
    with open(intake_path) as f:
        intake = json.load(f)

    result = run_network_search(intake)
    print(f"\nCompanies: {result['summary']['companies_found']}, "
          f"Officers: {result['summary']['officer_positions_found']}, "
          f"Entities: {result['summary']['associated_entities']}")
