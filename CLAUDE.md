# Vetting Pipeline Project - Session Status

## Last Updated: 2026-03-07 (Session 2)

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

## Key Files
- `/Users/shannonwheatman/vetting/api_database_research.md` — API/database research
- `/Users/shannonwheatman/vetting/config.py` — Central config (API keys, endpoints, risk dimensions, scoring)
- `/Users/shannonwheatman/vetting/config_tavily.py` — Tavily domain filtering & source quality prompt
- `/Users/shannonwheatman/vetting/.env` — API keys (OpenSanctions, LDA, SAM.gov, CourtListener, Anthropic, Tavily, FEC, Congress)
- `/Users/shannonwheatman/vetting/LOVABLE_PROMPT.md` — Lovable dashboard spec
- `/Users/shannonwheatman/vetting/scripts/pipeline.py` — Main orchestrator
- `/Users/shannonwheatman/vetting/scripts/synthesize.py` — Step 13: Claude synthesis with SOURCE_QUALITY_PROMPT

## Pipeline Scripts (in `scripts/`)
- `intake.py` (Step 0), `check_sanctions.py` (Step 1), `check_debarment.py` (Step 2)
- `search_news.py` (Steps 3/10), `search_litigation.py` (Step 4), `search_corporate.py` (Step 5)
- `search_fec.py` (Step 6), `search_sec.py` (Step 7), `search_lobbying.py` (Step 8)
- `search_bankruptcy.py` (Step 9), `search_international.py` (Step 12)
- `synthesize.py` (Step 13), `pipeline.py` (orchestrator)

## Perplexity Reports (in ~/Downloads/)
- `TMG Vetting Pipeline  Tavily Domain Configuration & Quality Prompt.pdf` — Full Tavily config guide (implemented)
- `So help me curate a list of websites that my vetti.pdf` — Summary of Tavily strategy
- `TMG Vetting Pipeline  Risk Scoring Dimensions & Weights Review (1).pdf` — Scoring dimensions review
- `vetting_questionnaire.pdf` / `.docx` — Client vetting questionnaire

## Next Steps / Not Done
- Test pipeline end-to-end with a real subject
- Verify all API integrations work (some scripts may need debugging)
- Build Lovable dashboard (spec in LOVABLE_PROMPT.md)
- No git repo initialized yet
