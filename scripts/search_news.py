"""
Step 3 / Step 10: News & Media Search via Tavily
=================================================
Step 3 (basic): 3 targeted searches for Quick Screen / Standard Vet
Step 10 (deep): 12+ targeted searches for Deep Dive
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


def run_news_search(intake: dict, deep: bool = False) -> dict:
    """Run news/media searches for a subject."""

    name = intake["subject"]["name"]
    company = intake["subject"].get("company") or ""
    subject_id = intake["subject_id"]
    step = 10 if deep else 3

    mode = "deep" if deep else "basic"
    print(f"  🔍 Step {step}: Searching news/media ({mode}) for '{name}'...")

    # Select query templates
    templates = config.TAVILY_DEEP_QUERIES if deep else config.TAVILY_BASIC_QUERIES

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

    result = {
        "step": step,
        "step_name": f"News/Media Search ({'Deep' if deep else 'Basic'})",
        "subject_id": subject_id,
        "subject_name": name,
        "mode": mode,
        "total_queries": len(templates),
        "total_unique_sources": len(all_sources),
        "searches": all_results,
        "all_sources": sorted(all_sources, key=lambda x: x.get("score", 0), reverse=True),
        "metadata": {
            "checked_at": datetime.now(timezone.utc).isoformat(),
            "search_depth": "advanced" if deep else "basic",
            "tavily_api": True,
        },
    }

    # Save
    output_path = config.NEWS_DIR / f"{subject_id}.json"
    with open(output_path, "w") as f:
        json.dump(result, f, indent=2)

    print(f"  ✅ Step {step}: Found {len(all_sources)} unique sources across {len(templates)} queries → {output_path.name}")

    return result


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
    print(f"\nTotal sources: {result['total_unique_sources']}")
