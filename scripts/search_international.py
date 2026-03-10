"""
Step 12: International Checks — OpenSanctions PEP + Tavily + ProPublica Nonprofits
===================================================================================
Deep PEP check via OpenSanctions, foreign media via Tavily,
nonprofit/NGO connections via ProPublica Nonprofit Explorer API.
For foreign subjects or subjects with international exposure.
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
from config_international import (
    get_corruption_search_terms,
    get_country_news_domains,
    get_country_avoid_domains,
    get_country_config,
)


def deep_pep_check(name: str, subject_type: str = "individual") -> dict:
    """Deep PEP (Politically Exposed Person) check via OpenSanctions."""
    schema = "Person" if subject_type == "individual" else "Company"

    payload = {
        "queries": {
            "pep_check": {
                "schema": schema,
                "properties": {
                    "name": [name],
                },
            }
        }
    }

    try:
        resp = requests.post(
            config.ENDPOINTS["opensanctions_pep"],
            json=payload,
            headers={
                "Authorization": f"ApiKey {config.OPENSANCTIONS_API_KEY}",
                "Content-Type": "application/json",
            },
            timeout=config.REQUEST_TIMEOUT,
        )
        resp.raise_for_status()
        data = resp.json()

        results = data.get("responses", {}).get("pep_check", {}).get("results", [])

        pep_matches = []
        for r in results:
            if r.get("score", 0) >= 0.5:  # Lower threshold for PEP — cast wider net
                pep_matches.append({
                    "name": r.get("caption", ""),
                    "score": r.get("score", 0),
                    "schema": r.get("schema", ""),
                    "datasets": r.get("datasets", []),
                    "properties": {
                        k: v for k, v in r.get("properties", {}).items()
                        if k in ["name", "country", "birthDate", "nationality",
                                 "topics", "notes", "position", "role"]
                    },
                    "topics": r.get("properties", {}).get("topics", []),
                })

        return {
            "source": "OpenSanctions PEP Database",
            "query": name,
            "total_results": len(results),
            "pep_matches": len(pep_matches),
            "matches": pep_matches,
            "checked_at": datetime.now(timezone.utc).isoformat(),
        }
    except Exception as e:
        return {
            "source": "OpenSanctions PEP Database",
            "query": name,
            "error": str(e),
            "total_results": 0,
            "pep_matches": 0,
            "matches": [],
            "checked_at": datetime.now(timezone.utc).isoformat(),
        }


def search_foreign_media(name: str, country: str = "", company: str = "") -> list:
    """Search for foreign media coverage via Tavily with domain filtering."""
    queries = [
        f"{name} foreign government connections",
        f"{name} international business operations",
        f"{name} {country} political ties" if country and country != "US" else f"{name} foreign political ties",
    ]

    # Per Perplexity report: first query uses INCLUDE_INTERNATIONAL for authoritative sources,
    # remaining queries use open search (global exclude only) for local/regional discovery
    step_keys = ["international", "international_local", "international_local"]

    results = []
    seen_urls = set()

    for query, step_key in zip(queries, step_keys):
        try:
            overrides = {}
            if country and country != "US" and step_key == "international_local":
                overrides["country"] = country

            params = get_tavily_params(step_key, query, **overrides)
            params["api_key"] = config.TAVILY_API_KEY

            resp = requests.post(
                config.ENDPOINTS["tavily_search"],
                json=params,
                timeout=30,
            )
            resp.raise_for_status()
            data = resp.json()

            search_record = {
                "query": query,
                "answer": data.get("answer", ""),
                "results": [],
            }

            for r in data.get("results", []):
                url = r.get("url", "")
                if url not in seen_urls:
                    seen_urls.add(url)
                    search_record["results"].append({
                        "title": r.get("title", ""),
                        "url": url,
                        "content": r.get("content", "")[:500],
                        "score": r.get("score", 0),
                        "published_date": r.get("published_date", ""),
                    })

            results.append(search_record)
            time.sleep(config.REQUEST_DELAY)

        except Exception as e:
            results.append({"query": query, "error": str(e), "results": []})

    return results


def search_propublica_nonprofits(name: str) -> dict:
    """Search ProPublica Nonprofit Explorer for NGO/nonprofit connections."""
    try:
        resp = requests.get(
            config.ENDPOINTS["propublica_nonprofits"],
            params={"q": name},
            timeout=config.REQUEST_TIMEOUT,
        )
        resp.raise_for_status()
        data = resp.json()

        organizations = []
        for org in data.get("organizations", [])[:20]:
            organizations.append({
                "name": org.get("name", ""),
                "ein": org.get("ein", ""),
                "city": org.get("city", ""),
                "state": org.get("state", ""),
                "ntee_code": org.get("ntee_code", ""),
                "subsection_code": org.get("subsection_code", ""),
                "total_revenue": org.get("total_revenue", 0),
                "total_assets": org.get("total_assets", 0),
            })

        return {
            "source": "ProPublica Nonprofit Explorer",
            "query": name,
            "total_results": data.get("total_results", 0),
            "organizations": organizations,
            "checked_at": datetime.now(timezone.utc).isoformat(),
        }
    except Exception as e:
        return {
            "source": "ProPublica Nonprofit Explorer",
            "query": name,
            "error": str(e),
            "total_results": 0,
            "organizations": [],
            "checked_at": datetime.now(timezone.utc).isoformat(),
        }


def search_country_corruption(name: str, country: str) -> list:
    """
    Run country-specific anti-corruption queries via Tavily.
    Uses institution-specific terminology from config_international.py.
    This is the key addition for international vetting — surfaces NAB references,
    ED cases, SFO investigations, etc. that generic queries miss.
    """
    corruption_terms = get_corruption_search_terms(country)
    country_news = get_country_news_domains(country, tiers=["tier1", "tier2"])
    country_avoid = get_country_avoid_domains(country)
    country_cfg = get_country_config(country)
    country_name = country_cfg.get("name", country) if country_cfg else country

    if not corruption_terms:
        print(f"    No country-specific corruption terms for '{country}', using generic")

    results = []
    seen_urls = set()

    for i, term in enumerate(corruption_terms):
        query = f"{name} {term}"

        try:
            # Alternate between authoritative country sources and open search
            if i % 3 == 0 and country_news:
                # Authoritative pass: include country tier 1+2 sources
                overrides = {"include_domains": country_news, "max_results": 10}
                step_key = "international"
            else:
                # Open pass: exclude global noise + country avoid list
                extra_excludes = country_avoid if country_avoid else []
                overrides = {"max_results": 10}
                step_key = "international_local"

            params = get_tavily_params(step_key, query, **overrides)
            params["api_key"] = config.TAVILY_API_KEY

            resp = requests.post(
                config.ENDPOINTS["tavily_search"],
                json=params,
                timeout=30,
            )
            resp.raise_for_status()
            data = resp.json()

            search_record = {
                "query": query,
                "answer": data.get("answer", ""),
                "results": [],
            }

            for r in data.get("results", []):
                url = r.get("url", "")
                if url and url not in seen_urls:
                    seen_urls.add(url)
                    search_record["results"].append({
                        "title": r.get("title", ""),
                        "url": url,
                        "content": r.get("content", "")[:500],
                        "score": r.get("score", 0),
                        "published_date": r.get("published_date", ""),
                    })

            results.append(search_record)
            time.sleep(config.REQUEST_DELAY)

        except Exception as e:
            results.append({"query": query, "error": str(e), "results": []})

    total_sources = sum(len(s.get("results", [])) for s in results)
    print(f"    Country corruption search ({country_name}): {len(corruption_terms)} queries → {total_sources} sources")
    return results


def run_international_search(intake: dict) -> dict:
    """Run international checks for a subject."""

    name = intake["subject"]["name"]
    subject_type = intake["subject"]["type"]
    subject_id = intake["subject_id"]
    country = intake["subject"].get("country", "")
    company = intake["subject"].get("company", "")

    print(f"  🔍 Step 12: Running international checks for '{name}'...")

    # 1. Deep PEP check
    pep_result = deep_pep_check(name, subject_type)
    time.sleep(config.REQUEST_DELAY)

    # 2. Foreign media search via Tavily (generic queries)
    foreign_media = search_foreign_media(name, country, company)
    time.sleep(config.REQUEST_DELAY)

    # 3. Country-specific anti-corruption searches (NEW — the key addition)
    corruption_results = []
    if country and country.upper() not in ("US", "USA", "UNITED STATES"):
        corruption_results = search_country_corruption(name, country)
        time.sleep(config.REQUEST_DELAY)

    # 4. ProPublica Nonprofit Explorer
    nonprofits = search_propublica_nonprofits(name)

    # Count total sources
    total_foreign_sources = sum(
        len(s.get("results", [])) for s in foreign_media
    )
    total_corruption_sources = sum(
        len(s.get("results", [])) for s in corruption_results
    )

    result = {
        "step": 12,
        "step_name": "International Checks",
        "subject_id": subject_id,
        "subject_name": name,
        "summary": {
            "pep_matches": pep_result.get("pep_matches", 0),
            "foreign_media_sources": total_foreign_sources,
            "corruption_search_sources": total_corruption_sources,
            "nonprofit_results": nonprofits.get("total_results", 0),
        },
        "pep_check": pep_result,
        "foreign_media": foreign_media,
        "corruption_searches": corruption_results,
        "nonprofits": nonprofits,
        "metadata": {
            "checked_at": datetime.now(timezone.utc).isoformat(),
            "sources": [
                "OpenSanctions PEP",
                "Tavily (foreign media)",
                "Tavily (country corruption — " + (get_country_config(country) or {}).get("name", country) + ")",
                "ProPublica Nonprofit Explorer",
            ],
            "country_config_used": bool(get_country_config(country)),
        },
    }

    # Save
    output_path = config.INTERNATIONAL_DIR / f"{subject_id}.json"
    with open(output_path, "w") as f:
        json.dump(result, f, indent=2)

    pep_note = f" (PEP: {pep_result['pep_matches']} matches)" if pep_result.get("pep_matches") else ""
    print(f"  ✅ Step 12: {total_foreign_sources} foreign media, "
          f"{total_corruption_sources} corruption search, "
          f"{nonprofits.get('total_results', 0)} nonprofits{pep_note} → {output_path.name}")

    return result


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Step 12: International Checks")
    parser.add_argument("--subject-id", required=True)
    args = parser.parse_args()

    intake_path = config.INTAKE_DIR / f"{args.subject_id}.json"
    with open(intake_path) as f:
        intake = json.load(f)

    result = run_international_search(intake)
    print(f"\nPEP matches: {result['summary']['pep_matches']}, "
          f"Foreign media: {result['summary']['foreign_media_sources']}, "
          f"Nonprofits: {result['summary']['nonprofit_results']}")
