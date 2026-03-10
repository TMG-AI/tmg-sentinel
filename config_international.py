"""
TMG Vetting Pipeline — International Country Configuration
============================================================
Country-specific anti-corruption bodies, legal terminology, search terms,
and news sources for international due diligence.

Based on Perplexity research report: "Anti-Corruption Institutions & International
Vetting Reference Guide" (March 2026).

To add a new country:
  1. Add an entry to COUNTRY_CONFIGS keyed by ISO 2-letter code (lowercase)
  2. Follow the schema: anti_corruption_bodies, key_search_terms, news_sources
  3. Run a test search to verify queries surface the right articles

Country code lookup: use the --country flag value from pipeline.py.
The pipeline normalizes to match against these keys.
"""

# ─── Country Code Normalization ─────────────────────────────

# Maps common country name variations → ISO 2-letter code
COUNTRY_ALIASES = {
    # Pakistan
    "pakistan": "pk", "pk": "pk", "pak": "pk",
    # India
    "india": "in", "in": "in", "ind": "in",
    # United Kingdom
    "uk": "gb", "gb": "gb", "united kingdom": "gb", "england": "gb", "britain": "gb",
    # UAE
    "uae": "ae", "ae": "ae", "united arab emirates": "ae",
    # Saudi Arabia
    "saudi arabia": "sa", "sa": "sa", "saudi": "sa", "ksa": "sa",
    # Nigeria
    "nigeria": "ng", "ng": "ng",
    # Kenya
    "kenya": "ke", "ke": "ke",
    # South Africa
    "south africa": "za", "za": "za",
    # Brazil
    "brazil": "br", "br": "br",
    # Mexico
    "mexico": "mx", "mx": "mx",
    # Colombia
    "colombia": "co", "co": "co",
    # Turkey
    "turkey": "tr", "tr": "tr", "türkiye": "tr", "turkiye": "tr",
    # Philippines
    "philippines": "ph", "ph": "ph",
    # Indonesia
    "indonesia": "id", "id": "id",
    # South Korea
    "south korea": "kr", "kr": "kr", "korea": "kr",
    # Japan
    "japan": "jp", "jp": "jp",
    # Australia
    "australia": "au", "au": "au",
    # Canada
    "canada": "ca", "ca": "ca",
    # Israel
    "israel": "il", "il": "il",
    # France
    "france": "fr", "fr": "fr",
    # Germany
    "germany": "de", "de": "de",
    # Italy
    "italy": "it", "it": "it",
    # China
    "china": "cn", "cn": "cn", "prc": "cn",
    # Russia
    "russia": "ru", "ru": "ru",
}


def normalize_country_code(country: str) -> str:
    """Normalize a country name/code to ISO 2-letter lowercase."""
    if not country:
        return ""
    return COUNTRY_ALIASES.get(country.strip().lower(), country.strip().lower())


# ─── Country Configurations ─────────────────────────────────

COUNTRY_CONFIGS = {

    # ═══════════════════════════════════════════════════════════
    # PAKISTAN
    # ═══════════════════════════════════════════════════════════
    "pk": {
        "name": "Pakistan",
        "anti_corruption_bodies": [
            {
                "name": "National Accountability Bureau",
                "abbrev": "NAB",
                "what_they_file": [
                    "references (corruption cases filed in accountability courts)",
                    "plea bargain approvals",
                    "inquiry and investigation authorizations",
                ],
                "key_legal_terms": [
                    "NAB reference",
                    "accountability court",
                    "plea bargain",
                    "corruption and corrupt practices",
                    "benami properties",
                    "assets beyond means",
                    "misuse of authority",
                ],
            },
            {
                "name": "Federal Investigation Agency",
                "abbrev": "FIA",
                "what_they_file": [
                    "FIR (First Information Report) for financial crimes",
                    "money laundering investigations",
                    "cybercrime cases",
                ],
                "key_legal_terms": [
                    "FIA investigation",
                    "money laundering FIA",
                    "FIR registered",
                ],
            },
            {
                "name": "Supreme Court Joint Investigation Team",
                "abbrev": "JIT",
                "what_they_file": [
                    "JIT reports (Supreme Court-mandated investigations)",
                    "forensic audit findings",
                ],
                "key_legal_terms": [
                    "JIT report",
                    "JIT investigation",
                    "joint investigation team",
                    "Supreme Court JIT",
                ],
            },
        ],

        # These get appended as Tavily queries: "{name} {term}"
        "key_search_terms": [
            "NAB reference",
            "NAB inquiry",
            "NAB investigation",
            "accountability court",
            "accountability court verdict",
            "benami accounts",
            "benami properties",
            "assets beyond means",
            "corruption case",
            "plea bargain NAB",
            "money laundering",
            "JIT investigation",
            "fake accounts case",
            "misuse of authority",
        ],

        "news_sources": {
            "tier1": ["dawn.com", "thenews.com.pk", "dailytimes.com.pk"],
            "tier2": ["tribune.com.pk", "brecorder.com", "geo.tv", "arynews.tv"],
            "tier3": ["nation.com.pk", "humnews.pk", "samaaenglish.tv"],
            "avoid": ["pakobserver.net"],
        },
    },

    # ═══════════════════════════════════════════════════════════
    # INDIA
    # ═══════════════════════════════════════════════════════════
    "in": {
        "name": "India",
        "anti_corruption_bodies": [
            {
                "name": "Central Bureau of Investigation",
                "abbrev": "CBI",
                "what_they_file": [
                    "FIR (First Information Report)",
                    "chargesheets",
                    "RC (Regular Case) filings",
                ],
                "key_legal_terms": [
                    "CBI case",
                    "CBI chargesheet",
                    "CBI FIR",
                    "CBI investigation",
                ],
            },
            {
                "name": "Enforcement Directorate",
                "abbrev": "ED",
                "what_they_file": [
                    "ECIR (Enforcement Case Information Report)",
                    "provisional attachment orders",
                    "PMLA (Prevention of Money Laundering Act) cases",
                ],
                "key_legal_terms": [
                    "ED case",
                    "ED raid",
                    "ED investigation",
                    "PMLA case",
                    "money laundering ED",
                    "provisional attachment",
                    "ECIR",
                ],
            },
            {
                "name": "Lokpal / Lokayukta",
                "abbrev": "Lokpal",
                "what_they_file": [
                    "complaints against public servants",
                    "anti-corruption investigations",
                ],
                "key_legal_terms": [
                    "Lokpal complaint",
                    "Lokayukta investigation",
                ],
            },
        ],

        "key_search_terms": [
            "CBI case",
            "CBI chargesheet",
            "ED case",
            "ED raid",
            "ED investigation",
            "PMLA case",
            "money laundering",
            "disproportionate assets",
            "lookout circular",
            "corruption case",
            "benami property",
            "income tax raid",
            "hawala",
            "Prevention of Corruption Act",
        ],

        "news_sources": {
            "tier1": ["thehindu.com", "indianexpress.com", "ndtv.com"],
            "tier2": ["thewire.in", "scroll.in", "economictimes.indiatimes.com", "livemint.com"],
            "tier3": ["tribuneindia.com", "deccanherald.com", "firstpost.com"],
            "avoid": [],
        },
    },

    # ═══════════════════════════════════════════════════════════
    # UNITED KINGDOM
    # ═══════════════════════════════════════════════════════════
    "gb": {
        "name": "United Kingdom",
        "anti_corruption_bodies": [
            {
                "name": "Serious Fraud Office",
                "abbrev": "SFO",
                "what_they_file": [
                    "criminal charges for serious/complex fraud",
                    "bribery and corruption prosecutions",
                    "deferred prosecution agreements (DPAs)",
                ],
                "key_legal_terms": [
                    "SFO investigation",
                    "SFO prosecution",
                    "deferred prosecution agreement",
                    "Bribery Act",
                    "unexplained wealth order",
                ],
            },
            {
                "name": "National Crime Agency",
                "abbrev": "NCA",
                "what_they_file": [
                    "unexplained wealth orders (UWOs)",
                    "account freezing orders",
                    "money laundering investigations",
                ],
                "key_legal_terms": [
                    "NCA investigation",
                    "unexplained wealth order",
                    "account freezing order",
                    "Proceeds of Crime Act",
                ],
            },
            {
                "name": "Financial Conduct Authority",
                "abbrev": "FCA",
                "what_they_file": [
                    "enforcement actions",
                    "fines and penalties",
                    "prohibition orders",
                ],
                "key_legal_terms": [
                    "FCA enforcement",
                    "FCA fine",
                    "FCA investigation",
                    "prohibition order",
                ],
            },
        ],

        "key_search_terms": [
            "SFO investigation",
            "SFO prosecution",
            "unexplained wealth order",
            "Bribery Act prosecution",
            "NCA investigation",
            "FCA enforcement",
            "Companies House disqualification",
            "director disqualified",
            "money laundering",
            "sanctions evasion",
            "Proceeds of Crime Act",
            "fraud prosecution",
        ],

        "news_sources": {
            "tier1": ["theguardian.com", "ft.com", "bbc.com", "bbc.co.uk", "thetimes.com"],
            "tier2": ["telegraph.co.uk", "independent.co.uk", "channel4.com", "sky.com"],
            "tier3": ["cityam.com", "thisismoney.co.uk"],
            "avoid": [],  # dailymail.co.uk, thesun.co.uk already in global exclude
        },
    },

    # ═══════════════════════════════════════════════════════════
    # UAE
    # ═══════════════════════════════════════════════════════════
    "ae": {
        "name": "United Arab Emirates",
        "anti_corruption_bodies": [
            {
                "name": "State Audit Institution",
                "abbrev": "SAI",
                "what_they_file": ["audit reports on government entities"],
                "key_legal_terms": ["State Audit Institution report"],
            },
            {
                "name": "Abu Dhabi Accountability Authority",
                "abbrev": "ADAA",
                "what_they_file": ["accountability investigations"],
                "key_legal_terms": ["ADAA investigation"],
            },
        ],

        "key_search_terms": [
            "money laundering UAE",
            "financial crime Dubai",
            "sanctions evasion UAE",
            "DFSA enforcement",
            "ADGM sanctions",
            "gold smuggling",
            "hawala network",
            "shell company Dubai",
            "corruption probe UAE",
            "fraud case Dubai",
        ],

        "news_sources": {
            "tier1": ["thenationalnews.com", "khaleejtimes.com", "gulfnews.com"],
            "tier2": ["arabianbusiness.com", "zawya.com", "argaam.com"],
            "tier3": [],
            "avoid": [],
        },
    },

    # ═══════════════════════════════════════════════════════════
    # NIGERIA
    # ═══════════════════════════════════════════════════════════
    "ng": {
        "name": "Nigeria",
        "anti_corruption_bodies": [
            {
                "name": "Economic and Financial Crimes Commission",
                "abbrev": "EFCC",
                "what_they_file": [
                    "arraignments and charges",
                    "asset recovery actions",
                    "money laundering prosecutions",
                ],
                "key_legal_terms": [
                    "EFCC arrest",
                    "EFCC arraignment",
                    "EFCC investigation",
                    "EFCC prosecution",
                ],
            },
            {
                "name": "Independent Corrupt Practices Commission",
                "abbrev": "ICPC",
                "what_they_file": [
                    "corruption prosecutions",
                    "asset declarations investigations",
                ],
                "key_legal_terms": [
                    "ICPC investigation",
                    "ICPC prosecution",
                    "asset declaration",
                ],
            },
        ],

        "key_search_terms": [
            "EFCC arrest",
            "EFCC arraignment",
            "EFCC investigation",
            "EFCC prosecution",
            "ICPC corruption",
            "money laundering Nigeria",
            "corruption probe Nigeria",
            "asset forfeiture Nigeria",
            "fraud case Nigeria",
            "oil theft",
        ],

        "news_sources": {
            "tier1": ["premiumtimesng.com", "punchng.com", "thecable.ng"],
            "tier2": ["guardian.ng", "vanguardngr.com", "dailytrust.com"],
            "tier3": ["thisdaylive.com", "sunnewsonline.com"],
            "avoid": [],
        },
    },

    # ═══════════════════════════════════════════════════════════
    # BRAZIL
    # ═══════════════════════════════════════════════════════════
    "br": {
        "name": "Brazil",
        "anti_corruption_bodies": [
            {
                "name": "Ministério Público Federal",
                "abbrev": "MPF",
                "what_they_file": [
                    "denúncias (criminal complaints)",
                    "ações de improbidade (misconduct actions)",
                ],
                "key_legal_terms": [
                    "MPF denúncia",
                    "Lava Jato",
                    "operação",
                    "improbidade administrativa",
                ],
            },
            {
                "name": "Controladoria-Geral da União",
                "abbrev": "CGU",
                "what_they_file": [
                    "administrative sanctions",
                    "company debarments (CEIS list)",
                ],
                "key_legal_terms": [
                    "CGU sanção",
                    "CEIS",
                    "empresa inidônea",
                ],
            },
        ],

        "key_search_terms": [
            "Lava Jato",
            "corruption probe Brazil",
            "MPF investigation",
            "Operação",
            "money laundering Brazil",
            "improbidade administrativa",
            "corruption case Brazil",
            "bribery Brazil",
            "plea deal delação",
            "political corruption Brazil",
        ],

        "news_sources": {
            "tier1": ["reuters.com", "bloomberg.com", "ft.com"],  # English coverage
            "tier2": ["braziljournal.com", "riotimesonline.com"],
            "tier3": [],
            "avoid": [],
        },
    },

    # ═══════════════════════════════════════════════════════════
    # TURKEY
    # ═══════════════════════════════════════════════════════════
    "tr": {
        "name": "Turkey",
        "anti_corruption_bodies": [
            {
                "name": "Court of Accounts",
                "abbrev": "Sayıştay",
                "what_they_file": ["audit reports on public spending"],
                "key_legal_terms": ["Sayıştay report", "audit finding"],
            },
        ],

        "key_search_terms": [
            "corruption case Turkey",
            "OFAC sanctions Turkey",
            "money laundering Turkey",
            "fraud prosecution Turkey",
            "Halkbank case",
            "sanctions evasion Turkey",
            "political corruption Turkey",
            "bribery Turkey",
            "corruption probe Istanbul",
            "financial crime Turkey",
        ],

        "news_sources": {
            "tier1": ["hurriyetdailynews.com", "dailysabah.com"],
            "tier2": ["ahvalnews.com", "bianet.org"],
            "tier3": [],
            "avoid": [],  # State-influenced outlets are common; rely on cross-referencing
        },
    },

    # ═══════════════════════════════════════════════════════════
    # SOUTH AFRICA
    # ═══════════════════════════════════════════════════════════
    "za": {
        "name": "South Africa",
        "anti_corruption_bodies": [
            {
                "name": "Hawks (Directorate for Priority Crime Investigation)",
                "abbrev": "Hawks",
                "what_they_file": ["criminal investigations", "arrests"],
                "key_legal_terms": ["Hawks investigation", "Hawks arrest"],
            },
            {
                "name": "Special Investigating Unit",
                "abbrev": "SIU",
                "what_they_file": ["proclamation investigations", "civil recovery"],
                "key_legal_terms": ["SIU investigation", "SIU proclamation"],
            },
            {
                "name": "Zondo Commission",
                "abbrev": "Zondo",
                "what_they_file": ["state capture commission findings"],
                "key_legal_terms": ["state capture", "Zondo Commission"],
            },
        ],

        "key_search_terms": [
            "state capture",
            "Zondo Commission",
            "Hawks investigation",
            "SIU investigation",
            "corruption case South Africa",
            "NPA prosecution",
            "money laundering South Africa",
            "tender fraud",
            "BEE fraud",
            "Gupta family",
        ],

        "news_sources": {
            "tier1": ["dailymaverick.co.za", "news24.com", "mg.co.za"],
            "tier2": ["businesslive.co.za", "timeslive.co.za", "iol.co.za"],
            "tier3": ["ewn.co.za", "citizen.co.za"],
            "avoid": [],
        },
    },

    # ═══════════════════════════════════════════════════════════
    # KENYA
    # ═══════════════════════════════════════════════════════════
    "ke": {
        "name": "Kenya",
        "anti_corruption_bodies": [
            {
                "name": "Ethics and Anti-Corruption Commission",
                "abbrev": "EACC",
                "what_they_file": ["investigations", "asset recovery"],
                "key_legal_terms": ["EACC investigation", "EACC arrest"],
            },
            {
                "name": "Directorate of Criminal Investigations",
                "abbrev": "DCI",
                "what_they_file": ["criminal investigations", "fraud probes"],
                "key_legal_terms": ["DCI investigation", "DCI probe"],
            },
        ],

        "key_search_terms": [
            "EACC investigation",
            "corruption case Kenya",
            "DCI probe",
            "money laundering Kenya",
            "NYS scandal",
            "tender fraud Kenya",
            "asset recovery Kenya",
            "graft case Kenya",
        ],

        "news_sources": {
            "tier1": ["nation.africa", "standardmedia.co.ke", "the-star.co.ke"],
            "tier2": ["businessdailyafrica.com", "capitalfm.co.ke"],
            "tier3": [],
            "avoid": [],
        },
    },

    # ═══════════════════════════════════════════════════════════
    # SAUDI ARABIA
    # ═══════════════════════════════════════════════════════════
    "sa": {
        "name": "Saudi Arabia",
        "anti_corruption_bodies": [
            {
                "name": "Control and Anti-Corruption Authority",
                "abbrev": "Nazaha",
                "what_they_file": ["corruption investigations", "arrests"],
                "key_legal_terms": ["Nazaha investigation", "Nazaha arrest"],
            },
        ],

        "key_search_terms": [
            "corruption case Saudi",
            "Nazaha arrest",
            "Ritz-Carlton detention",
            "money laundering Saudi",
            "bribery Saudi Arabia",
            "fraud case Saudi",
            "sanctions Saudi",
            "financial crime Saudi",
        ],

        "news_sources": {
            "tier1": ["arabnews.com", "thenationalnews.com"],
            "tier2": ["khaleejtimes.com", "arabianbusiness.com"],
            "tier3": [],
            "avoid": [],  # Most Saudi media is state-influenced; rely on international coverage
        },
    },

    # ═══════════════════════════════════════════════════════════
    # MEXICO
    # ═══════════════════════════════════════════════════════════
    "mx": {
        "name": "Mexico",
        "anti_corruption_bodies": [
            {
                "name": "Fiscalía General de la República",
                "abbrev": "FGR",
                "what_they_file": ["criminal investigations", "arrest warrants"],
                "key_legal_terms": ["FGR investigation", "FGR orden de aprehensión"],
            },
            {
                "name": "Auditoría Superior de la Federación",
                "abbrev": "ASF",
                "what_they_file": ["audit reports", "financial irregularity findings"],
                "key_legal_terms": ["ASF audit", "ASF irregularidades"],
            },
        ],

        "key_search_terms": [
            "corruption case Mexico",
            "FGR investigation",
            "money laundering Mexico",
            "cartel connection",
            "Odebrecht Mexico",
            "huachicol",
            "corruption probe Mexico",
            "narco ties",
            "extradition Mexico",
            "financial crime Mexico",
        ],

        "news_sources": {
            "tier1": ["reuters.com", "apnews.com"],  # English coverage best via wire services
            "tier2": ["mexiconewsdaily.com", "elfinanciero.com.mx"],
            "tier3": [],
            "avoid": [],
        },
    },

    # ═══════════════════════════════════════════════════════════
    # PHILIPPINES
    # ═══════════════════════════════════════════════════════════
    "ph": {
        "name": "Philippines",
        "anti_corruption_bodies": [
            {
                "name": "Office of the Ombudsman",
                "abbrev": "Ombudsman",
                "what_they_file": ["criminal and administrative cases against public officials"],
                "key_legal_terms": ["Ombudsman case", "Sandiganbayan case", "plunder case"],
            },
            {
                "name": "Anti-Money Laundering Council",
                "abbrev": "AMLC",
                "what_they_file": ["freeze orders", "money laundering investigations"],
                "key_legal_terms": ["AMLC investigation", "AMLC freeze order"],
            },
        ],

        "key_search_terms": [
            "Ombudsman case Philippines",
            "Sandiganbayan verdict",
            "plunder case",
            "AMLC investigation",
            "corruption case Philippines",
            "money laundering Philippines",
            "graft case Philippines",
            "pork barrel scam",
            "PDAF scam",
        ],

        "news_sources": {
            "tier1": ["inquirer.net", "rappler.com", "philstar.com"],
            "tier2": ["manilatimes.net", "gmanetwork.com"],
            "tier3": [],
            "avoid": [],
        },
    },
}


# ─── Generic Fallback Terms ─────────────────────────────────
# Used when country has no specific config yet
GENERIC_CORRUPTION_TERMS = [
    "corruption case",
    "corruption investigation",
    "corruption charges",
    "money laundering",
    "bribery",
    "fraud prosecution",
    "embezzlement",
    "graft",
    "sanctions violation",
    "financial crime",
    "anti-corruption investigation",
    "accountability",
]


def get_country_config(country: str) -> dict:
    """Get country config by name or code. Returns empty dict if not found."""
    code = normalize_country_code(country)
    return COUNTRY_CONFIGS.get(code, {})


def get_corruption_search_terms(country: str) -> list[str]:
    """Get corruption search terms for a country. Falls back to generic terms."""
    cfg = get_country_config(country)
    if cfg:
        return cfg["key_search_terms"]
    return GENERIC_CORRUPTION_TERMS


def get_country_news_domains(country: str, tiers: list[str] = None) -> list[str]:
    """Get news source domains for a country. Default: tier1 + tier2."""
    cfg = get_country_config(country)
    if not cfg:
        return []
    tiers = tiers or ["tier1", "tier2"]
    domains = []
    for tier in tiers:
        domains.extend(cfg.get("news_sources", {}).get(tier, []))
    return domains


def get_country_avoid_domains(country: str) -> list[str]:
    """Get domains to avoid for a country."""
    cfg = get_country_config(country)
    if not cfg:
        return []
    return cfg.get("news_sources", {}).get("avoid", [])
