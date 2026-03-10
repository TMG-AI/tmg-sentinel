"""
TMG Vetting Pipeline — Tavily Search Configuration
Source quality controls for due diligence research.

Based on Perplexity report: "TMG Vetting Pipeline: Tavily Domain Configuration & Source Quality Guide"
Strategy: exclude list globally; include lists only for targeted, dimension-specific searches.
"""

# ==============================================================
# GLOBAL EXCLUDE LIST (apply to ALL Tavily search calls)
# ==============================================================

EXCLUDE_DOMAINS_UGC = [
    "wikipedia.org", "reddit.com", "quora.com", "medium.com",
    "substack.com", "tumblr.com", "livejournal.com", "blogspot.com",
    "wordpress.com", "answers.yahoo.com", "wikihow.com", "ehow.com",
    "about.com", "hubpages.com", "squidoo.com",
]

EXCLUDE_DOMAINS_TABLOIDS_PARTISAN = [
    "dailymail.co.uk", "nypost.com", "thesun.co.uk", "thesun.com",
    "mirror.co.uk", "express.co.uk", "newsbreak.com", "msn.com",
    "yahoo.com", "aol.com", "patch.com", "examiner.com", "inquisitr.com",
    "breitbart.com", "infowars.com", "naturalnews.com", "zerohedge.com",
    "thegatewaypundit.com", "oann.com", "newsmax.com",
    "occupydemocrats.com", "palmerreport.com", "dailycaller.com",
    "dailywire.com", "epochtimes.com", "bipartisanreport.com",
    "addictinginfo.org", "buzzfeed.com",
    # NOTE: expressnews.com REMOVED — it's Express News Pakistan, a legitimate source
]

EXCLUDE_DOMAINS_STATE_MEDIA = [
    "rt.com", "sputniknews.com", "tass.com",
    "globaltimes.cn", "presstv.ir", "kcna.kp",
]

EXCLUDE_DOMAINS_NOISE = [
    "sitejabber.com", "trustpilot.com", "glassdoor.com", "indeed.com",
    "yelp.com", "bbb.org", "ripoffreport.com", "complaintsboard.com",
    "pissedconsumer.com", "scamadviser.com", "celebrity-net-worth.com",
    "famousbirthdays.com", "imdb.com", "pinterest.com", "tiktok.com",
    "instagram.com", "facebook.com", "linkedin.com",
]

TAVILY_GLOBAL_EXCLUDE = (
    EXCLUDE_DOMAINS_UGC
    + EXCLUDE_DOMAINS_TABLOIDS_PARTISAN
    + EXCLUDE_DOMAINS_STATE_MEDIA
    + EXCLUDE_DOMAINS_NOISE
)
# Current count: ~65 domains (well under Tavily's 150 limit)


# ==============================================================
# INCLUDE LISTS (use per-step, NOT globally)
# ==============================================================

INCLUDE_NEWS_WIRE = [
    "apnews.com", "reuters.com", "bbc.com", "bbc.co.uk",
]

INCLUDE_INVESTIGATIVE = [
    # US quality newspapers
    "nytimes.com", "washingtonpost.com", "wsj.com", "bloomberg.com",
    "ft.com", "economist.com", "propublica.org", "icij.org",
    "occrp.org", "publicintegrity.org", "revealnews.org",
    "theguardian.com", "newyorker.com", "theatlantic.com",
    "latimes.com", "bostonglobe.com", "inquirer.com",
    "politico.com", "pbs.org", "npr.org",
    # Business/financial press
    "fortune.com", "forbes.com", "cnbc.com",
    # International quality press
    "dw.com", "france24.com", "aljazeera.com", "scmp.com",
]

INCLUDE_POLITICAL = [
    "opensecrets.org", "fec.gov", "politico.com", "thehill.com",
    "rollcall.com", "congress.gov", "govtrack.us", "ballotpedia.org",
    "followthemoney.org", "justice.gov", "c-span.org",
]

INCLUDE_LEGAL = [
    "law360.com", "law.com", "courtlistener.com", "pacermonitor.com",
    "sec.gov", "sec.report", "justice.gov", "ftc.gov", "finra.org",
    "treasury.gov", "govinfo.gov", "law.cornell.edu",
]

INCLUDE_INTERNATIONAL = [
    # International orgs & watchdogs
    "transparency.org", "globalwitness.org", "opensanctions.org",
    "worldbank.org", "fatf-gafi.org", "un.org", "state.gov",
    "icij.org", "occrp.org", "cfr.org", "hrw.org", "amnesty.org",
    "freedomhouse.org", "chathamhouse.org", "brookings.edu",
    "carnegieendowment.org", "csis.org", "rand.org",
    # Cross-border investigative networks
    "thebureauinvestigates.com", "correctiv.org", "bellingcat.com",
    # Key regional quality press (English-language)
    "dawn.com", "thenews.com.pk", "tribune.com.pk",           # Pakistan
    "thehindu.com", "indianexpress.com", "livemint.com",       # India
    "dailymaverick.co.za", "mg.co.za",                          # South Africa
    "premiumtimesng.com", "thecable.ng",                        # Nigeria
    "nation.africa",                                             # Kenya
    "inquirer.net", "rappler.com",                               # Philippines
    "thenationalnews.com",                                       # UAE/Gulf
    "hurriyetdailynews.com",                                     # Turkey
]

INCLUDE_CORPORATE = [
    "sec.gov", "sec.report", "gleif.org", "crunchbase.com",
    "bloomberg.com", "ft.com", "wsj.com",
    "businesswire.com", "prnewswire.com", "globenewswire.com",
    "accesswire.com", "dnb.com", "pitchbook.com",
]


# ==============================================================
# HELPER: Build Tavily search params per step
# ==============================================================

def get_tavily_params(step: str, query: str, **overrides) -> dict:
    """
    Returns Tavily API params with appropriate domain filtering
    for each pipeline step.

    Steps:
        news_basic      — Step 3: Quick news scan (basic, 1yr)
        news_deep       — Step 10: Deep news investigation (advanced, all time)
        news_deep_investigative — Step 10: Investigative sources only
        social_media    — Step 11: Social profile search
        political       — Step 6/8: FEC/lobbying context
        legal           — Step 4/7/9: Litigation/regulatory
        international   — Step 12: International sources
        international_local — Step 12: Local foreign media
        corporate       — Step 5: Corporate filings
        synthesis_gapfill — Step 13: Targeted verification
    """
    base = {
        "query": query,
        "search_depth": "advanced",
        "max_results": 10,
        "exclude_domains": list(TAVILY_GLOBAL_EXCLUDE),
        "include_answer": False,
        "include_raw_content": False,
    }

    step_config = {
        "news_basic": {
            "topic": "news",
            "search_depth": "basic",
            "max_results": 10,
            "time_range": "year",
        },
        "news_deep": {
            "topic": "news",
            "search_depth": "advanced",
            "max_results": 15,
        },
        "news_deep_investigative": {
            "topic": "general",
            "search_depth": "advanced",
            "max_results": 10,
            "include_domains": INCLUDE_INVESTIGATIVE,
        },
        "social_media": {
            "topic": "general",
            "search_depth": "basic",
            "max_results": 10,
        },
        "political": {
            "topic": "general",
            "search_depth": "advanced",
            "max_results": 10,
            "include_domains": INCLUDE_POLITICAL,
        },
        "legal": {
            "topic": "general",
            "search_depth": "advanced",
            "max_results": 10,
            "include_domains": INCLUDE_LEGAL,
        },
        "international": {
            "topic": "news",
            "search_depth": "advanced",
            "max_results": 15,
            "include_domains": INCLUDE_INTERNATIONAL,
        },
        "international_local": {
            "topic": "general",
            "search_depth": "advanced",
            "max_results": 10,
            # use overrides to set "country" param per subject
        },
        "corporate": {
            "topic": "general",
            "search_depth": "advanced",
            "max_results": 10,
            "include_domains": INCLUDE_CORPORATE,
        },
        "synthesis_gapfill": {
            "topic": "general",
            "search_depth": "advanced",
            "max_results": 10,
        },
    }

    if step in step_config:
        base.update(step_config[step])

    base.update(overrides)
    return base


# ==============================================================
# SOURCE QUALITY PROMPT (inject into Claude synthesis — Step 13)
# ==============================================================

SOURCE_QUALITY_PROMPT = """
## SOURCE QUALITY AND EVALUATION RULES

You are synthesizing due diligence research for The Messina Group. All findings
must be grounded in verifiable, authoritative sources. Follow these rules strictly.

### Source Trust Hierarchy (highest to lowest)
1. GOVERNMENT DATABASES & OFFICIAL RECORDS: OFAC, SEC, DOJ, FEC, SAM.gov,
   UN sanctions, court records, congressional records. Treat as ground truth.
2. COURT FILINGS & LEGAL RECORDS: CourtListener, PACER, state court records.
   Treat as factual record of proceedings (not as proof of guilt).
3. REGULATORY FILINGS: SEC EDGAR, Senate LDA lobbying disclosures, FARA filings.
   Treat as factual disclosures (note: self-reported, may be incomplete).
4. WIRE SERVICES & INVESTIGATIVE JOURNALISM: AP, Reuters, ProPublica, ICIJ,
   OCCRP, major newspaper investigations. High reliability but verify claims
   against primary sources when possible.
5. QUALITY NEWS OUTLETS: NYT, WSJ, WaPo, Bloomberg, FT, Guardian, BBC,
   Economist, Politico, The Hill. Reliable but distinguish news reporting
   from opinion/editorial content.
6. THINK TANKS & RESEARCH ORGANIZATIONS: Brookings, CFR, CSIS, Carnegie,
   Transparency International, Global Witness, Freedom House. Useful for
   context and analysis but may have institutional perspectives.
7. PRESS RELEASES & CORPORATE COMMUNICATIONS: BusinessWire, PR Newswire,
   company websites. Treat as the subject's own claims — useful for context
   but inherently self-serving. Never treat as independent verification.

### Sources to NEVER cite or rely on
- Wikipedia or any wiki-based source
- Reddit, Quora, or any forum/discussion board
- Medium, Substack, or self-published blogs (unless by a recognized expert
  AND corroborated by Tier 1-5 sources)
- Content farms, tabloids, or partisan outlets (Daily Mail, NY Post, Breitbart,
  InfoWars, RT, Sputnik, Global Times, etc.)
- Social media posts as primary evidence (may reference for context only,
  clearly labeled as "social media claim, unverified")
- AI-generated summaries or chatbot outputs
- Celebrity gossip or entertainment sites
- Review sites (Glassdoor, Yelp, BBB, Trustpilot)
- Any source that cannot be traced to an identifiable author or organization

### How to Handle Source Conflicts
- When sources conflict, state the conflict explicitly
- Weight government/court records above news reports
- Weight original reporting above aggregated/rewritten content
- When a claim appears in only one source, flag it as "single-source,
  requires verification" — do NOT present it as established fact
- For international subjects: note when coverage is limited to state-controlled
  media from the subject's country, as this may be unreliable

### Per-Country Source Tier Weighting (for international subjects)
When evaluating sources from country-specific news outlets, apply these
quality weights based on the source domain's tier in our country config:
- Tier 1 sources (e.g., Dawn, The Hindu, Daily Maverick): weight 1.0 — Authoritative national press
- Tier 2 sources (e.g., Tribune, Business Recorder, Geo): weight 0.7 — Reliable but may have editorial lean
- Tier 3 sources (e.g., The Nation, Samaa): weight 0.4 — Use with caution, requires corroboration
- Avoid-listed sources: weight 0.1 — Do not cite as primary evidence

### Corroboration Rules
- CONFIRMED: Requires 2+ independent Tier 1/2 sources, OR 1 official government
  document/court record. Use this label freely when met.
- REPORTED: Single Tier 1/2 source. State the source and note it is single-source.
- ALLEGED: Under investigation or unproven. Clearly label as allegation.
- UNCORROBORATED: Only appears in Tier 3 or lower sources. Flag explicitly:
  "This claim appears only in [source] and has not been independently verified."
- Cross-check rule: If a story appears in BOTH pro-government AND opposition media
  outlets, treat it as more credible regardless of individual outlet tier.
- For red and yellow flags: require at least 2 independent Tier 1-5 sources
  before flagging (except government database matches, which are standalone flags)

### Citation Requirements in Output
- Every factual claim must cite its source with enough detail to verify
  (publication name, date, title/description)
- Clearly distinguish between: CONFIRMED, REPORTED, ALLEGED, and UNCORROBORATED
  using the corroboration rules above
- Flag any finding where the ONLY available sources are below Tier 5
"""
