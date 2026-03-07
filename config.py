"""
TMG Client Vetting Pipeline — Central Configuration
====================================================
All API keys, endpoints, scoring weights, and pipeline settings in one place.
Modeled after /Users/shannonwheatman/palantir/config.py
"""

import os
import ssl
import certifi
from pathlib import Path
from dotenv import load_dotenv

# ─── Project Paths ──────────────────────────────────────────
PROJECT_ROOT = Path(__file__).parent
load_dotenv(PROJECT_ROOT / ".env", override=True)

DATA_DIR = PROJECT_ROOT / "data"
SCRIPTS_DIR = PROJECT_ROOT / "scripts"

# Data subdirectories (one per pipeline step)
INTAKE_DIR = DATA_DIR / "intake"
SANCTIONS_DIR = DATA_DIR / "sanctions"
DEBARMENT_DIR = DATA_DIR / "debarment"
NEWS_DIR = DATA_DIR / "news"
LITIGATION_DIR = DATA_DIR / "litigation"
CORPORATE_DIR = DATA_DIR / "corporate"
FEC_DIR = DATA_DIR / "fec"
SEC_DIR = DATA_DIR / "sec"
LOBBYING_DIR = DATA_DIR / "lobbying"
BANKRUPTCY_DIR = DATA_DIR / "bankruptcy"
SOCIAL_MEDIA_DIR = DATA_DIR / "social_media"
INTERNATIONAL_DIR = DATA_DIR / "international"
UNIFIED_DIR = DATA_DIR / "unified"
CACHE_DIR = DATA_DIR / "cache"

# Create all directories
for d in [INTAKE_DIR, SANCTIONS_DIR, DEBARMENT_DIR, NEWS_DIR, LITIGATION_DIR,
          CORPORATE_DIR, FEC_DIR, SEC_DIR, LOBBYING_DIR, BANKRUPTCY_DIR,
          SOCIAL_MEDIA_DIR, INTERNATIONAL_DIR, UNIFIED_DIR, CACHE_DIR]:
    d.mkdir(parents=True, exist_ok=True)

# ─── SSL Context (macOS Python fix) ────────────────────────
SSL_CTX = ssl.create_default_context(cafile=certifi.where())

# ─── API Keys ───────────────────────────────────────────────
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")
FEC_API_KEY = os.getenv("FEC_API_KEY")
CONGRESS_GOV_API_KEY = os.getenv("CONGRESS_GOV_API_KEY")
OPENSANCTIONS_API_KEY = os.getenv("OPENSANCTIONS_API_KEY")
LDA_API_KEY = os.getenv("LDA_API_KEY")
SAM_GOV_API_KEY = os.getenv("SAM_GOV_API_KEY")
COURTLISTENER_API_TOKEN = os.getenv("COURTLISTENER_API_TOKEN")
SEC_EDGAR_USER_AGENT = os.getenv("SEC_EDGAR_USER_AGENT", "TMG Vetting Pipeline contact@themessinagroup.com")

# ─── API Endpoints ──────────────────────────────────────────
ENDPOINTS = {
    # Sanctions / Watchlists (Step 1)
    "opensanctions_match": "https://api.opensanctions.org/match/default",
    "interpol_red_notices": "https://ws-public.interpol.int/notices/v1/red",

    # Debarment / Exclusion (Step 2)
    "sam_gov_exclusions": "https://api.sam.gov/entity-information/v4/exclusions",

    # News / Media (Steps 3, 10)
    "tavily_search": "https://api.tavily.com/search",

    # Litigation (Step 4)
    "courtlistener_search": "https://www.courtlistener.com/api/rest/v4/search/",
    "courtlistener_dockets": "https://www.courtlistener.com/api/rest/v4/dockets/",

    # Corporate / Business (Step 5)
    "sec_edgar_company": "https://efts.sec.gov/LATEST/search-index",
    "sec_edgar_submissions": "https://data.sec.gov/submissions/",
    "gleif_lei": "https://api.gleif.org/api/v1/lei-records",

    # Campaign Finance (Step 6)
    "openfec_candidates": "https://api.open.fec.gov/v1/candidates/search/",
    "openfec_receipts": "https://api.open.fec.gov/v1/schedules/schedule_a/",
    "openfec_committees": "https://api.open.fec.gov/v1/committees/",

    # SEC Filings (Step 7)
    "sec_efts_search": "https://efts.sec.gov/LATEST/search-index",

    # Lobbying (Step 8)
    "senate_lda_filings": "https://lda.senate.gov/api/v1/filings/",
    "senate_lda_registrants": "https://lda.senate.gov/api/v1/registrants/",
    "senate_lda_lobbyists": "https://lda.senate.gov/api/v1/lobbyists/",

    # Bankruptcy (Step 9) — uses CourtListener
    "courtlistener_bankruptcy": "https://www.courtlistener.com/api/rest/v4/search/",

    # International (Step 12)
    "opensanctions_pep": "https://api.opensanctions.org/match/peps",
    "propublica_nonprofits": "https://projects.propublica.org/nonprofits/api/v2/search.json",
}

# ─── Vetting Levels ─────────────────────────────────────────
VETTING_LEVELS = {
    "quick_screen": {
        "label": "Quick Screen",
        "steps": [0, 1, 2, 3, 13],  # Intake, Sanctions, Debarment, Basic News, Synthesis
        "description": "Sanctions, debarment, basic news scan. ~5 minutes.",
    },
    "standard_vet": {
        "label": "Standard Vet",
        "steps": [0, 1, 2, 3, 4, 5, 6, 7, 8, 13],  # + Litigation, Corporate, FEC, SEC, Lobbying
        "description": "Full domestic background check. ~15 minutes.",
    },
    "deep_dive": {
        "label": "Deep Dive",
        "steps": [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 12, 13],  # Everything (Step 11 folded into Step 10)
        "description": "Comprehensive investigation. ~30 minutes.",
    },
}

# Step number → script name mapping
STEP_SCRIPTS = {
    0: "intake.py",
    1: "check_sanctions.py",
    2: "check_debarment.py",
    3: "search_news.py",
    4: "search_litigation.py",
    5: "search_corporate.py",
    6: "search_fec.py",
    7: "search_sec.py",
    8: "search_lobbying.py",
    9: "search_bankruptcy.py",
    10: "search_news.py",        # --deep mode
    11: "search_social.py",
    12: "search_international.py",
    13: "synthesize.py",
}

STEP_NAMES = {
    0: "Intake",
    1: "Sanctions/Watchlist Check",
    2: "Government Debarment/Exclusion",
    3: "News/Media Scan",
    4: "Court Records/Litigation",
    5: "Corporate Filings",
    6: "FEC/Campaign Finance",
    7: "SEC Filings",
    8: "Lobbying Disclosures",
    9: "Bankruptcy Filings",
    10: "Expanded News/Media (Deep)",
    11: "Social Media Review",
    12: "International Checks",
    13: "Claude Synthesis",
}

# ─── Risk Scoring Configuration ─────────────────────────────

# Binary Pre-Check Gates (PASS/FAIL)
BINARY_GATES = {
    "sanctions": {
        "label": "Sanctions / Watchlist Gate",
        "sources": ["OFAC SDN", "UN Sanctions", "EU Sanctions", "OpenSanctions", "Interpol"],
        "fail_result": "AUTO-REJECT",
        "fail_tier": "CRITICAL",
    },
    "debarment": {
        "label": "Government Exclusion Gate",
        "sources": ["SAM.gov Exclusions", "HHS OIG LEIE"],
        "fail_result": "AUTO-REJECT",
        "fail_tier": "CRITICAL",
    },
}

# Weighted Risk Dimensions (7 dimensions, sum to 1.0)
RISK_DIMENSIONS = {
    "litigation_legal": {
        "label": "Litigation / Legal Risk",
        "weight": 0.22,
        "sub_factors": ["criminal_cases", "civil_fraud_corruption", "repeated_civil_litigation", "past_resolved", "bankruptcy"],
    },
    "media_reputation": {
        "label": "Media / Reputation Risk",
        "weight": 0.20,
        "sub_factors": ["major_scandals", "investigations", "negative_coverage", "social_media_findings"],
    },
    "international_pep": {
        "label": "International / PEP Risk",
        "weight": 0.15,
        "sub_factors": ["pep_status", "country_risk", "fara_exposure", "source_reliability"],
    },
    "financial_sec": {
        "label": "Financial / SEC Risk",
        "weight": 0.12,
        "sub_factors": ["sec_enforcement", "financial_irregularities", "unclear_financials"],
    },
    "corporate_business": {
        "label": "Corporate / Business Risk",
        "weight": 0.11,
        "sub_factors": ["ownership_complexity", "shell_companies", "unclear_affiliations"],
    },
    "political_lobbying": {
        "label": "Political / Lobbying Risk",
        "weight": 0.10,
        "sub_factors": ["fara_issues", "investigation_links", "watchlist_lobbying", "pay_to_play"],
    },
    "conflict_of_interest": {
        "label": "Conflict of Interest",
        "weight": 0.10,
        "sub_factors": ["direct_conflict", "indirect_conflict", "future_conflict"],
    },
}

# Verify weights sum to 1.0
assert abs(sum(d["weight"] for d in RISK_DIMENSIONS.values()) - 1.0) < 0.001, \
    f"Risk dimension weights must sum to 1.0, got {sum(d['weight'] for d in RISK_DIMENSIONS.values())}"

# Engagement Context Multipliers
ENGAGEMENT_MULTIPLIERS = {
    "fara_foreign_political": 1.3,
    "foreign_corporate": 1.15,
    "domestic_political": 1.0,
    "domestic_corporate": 0.85,
}

# Temporal Decay Factors
TEMPORAL_DECAY = {
    "0-2_years": 1.0,
    "2-5_years": 0.7,
    "5-10_years": 0.4,
    "10+_years": 0.2,
}

# Risk Tier Thresholds
RISK_TIERS = [
    {"range": (0, 2.5), "tier": "LOW", "recommendation": "Approve", "action": "Standard engagement terms"},
    {"range": (2.5, 4.5), "tier": "MODERATE", "recommendation": "Conditional Approve", "action": "Engagement-specific caveats; documented rationale"},
    {"range": (4.5, 6.5), "tier": "ELEVATED", "recommendation": "Further Review", "action": "Manual deep-dive by vetter; leadership sign-off required"},
    {"range": (6.5, 10.01), "tier": "HIGH", "recommendation": "Recommend Reject", "action": "Partnership-level decision required to override"},
]

def get_risk_tier(composite_score: float) -> dict:
    """Return the risk tier dict for a given composite score."""
    for tier in RISK_TIERS:
        low, high = tier["range"]
        if low <= composite_score < high:
            return tier
    return RISK_TIERS[-1]  # Default to HIGH if somehow out of range


# ─── Tavily Search Configuration ────────────────────────────
TAVILY_BASIC_QUERIES = [
    "{name} controversy scandal",
    "{name} lawsuit litigation legal",
    "{name} {company} background",
]

TAVILY_DEEP_QUERIES = [
    "{name} controversy scandal investigation",
    "{name} lawsuit litigation fraud",
    "{name} criminal indictment conviction",
    "{name} sanctions violations regulatory",
    "{name} political donations lobbying",
    "{name} SEC enforcement violation",
    "{name} bankruptcy financial problems",
    "{name} {company} business dealings",
    "{name} social media statements views",
    "{name} international connections foreign",
    "{name} corruption bribery",
    "{name} {company} reputation reviews",
    # Social media targeted queries (folded from eliminated Step 11)
    "{name} site:twitter.com OR site:x.com",
    "{name} social media statements controversial",
    "{name} facebook linkedin public posts",
]

# ─── Pipeline Settings ──────────────────────────────────────
REQUEST_DELAY = 0.5  # seconds between API calls (rate limiting)
REQUEST_TIMEOUT = 15  # seconds
MAX_RETRIES = 2

# Claude Synthesis Model
CLAUDE_MODEL = "claude-opus-4-0"  # Opus 4 for highest quality synthesis

# ─── TMG Team ───────────────────────────────────────────────
TMG_TEAM = ["Jim", "Ben", "Tara", "Shannon"]
DEFAULT_CC = ["Tara"]  # Tara is almost always CC'd


def verify_keys():
    """Print status of all API keys."""
    keys = {
        "ANTHROPIC_API_KEY": ANTHROPIC_API_KEY,
        "TAVILY_API_KEY": TAVILY_API_KEY,
        "FEC_API_KEY": FEC_API_KEY,
        "CONGRESS_GOV_API_KEY": CONGRESS_GOV_API_KEY,
        "OPENSANCTIONS_API_KEY": OPENSANCTIONS_API_KEY,
        "LDA_API_KEY": LDA_API_KEY,
        "SAM_GOV_API_KEY": SAM_GOV_API_KEY,
        "COURTLISTENER_API_TOKEN": COURTLISTENER_API_TOKEN,
    }
    print("=" * 50)
    print("TMG Vetting Pipeline — API Key Status")
    print("=" * 50)
    all_good = True
    for name, val in keys.items():
        if val:
            print(f"  ✅ {name} = {val[:12]}...")
        else:
            print(f"  ❌ {name} = MISSING")
            all_good = False
    print("=" * 50)
    return all_good


if __name__ == "__main__":
    verify_keys()
