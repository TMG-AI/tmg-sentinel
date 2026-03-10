# Vetting Pipeline Project - Session Status

## User Preferences
- **NEVER produce Markdown (.md) files** for memos, reports, or documents. Always use DOCX format. Shannon shares these with colleagues.

## Last Updated: 2026-03-10 (Session 12)

## Completed (Session 12) — Source Relevance Split + Vetting Level Simplification

1. **Risk vs. Context source split** — Tavily search results are now split into two buckets:
   - **Risk sources**: Mention the subject (company name, exec names) in title or content. ONLY these are used for risk scoring in synthesis.
   - **Context sources**: Industry/sector background that doesn't mention the subject. Presented to Claude as background only, explicitly excluded from scoring.
   - This fixes the Anduril problem where 90% of 278 sources were irrelevant defense industry noise.

2. **Industry context queries** — New `TAVILY_INDUSTRY_CONTEXT_QUERIES` in config.py. Sector-level searches (defense_tech, energy, pharma, finance, tech, government) that run WITHOUT the subject name. Tagged as context, not used for scoring.

3. **Relevance filter in search_news.py** — `_build_relevance_terms()` extracts subject name parts and company name parts. `_is_relevant()` checks if title/content mentions any term. Sources from subject-specific queries that don't mention the subject are moved to context.

4. **Vetting levels simplified** — Removed `quick_screen` and `standard_vet`. Everything is now `deep_dive` by default. No `--level` flag needed.

5. **Anduril Industries vetting completed** — Deep dive run, results in `data/unified/anduril_industries.json`.

6. **Sharjeel Inam Memon vetting completed** — Pakistan deep dive, pushed to Lovable.

### Key Code Changes (Session 12)
- **`scripts/search_news.py`**: Added `_build_relevance_terms()`, `_is_relevant()`, `_infer_sector()`. Results split into `risk_sources` and `context_sources`. Industry context queries run separately. Output JSON now has `risk_sources`, `context_sources`, `risk_source_count`, `context_source_count` fields.
- **`config.py`**: Removed `quick_screen` and `standard_vet` from `VETTING_LEVELS`. Added `TAVILY_INDUSTRY_CONTEXT_QUERIES` dict with 7 sector configs.
- **`scripts/synthesize.py`**: `collect_tavily_sources()` now returns tuple `(risk_sources, context_sources)`. `format_news_for_prompt()` uses `risk_sources`. New `format_context_for_prompt()` for background. Prompt explicitly tells Claude not to use context sources for scoring. Unified JSON output includes `context_sources` array.
- **`scripts/pipeline.py`**: Default vetting level changed to `deep_dive`.

## Completed (Session 11) — Perplexity-Recommended Improvements
Based on Perplexity report analyzing pipeline gaps vs. professional due diligence firms (Kroll, Control Risks, Nardello). Five high-value changes implemented:

1. **Source tier weighting in synthesis prompt** — `config_tavily.py` SOURCE_QUALITY_PROMPT now includes per-country tier weights (Tier 1=1.0, Tier 2=0.7, Tier 3=0.4, avoid=0.1) and corroboration rules. Claude must now use CONFIRMED/REPORTED/ALLEGED/UNCORROBORATED labels. Cross-check rule: stories in both pro-gov AND opposition outlets get credibility boost.

2. **Universal investigator-style queries** — `config.py` adds `TAVILY_INVESTIGATOR_QUERIES` (8 queries): investigation/probe, indicted/charged, money laundering/bribery, sanctions/blacklist, tax evasion/offshore, shell company, fraud/embezzlement, arrest warrant. Applied to ALL deep searches regardless of country.

3. **Red flag categories beyond corruption** — `config.py` adds `TAVILY_RED_FLAG_QUERIES` (8 queries): human rights violations, torture/extrajudicial, environmental disaster, forced labor/child labor, kleptocracy/state capture, unexplained wealth, family dynasty networks, terrorism financing. Applied to ALL deep searches.

4. **Corporate Network Discovery (Step 15)** — NEW step. `scripts/search_network.py` uses OpenCorporates API (when key available) or Tavily fallback to discover corporate associations, directorships, subsidiaries, co-directors. Associated entities are cross-referenced against corruption/sanctions/news data in synthesis. This is how you organically find hidden connections (e.g., Omni Group) without hardcoding.

5. **Reverse queries** — `config.py` adds `TAVILY_REVERSE_QUERIES` (4 templates): scandal-first searches like "corruption scandal {country} {sector}" that find cases first, then check if subject appears. Only for international subjects. Sector auto-inferred from bio/engagement type.

### Key Code Changes (Session 11)
- **`config_tavily.py`**: SOURCE_QUALITY_PROMPT expanded with Per-Country Source Tier Weighting and Corroboration Rules sections.
- **`config.py`**: Added `TAVILY_INVESTIGATOR_QUERIES` (8), `TAVILY_RED_FLAG_QUERIES` (8), `TAVILY_REVERSE_QUERIES` (4). Added `OPENCORPORATES_API_KEY` env var, `NETWORK_DIR`, Step 15 to `STEP_SCRIPTS`/`STEP_NAMES`/vetting levels. Standard vet steps now: `[0, 1, 2, 3, 4, 5, 15, 6, 7, 8, 10, 11, 14, 13]`.
- **`scripts/search_news.py`**: Deep search now appends investigator queries, red flag queries, and (for international) reverse queries. Total deep queries increased from ~20 to ~40+ per subject.
- **NEW: `scripts/search_network.py`**: Step 15. OpenCorporates company + officer search, with Tavily fallback. Produces associated_entities list for cross-referencing.
- **`scripts/pipeline.py`**: Added Step 15 block between Step 5 (Corporate) and Step 6 (FEC). Imports `search_network`.
- **`scripts/synthesize.py`**: Added `format_network_for_prompt()`. Loads network data in `load_all_step_data()`. Prompt includes CORPORATE NETWORK DISCOVERY section with cross-reference instruction.

### Impact on Query Volume
- Basic queries (Step 3): unchanged (3 queries)
- Deep queries (Step 10): ~15 → ~35-40 queries (+ 8 investigator + 8 red flag + 5 country corruption + 4 reverse)
- Step 15 (Network): 3-5 Tavily queries (fallback mode) or 2-7 OpenCorporates API calls
- Total per standard_vet: ~50-55 Tavily queries (was ~30-40)

### OpenCorporates Setup
To enable structured corporate data instead of Tavily fallback:
1. Register at https://opencorporates.com (free tier: 50 requests/day)
2. Add to `.env`: `OPENCORPORATES_API_KEY=your_key_here`
3. Pipeline auto-detects and uses OpenCorporates when key is present

### Shah Re-Run Results (Session 10)
- **Factual Risk: 7.11/10 HIGH — Recommend Reject**
- **RCS: 5.35/10 ELEVATED**
- **Combined Decision: HIGH — Recommend Reject**
- Pipeline surfaced: NAB references (Nooriabad, fake accounts, misuse of power), JIT findings, accountability court proceedings, ECL placement, benami account allegations, 2024 acquittal
- 224 Tavily sources, 74 mentions of key corruption terms across output
- Zero hardcoding — all found organically via country-specific corruption vocabulary

## Completed (Session 10)
- **Country-specific anti-corruption search** — NEW. `config_international.py` defines per-country anti-corruption bodies, legal terminology, and search terms. Step 12 now runs 10-14 additional Tavily queries using country-specific corruption vocabulary (e.g., "NAB reference", "accountability court" for Pakistan; "ED case", "CBI chargesheet" for India; "SFO investigation" for UK). This is the fix for the Shah vetting gap where generic queries missed NAB/JIT/fake-accounts corruption.
- **Country configs for 12 countries** — Pakistan, India, UK, UAE, Nigeria, Kenya, South Africa, Brazil, Mexico, Turkey, Philippines, Saudi Arabia. Each has: anti-corruption bodies with abbreviations, key legal terms, tiered news sources (domain names), and avoid lists. Generic fallback terms for unconfigured countries.
- **Tavily domain filtering fixed** — Removed `expressnews.com` from global block list (was blocking Express News Pakistan). Added 15+ regional quality press sources to `INCLUDE_INTERNATIONAL` (Dawn, The Hindu, Daily Maverick, Premium Times, Rappler, etc.) + cross-border investigative networks (Bureau of Investigative Journalism, Correctiv, Bellingcat).
- **Deep news search enhanced** — `search_news.py` Step 10 now appends top 5 country-specific corruption terms for international subjects, so corruption coverage surfaces in the news step too, not just Step 12.
- **Citation enrichment updated** — `synthesize.py` now collects sources from `corruption_searches` field for [n] citation matching.
- **Prompt updated** — `format_international_for_prompt()` now includes full corruption search results with article titles and snippets.

## Key Code Changes (Session 10)
- **NEW: `config_international.py`** — Country configs with `COUNTRY_CONFIGS` dict, `normalize_country_code()`, `get_corruption_search_terms()`, `get_country_news_domains()`, `get_country_avoid_domains()`. Helper `COUNTRY_ALIASES` maps name variations → ISO codes.
- **`scripts/search_international.py`**: Added `search_country_corruption()` function. `run_international_search()` now calls it for non-US subjects, producing `corruption_searches` field in output JSON.
- **`scripts/search_news.py`**: Imports `get_corruption_search_terms`, appends top 5 terms to deep search templates for international subjects.
- **`config_tavily.py`**: Removed `expressnews.com` from `EXCLUDE_DOMAINS_TABLOIDS_PARTISAN`. Expanded `INCLUDE_INTERNATIONAL` with regional quality press + investigative networks.
- **`scripts/synthesize.py`**: `format_international_for_prompt()` now renders corruption search results. `collect_tavily_sources()` now includes corruption search sources for citation enrichment.

## Ready to Re-Run: Syed Murad Ali Shah
```bash
cd /Users/shannonwheatman/vetting && python3 scripts/pipeline.py \
  --name "Syed Murad Ali Shah" \
  --type individual \
  --country Pakistan \
  --city "Karachi, Sindh" \
  --engagement fara_foreign_political \
  --level standard_vet \
  --bio "Chief Minister of Sindh province, Pakistan. PPP politician." \
  --referral "International engagement assessment"
```
Pipeline will now run 14 Pakistan-specific corruption queries in Step 12 (NAB reference, accountability court, benami accounts, etc.) in addition to 20 deep news queries (5 with corruption terms) and PEP check. Should surface the NAB Nooriabad case, JIT fake-accounts findings, and Omni Group connections that were missed in Session 9.

## Completed (Session 9)
- **International subject support** — Pipeline now handles non-US subjects correctly:
  - `pipeline.py`: Auto-skips US-only steps (2/Debarment, 4/Litigation, 6/FEC, 7/SEC, 8/Lobbying, 9/Bankruptcy, 14/Contracts) when country ≠ US. Auto-includes Step 12 (International) for non-US subjects even on standard_vet.
  - `config.py`: Added `RISK_DIMENSIONS_INTERNATIONAL` — rebalanced weights (Media 30%, International/PEP 30%, Litigation 12%, Financial 6%, Corporate 7%, Political 5%, COI 10%) since US databases don't apply.
  - `synthesize.py`: Uses international weights for non-US subjects in prompt construction, score computation, and score printing. Adds "INTERNATIONAL SUBJECT NOTICE" to prompt telling Claude not to penalize for missing US data.
- **No changes to US subject flow** — all edits gated behind `is_us` check. Existing Peter Thiel / Palantir vettings unaffected.

## Key Code Changes (Session 9)
- **`scripts/pipeline.py`** (~lines 56-77): `US_ONLY_STEPS` dict + `is_us` gate. Steps list is now copied with `list()` to avoid mutating config. Step 12 auto-inserted for non-US standard_vet.
- **`config.py`** (~lines 222-257): `RISK_DIMENSIONS_INTERNATIONAL` dict with rebalanced weights + assert.
- **`scripts/synthesize.py`**: Three changes:
  - `build_synthesis_prompt()` (~line 551): Selects `risk_dims` based on country. Adds international context block to prompt.
  - `run_synthesis()` (~line 916): Selects `risk_dims` based on country.
  - Score computation (~line 985) and score printing (~line 1299): Use `risk_dims` instead of hardcoded `config.RISK_DIMENSIONS`.

## Ready to Run: Syed Murad Ali Shah
```bash
cd /Users/shannonwheatman/vetting && python3 scripts/pipeline.py \
  --name "Syed Murad Ali Shah" \
  --type individual \
  --country Pakistan \
  --city "Karachi, Sindh" \
  --engagement fara_foreign_political \
  --level standard_vet \
  --bio "Chief Minister of Sindh province, Pakistan. PPP politician." \
  --referral "International engagement assessment"
```
Steps that will run: 0 (Intake), 1 (Sanctions), 3 (Basic News), 5 (Corporate/GLEIF), 10 (Deep News), 11 (Exec ID — will skip for individual), 12 (International/PEP), 13 (Synthesis)

## Completed (Session 8)
- **Executive summary rewrite** — Added post-synthesis Claude Sonnet call to rewrite exec summary with BOTH factual + RCS scores and Combined Decision. Before: summaries only reflected factual risk (Palantir said "CONDITIONAL APPROVE"). After: summaries reflect Combined Decision (Palantir says "REJECT — HIGH").
- **Client conflict analysis strengthened** — Updated synthesis prompt to REQUIRE naming specific TMG clients by name with sensitivity tiers in conflict_of_interest sub-factors. Before: vague "ICE conflicts with civil liberties groups" (score 5.5). After: "Google LLC (HIGH), Coinbase (HIGH), TikTok (HIGH), AB Foundation, AB Democracy Matters" (score 7.0).
- **Pipeline memo updated** — `TMG_Vetting_Pipeline_Memo.docx` updated with Session 7 changes: Step 11 (Executive ID), Step 14 (Gov Contracts), Combined Decision section, updated examples with deep dive data.
- **Lovable vettings fixed** — Cleaned up `public/data/vettings/` to match `_deep` filenames in index. Removed stale non-deep copies.
- **All pushed to GitHub** — `palantir_technologies_deep.json` and `peter_thiel_deep.json` updated with rewritten exec summaries and stronger COI analysis.

## Key Code Changes (Session 8)
- **`scripts/synthesize.py`** (~line 1112): Added `rewrite_prompt` block that calls Claude Sonnet to rewrite executive summary after combined_decision is computed. Uses the original summary content but updates Risk Assessment and Recommendation sections with both scores.
- **`scripts/synthesize.py`** (~line 160): Strengthened `format_conflicts_for_prompt()` — now requires Claude to name specific TMG clients, check every client against research data, and include sensitivity tiers.
- **`scripts/synthesize.py`** (~line 549): Added conflict_of_interest-specific instructions in dimension text — explicitly tells Claude to name clients and check Google LLC, Coinbase, etc.

## Current Test Results (Session 8)
### Peter Thiel Deep Dive
- Factual: 5.38/10 ELEVATED
- RCS: 8.3/10 CRITICAL
- Combined: **CRITICAL — Recommend Reject**
- Headline: "Jim Messina's Firm Now Advising Billionaire Who Funded Trump's Rise and Destroyed Gawker"

### Palantir Deep Dive
- Factual: 3.72/10 MODERATE
- RCS: 7.83/10 HIGH
- Combined: **HIGH — Recommend Reject (requires unanimous partner approval)**
- Headline: "Obama's Campaign Manager's Firm Now Working with Trump Donor's Surveillance Company Behind ICE Deportations"
- Divergence Alert: YES
- COI: 7.0/10 — Google LLC (HIGH), Coinbase (HIGH), TikTok (HIGH), AB Foundation, AB Democracy Matters

## Known Issues / Caution
- **Synthesis variance**: Each re-run produces slightly different scores since Claude is non-deterministic. Factual scores bounce ±0.5, RCS ±0.3. COI is most variable because it depends on Claude's interpretation of "conflict."
- **Executives + contracts data not in deep dive**: The `palantir_technologies_deep.json` `steps_completed` list only shows 11 steps — executives and contracts steps ran in the standard vet but raw data wasn't loaded into the deep dive synthesis because subject_id differs. The `key_executives` and `government_contracts` fields may be missing from the deep dive JSON.
- **Lovable caching**: Lovable may cache old JSON files. After pushing, user may need to trigger a new deploy or hard-refresh.

## Architecture Decision (Session 4)
**Lovable CANNOT run Python code.** The FastAPI server / localhost approach from Session 3 was wrong — Lovable previews run in the cloud and can't reach localhost. After evaluating options (Vercel, n8n, ngrok), we chose the **Palantir model**:

1. Shannon runs the Python pipeline locally from terminal
2. Pipeline outputs unified JSON to `data/unified/<subject_id>.json`
3. Shannon commits and pushes to GitHub
4. Lovable reads the JSON files from the repo and displays results to the team
5. The Submit Vetting form in Lovable sends an email (mailto) to Shannon instead of calling an API

**The FastAPI server (`server.py`) is no longer used.**

## Completed (Session 7)
- **Executive Identification & Mini-Vet (Step 11)** — NEW. When vetting an organization, identifies top executives via SEC EDGAR Form 3/4 filings, then runs mini due diligence on each: FEC donations, targeted news search, and sanctions screening. Falls back to Tavily web search for private companies. Tested on Palantir: found 10 executives including Karp, Thiel, Sankar, Cohen, Glazer. Vetted 8 with FEC/news/sanctions.
- **Government Contracts Search (Step 14)** — NEW. Searches USAspending.gov API (no API key needed) for federal contract awards by company name. Returns contract amounts, awarding agencies, descriptions. Tested on Palantir: 414 awards, $3.94B total across 15 agencies (DoD $2.3B, HHS $405M, DHS $353M, DOJ $209M).
- **Org-Specific Tavily Queries** — When deep-searching an organization, 6 additional queries now run: boycott/protest activity, CEO/executive statements, government contracts, political donation returns, employee dissent/whistleblower, surveillance/enforcement/civil liberties.
- **Pipeline integration** — Both new steps integrated into pipeline.py, config.py, and synthesize.py. Standard vet and deep dive levels now include Steps 11 and 14.
- **Bug fix: EDGAR XML parsing** — Fixed XSL path filtering (was returning HTML instead of XML) and boolean parsing (EDGAR uses both "1" and "true" for flags).
- **Request timeout bumped** — CourtListener pagination timeout increased from 15→30→45 seconds in config.py.

## Completed (Session 6)
- **Combined Decision logic** — `synthesize.py` now produces a `combined_decision` field that takes the MORE CAUTIOUS of factual risk vs RCS. Previously the `scoring.recommendation` only reflected factual risk, ignoring RCS entirely. Now the unified JSON has `combined_decision.recommendation`, `combined_decision.combined_tier`, and `combined_decision.driver` explaining which score drove the decision.
- **Pagination added to CourtListener searches** — Both `search_litigation.py` (Step 4) and `search_bankruptcy.py` (Step 9) now paginate through ALL results (up to 500, safety cap 25 pages × 20). Previously they only fetched the first 20 results regardless of how many existed (e.g., 247 bankruptcy results but only 20 reviewed).
- **Deep dive intake files created** — `peter_thiel_deep` and `palantir_technologies_deep` intake files in `data/intake/` for running deep_dive level (adds Step 9 bankruptcy + Step 12 international) while preserving original standard_vet data.
- **TMG Vetting Pipeline Memo** — Comprehensive memo written for non-technical TMG leadership at `~/Downloads/TMG_Vetting_Pipeline_Memo.docx`. Covers: full pipeline methodology, scoring details (both factual and RCS), what's automated vs manual, what could be automated with paid APIs and estimated costs.
- **Erik Prince test data cleaned up** — removed `data/unified/erik_prince.json` (was never a real pipeline run)
- **Lovable RCA prompt created** — `LOVABLE_RCA_PROMPT.md` and copy at `~/Downloads/LOVABLE_RCA_PROMPT.md` for pasting into Lovable

## Completed (Session 5)
- **TMG Client Conflict Check** — Pipeline reads `data/tmg_clients.csv` (54 clients from August 2025 Excel) and checks subject against client list during synthesis. Fuzzy matching with common-word filtering to reduce false positives.
- **Reputational Contagion Analysis (RCA)** — NEW major feature. Based on Perplexity report "Partisan Alignment & Reputational Contagion Analysis". Adds a separate scoring dimension to synthesis that evaluates whether working with a subject could harm TMG's brand, stakeholder relationships, or political reputation.
  - 6 scored questions (0-10): Partisan Alignment (25%), Stakeholder Backlash (20%), Narrative Vulnerability (15%), Client Conflicts (15%), Industry Toxicity (15%), Temporal Context (10%)
  - Produces a **Reputational Contagion Score (RCS)** alongside the factual risk score
  - Risk tiers: LOW (0-2.5), MODERATE (2.5-4.5), ELEVATED (4.5-6.5), HIGH (6.5-8.0), CRITICAL (8.0-10)
  - **Divergence alerts** when factual risk is low but reputational risk is high (the "Peter Thiel problem")
  - Includes "most damaging headline" test from Q3
  - Config lives in `config_tmg_identity.py` — TMG identity context, sector toxicity lists, RCS tiers
  - Integrated into `synthesize.py` — runs as part of Step 13 Claude synthesis, no extra API calls
- **Deep research** completed on TMG background, association risk frameworks, and Peter Thiel reputational profile

## Completed (Session 4)
- **Architecture changed** — from FastAPI server to local CLI + Git push + Lovable reads JSON
- **Pipeline tested end-to-end** — Peter Thiel quick_screen completed (3.31/10 MODERATE)
- **Deep news added to standard_vet** — Step 10 (15 Tavily queries) now runs in standard_vet, not just deep_dive
- **Manual findings support added**:
  - `data/manual/` directory for human researcher findings (property, social media, references, etc.)
  - `data/manual/_TEMPLATE.json` — copy this for each subject
  - `synthesize.py` loads manual findings and includes them in Claude prompt as HIGH-CONFIDENCE evidence
  - `--no-synthesis` flag pauses pipeline before synthesis so you can add manual data
- **CLI expanded** — pipeline.py now accepts `--city`, `--bio`, `--referral` flags
- **Peter Thiel standard_vet with deep news** — 114 Tavily sources, 257 court dockets, 387 EDGAR filings, 533 FEC contributions, 1950 SEC filings, lobbying data
- **Synthesis running** — unified JSON being generated at `data/unified/peter_thiel.json`

## Key Files
- `/Users/shannonwheatman/vetting/config.py` — Central config (API keys, endpoints, risk dimensions, scoring, vetting levels)
- `/Users/shannonwheatman/vetting/config_tavily.py` — Tavily domain filtering & source quality prompt
- `/Users/shannonwheatman/vetting/config_tmg_identity.py` — TMG identity context, RCA prompt, RCS tiers, sector toxicity lists
- `/Users/shannonwheatman/vetting/data/tmg_clients.csv` — TMG client list (54 clients from August 2025 Excel)
- `/Users/shannonwheatman/vetting/.env` — API keys (8 keys, all verified working)
- `/Users/shannonwheatman/vetting/requirements.txt` — Python dependencies
- `/Users/shannonwheatman/vetting/scripts/pipeline.py` — Main orchestrator (CLI entry point)
- `/Users/shannonwheatman/vetting/scripts/synthesize.py` — Step 13: Claude synthesis with combined_decision (factual + RCS)
- `/Users/shannonwheatman/vetting/scripts/search_litigation.py` — Step 4: CourtListener with full pagination
- `/Users/shannonwheatman/vetting/scripts/search_bankruptcy.py` — Step 9: CourtListener bankruptcy with full pagination
- `/Users/shannonwheatman/vetting/scripts/search_executives.py` — Step 11: Executive ID + mini-vet (EDGAR Form 3/4 → FEC, news, sanctions per exec)
- `/Users/shannonwheatman/vetting/scripts/search_contracts.py` — Step 14: USAspending.gov government contracts (no API key)
- `/Users/shannonwheatman/vetting/data/manual/_TEMPLATE.json` — Template for manual findings
- `/Users/shannonwheatman/vetting/data/unified/` — Final output JSONs (this is what Lovable displays)
- `/Users/shannonwheatman/vetting/LOVABLE_RCA_PROMPT.md` — OLD Lovable prompt (RCA only, Session 6)
- `/Users/shannonwheatman/vetting/LOVABLE_DASHBOARD_PROMPT.md` — NEW comprehensive Lovable prompt (RCS + combined decision + executives + contracts). Also copied to ~/Downloads/
- `/Users/shannonwheatman/vetting/src/lib/types.ts` — Lovable TypeScript types
- `/Users/shannonwheatman/vetting/src/lib/vetting-store.ts` — Lovable Zustand store
- `/Users/shannonwheatman/vetting/server.py` — **DEPRECATED** FastAPI server (no longer used)

## How to Run a Vetting

### Option A: Full auto (no manual findings)
```bash
cd /Users/shannonwheatman/vetting
python3 scripts/pipeline.py \
  --name "Subject Name" \
  --type individual \
  --company "Company" \
  --country US \
  --city "City, ST" \
  --bio "Brief bio..." \
  --referral "How they came to TMG" \
  --engagement domestic_political \
  --level standard_vet
```

### Option B: With manual findings (recommended)
```bash
# Step 1: Run research, pause before synthesis
python3 scripts/pipeline.py \
  --name "Subject Name" \
  --company "Company" \
  --engagement domestic_political \
  --level standard_vet \
  --no-synthesis

# Step 2: Add manual findings
cp data/manual/_TEMPLATE.json data/manual/subject_name.json
# Edit the file with property records, social media, references, etc.

# Step 3: Run synthesis (includes manual findings)
python3 scripts/synthesize.py --subject-id subject_name
```

### Option C: Re-run synthesis with new manual data
```bash
# Edit or create data/manual/subject_name.json
python3 scripts/synthesize.py --subject-id subject_name
```

### Push results to Lovable
```bash
git add data/unified/subject_name.json
git commit -m "Add vetting: Subject Name"
git push
```

## Vetting Levels
- **quick_screen**: Steps 0,1,2,3,13 — Sanctions, debarment, basic news (3 queries), synthesis
- **standard_vet**: Steps 0,1,2,3,4,5,6,7,8,10,11,14,13 — All APIs + deep news + exec ID + gov contracts, synthesis
- **deep_dive**: Steps 0,1,2,3,4,5,6,7,8,9,10,11,12,14,13 — Everything + bankruptcy + international + exec ID + gov contracts

## Pipeline Scripts (in `scripts/`)
- `intake.py` (Step 0), `check_sanctions.py` (Step 1), `check_debarment.py` (Step 2)
- `search_news.py` (Steps 3/10), `search_litigation.py` (Step 4 — now with pagination), `search_corporate.py` (Step 5)
- `search_fec.py` (Step 6), `search_sec.py` (Step 7), `search_lobbying.py` (Step 8)
- `search_bankruptcy.py` (Step 9 — now with pagination), `search_executives.py` (Step 11 — orgs only)
- `search_international.py` (Step 12), `search_contracts.py` (Step 14 — USAspending.gov)
- `synthesize.py` (Step 13 — now with combined_decision), `pipeline.py` (orchestrator)

## Manual Findings Categories
Use `data/manual/_TEMPLATE.json` as a starting point. Categories:
- `property_assets` — Real estate, property records from county assessor
- `reference_checks` — Phone calls, personal references
- `social_media` — LinkedIn, X/Twitter, Facebook findings
- `other` — Anything else (documents, email chains, etc.)
- `notes` — Free-form vetter observations passed to Claude

## Git Repo
- **URL**: https://github.com/TMG-AI/tmg-sentinel
- **Branch**: main
- Contains: Lovable frontend (src/), Python pipeline (scripts/), data output (data/)

## What Lovable Needs (NOT DONE YET)
1. **Submit form → email**: Change "Confirm & Start Vetting" to open a mailto link to Shannon's Gmail with all form fields in the body, instead of calling addVetting()
2. **Dashboard reads from JSON files**: Remove mock data. Load vetting results from JSON files committed to the repo (in `public/data/` or similar). Each file follows the existing `VettingResultJSON` type in types.ts.
3. **Sources section on VettingDetail page** — types are there, UI rendering may need work
4. **Combined Decision display** — The unified JSON now has a `combined_decision` object. Lovable should display this as the PRIMARY recommendation, not just `scoring.recommendation`
5. **Deep dive results** — Once `peter_thiel_deep.json` and `palantir_technologies_deep.json` are generated, copy them to `public/data/vettings/` and update `public/data/vettings-index.json`

## Pipeline Output — Three Decision Layers
The unified JSON now produces:
1. **Factual Risk Score** (0-10) — Traditional due diligence: sanctions, litigation, SEC, FEC, news → `scoring.recommendation`
2. **Reputational Contagion Score** (0-10) — TMG-specific: partisan alignment, stakeholder backlash, narrative vulnerability, client conflicts, industry toxicity, temporal context → `reputational_contagion.rcs_recommendation`
3. **Combined Decision** — Takes the MORE CAUTIOUS of the two → `combined_decision.recommendation` (THIS IS THE ONE TO DISPLAY)

If factual risk is LOW but RCS is HIGH, a **DIVERGENCE ALERT** is flagged. The combined decision will reflect the higher-risk signal.

## Test Data — Standard Vet (original, preserved)

### Peter Thiel (standard_vet)
- **Subject ID**: `peter_thiel`
- **Engagement**: domestic_political (1.0x multiplier)
- **Level**: standard_vet
- **Factual Risk**: 3.31/10 MODERATE — Conditional Approve (from quick screen; standard_vet synthesis was pre-RCA)
- **NOTE**: This was synthesized BEFORE combined_decision and full RCA existed

### Palantir Technologies (standard_vet)
- **Subject ID**: `palantir_technologies`
- **Type**: organization
- **Engagement**: domestic_corporate (0.85x multiplier)
- **Level**: standard_vet
- **Factual Risk: 2.41/10 LOW** — Approve
- **RCS: 4.85/10 ELEVATED** — Requires Jim/Tara/partner sign-off
- **NOTE**: No combined_decision field (synthesized before Session 6 fix)

## Test Data — Deep Dive (new, with combined_decision + pagination)

### Peter Thiel (deep_dive)
- **Subject ID**: `peter_thiel_deep`
- **Engagement**: domestic_political (1.0x multiplier)
- **Level**: deep_dive (adds bankruptcy Step 9, international Step 12)
- **Status**: AWAITING RUN — Shannon needs to run in terminal

### Palantir Technologies (deep_dive)
- **Subject ID**: `palantir_technologies_deep`
- **Type**: organization
- **Engagement**: domestic_corporate (0.85x multiplier)
- **Level**: deep_dive
- **Status**: AWAITING RUN — Shannon needs to run in terminal after Peter Thiel

## Lovable Integration Status
- `LOVABLE_RCA_PROMPT.md` — Full prompt for Lovable to add RCA display, dual scores, divergence alerts, mailto form
- `public/data/vettings-index.json` — Currently lists peter_thiel.json and palantir_technologies.json
- `public/data/vettings/*.json` — Copies of unified JSONs where Lovable's store reads from
- Shannon should paste `LOVABLE_RCA_PROMPT.md` contents into Lovable chat to implement
- **After deep dives complete**: copy `_deep` JSONs to `public/data/vettings/` and update index

## What's Next
1. **Run deep dives in terminal** — commands need updating for new steps (11, 14)
2. **Give Lovable the RCA prompt** — paste LOVABLE_RCA_PROMPT.md content into Lovable
3. **Update Lovable to display combined_decision** — not just scoring.recommendation
4. **Update Lovable to display executive findings and government contracts** — new data in unified JSON
5. **Copy deep dive results to public/data/vettings/** and update index after runs complete
6. **Test more subjects** — run pipeline on realistic potential clients
7. **FEC limitation**: Karp's $1M MAGA Inc / inauguration donations not captured by schedule_a individual search — those are committee-level transfers. News searches will catch these, but consider adding PAC/committee contribution search in a future iteration.

## Deep Dive Terminal Commands (Updated Session 7 — now includes Step 11 + Step 14)

### Peter Thiel Deep Dive (individual — Step 11 will auto-skip)
```bash
cd /Users/shannonwheatman/vetting && python3 scripts/pipeline.py \
  --name "Peter Thiel" \
  --type individual \
  --company "Palantir Technologies" \
  --country US \
  --engagement domestic_political \
  --level deep_dive
```
Note: Step 11 (exec ID) auto-skips for individuals. Step 14 (contracts) will search "Palantir Technologies".

### Palantir Deep Dive (organization — full exec + contracts)
```bash
cd /Users/shannonwheatman/vetting && python3 scripts/pipeline.py \
  --name "Palantir Technologies" \
  --type organization \
  --company "Palantir Technologies" \
  --country US \
  --city "Denver, CO" \
  --engagement domestic_corporate \
  --level deep_dive
```
Note: Step 11 identifies executives via EDGAR, mini-vets each. Step 14 pulls gov contracts from USAspending.gov. Deep news now includes 6 org-specific queries (boycotts, exec statements, etc.).

## Perplexity Reports (in ~/Downloads/)
- `TMG Vetting Pipeline  Tavily Domain Configuration & Quality Prompt.pdf`
- `So help me curate a list of websites that my vetti.pdf`
- `TMG Vetting Pipeline  Risk Scoring Dimensions & Weights Review (1).pdf`
- `vetting_questionnaire.pdf` / `.docx`
- `TMG Vetting Pipeline  Partisan Alignment & Reputational Contagion Analysis.pdf` — Framework for RCA (implemented in Session 5)

## Session 7 Code Changes Summary
1. **NEW: `scripts/search_executives.py`** — Step 11. Identifies executives via SEC EDGAR Form 3/4 XML parsing (CIK lookup → submissions → parse ownership XML). For each executive: FEC donations, Tavily news, OpenSanctions. Falls back to Tavily for non-SEC companies. Auto-skips for individuals.
2. **NEW: `scripts/search_contracts.py`** — Step 14. Searches USAspending.gov POST API for contracts + IDVs by company name. Paginates (up to 1000 results). Aggregates by agency. No API key needed.
3. **`config.py`** — Added `EXECUTIVES_DIR`, `CONTRACTS_DIR`, `usaspending_awards` endpoint. Updated vetting levels to include Steps 11, 14. Added `TAVILY_ORG_QUERIES` (6 org-specific deep queries). Updated `STEP_SCRIPTS` and `STEP_NAMES`.
4. **`scripts/search_news.py`** — Now appends `TAVILY_ORG_QUERIES` during deep search when subject_type == "organization".
5. **`scripts/pipeline.py`** — Added Step 11 and Step 14 blocks. Imports `search_executives` and `search_contracts`.
6. **`scripts/synthesize.py`** — Added `format_executives_for_prompt()` and `format_contracts_for_prompt()`. Updated `load_all_step_data()` to load executives and contracts. Updated prompt to include both new data sections.

## Session 6 Code Changes Summary
1. **`scripts/synthesize.py`** — Added `combined_decision` block after RCS computation (~line 970). Takes max severity of factual tier vs RCS tier. New fields: `recommendation`, `combined_tier`, `factual_tier`, `factual_score`, `rcs_tier`, `rcs_score`, `driver`, `driver_detail`.
2. **`scripts/search_litigation.py`** — Replaced single-page `search_courtlistener()` with paginated version. MAX_PAGES=25 (500 results cap). Both dockets and opinions now fully paginated. Removed `[:10]` cap on opinions and `[:5]` cap on output.
3. **`scripts/search_bankruptcy.py`** — Same pagination treatment. MAX_PAGES=25. Gracefully handles errors mid-pagination (returns what was collected).
4. **`data/intake/peter_thiel_deep.json`** and **`data/intake/palantir_technologies_deep.json`** — Deep dive intake files with `_deep` suffix subject IDs.
