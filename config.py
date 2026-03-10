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
EXECUTIVES_DIR = DATA_DIR / "executives"
INTERNATIONAL_DIR = DATA_DIR / "international"
CONTRACTS_DIR = DATA_DIR / "contracts"
NETWORK_DIR = DATA_DIR / "network"
MANUAL_DIR = DATA_DIR / "manual"
UNIFIED_DIR = DATA_DIR / "unified"
CACHE_DIR = DATA_DIR / "cache"

# Create all directories
for d in [INTAKE_DIR, SANCTIONS_DIR, DEBARMENT_DIR, NEWS_DIR, LITIGATION_DIR,
          CORPORATE_DIR, FEC_DIR, SEC_DIR, LOBBYING_DIR, BANKRUPTCY_DIR,
          SOCIAL_MEDIA_DIR, EXECUTIVES_DIR, INTERNATIONAL_DIR, CONTRACTS_DIR,
          NETWORK_DIR, MANUAL_DIR, UNIFIED_DIR, CACHE_DIR]:
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
OPENCORPORATES_API_KEY = os.getenv("OPENCORPORATES_API_KEY", "")  # Free tier — register at opencorporates.com

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

    # Government Contracts (Step 14) — no API key needed
    "usaspending_awards": "https://api.usaspending.gov/api/v2/search/spending_by_award/",

    # Corporate Network Discovery (Step 15) — OpenCorporates free tier
    "opencorporates_search": "https://api.opencorporates.com/v0.4/companies/search",
    "opencorporates_officers": "https://api.opencorporates.com/v0.4/officers/search",
}

# ─── Vetting Levels ─────────────────────────────────────────
VETTING_LEVELS = {
    "deep_dive": {
        "label": "Deep Dive",
        "steps": [0, 1, 2, 3, 4, 5, 15, 6, 7, 8, 9, 10, 11, 12, 14, 13],  # Everything
        "description": "Comprehensive investigation with corporate network, executive vetting and gov contracts.",
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
    11: "search_executives.py",
    12: "search_international.py",
    13: "synthesize.py",
    14: "search_contracts.py",
    15: "search_network.py",
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
    11: "Executive Identification & Mini-Vet",
    12: "International Checks",
    13: "Claude Synthesis",
    14: "Government Contracts",
    15: "Corporate Network Discovery (OpenCorporates)",
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

# International Risk Dimension Overrides
# For non-US subjects, FEC/SEC/Lobbying data won't exist.
# Redistribute that weight (0.10 + 0.12 + 0.10 = 0.32) to dimensions with data.
RISK_DIMENSIONS_INTERNATIONAL = {
    "litigation_legal": {
        "label": "Litigation / Legal Risk",
        "weight": 0.12,   # Reduced — no US court data, only news-based legal findings
        "sub_factors": ["criminal_cases", "civil_fraud_corruption", "repeated_civil_litigation", "past_resolved", "bankruptcy"],
    },
    "media_reputation": {
        "label": "Media / Reputation Risk",
        "weight": 0.30,   # Major increase — Tavily news is the primary evidence source
        "sub_factors": ["major_scandals", "investigations", "negative_coverage", "social_media_findings"],
    },
    "international_pep": {
        "label": "International / PEP Risk",
        "weight": 0.30,   # Major increase — PEP status, country risk are central for foreign subjects
        "sub_factors": ["pep_status", "country_risk", "fara_exposure", "source_reliability"],
    },
    "financial_sec": {
        "label": "Financial / Regulatory Risk",
        "weight": 0.06,   # Reduced — no SEC data, but financial irregularities may appear in news
        "sub_factors": ["sec_enforcement", "financial_irregularities", "unclear_financials"],
    },
    "corporate_business": {
        "label": "Corporate / Business Risk",
        "weight": 0.07,   # Slightly reduced — GLEIF still works, but no US corporate filings
        "sub_factors": ["ownership_complexity", "shell_companies", "unclear_affiliations"],
    },
    "political_lobbying": {
        "label": "Political / Lobbying Risk",
        "weight": 0.05,   # Reduced — no LDA data, but political risk still relevant from news
        "sub_factors": ["fara_issues", "investigation_links", "watchlist_lobbying", "pay_to_play"],
    },
    "conflict_of_interest": {
        "label": "Conflict of Interest",
        "weight": 0.10,   # Unchanged — TMG client conflicts apply regardless of country
        "sub_factors": ["direct_conflict", "indirect_conflict", "future_conflict"],
    },
}

# Verify international weights sum to 1.0
assert abs(sum(d["weight"] for d in RISK_DIMENSIONS_INTERNATIONAL.values()) - 1.0) < 0.001, \
    f"International risk dimension weights must sum to 1.0, got {sum(d['weight'] for d in RISK_DIMENSIONS_INTERNATIONAL.values())}"

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

# Additional queries when subject_type == "organization"
TAVILY_ORG_QUERIES = [
    "{name} boycott protest activist opposition campaign",
    "{name} CEO executive statements controversial remarks",
    "{name} government contracts federal spending agency",
    "{name} donations political money returned rejected",
    "{name} employee dissent whistleblower internal opposition",
    "{name} surveillance enforcement immigration civil liberties",
]

# Universal investigator-style queries (per Kroll/Control Risks/Nardello patterns)
# Pair subject name with crime categories and legal verbs.
# Applied to ALL deep searches regardless of country.
TAVILY_INVESTIGATOR_QUERIES = [
    "{name} investigation probe inquiry",
    "{name} indicted charged prosecutors",
    "{name} money laundering bribery kickbacks",
    "{name} sanctions blacklist designated",
    "{name} tax evasion offshore accounts",
    "{name} shell company front company",
    "{name} fraud embezzlement misappropriation",
    "{name} arrest warrant detained",
]

# Red flag category queries beyond corruption (per Perplexity recommendations)
# Human rights, environmental, labor, kleptocracy, family/dynastic networks
TAVILY_RED_FLAG_QUERIES = [
    "{name} human rights violations abuses",
    "{name} torture extrajudicial killings forced disappearance",
    "{name} environmental disaster pollution oil spill",
    "{name} forced labor child labor sweatshop wage theft",
    "{name} kleptocracy state capture oligarch",
    "{name} unexplained wealth illicit enrichment",
    "{name} family dynasty political business network",
    "{name} terrorism financing extremism",
]

# Reverse queries: search for the scandal first, see if subject appears.
# Uses {country} and optionally {sector}. Only for international subjects.
TAVILY_REVERSE_QUERIES = [
    "corruption scandal {country} {sector}",
    "bribery investigation {country} {sector}",
    "money laundering {country} {sector}",
    "sanctions evasion {country}",
]

# ─── Industry Context Queries ─────────────────────────────────
# Sector-level background queries that do NOT include the subject name.
# These provide industry context for the synthesis but are NOT used in risk scoring.
# Keyed by sector (inferred from bio/engagement in search_news.py).
TAVILY_INDUSTRY_CONTEXT_QUERIES = {
    "defense_tech": [
        "defense technology industry controversy ethics 2024 2025",
        "autonomous weapons AI military ethics debate",
        "defense contractor government oversight accountability",
        "border surveillance technology civil liberties concerns",
        "Pentagon defense tech startup contracting controversy",
    ],
    "energy": [
        "oil gas industry environmental controversy 2024 2025",
        "energy company regulatory enforcement actions",
        "fossil fuel industry climate litigation",
    ],
    "pharma_health": [
        "pharmaceutical industry pricing controversy 2024 2025",
        "biotech regulatory enforcement FDA warning",
        "healthcare company fraud whistleblower",
    ],
    "finance": [
        "financial services industry regulatory enforcement 2024 2025",
        "bank fintech compliance controversy",
        "investment fund SEC enforcement action",
    ],
    "tech": [
        "big tech industry regulation antitrust 2024 2025",
        "AI technology ethics controversy surveillance",
        "tech company data privacy enforcement",
    ],
    "government": [
        "political corruption trends enforcement 2024 2025",
        "government official ethics violations investigations",
    ],
    "general_corporate": [
        "corporate governance scandal controversy 2024 2025",
        "ESG controversy corporate accountability",
    ],
}

# ─── Pipeline Settings ──────────────────────────────────────
REQUEST_DELAY = 0.5  # seconds between API calls (rate limiting)
REQUEST_TIMEOUT = 30  # seconds (bumped from 15 — CourtListener pagination was timing out)
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
