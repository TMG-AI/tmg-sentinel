"""
Step 13: Claude Synthesis — Risk Assessment & Unified Profile
=============================================================
Takes ALL step output JSONs, sends to Claude API, scores 7 risk dimensions,
applies temporal decay + engagement multiplier + confidence modifier,
produces unified JSON matching the LOVABLE_PROMPT.md schema.

This is the ONLY LLM step in the pipeline. Everything before is factual API data.
"""

import json
import re
import sys
import os
import time
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config
from config_tavily import SOURCE_QUALITY_PROMPT
from config_tmg_identity import get_rca_prompt, get_rcs_tier

try:
    import anthropic
except ImportError:
    os.system("pip3 install anthropic --quiet")
    import anthropic


# ─── Tavily Source Collection ──────────────────────────────

def collect_tavily_sources(step_data: dict) -> list:
    """
    Collect ALL Tavily sources from news + international step data into a
    deduplicated master sources array with IDs, matching Palantir's pattern.
    Returns: [{"id": 1, "url": "...", "title": "...", "score": 0.85}, ...]
    """
    seen_urls = set()
    sources = []
    source_id = 1

    # Collect from news/media searches
    news = step_data.get("news", {})
    for search in news.get("searches", []):
        for r in search.get("results", []):
            url = r.get("url", "")
            if url and url not in seen_urls:
                seen_urls.add(url)
                sources.append({
                    "id": source_id,
                    "url": url,
                    "title": r.get("title", ""),
                    "score": r.get("score", 0),
                    "content_snippet": (r.get("content", "") or "")[:300],
                })
                source_id += 1

    # Collect from international foreign media searches
    intl = step_data.get("international", {})
    for search in intl.get("foreign_media", []):
        for r in search.get("results", []):
            url = r.get("url", "")
            if url and url not in seen_urls:
                seen_urls.add(url)
                sources.append({
                    "id": source_id,
                    "url": url,
                    "title": r.get("title", ""),
                    "score": r.get("score", 0),
                    "content_snippet": (r.get("content", "") or "")[:300],
                })
                source_id += 1

    # Sort by relevance score descending
    sources.sort(key=lambda s: s.get("score", 0), reverse=True)
    # Reassign IDs after sort so [1] = most relevant
    for i, s in enumerate(sources):
        s["id"] = i + 1

    return sources


def build_sources_reference(sources: list) -> str:
    """Build a numbered source reference list for the Claude prompt."""
    if not sources:
        return "No web sources available."
    lines = []
    for s in sources[:100]:  # Limit to top 100 for prompt size
        lines.append(f"  [{s['id']}] {s['title']}")
        lines.append(f"      URL: {s['url']}")
        if s.get("content_snippet"):
            lines.append(f"      Snippet: {s['content_snippet'][:200]}")
    return "\n".join(lines)


def enrich_evidence_with_sources(synthesized: dict, sources: list) -> dict:
    """
    Post-synthesis enrichment: for each evidence item, match it to Tavily
    sources and add source_urls arrays with {url, title} objects.
    Also resolves [n] citation references to actual URLs.
    """
    # Build lookup by ID
    source_by_id = {s["id"]: s for s in sources}
    # Build lookup by URL for reverse matching
    url_to_source = {s["url"]: s for s in sources}

    dimensions = synthesized.get("dimensions", {})
    total_enriched = 0

    for dim_key, dim_data in dimensions.items():
        for ev in dim_data.get("evidence", []):
            source_urls = []
            text = ev.get("text", "")

            # Extract [n] citations from evidence text
            citation_ids = [int(m) for m in re.findall(r'\[(\d+)\]', text)]
            for cid in citation_ids:
                src = source_by_id.get(cid)
                if src:
                    source_urls.append({"url": src["url"], "title": src["title"]})

            # If evidence already has a URL, include it
            existing_url = ev.get("url", "")
            if existing_url and existing_url not in {su["url"] for su in source_urls}:
                # Try to find title from sources
                matched = url_to_source.get(existing_url)
                title = matched["title"] if matched else ev.get("source", "")
                source_urls.append({"url": existing_url, "title": title})

            # If no source_urls found, try fuzzy matching by source name
            if not source_urls and ev.get("source"):
                source_name = ev["source"].lower()
                for s in sources[:50]:
                    if source_name in s.get("title", "").lower() or source_name in s.get("url", "").lower():
                        source_urls.append({"url": s["url"], "title": s["title"]})
                        break

            ev["source_urls"] = source_urls
            if source_urls:
                total_enriched += 1

    print(f"  Enrichment: {total_enriched} evidence items linked to sources")
    return synthesized


# ─── TMG Client Conflict Check ─────────────────────────────

def check_client_conflicts(name: str, company: str = "") -> dict:
    """Check vetting subject against TMG client list for conflicts."""
    client_csv = config.PROJECT_ROOT / "data" / "tmg_clients.csv"
    if not client_csv.exists():
        return {"checked": False, "reason": "No client list found at data/tmg_clients.csv"}

    import csv
    with open(client_csv) as f:
        reader = csv.DictReader(f)
        clients = [row["client_name"].strip() for row in reader if row.get("client_name")]

    name_lower = name.lower()
    company_lower = (company or "").lower()
    # Also extract individual words for partial matching
    name_parts = set(name_lower.split())
    company_parts = set(w for w in company_lower.replace("/", " ").replace(",", " ").split() if len(w) > 3)

    exact_matches = []
    partial_matches = []

    for client in clients:
        client_lower = client.lower()
        # Exact or near-exact match
        if name_lower in client_lower or client_lower in name_lower:
            exact_matches.append(client)
        elif company_lower and (company_lower in client_lower or client_lower in company_lower):
            exact_matches.append(client)
        # Partial match — company name words appear in client name
        elif company_parts:
            overlap = company_parts & set(client_lower.replace("(", " ").replace(")", " ").split())
            if overlap and len(overlap) >= 1:
                # Filter out common words
                meaningful = overlap - {"the", "inc", "llc", "corp", "group", "company", "services",
                                        "fund", "capital", "technologies", "management", "partners",
                                        "foundation", "ventures", "advisors", "solutions", "global",
                                        "national", "american", "united", "international"}
                if meaningful:
                    partial_matches.append({"client": client, "matched_words": list(meaningful)})

    return {
        "checked": True,
        "total_clients": len(clients),
        "exact_matches": exact_matches,
        "partial_matches": partial_matches,
        "has_conflicts": len(exact_matches) > 0,
        "has_potential_conflicts": len(partial_matches) > 0,
    }


def format_conflicts_for_prompt(conflicts: dict) -> str:
    if not conflicts.get("checked"):
        return "Client conflict check not available (no client list found)."
    lines = [f"Checked against {conflicts['total_clients']} active TMG clients."]
    if conflicts["exact_matches"]:
        lines.append(f"EXACT MATCHES FOUND: {', '.join(conflicts['exact_matches'])}")
    if conflicts["partial_matches"]:
        for pm in conflicts["partial_matches"]:
            lines.append(f"POTENTIAL MATCH: {pm['client']} (matched: {', '.join(pm['matched_words'])})")
    if not conflicts["exact_matches"] and not conflicts["partial_matches"]:
        lines.append("No conflicts found with current TMG clients.")
    return "\n".join(lines)


# ─── Load Step Outputs ──────────────────────────────────────

def load_step_json(directory: Path, subject_id: str) -> dict:
    """Load a step's output JSON if it exists."""
    path = directory / f"{subject_id}.json"
    if not path.exists():
        return {}
    with open(path) as f:
        return json.load(f)


def load_all_step_data(subject_id: str, vetting_level: str) -> dict:
    """Load all available step output data for a subject."""
    data = {
        "intake": load_step_json(config.INTAKE_DIR, subject_id),
        "sanctions": load_step_json(config.SANCTIONS_DIR, subject_id),
        "debarment": load_step_json(config.DEBARMENT_DIR, subject_id),
        "news": load_step_json(config.NEWS_DIR, subject_id),
        "litigation": load_step_json(config.LITIGATION_DIR, subject_id),
        "corporate": load_step_json(config.CORPORATE_DIR, subject_id),
        "fec": load_step_json(config.FEC_DIR, subject_id),
        "sec": load_step_json(config.SEC_DIR, subject_id),
        "lobbying": load_step_json(config.LOBBYING_DIR, subject_id),
        "bankruptcy": load_step_json(config.BANKRUPTCY_DIR, subject_id),
        "international": load_step_json(config.INTERNATIONAL_DIR, subject_id),
        "manual": load_step_json(config.MANUAL_DIR, subject_id),
    }

    # Report what we loaded
    available = [k for k, v in data.items() if v]
    missing = [k for k, v in data.items() if not v]
    print(f"  Sources loaded: {', '.join(available)}")
    if missing:
        print(f"  Sources missing: {', '.join(missing)}")

    return data


# ─── Format Data for Prompt ─────────────────────────────────

def format_sanctions_for_prompt(data: dict) -> str:
    if not data:
        return "No sanctions data available."
    gate = data.get("gate", {})
    lines = [f"GATE STATUS: {gate.get('status', 'UNKNOWN')}"]
    if gate.get("is_pep"):
        lines.append(f"PEP STATUS: YES — {len(data.get('pep_info', {}).get('pep_matches', []))} match(es)")
    if gate.get("details"):
        for d in gate["details"]:
            lines.append(f"  DETAIL: {d}")
    os_result = data.get("opensanctions", {})
    lines.append(f"OpenSanctions: {os_result.get('total_results', 0)} results, {os_result.get('high_confidence_matches', 0)} high-confidence matches")
    interpol = data.get("interpol", {})
    lines.append(f"Interpol: {interpol.get('total_results', 0)} results")
    return "\n".join(lines)


def format_debarment_for_prompt(data: dict) -> str:
    if not data:
        return "No debarment data available."
    gate = data.get("gate", {})
    return f"GATE STATUS: {gate.get('status', 'UNKNOWN')}\nMatches: {gate.get('total_matches', 0)}"


def format_news_for_prompt(data: dict, sources: list = None) -> str:
    if not data:
        return "No news data available."
    # Build URL→source_id lookup for [n] references
    url_to_id = {}
    if sources:
        url_to_id = {s["url"]: s["id"] for s in sources}

    lines = [f"Mode: {data.get('mode', 'unknown')}, {data.get('total_unique_sources', 0)} unique sources across {data.get('total_queries', 0)} queries"]
    for search in data.get("searches", [])[:15]:
        if search.get("answer"):
            lines.append(f"\nQuery: {search['query']}")
            lines.append(f"Answer: {search['answer'][:500]}")
        for r in search.get("results", [])[:5]:
            url = r.get("url", "")
            sid = url_to_id.get(url)
            ref = f" [{sid}]" if sid else ""
            lines.append(f"  - {r.get('title', '')}{ref}: {r.get('content', '')[:250]}")
            if url:
                lines.append(f"    URL: {url}")
    return "\n".join(lines)


def format_litigation_for_prompt(data: dict) -> str:
    if not data:
        return "No litigation data available."
    summary = data.get("summary", {})
    lines = [
        f"Total dockets: {summary.get('total_dockets', 0)}, Opinions: {summary.get('total_opinions', 0)}",
        f"Red flags: {summary.get('red_flags', 0)}, Yellow flags: {summary.get('yellow_flags', 0)}",
    ]
    for rf in data.get("red_flags", []):
        lines.append(f"  RED FLAG: {rf.get('case_name', '')} — {', '.join(rf.get('flags', []))} ({rf.get('date_filed', '')})")
    for case in data.get("cases", [])[:10]:
        cl = case.get("classification", {})
        lines.append(f"  Case: {case.get('case_name', '')} | Court: {case.get('court', '')} | Filed: {case.get('date_filed', '')} | Risk: {cl.get('risk_level', 'low')}")
    return "\n".join(lines)


def format_corporate_for_prompt(data: dict) -> str:
    if not data:
        return "No corporate data available."
    summary = data.get("summary", {})
    lines = [
        f"EDGAR person filings: {summary.get('edgar_person_filings', 0)}",
        f"EDGAR company filings: {summary.get('edgar_company_filings', 0)}",
        f"GLEIF entities: {summary.get('gleif_entities', 0)}",
    ]
    # SEC EDGAR person results
    person = data.get("sec_edgar_person", {})
    for filing in person.get("filings", [])[:5]:
        lines.append(f"  Person filing: {filing.get('entity_name', '')} — {filing.get('form_type', '')} ({filing.get('filed_date', '')})")
    # GLEIF
    gleif = data.get("gleif", {})
    for entity in gleif.get("records", [])[:5]:
        lines.append(f"  LEI: {entity.get('entity', {}).get('legalName', {}).get('name', '')} ({entity.get('entity', {}).get('jurisdiction', '')})")
    return "\n".join(lines)


def format_fec_for_prompt(data: dict) -> str:
    if not data:
        return "No FEC data available."
    summary = data.get("summary", {})
    lines = [
        f"Total contributions: {summary.get('total_contributions', 0)}",
        f"Total amount: ${summary.get('total_amount', 0):,.2f}",
        f"Is candidate: {summary.get('is_candidate', False)}",
    ]
    contrib_data = data.get("contributions", {})
    if isinstance(contrib_data, dict):
        for rec in contrib_data.get("top_recipients", [])[:5]:
            lines.append(f"  Top recipient: {rec.get('name', '')} — ${rec.get('total', 0):,.0f}")
        for c in contrib_data.get("contributions", [])[:10]:
            lines.append(f"  ${c.get('contribution_receipt_amount', 0):,.0f} to {c.get('committee', {}).get('name', '')} ({c.get('contribution_receipt_date', '')})")
    return "\n".join(lines)


def format_sec_for_prompt(data: dict) -> str:
    if not data:
        return "No SEC data available."
    summary = data.get("summary", {})
    lines = [
        f"Total filings: {summary.get('total_filings', 0)}, Enforcement: {summary.get('enforcement_actions', 0)}",
        f"Company filings: {summary.get('company_filings', 0)}, Insider trading: {summary.get('insider_trading_filings', 0)}",
    ]
    for filing in data.get("general_filings", {}).get("filings", [])[:10]:
        lines.append(f"  {filing.get('form_type', '')} — {filing.get('entity_name', '')} ({filing.get('filed_date', '')})")
    for rf in data.get("red_flags", []):
        lines.append(f"  RED FLAG: {rf}")
    return "\n".join(lines)


def format_lobbying_for_prompt(data: dict) -> str:
    if not data:
        return "No lobbying data available."
    summary = data.get("summary", {})
    lines = [
        f"Person filings: {summary.get('person_filings', 0)}",
        f"Unique registrants: {summary.get('unique_registrants', 0)}, Unique clients: {summary.get('unique_clients', 0)}",
    ]
    for reg in data.get("unique_registrants", [])[:10]:
        if isinstance(reg, dict):
            lines.append(f"  Registrant: {reg.get('name', '')}")
        else:
            lines.append(f"  Registrant: {reg}")
    for client in data.get("unique_clients", [])[:10]:
        if isinstance(client, dict):
            lines.append(f"  Client: {client.get('name', '')}")
        else:
            lines.append(f"  Client: {client}")
    return "\n".join(lines)


def format_bankruptcy_for_prompt(data: dict) -> str:
    if not data:
        return "No bankruptcy data available."
    summary = data.get("summary", {})
    lines = [f"Total results: {summary.get('total_results', 0)}, Debtor filings: {summary.get('debtor_filings', 0)}"]
    for filing in data.get("filings", [])[:10]:
        lines.append(f"  {filing.get('case_name', '')} | {filing.get('chapter', '')} | Role: {filing.get('role', '')} | Filed: {filing.get('date_filed', '')}")
    return "\n".join(lines)


def format_international_for_prompt(data: dict) -> str:
    if not data:
        return "No international data available."
    summary = data.get("summary", {})
    lines = [
        f"PEP matches: {summary.get('pep_matches', 0)}",
        f"Foreign media sources: {summary.get('foreign_media_sources', 0)}",
        f"Nonprofit results: {summary.get('nonprofit_results', 0)}",
    ]
    pep = data.get("pep_check", {})
    for match in pep.get("matches", [])[:5]:
        lines.append(f"  PEP: {match.get('name', '')} (score: {match.get('score', 0):.2f}, datasets: {', '.join(match.get('datasets', [])[:3])})")
    for search in data.get("foreign_media", [])[:5]:
        if search.get("answer"):
            lines.append(f"  Media: {search['answer'][:300]}")
    for org in data.get("nonprofits", {}).get("organizations", [])[:5]:
        lines.append(f"  Nonprofit: {org.get('name', '')} ({org.get('city', '')}, {org.get('state', '')})")
    return "\n".join(lines)


def format_manual_for_prompt(data: dict) -> str:
    if not data:
        return "No manual findings provided."
    lines = []
    for finding in data.get("findings", []):
        cat = finding.get("category", "general")
        title = finding.get("title", "Untitled")
        desc = finding.get("description", "")
        source = finding.get("source", "Manual research")
        date = finding.get("date", "")
        relevance = finding.get("risk_relevance", "")
        lines.append(f"  [{cat.upper()}] {title}")
        lines.append(f"    {desc}")
        lines.append(f"    Source: {source} | Date: {date}")
        if relevance:
            lines.append(f"    Risk relevance: {relevance}")
        lines.append("")
    if data.get("notes"):
        lines.append(f"  VETTER NOTES: {data['notes']}")
    return "\n".join(lines) if lines else "No manual findings provided."


# ─── Build Synthesis Prompt ─────────────────────────────────

def build_synthesis_prompt(intake: dict, step_data: dict, sources: list = None) -> str:
    """Build the full synthesis prompt for Claude."""

    subject = intake.get("subject", {})
    context = intake.get("context", {})
    name = subject.get("name", "Unknown")
    company = subject.get("company", "N/A")
    country = subject.get("country", "US")
    engagement_type = context.get("engagement_type", "domestic_corporate")
    vetting_level = context.get("vetting_level", "standard_vet")
    multiplier = config.ENGAGEMENT_MULTIPLIERS.get(engagement_type, 1.0)

    # Build dimension weights text
    dim_text = "\n".join(
        f"  {i+1}. {d['label']} — Weight: {d['weight']*100:.0f}%"
        for i, (k, d) in enumerate(config.RISK_DIMENSIONS.items())
    )

    # Format all step data
    sanctions_text = format_sanctions_for_prompt(step_data.get("sanctions", {}))
    debarment_text = format_debarment_for_prompt(step_data.get("debarment", {}))
    news_text = format_news_for_prompt(step_data.get("news", {}), sources=sources)
    litigation_text = format_litigation_for_prompt(step_data.get("litigation", {}))
    corporate_text = format_corporate_for_prompt(step_data.get("corporate", {}))
    fec_text = format_fec_for_prompt(step_data.get("fec", {}))
    sec_text = format_sec_for_prompt(step_data.get("sec", {}))
    lobbying_text = format_lobbying_for_prompt(step_data.get("lobbying", {}))
    bankruptcy_text = format_bankruptcy_for_prompt(step_data.get("bankruptcy", {}))
    international_text = format_international_for_prompt(step_data.get("international", {}))
    manual_text = format_manual_for_prompt(step_data.get("manual", {}))

    # Client conflict check
    conflicts = check_client_conflicts(name, company)
    conflicts_text = format_conflicts_for_prompt(conflicts)

    # Build sources reference for citations
    sources_ref = build_sources_reference(sources or [])

    # Get the Reputational Contagion Analysis prompt
    rca_prompt = get_rca_prompt()

    prompt = f"""You are a senior due diligence analyst for The Messina Group (TMG), a political consulting firm.
You are producing a factual, evidence-based risk assessment for a potential client.

## SUBJECT
Name: {name}
Company: {company}
Country: {country}
Engagement Type: {engagement_type} (risk multiplier: {multiplier}x)
Vetting Level: {vetting_level}
Bio: {context.get('brief_bio', 'None provided')}

## YOUR TASK
Analyze ALL the data below and produce a unified risk assessment JSON. You must:
1. Score each of the 7 risk dimensions (0-10, where 0=no risk, 10=extreme risk)
2. Provide evidence-based rationale for each score WITH CITATIONS
3. Identify red flags (auto-disqualify) and yellow flags (further investigation)
4. Write an executive summary suitable for TMG leadership
5. Make a recommendation: Approve / Conditional Approve / Further Review / Recommend Reject

## CITATION RULES (CRITICAL)
You have a numbered source reference list below. When writing evidence items:
- Use [n] citations to reference specific sources (e.g., "FBI investigation for arms trafficking [3]")
- Each evidence item MUST include at least one [n] citation when a web source is available
- For government database findings (SEC, FEC, CourtListener, SAM.gov), use the database name as the source
- For news/media findings, always cite the specific [n] source
- Include the actual URL in the evidence url field when possible

## RISK DIMENSIONS (score each 0-10)
{dim_text}

## SCORING GUIDELINES
- 0-2: Minimal or no risk indicators found
- 3-4: Minor concerns, routine for this type of client
- 5-6: Moderate concerns requiring attention
- 7-8: Significant risk, serious concerns
- 9-10: Extreme risk, near auto-reject level

## TEMPORAL DECAY (apply to individual findings)
- Last 2 years: Full weight (1.0x)
- 2-5 years ago: Moderate weight (0.7x)
- 5-10 years ago: Reduced weight (0.4x)
- 10+ years ago: Minimal weight (0.2x) — unless ongoing

## CONFIDENCE LEVELS
- HIGH: Multiple sources agree, strong evidence
- MEDIUM: Some evidence but gaps exist
- LOW: Limited data, position inferred — recommend manual review

{SOURCE_QUALITY_PROMPT}

## RED FLAGS (any of these = near auto-reject)
- Active criminal cases
- Active fraud/corruption litigation
- Ongoing major regulatory enforcement
- Association with sanctioned entities
- Major unresolved scandals
- Documented corruption investigations

## YELLOW FLAGS (need further investigation)
- Repeated litigation
- Past controversies
- Significant negative media coverage
- Controversial industry involvement
- Unclear financial dealings
- Potential client conflicts

---

## SANCTIONS / WATCHLIST DATA (Step 1)
{sanctions_text}

## DEBARMENT / EXCLUSION DATA (Step 2)
{debarment_text}

## NEWS / MEDIA DATA (Steps 3/10)
{news_text}

## LITIGATION / COURT RECORDS (Step 4)
{litigation_text}

## CORPORATE / BUSINESS DATA (Step 5)
{corporate_text}

## FEC / CAMPAIGN FINANCE DATA (Step 6)
{fec_text}

## SEC / FINANCIAL DATA (Step 7)
{sec_text}

## LOBBYING DATA (Step 8)
{lobbying_text}

## BANKRUPTCY DATA (Step 9)
{bankruptcy_text}

## INTERNATIONAL / PEP DATA (Step 12)
{international_text}

## MANUAL FINDINGS (from human researcher — treat as HIGH-CONFIDENCE primary evidence)
{manual_text}

## TMG CLIENT CONFLICT CHECK (use this for the conflict_of_interest dimension)
{conflicts_text}

---

## SOURCE REFERENCE LIST (use [n] citations in evidence)
{sources_ref}

---

Return ONLY valid JSON (no markdown code fences, no commentary). The JSON must match this exact schema:

{{
  "subject": {{
    "name": "{name}",
    "type": "{subject.get('type', 'individual')}",
    "company": "{company or ''}",
    "country": "{country}",
    "city": "{subject.get('city', '') or ''}"
  }},
  "gates": {{
    "sanctions": {{
      "status": "PASS or FAIL",
      "sources_checked": ["list of sources checked"],
      "matches": [],
      "checked_at": "ISO timestamp"
    }},
    "debarment": {{
      "status": "PASS or FAIL",
      "sources_checked": ["list of sources checked"],
      "matches": [],
      "checked_at": "ISO timestamp"
    }}
  }},
  "dimensions": {{
    "litigation_legal": {{
      "score": 0,
      "weight": 0.22,
      "confidence": "HIGH/MEDIUM/LOW",
      "summary": "1-2 sentence summary of findings",
      "sub_factors": {{
        "criminal_cases": {{"score": 0, "detail": "..."}},
        "civil_fraud_corruption": {{"score": 0, "detail": "..."}},
        "repeated_civil_litigation": {{"score": 0, "detail": "..."}},
        "past_resolved": {{"score": 0, "detail": "..."}},
        "bankruptcy": {{"score": 0, "detail": "..."}}
      }},
      "evidence": [
        {{"text": "Finding description with [n] citation", "source": "Source name", "url": "URL if available", "date": "Date if known", "temporal_weight": 1.0, "source_urls": [{{"url": "https://...", "title": "Source title"}}]}}
      ]
    }},
    "media_reputation": {{
      "score": 0,
      "weight": 0.20,
      "confidence": "HIGH/MEDIUM/LOW",
      "summary": "...",
      "sub_factors": {{}},
      "evidence": []
    }},
    "international_pep": {{
      "score": 0,
      "weight": 0.15,
      "confidence": "HIGH/MEDIUM/LOW",
      "summary": "...",
      "sub_factors": {{
        "pep_status": {{"score": 0, "detail": "..."}},
        "country_risk": {{"score": 0, "detail": "..."}},
        "fara_exposure": {{"score": 0, "detail": "..."}},
        "source_reliability": {{"score": 0, "detail": "..."}}
      }},
      "evidence": []
    }},
    "financial_sec": {{
      "score": 0,
      "weight": 0.12,
      "confidence": "HIGH/MEDIUM/LOW",
      "summary": "...",
      "sub_factors": {{}},
      "evidence": []
    }},
    "corporate_business": {{
      "score": 0,
      "weight": 0.11,
      "confidence": "HIGH/MEDIUM/LOW",
      "summary": "...",
      "sub_factors": {{}},
      "evidence": []
    }},
    "political_lobbying": {{
      "score": 0,
      "weight": 0.10,
      "confidence": "HIGH/MEDIUM/LOW",
      "summary": "...",
      "sub_factors": {{
        "fara_issues": {{"score": 0, "detail": "..."}},
        "investigation_links": {{"score": 0, "detail": "..."}},
        "watchlist_lobbying": {{"score": 0, "detail": "..."}},
        "pay_to_play": {{"score": 0, "detail": "..."}}
      }},
      "evidence": []
    }},
    "conflict_of_interest": {{
      "score": 0,
      "weight": 0.10,
      "confidence": "HIGH/MEDIUM/LOW",
      "summary": "...",
      "sub_factors": {{
        "direct_conflict": {{"score": 0, "detail": "..."}},
        "indirect_conflict": {{"score": 0, "detail": "..."}},
        "future_conflict": {{"score": 0, "detail": "..."}}
      }},
      "evidence": []
    }}
  }},
  "scoring": {{
    "raw_composite": 0.0,
    "engagement_multiplier": {multiplier},
    "adjusted_composite": 0.0,
    "confidence_modifier": "none or bump_one_tier",
    "final_composite": 0.0,
    "risk_tier": "LOW/MODERATE/ELEVATED/HIGH",
    "recommendation": "Approve/Conditional Approve/Further Review/Recommend Reject"
  }},
  "flags": {{
    "red": [
      {{"category": "dimension_key", "title": "Short title", "description": "Detail", "source": "Source", "date": "Date", "severity": "critical/major"}}
    ],
    "yellow": [
      {{"category": "dimension_key", "title": "Short title", "description": "Detail", "source": "Source", "date": "Date", "severity": "moderate/minor"}}
    ]
  }},
  "executive_summary": "## Summary\\n\\nMultiple paragraph executive summary in markdown format suitable for email to TMG leadership. Include: Biography, Professional Background, Key Findings, Risk Assessment, Recommendation.\\n\\n## Key Findings\\n\\n- Finding 1\\n- Finding 2\\n\\n## Recommendation\\n\\n**RECOMMENDATION** — rationale...",
  "reputational_contagion": {{
    "q1_partisan_alignment": {{"score": 0, "weight": 0.25, "evidence": "Specific evidence for partisan alignment score"}},
    "q2_stakeholder_backlash": {{"score": 0, "weight": 0.20, "evidence": "Specific evidence for stakeholder backlash score"}},
    "q3_narrative_vulnerability": {{"score": 0, "weight": 0.15, "evidence": "Specific evidence", "damaging_headline": "The most damaging plausible one-sentence headline"}},
    "q4_client_conflicts": {{"score": 0, "weight": 0.15, "evidence": "Specific evidence for client conflict score"}},
    "q5_industry_toxicity": {{"score": 0, "weight": 0.15, "evidence": "Specific evidence for industry toxicity score"}},
    "q6_temporal_context": {{"score": 0, "weight": 0.10, "evidence": "Specific evidence for temporal context score"}},
    "composite_rcs": 0.0,
    "rcs_risk_tier": "LOW/MODERATE/ELEVATED/HIGH/CRITICAL",
    "rcs_recommendation": "Recommendation based on reputational contagion score",
    "divergence_alert": "If factual risk is LOW but RCS is HIGH, explain the divergence here. Otherwise null.",
    "most_damaging_headline": "Copy the headline from Q3 here"
  }},
  "metadata": {{
    "pipeline_version": "v1.0",
    "vetting_level": "{vetting_level}",
    "steps_completed": [],
    "started_at": "",
    "completed_at": "",
    "total_duration_seconds": 0
  }}
}}

IMPORTANT SCORING RULES:
1. Calculate raw_composite as the weighted average: sum(dimension_score * weight) for all 7 dimensions
2. Apply engagement_multiplier: adjusted_composite = raw_composite * {multiplier}
3. Cap adjusted_composite at 10.0
4. If overall confidence is LOW, set confidence_modifier to "bump_one_tier" and bump the recommendation one tier more cautious
5. Determine risk_tier based on final_composite: 0-2.5=LOW, 2.5-4.5=MODERATE, 4.5-6.5=ELEVATED, 6.5-10=HIGH
6. Set recommendation based on risk_tier: LOW=Approve, MODERATE=Conditional Approve, ELEVATED=Further Review, HIGH=Recommend Reject

---

{rca_prompt}

IMPORTANT RCS SCORING RULES:
7. Calculate composite_rcs = (Q1 * 0.25) + (Q2 * 0.20) + (Q3 * 0.15) + (Q4 * 0.15) + (Q5 * 0.15) + (Q6 * 0.10)
8. Determine rcs_risk_tier: 0-2.5=LOW, 2.5-4.5=MODERATE, 4.5-6.5=ELEVATED, 6.5-8.0=HIGH, 8.0-10=CRITICAL
9. If factual risk_tier is LOW or MODERATE but rcs_risk_tier is HIGH or CRITICAL, set divergence_alert explaining why
10. The reputational_contagion section is REQUIRED — always fill it out completely"""

    return prompt


# ─── JSON Repair ────────────────────────────────────────────

def repair_json(text: str) -> str:
    """Try to extract and repair JSON from Claude's response."""
    # Remove markdown code fences
    fence_match = re.search(r'```(?:json)?\s*\n?(.*?)\n?\s*```', text, re.DOTALL)
    if fence_match:
        text = fence_match.group(1).strip()
    elif not text.strip().startswith("{"):
        brace_idx = text.find("{")
        if brace_idx != -1:
            text = text[brace_idx:]

    # Trim any trailing content after the final }
    last_brace = text.rfind("}")
    if last_brace != -1:
        text = text[:last_brace + 1]

    return text


# ─── Main Synthesis ─────────────────────────────────────────

def run_synthesis(intake: dict) -> dict:
    """Run Claude synthesis on all step data."""

    name = intake["subject"]["name"]
    subject_id = intake["subject_id"]
    vetting_level = intake["context"]["vetting_level"]
    engagement_type = intake["context"]["engagement_type"]

    print(f"  🧠 Step 13: Running Claude synthesis for '{name}'...")

    # Load all step data
    step_data = load_all_step_data(subject_id, vetting_level)

    # Collect all Tavily sources into master list
    sources = collect_tavily_sources(step_data)
    print(f"  Collected {len(sources)} unique web sources for citation enrichment")

    # Build prompt (with sources for [n] citations)
    prompt = build_synthesis_prompt(intake, step_data, sources=sources)

    # Call Claude
    client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)
    response = None

    for attempt in range(3):
        try:
            with client.messages.stream(
                model=config.CLAUDE_MODEL,
                max_tokens=8000,
                messages=[{"role": "user", "content": prompt}],
            ) as stream:
                response = stream.get_final_message()
            break
        except Exception as e:
            print(f"  Attempt {attempt + 1} failed: {e}")
            if attempt < 2:
                time.sleep(10)
            else:
                print("  ERROR: All 3 Claude API attempts failed")
                return {"error": "Claude API failed after 3 attempts", "subject_id": subject_id}

    if not response or not response.content:
        print("  WARNING: Empty response from Claude")
        return {"error": "Empty Claude response", "subject_id": subject_id}

    response_text = response.content[0].text.strip()

    # Parse JSON
    cleaned = repair_json(response_text)
    try:
        synthesized = json.loads(cleaned)
    except json.JSONDecodeError as e:
        print(f"  ERROR: JSON parse failed: {e}")
        error_path = config.UNIFIED_DIR / f"{subject_id}_raw_response.txt"
        with open(error_path, "w") as f:
            f.write(response_text)
        print(f"  Raw response saved to: {error_path}")
        return {"error": f"JSON parse failed: {e}", "subject_id": subject_id}

    # ── Enrich evidence with Tavily source URLs ──
    synthesized = enrich_evidence_with_sources(synthesized, sources)

    # ── Inject master sources array ──
    # Strip content_snippet from output (was only for prompt building)
    synthesized["sources"] = [
        {"id": s["id"], "url": s["url"], "title": s["title"], "score": s["score"]}
        for s in sources
    ]

    # ── Validate and fix scoring ──
    dimensions = synthesized.get("dimensions", {})
    weighted_sum = 0.0
    total_weight = 0.0
    dim_confidence = []

    for dim_key, dim_config in config.RISK_DIMENSIONS.items():
        dim_data = dimensions.get(dim_key, {})
        score = dim_data.get("score", 0)
        if isinstance(score, str):
            try:
                score = float(score)
            except ValueError:
                score = 0.0
        score = max(0, min(10, float(score)))
        weight = dim_config["weight"]

        # Ensure weight is set correctly
        dim_data["weight"] = weight
        dim_data["score"] = score
        dimensions[dim_key] = dim_data

        weighted_sum += score * weight
        total_weight += weight
        dim_confidence.append(dim_data.get("confidence", "MEDIUM"))

    raw_composite = round(weighted_sum / total_weight, 2) if total_weight > 0 else 0
    multiplier = config.ENGAGEMENT_MULTIPLIERS.get(engagement_type, 1.0)
    adjusted_composite = round(min(10, raw_composite * multiplier), 2)

    # Determine overall confidence
    low_count = sum(1 for c in dim_confidence if c == "LOW")
    if low_count >= 3:
        overall_confidence = "LOW"
        confidence_modifier = "bump_one_tier"
    elif low_count >= 1:
        overall_confidence = "MEDIUM"
        confidence_modifier = "none"
    else:
        overall_confidence = "HIGH"
        confidence_modifier = "none"

    final_composite = adjusted_composite

    # Get risk tier
    tier_info = config.get_risk_tier(final_composite)

    # Apply confidence bump if needed
    recommendation = tier_info["recommendation"]
    if confidence_modifier == "bump_one_tier":
        tier_idx = config.RISK_TIERS.index(tier_info)
        if tier_idx < len(config.RISK_TIERS) - 1:
            tier_info = config.RISK_TIERS[tier_idx + 1]
            recommendation = tier_info["recommendation"]

    # Update scoring in synthesized output
    synthesized["scoring"] = {
        "raw_composite": raw_composite,
        "engagement_multiplier": multiplier,
        "adjusted_composite": adjusted_composite,
        "confidence_modifier": confidence_modifier,
        "final_composite": final_composite,
        "risk_tier": tier_info["tier"],
        "recommendation": recommendation,
    }

    # ── Validate and fix Reputational Contagion Score ──
    rca = synthesized.get("reputational_contagion", {})
    rcs_weights = {
        "q1_partisan_alignment": 0.25,
        "q2_stakeholder_backlash": 0.20,
        "q3_narrative_vulnerability": 0.15,
        "q4_client_conflicts": 0.15,
        "q5_industry_toxicity": 0.15,
        "q6_temporal_context": 0.10,
    }
    rcs_weighted_sum = 0.0
    for q_key, q_weight in rcs_weights.items():
        q_data = rca.get(q_key, {})
        q_score = q_data.get("score", 0)
        if isinstance(q_score, str):
            try:
                q_score = float(q_score)
            except ValueError:
                q_score = 0.0
        q_score = max(0, min(10, float(q_score)))
        q_data["score"] = q_score
        q_data["weight"] = q_weight
        rca[q_key] = q_data
        rcs_weighted_sum += q_score * q_weight

    composite_rcs = round(rcs_weighted_sum, 2)
    rcs_tier_info = get_rcs_tier(composite_rcs)
    rca["composite_rcs"] = composite_rcs
    rca["rcs_risk_tier"] = rcs_tier_info["tier"]
    rca["rcs_recommendation"] = rcs_tier_info["recommendation"]

    # Check for divergence between factual and reputational scores
    factual_tier = tier_info["tier"]
    rcs_tier = rcs_tier_info["tier"]
    if factual_tier in ("LOW", "MODERATE") and rcs_tier in ("HIGH", "CRITICAL"):
        rca["divergence_alert"] = (
            f"DIVERGENCE: Factual risk is {factual_tier} ({final_composite}/10) but "
            f"reputational contagion risk is {rcs_tier} ({composite_rcs}/10). "
            f"Subject passes traditional due diligence screening but poses significant "
            f"reputational risk to TMG's brand and stakeholder relationships."
        )
    else:
        rca["divergence_alert"] = None

    # Propagate headline from Q3
    q3_data = rca.get("q3_narrative_vulnerability", {})
    rca["most_damaging_headline"] = q3_data.get("damaging_headline", "N/A")

    synthesized["reputational_contagion"] = rca

    # Count enrichment stats
    total_evidence = 0
    enriched_evidence = 0
    total_source_urls = 0
    for dim_data in dimensions.values():
        for ev in dim_data.get("evidence", []):
            total_evidence += 1
            su = ev.get("source_urls", [])
            if su:
                enriched_evidence += 1
                total_source_urls += len(su)

    # Update metadata
    synthesized["metadata"] = {
        "pipeline_version": "v1.1",
        "vetting_level": vetting_level,
        "steps_completed": [k for k, v in step_data.items() if v],
        "started_at": intake.get("metadata", {}).get("created_at", ""),
        "completed_at": datetime.now(timezone.utc).isoformat(),
        "total_duration_seconds": 0,
        "model": config.CLAUDE_MODEL,
        "input_tokens": response.usage.input_tokens,
        "output_tokens": response.usage.output_tokens,
        "tavily_sources": len(sources),
        "citation_enrichment": {
            "total_evidence_items": total_evidence,
            "items_with_source_urls": enriched_evidence,
            "total_source_urls_added": total_source_urls,
        },
    }

    # Save
    output_path = config.UNIFIED_DIR / f"{subject_id}.json"
    with open(output_path, "w") as f:
        json.dump(synthesized, f, indent=2)

    file_size = output_path.stat().st_size / 1024
    print(f"  ✅ Step 13: Synthesis complete → {output_path.name} ({file_size:.1f} KB)")
    print(f"  Tokens: {response.usage.input_tokens} in, {response.usage.output_tokens} out")
    print(f"  Composite Score: {final_composite}/10 ({tier_info['tier']})")
    print(f"  Recommendation: {recommendation}")
    print(f"  Confidence: {overall_confidence}")

    # Print dimension scores
    for dim_key, dim_config in config.RISK_DIMENSIONS.items():
        dim_data = dimensions.get(dim_key, {})
        print(f"    {dim_config['label']}: {dim_data.get('score', '?')}/10 ({dim_data.get('confidence', '?')})")

    # Print Reputational Contagion Score
    print(f"\n  --- Reputational Contagion Analysis ---")
    print(f"  RCS Composite: {composite_rcs}/10 ({rcs_tier_info['tier']})")
    print(f"  RCS Recommendation: {rcs_tier_info['recommendation']}")
    rcs_labels = {
        "q1_partisan_alignment": "Partisan Alignment",
        "q2_stakeholder_backlash": "Stakeholder Backlash",
        "q3_narrative_vulnerability": "Narrative Vulnerability",
        "q4_client_conflicts": "Client Conflicts",
        "q5_industry_toxicity": "Industry Toxicity",
        "q6_temporal_context": "Temporal Context",
    }
    for q_key, q_label in rcs_labels.items():
        q_data = rca.get(q_key, {})
        print(f"    {q_label}: {q_data.get('score', '?')}/10")
    headline = rca.get("most_damaging_headline", "N/A")
    if headline and headline != "N/A":
        print(f"  Most Damaging Headline: \"{headline}\"")
    if rca.get("divergence_alert"):
        print(f"  !! {rca['divergence_alert']}")

    return synthesized


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Step 13: Claude Synthesis")
    parser.add_argument("--subject-id", required=True)
    args = parser.parse_args()

    intake_path = config.INTAKE_DIR / f"{args.subject_id}.json"
    with open(intake_path) as f:
        intake = json.load(f)

    result = run_synthesis(intake)
    if result.get("error"):
        print(f"\nERROR: {result['error']}")
    else:
        scoring = result.get("scoring", {})
        rca = result.get("reputational_contagion", {})
        print(f"\n{'='*50}")
        print(f"FACTUAL Risk Score: {scoring.get('final_composite', 'N/A')}/10 ({scoring.get('risk_tier', 'N/A')})")
        print(f"REPUTATIONAL Contagion Score: {rca.get('composite_rcs', 'N/A')}/10 ({rca.get('rcs_risk_tier', 'N/A')})")
        print(f"Factual Recommendation: {scoring.get('recommendation', 'N/A')}")
        print(f"Reputational Recommendation: {rca.get('rcs_recommendation', 'N/A')}")
        if rca.get("divergence_alert"):
            print(f"\n!! DIVERGENCE ALERT: {rca['divergence_alert']}")
        print(f"{'='*50}")
