# Vetting Pipeline Project - Session Status

## Last Updated: 2026-03-07 (Session 3)

## Completed
- Full API/database research for client vetting pipeline across 5 categories
- Research document created at `/Users/shannonwheatman/vetting/api_database_research.md`
- API keys/accounts set up for chosen services (in `.env`)
- Consolidated `tmg-vetting/` into `vetting/` (tmg-vetting deleted)
- Pipeline code scaffolded (from prior session): 14 scripts, config.py, full pipeline.py orchestrator
- **Tavily domain filtering & source quality config** — `config_tavily.py` created from Perplexity report:
  - Global exclude list: 68 domains (Wikipedia, Reddit, tabloids, state media, SEO spam, review sites)
  - 6 targeted include lists: News/Wire, Investigative, Political, Legal, International, Corporate
  - `get_tavily_params()` helper auto-configures domain filtering per pipeline step
  - `SOURCE_QUALITY_PROMPT` with 7-tier source trust hierarchy, citation rules, conflict handling
- Integrated `config_tavily` into: `search_news.py`, `search_international.py`, `synthesize.py`
- All scripts compile clean
- **Git repo set up**: pushed to `https://github.com/TMG-AI/tmg-sentinel` (main branch)
- **Lovable app already exists** in repo — React/Vite/Shadcn dashboard with:
  - Dashboard, Submit Vetting form, VettingDetail page, History, Settings
  - 5 mock vettings, Zustand store, full TypeScript types
  - Uses "Upload Results JSON" button to load pipeline results (same as Palantir pattern)
- **Gap analysis completed** — Pipeline output vs Lovable types are 95% aligned:
  - `sources` array (Tavily citations) — pipeline produces it, Lovable needs to add to types.ts and render
  - `source_urls` on evidence items — pipeline produces it, Lovable needs to add to Evidence interface and render
  - Everything else matches: subject, gates, 7 dimensions, scoring, flags, executive_summary, metadata

## Key Files
- `/Users/shannonwheatman/vetting/api_database_research.md` — API/database research
- `/Users/shannonwheatman/vetting/config.py` — Central config (API keys, endpoints, risk dimensions, scoring)
- `/Users/shannonwheatman/vetting/config_tavily.py` — Tavily domain filtering & source quality prompt
- `/Users/shannonwheatman/vetting/.env` — API keys (OpenSanctions, LDA, SAM.gov, CourtListener, Anthropic, Tavily, FEC, Congress)
- `/Users/shannonwheatman/vetting/LOVABLE_PROMPT.md` — Lovable dashboard spec
- `/Users/shannonwheatman/vetting/scripts/pipeline.py` — Main orchestrator
- `/Users/shannonwheatman/vetting/scripts/synthesize.py` — Step 13: Claude synthesis with SOURCE_QUALITY_PROMPT
- `/Users/shannonwheatman/vetting/src/lib/types.ts` — Lovable TypeScript types (VettingResultJSON)
- `/Users/shannonwheatman/vetting/src/lib/mock-data.ts` — 5 mock vettings
- `/Users/shannonwheatman/vetting/src/lib/vetting-store.ts` — Zustand store with uploadResults()
- `/Users/shannonwheatman/vetting/src/pages/VettingDetail.tsx` — Full results display (gates, dimensions, flags, executive summary, decision)

## Pipeline Scripts (in `scripts/`)
- `intake.py` (Step 0), `check_sanctions.py` (Step 1), `check_debarment.py` (Step 2)
- `search_news.py` (Steps 3/10), `search_litigation.py` (Step 4), `search_corporate.py` (Step 5)
- `search_fec.py` (Step 6), `search_sec.py` (Step 7), `search_lobbying.py` (Step 8)
- `search_bankruptcy.py` (Step 9), `search_international.py` (Step 12)
- `synthesize.py` (Step 13), `pipeline.py` (orchestrator)

## Git Repo
- **URL**: https://github.com/TMG-AI/tmg-sentinel
- **Branch**: main
- Contains both Lovable frontend (src/) and Python pipeline (scripts/, config.py, config_tavily.py)

## Perplexity Reports (in ~/Downloads/)
- `TMG Vetting Pipeline  Tavily Domain Configuration & Quality Prompt.pdf` — Full Tavily config guide (implemented)
- `So help me curate a list of websites that my vetti.pdf` — Summary of Tavily strategy
- `TMG Vetting Pipeline  Risk Scoring Dimensions & Weights Review (1).pdf` — Scoring dimensions review
- `vetting_questionnaire.pdf` / `.docx` — Client vetting questionnaire

## How the Pipeline → Lovable Flow Works
1. User fills out vetting form in Lovable (subject name, type, company, engagement type, vetting level)
2. Pipeline runs from command line: `python3 scripts/pipeline.py --subject-id <id>`
3. Pipeline outputs unified JSON to `data/unified/<subject_id>.json`
4. Copy JSON to Lovable — use "Upload Results JSON" button on VettingDetail page
5. Lovable reads the JSON and displays full risk assessment with citations

## Lovable Changes Still Needed (give these to Lovable)
1. Add `sources: {id: number; url: string; title: string; score: number}[]` to VettingResultJSON in types.ts
2. Add Sources section to VettingDetail.tsx (numbered list of clickable Tavily citations)
3. Add `source_urls?: {url: string; title: string}[]` to Evidence interface in types.ts
4. Render source_urls as clickable citation link chips on evidence items in VettingDetail.tsx

## Next Steps / Not Done
- **Test pipeline end-to-end** with a real subject (Peter Thiel test planned)
- **Give Lovable the 2 type updates** (sources array + source_urls on evidence)
- Install Python dependencies (requirements.txt needed)
- Debug any API integration issues found during testing
