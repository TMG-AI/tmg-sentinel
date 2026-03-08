# Vetting Pipeline Project - Session Status

## Last Updated: 2026-03-07 (Session 5 — in progress)

## Architecture Decision (Session 4)
**Lovable CANNOT run Python code.** The FastAPI server / localhost approach from Session 3 was wrong — Lovable previews run in the cloud and can't reach localhost. After evaluating options (Vercel, n8n, ngrok), we chose the **Palantir model**:

1. Shannon runs the Python pipeline locally from terminal
2. Pipeline outputs unified JSON to `data/unified/<subject_id>.json`
3. Shannon commits and pushes to GitHub
4. Lovable reads the JSON files from the repo and displays results to the team
5. The Submit Vetting form in Lovable sends an email (mailto) to Shannon instead of calling an API

**The FastAPI server (`server.py`) is no longer used.**

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
- `/Users/shannonwheatman/vetting/scripts/synthesize.py` — Step 13: Claude synthesis (loads all step data + manual findings)
- `/Users/shannonwheatman/vetting/data/manual/_TEMPLATE.json` — Template for manual findings
- `/Users/shannonwheatman/vetting/data/unified/` — Final output JSONs (this is what Lovable displays)
- `/Users/shannonwheatman/vetting/src/lib/types.ts` — Lovable TypeScript types
- `/Users/shannonwheatman/vetting/src/lib/vetting-store.ts` — Lovable Zustand store (currently uses mock data)
- `/Users/shannonwheatman/vetting/src/pages/SubmitVetting.tsx` — Form (needs mailto change)
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
- **standard_vet**: Steps 0,1,2,3,4,5,6,7,8,10,13 — All APIs + deep news (15 queries), synthesis
- **deep_dive**: Steps 0,1,2,3,4,5,6,7,8,9,10,12,13 — Everything + bankruptcy + international

## Pipeline Scripts (in `scripts/`)
- `intake.py` (Step 0), `check_sanctions.py` (Step 1), `check_debarment.py` (Step 2)
- `search_news.py` (Steps 3/10), `search_litigation.py` (Step 4), `search_corporate.py` (Step 5)
- `search_fec.py` (Step 6), `search_sec.py` (Step 7), `search_lobbying.py` (Step 8)
- `search_bankruptcy.py` (Step 9), `search_international.py` (Step 12)
- `synthesize.py` (Step 13), `pipeline.py` (orchestrator)

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

## Pipeline Output — Two Scores Side by Side
The unified JSON now produces BOTH:
1. **Factual Risk Score** (0-10) — Traditional due diligence: sanctions, litigation, SEC, FEC, news
2. **Reputational Contagion Score** (0-10) — TMG-specific: partisan alignment, stakeholder backlash, narrative vulnerability, client conflicts, industry toxicity, temporal context

If factual risk is LOW but RCS is HIGH, a **DIVERGENCE ALERT** is flagged. This is the key innovation — catching "legally clean but reputationally toxic" subjects like Peter Thiel.

## Perplexity Reports (in ~/Downloads/)
- `TMG Vetting Pipeline  Tavily Domain Configuration & Quality Prompt.pdf`
- `So help me curate a list of websites that my vetti.pdf`
- `TMG Vetting Pipeline  Risk Scoring Dimensions & Weights Review (1).pdf`
- `vetting_questionnaire.pdf` / `.docx`
- `TMG Vetting Pipeline  Partisan Alignment & Reputational Contagion Analysis.pdf` — Framework for RCA (implemented in Session 5)

## Peter Thiel Test Data
- **Subject ID**: `peter_thiel`
- **Engagement**: domestic_political (1.0x multiplier)
- **Level**: standard_vet (with deep news)
- **Quick screen result**: 3.31/10 MODERATE — Conditional Approve
- **Standard vet**: 114 Tavily sources, synthesis running
- **Data files**: `data/intake/peter_thiel.json`, `data/sanctions/peter_thiel.json`, `data/debarment/peter_thiel.json`, `data/news/peter_thiel.json`, `data/litigation/peter_thiel.json`, `data/corporate/peter_thiel.json`, `data/fec/peter_thiel.json`, `data/sec/peter_thiel.json`, `data/lobbying/peter_thiel.json`, `data/unified/peter_thiel.json`

## Palantir Technologies Test Data (Session 5)
- **Subject ID**: `palantir_technologies`
- **Type**: organization
- **Engagement**: domestic_corporate (0.85x multiplier)
- **Level**: standard_vet
- **Factual Risk: 2.41/10 LOW** — Approve
- **RCS: 4.85/10 ELEVATED** — Requires Jim/Tara/partner sign-off
- Key RCS scores: Partisan Alignment 3, Stakeholder Backlash 6, Narrative Vulnerability 7, Client Conflicts 2, Industry Toxicity 7, Temporal Context 5
- Most Damaging Headline: "Obama Campaign Manager's Firm Now Helping Trump-Donor Thiel's Surveillance Company Target Americans"
- 98 Tavily sources, 248 dockets, 3166 EDGAR filings, 10000+ SEC filings

## Lovable Integration Status
- `LOVABLE_RCA_PROMPT.md` — Full prompt for Lovable to add RCA display, dual scores, divergence alerts, mailto form
- `public/data/vettings-index.json` — Lists peter_thiel.json and palantir_technologies.json
- `public/data/vettings/*.json` — Copies of unified JSONs where Lovable's store reads from
- Shannon should paste `LOVABLE_RCA_PROMPT.md` contents into Lovable chat to implement

## What's Next
1. **Give Lovable the RCA prompt** — paste LOVABLE_RCA_PROMPT.md content into Lovable
2. **Re-run Peter Thiel synthesis** with RCA module (current peter_thiel.json has RCA from pre-Session-5 synthesis)
3. **Test more subjects** — run standard_vet on realistic potential clients
