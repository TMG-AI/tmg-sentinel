"""
Step 3 / Step 10: News & Media Search via Tavily
=================================================
Step 3 (basic): 3 targeted searches
Step 10 (deep): 35+ targeted searches

Results are split into two buckets:
  - risk_sources: Mention the subject (company name, exec names) in title or content.
    Used for risk scoring in synthesis.
  - context_sources: Industry/sector background. NOT used for risk scoring.
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
from config_international import get_corruption_search_terms


def tavily_search(query: str, step: str = "news_basic", **overrides) -> dict:
    """Run a single Tavily search with domain filtering from config_tavily."""
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


def _build_relevance_terms(intake: dict) -> list:
    """Build list of lowercase terms that indicate a source is directly relevant."""
    terms = []
    name = intake["subject"]["name"].lower()
    company = (intake["subject"].get("company") or "").lower()

    # Full name and each name part (min 3 chars to avoid matching "of", "de", etc.)
    terms.append(name)
    for part in name.split():
        if len(part) >= 3:
            terms.append(part)

    # Company name and meaningful parts
    if company and company != name:
        terms.append(company)
        for part in company.split():
            if len(part) >= 3 and part.lower() not in ("inc", "llc", "ltd", "corp", "the", "and", "for"):
                terms.append(part)

    return list(set(terms))


def _is_relevant(source: dict, relevance_terms: list) -> bool:
    """Check if a source mentions the subject in title or content."""
    title = (source.get("title") or "").lower()
    content = (source.get("content") or "").lower()
    text = title + " " + content

    for term in relevance_terms:
        if term in text:
            return True
    return False


def run_news_search(intake: dict, deep: bool = False) -> dict:
    """Run news/media searches for a subject."""

    name = intake["subject"]["name"]
    company = intake["subject"].get("company") or ""
    subject_id = intake["subject_id"]
    step = 10 if deep else 3

    mode = "deep" if deep else "basic"
    print(f"  🔍 Step {step}: Searching news/media ({mode}) for '{name}'...")

    # Select query templates
    subject_type = intake["subject"].get("type", "individual")
    templates = list(config.TAVILY_DEEP_QUERIES if deep else config.TAVILY_BASIC_QUERIES)

    # Add org-specific queries for deep searches of organizations
    if deep and subject_type == "organization" and hasattr(config, "TAVILY_ORG_QUERIES"):
        templates.extend(config.TAVILY_ORG_QUERIES)

    # Add universal investigator-style queries for all deep searches
    if deep:
        templates.extend(config.TAVILY_INVESTIGATOR_QUERIES)

    # Add red flag category queries (human rights, environmental, etc.)
    if deep:
        templates.extend(config.TAVILY_RED_FLAG_QUERIES)

    # Add top country-specific corruption queries for international deep searches
    country = intake["subject"].get("country", "US")
    is_us = country.upper() in ("US", "USA", "UNITED STATES")
    if deep and not is_us:
        corruption_terms = get_corruption_search_terms(country)
        # Add top 5 corruption terms as news queries (Step 12 does the full set)
        for term in corruption_terms[:5]:
            templates.append("{name} " + term)

    # Add reverse queries for international subjects (scandal-first searches)
    if deep and not is_us:
        # Infer sector from bio/engagement type for reverse queries
        bio = intake.get("context", {}).get("brief_bio", "")
        engagement = intake.get("context", {}).get("engagement_type", "")
        sector = ""
        if "minister" in bio.lower() or "governor" in bio.lower() or "political" in engagement:
            sector = "government politics"
        elif "ceo" in bio.lower() or "corporate" in engagement:
            sector = "business corporate"
        elif "military" in bio.lower() or "defense" in engagement:
            sector = "military defense"

        for tmpl in config.TAVILY_REVERSE_QUERIES:
            templates.append(tmpl.format(
                name="{name}",  # keep {name} for later .format() call
                country=country,
                sector=sector,
            ).strip())

    # ─── Run subject-specific searches ────────────────────────
    all_results = []
    all_sources = []
    seen_urls = set()

    for i, template in enumerate(templates):
        query = template.format(name=name, company=company).strip()

        if deep:
            # First pass: open search (global exclude only); second pass: investigative sources
            step_key = "news_deep_investigative" if i == 0 else "news_deep"
        else:
            step_key = "news_basic"

        tavily_resp = tavily_search(query, step=step_key)

        results = tavily_resp.get("results", [])
        answer = tavily_resp.get("answer", "")

        search_record = {
            "query": query,
            "answer": answer,
            "num_results": len(results),
            "results": [],
        }

        for r in results:
            url = r.get("url", "")
            if url not in seen_urls:
                seen_urls.add(url)
                result_item = {
                    "title": r.get("title", ""),
                    "url": url,
                    "content": r.get("content", "")[:500],  # Truncate for storage
                    "score": r.get("score", 0),
                    "published_date": r.get("published_date", ""),
                }
                search_record["results"].append(result_item)
                all_sources.append(result_item)

        all_results.append(search_record)
        time.sleep(config.REQUEST_DELAY)

    # ─── Run industry context searches (deep only) ────────────
    context_results = []
    context_sources = []

    if deep and hasattr(config, "TAVILY_INDUSTRY_CONTEXT_QUERIES"):
        # Infer sector for context queries
        bio = intake.get("context", {}).get("brief_bio", "")
        engagement = intake.get("context", {}).get("engagement_type", "")
        sector = _infer_sector(bio, engagement, subject_type)

        if sector:
            print(f"  🔍 Step {step}: Running industry context searches for sector: {sector}...")
            context_templates = config.TAVILY_INDUSTRY_CONTEXT_QUERIES.get(sector, [])

            for template in context_templates:
                query = template.format(name=name, company=company).strip()
                tavily_resp = tavily_search(query, step="news_deep")
                results = tavily_resp.get("results", [])

                search_record = {
                    "query": query,
                    "answer": tavily_resp.get("answer", ""),
                    "num_results": len(results),
                    "category": "industry_context",
                    "results": [],
                }

                for r in results:
                    url = r.get("url", "")
                    if url not in seen_urls:
                        seen_urls.add(url)
                        result_item = {
                            "title": r.get("title", ""),
                            "url": url,
                            "content": r.get("content", "")[:500],
                            "score": r.get("score", 0),
                            "published_date": r.get("published_date", ""),
                        }
                        search_record["results"].append(result_item)
                        context_sources.append(result_item)

                context_results.append(search_record)
                time.sleep(config.REQUEST_DELAY)

    # ─── Split sources by relevance ───────────────────────────
    relevance_terms = _build_relevance_terms(intake)
    risk_sources = []
    spillover_context = []  # Sources from subject queries that don't mention subject

    for source in all_sources:
        if _is_relevant(source, relevance_terms):
            risk_sources.append(source)
        else:
            spillover_context.append(source)

    # Merge spillover into context_sources
    context_sources = spillover_context + context_sources

    print(f"  📊 Source split: {len(risk_sources)} risk sources, {len(context_sources)} context sources")

    result = {
        "step": step,
        "step_name": f"News/Media Search ({'Deep' if deep else 'Basic'})",
        "subject_id": subject_id,
        "subject_name": name,
        "mode": mode,
        "total_queries": len(templates) + len(context_results),
        "total_unique_sources": len(all_sources) + len(context_sources) - len(spillover_context),
        "risk_source_count": len(risk_sources),
        "context_source_count": len(context_sources),
        "searches": all_results,
        "context_searches": context_results,
        "risk_sources": sorted(risk_sources, key=lambda x: x.get("score", 0), reverse=True),
        "context_sources": sorted(context_sources, key=lambda x: x.get("score", 0), reverse=True),
        # Keep all_sources for backward compatibility
        "all_sources": sorted(all_sources, key=lambda x: x.get("score", 0), reverse=True),
        "metadata": {
            "checked_at": datetime.now(timezone.utc).isoformat(),
            "search_depth": "advanced" if deep else "basic",
            "tavily_api": True,
            "relevance_terms": relevance_terms,
        },
    }

    # Save
    output_path = config.NEWS_DIR / f"{subject_id}.json"
    with open(output_path, "w") as f:
        json.dump(result, f, indent=2)

    print(f"  ✅ Step {step}: {len(risk_sources)} risk sources + {len(context_sources)} context across {result['total_queries']} queries → {output_path.name}")

    return result


def _infer_sector(bio: str, engagement: str, subject_type: str) -> str:
    """Infer industry sector from bio and engagement type."""
    bio_lower = bio.lower()
    engagement_lower = engagement.lower()

    if any(w in bio_lower for w in ["defense", "military", "weapons", "drone", "surveillance", "missile"]):
        return "defense_tech"
    elif any(w in bio_lower for w in ["oil", "gas", "energy", "mining", "petroleum"]):
        return "energy"
    elif any(w in bio_lower for w in ["pharma", "drug", "biotech", "health"]):
        return "pharma_health"
    elif any(w in bio_lower for w in ["bank", "finance", "invest", "fund", "capital"]):
        return "finance"
    elif any(w in bio_lower for w in ["tech", "software", "ai", "data", "cloud", "cyber"]):
        return "tech"
    elif "minister" in bio_lower or "governor" in bio_lower or "senator" in bio_lower or "political" in engagement_lower:
        return "government"
    elif "corporate" in engagement_lower:
        return "general_corporate"
    return ""


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Step 3/10: News/Media Search")
    parser.add_argument("--subject-id", required=True)
    parser.add_argument("--deep", action="store_true", help="Run deep search (Step 10)")
    args = parser.parse_args()

    intake_path = config.INTAKE_DIR / f"{args.subject_id}.json"
    with open(intake_path) as f:
        intake = json.load(f)

    result = run_news_search(intake, deep=args.deep)
    print(f"\nRisk sources: {result['risk_source_count']}")
    print(f"Context sources: {result['context_source_count']}")
