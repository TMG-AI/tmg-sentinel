# Lovable Prompt — Copy Everything Below This Line

Build a **TMG Client Vetting Dashboard** — a professional internal web app for The Messina Group (TMG), a political consulting firm. This tool lets team members submit potential clients for vetting, tracks the automated vetting pipeline's progress, displays risk assessment results, and records approve/reject decisions with a full audit trail. Think of it as an internal due diligence command center.

## Overview

TMG needs to vet potential clients before signing contracts. The vetting process identifies reputational, legal, political, financial, and ethical risks. Currently this is done manually (6-10 requests per month, 1-12 hours each). This app wraps around an automated Python pipeline that checks sanctions lists, court records, corporate filings, campaign finance, SEC filings, lobbying disclosures, and news/media — then uses AI to synthesize a risk assessment.

The app has 5 main pages: Submit New Vetting, Active Vettings Dashboard, Vetting Results Detail, Vetting History, and Settings/Admin.

## Database (Supabase)

Use Supabase for all data storage. The app needs these tables:

### `vetting_requests` table
- `id` — UUID, primary key
- `subject_name` — text, required (the person or company being vetted)
- `subject_type` — enum: "individual" or "organization"
- `company_affiliation` — text, nullable
- `country` — text, nullable
- `city` — text, nullable
- `brief_bio` — text, nullable (background info provided by requester)
- `referral_source` — text, nullable (who referred this potential client)
- `engagement_type` — enum: "fara_foreign_political", "foreign_corporate", "domestic_political", "domestic_corporate"
- `vetting_level` — enum: "quick_screen", "standard_vet", "deep_dive"
- `requested_by` — text, required (who submitted the request — Jim, Ben, Tara, etc.)
- `requested_at` — timestamp with timezone, defaults to now()
- `status` — enum: "pending", "running", "gates_failed", "completed", "error"
- `pipeline_progress` — jsonb, nullable (tracks which steps have completed)
- `result_json` — jsonb, nullable (the full unified vetting result from the pipeline)
- `composite_score` — float, nullable (0-10 risk score)
- `risk_tier` — text, nullable ("LOW", "MODERATE", "ELEVATED", "HIGH", "CRITICAL")
- `recommendation` — text, nullable ("Approve", "Conditional Approve", "Further Review", "Recommend Reject", "Auto-Reject")
- `confidence` — text, nullable ("HIGH", "MEDIUM", "LOW")
- `decision` — enum, nullable: "approved", "conditionally_approved", "rejected", "pending_review"
- `decided_by` — text, nullable
- `decided_at` — timestamp, nullable
- `decision_notes` — text, nullable (rationale for the decision)
- `completed_at` — timestamp, nullable
- `flags` — jsonb, nullable (array of red/yellow flag objects)

### `vetting_documents` table
- `id` — UUID, primary key
- `vetting_id` — UUID, foreign key to vetting_requests
- `file_name` — text
- `file_url` — text (Supabase storage URL)
- `file_type` — text (pdf, docx, etc.)
- `uploaded_at` — timestamp

### `audit_log` table
- `id` — UUID, primary key
- `vetting_id` — UUID, foreign key to vetting_requests
- `action` — text (e.g., "submitted", "pipeline_started", "gate_failed", "completed", "decision_made", "reopened")
- `performed_by` — text
- `performed_at` — timestamp
- `details` — jsonb, nullable

### `tmg_clients` table (for conflict of interest checking)
- `id` — UUID, primary key
- `client_name` — text
- `industry` — text, nullable
- `engagement_type` — text, nullable
- `active` — boolean, default true
- `added_at` — timestamp

## Page 1: Submit New Vetting (main entry point)

A clean form for submitting a new vetting request. This is the most important page — make it intuitive.

**Form fields:**

Section: "Who are we vetting?"
- Subject Name (text input, required) — placeholder: "Full name of person or company"
- Subject Type (radio: Individual / Organization)
- Company Affiliation (text input, optional) — placeholder: "Company or organization name"
- Country (text input with autocomplete, optional) — placeholder: "Country of origin or primary operations"
- City (text input, optional)

Section: "Background Information"
- Brief Bio (large textarea, optional) — placeholder: "Any background info, context about who they are, how they came to us, what we know so far..."
- Referral Source (text input, optional) — placeholder: "Who referred them? How did they find TMG?"
- Engagement Type (select dropdown, required):
  - "FARA-Registerable Foreign Political Work" (shows a small orange warning badge: "1.3x risk multiplier")
  - "Foreign Corporate Engagement" (shows: "1.15x risk multiplier")
  - "Domestic Political Engagement"
  - "Routine Domestic Corporate" (shows: "0.85x risk multiplier — lower risk context")

Section: "Vetting Configuration"
- Vetting Level (3 large selectable cards, not a dropdown):
  - **Quick Screen** — "Sanctions, debarment, basic news scan. ~5 minutes. Best for: Known quantities, quick checks."
    Steps shown: Sanctions Check, Debarment Check, Basic News Scan, AI Synthesis
  - **Standard Vet** (selected by default, highlighted) — "Full domestic background check. ~15 minutes. Best for: Most new clients."
    Steps shown: Everything in Quick Screen + Litigation, Corporate Filings, Campaign Finance, SEC Filings, Lobbying
  - **Deep Dive** — "Comprehensive international investigation. ~30 minutes. Best for: Foreign clients, high-profile individuals, politically sensitive engagements."
    Steps shown: Everything in Standard + Bankruptcy, Expanded Media, Social Media, International/PEP Checks

Section: "Attachments" (optional)
- Drag-and-drop file upload area. Accepts PDF, DOCX, images. Text: "Drop resumes, bios, email chains, or any relevant documents here"
- Show uploaded file names with remove buttons

Section: "Submitted By"
- Your Name (select dropdown): Jim, Ben, Tara, Shannon, Other (with text input if Other)
- CC / Notify (multi-select checkboxes): Jim, Ben, Tara, Shannon — Tara is checked by default

Big green submit button: "Start Vetting" — with a confirmation dialog showing a summary of what was entered.

After submission: Redirect to the Active Vettings Dashboard with a success toast notification.

## Page 2: Active Vettings Dashboard (home page after first use)

Shows all vetting requests that are in progress or recently completed. This is the daily working view.

**Top stats bar** (4 metric cards):
- Total Active Vettings (count of status = "running" or "pending")
- Awaiting Decision (count of completed but decision = null)
- Completed This Month (count)
- Average Turnaround Time (average time from requested_at to completed_at)

**Main content: Vetting request cards** sorted by most recent first.

Each card shows:
- Subject name (large, bold)
- Subject type badge: "Individual" (blue) or "Organization" (purple)
- Engagement type badge with color:
  - FARA Foreign Political = orange
  - Foreign Corporate = yellow
  - Domestic Political = blue
  - Domestic Corporate = gray
- Vetting level badge: Quick Screen (green), Standard Vet (blue), Deep Dive (purple)
- Status indicator:
  - "Pending" — gray spinner
  - "Running" — animated blue progress bar showing which step is active (e.g., "Step 4/8: Searching litigation records...")
  - "Gates Failed" — red badge with skull icon (sanctions or debarment match found)
  - "Completed" — green checkmark
  - "Error" — red X
- If completed: Risk tier badge with color:
  - LOW = green
  - MODERATE = yellow
  - ELEVATED = orange
  - HIGH = red
  - CRITICAL = dark red/black
- Composite score (if completed): large number like "3.2 / 10"
- Recommendation text (if completed): "Approve", "Conditional Approve", "Further Review", "Recommend Reject", "Auto-Reject"
- Requested by and timestamp
- If decision has been made: Decision badge ("Approved" green, "Conditionally Approved" yellow, "Rejected" red) with who decided and when
- Click anywhere on the card to go to the detail page

**Filters**: By status, by vetting level, by risk tier, by engagement type, by requested_by. Search by subject name.

**Sort options**: Most recent, highest risk score, oldest first, awaiting decision.

## Page 3: Vetting Results Detail (click any vetting)

The comprehensive results page for a single vetting request. This is where decision-makers review findings and make go/no-go calls.

### Header Section
- Subject name (very large)
- Subject type, engagement type, country badges
- Vetting level badge
- Requested by [name] on [date]
- Status badge
- If completed: Large composite risk score gauge (semicircular or radial, 0-10, color-coded by tier)
- Risk tier badge (large)
- Recommendation badge (large)
- Confidence badge: HIGH (green), MEDIUM (yellow), LOW (red — with text "Low confidence — recommend manual review regardless of score")

### Binary Gate Results (always shown first)
Two prominent cards:
- **Sanctions / Watchlist Gate**: PASS (green checkmark) or FAIL (red X with details)
  - If FAIL: Show which list matched, the matched name, match confidence percentage
  - Sources checked: OFAC SDN, UN Sanctions, EU Sanctions, OpenSanctions, Interpol Red Notices
- **Government Exclusion Gate**: PASS (green checkmark) or FAIL (red X with details)
  - If FAIL: Show which database matched, exclusion type, excluding agency, dates
  - Sources checked: SAM.gov, HHS OIG LEIE

If either gate FAILED: Show a large red banner: "AUTO-REJECTED — [Sanctions/Debarment] match found. No composite score calculated. Legal counsel required to override." The rest of the scoring section is hidden/grayed out.

### Risk Dimension Scorecard (7 dimensions)
Show 7 horizontal progress bars, one per dimension, sorted by weight (highest first):

1. **Litigation / Legal Risk** (22%) — bar from 0-10
   - Sub-text showing key findings: "2 active civil cases found. No criminal records."
2. **Media / Reputation Risk** (20%)
   - Sub-text: "Moderate negative coverage. 3 controversy articles found."
3. **International / PEP Risk** (15%)
   - Sub-text: "Not a PEP. Country risk: Low (US-based)."
4. **Financial / SEC Risk** (12%)
   - Sub-text: "No SEC enforcement actions. Clean filing history."
5. **Corporate / Business Risk** (11%)
   - Sub-text: "3 active companies. Ownership structure clear."
6. **Political / Lobbying Risk** (10%)
   - Sub-text: "$45,000 in political contributions. No FARA issues."
7. **Conflict of Interest** (10%)
   - Sub-text: "No conflicts with current TMG clients identified."

Color the bars: 0-2.5 green, 2.5-4.5 yellow, 4.5-6.5 orange, 6.5-10 red.

Show the weight percentage next to each bar. Show the dimension score as a number at the end of the bar.

### Modifiers Section
Show which modifiers were applied:
- Confidence Modifier: "HIGH confidence — score used as-is" (or MEDIUM/LOW with explanation)
- Temporal Decay: "Findings weighted by recency (2-year: 1.0x, 5-year: 0.7x, 10-year: 0.4x)"
- Engagement Context: "FARA foreign political work — 1.3x risk multiplier applied" (show pre/post multiplier scores)

### Flags Inventory
Two sections side by side:
- **Red Flags** (red cards with exclamation icon): Each flag with source, date, description
- **Yellow Flags** (yellow cards with warning icon): Each flag with source, date, description

If no flags: Show green "No flags identified" message.

### Executive Summary
A card with the AI-generated executive summary text (the memo/email format that would be sent to leadership). This is the synthesis output. Should be well-formatted markdown with sections for: Biography, Professional Background, Key Findings, Risk Assessment, Recommendation.

### Evidence by Dimension (expandable accordion)
For each of the 7 dimensions, an expandable section showing:
- All evidence items found
- Each with: source name, URL (clickable), date, relevance, a snippet of the finding
- Organized by sub-factor within each dimension

### Attached Documents
Show any uploaded documents with download links.

### Decision Section (sticky at bottom or sidebar)
This is where the reviewer makes their call:

- 4 large buttons: **Approve** (green), **Conditionally Approve** (yellow), **Reject** (red), **Send for Further Review** (blue)
- Decision Notes textarea (required for Conditional Approve and Reject): "Explain the rationale for this decision..."
- Decided By (auto-filled from current user, editable)
- Submit Decision button

After decision is submitted: The card updates in the dashboard, audit log entry is created, and the decision section shows the recorded decision with timestamp.

If a decision has already been made, show it as a locked card with the decision, notes, who decided, and when. Include a "Reopen" button (creates an audit log entry).

### Pipeline Step Details (expandable at very bottom)
Technical section showing what the pipeline actually did:
- Each step: name, status (completed/skipped/error), start time, duration, number of results found
- Raw data links: "View raw sanctions JSON", "View raw litigation JSON", etc.

## Page 4: Vetting History

A searchable, filterable table of all past vettings. This is the institutional memory.

Columns: Subject Name, Type, Engagement Type, Vetting Level, Risk Score, Risk Tier, Recommendation, Decision, Requested By, Date, Decided By

All columns sortable. Full-text search across subject name, bio, and decision notes.

Filters: By date range, by risk tier, by decision, by engagement type, by requested_by.

Export to CSV button.

Click any row to go to the full detail page.

## Page 5: Settings / Admin

- **TMG Client List**: Table of current TMG clients (for conflict of interest checking). Add/edit/remove clients. Fields: Client Name, Industry, Engagement Type, Active status. Import from CSV button.
- **Team Members**: Manage who can submit and who can decide. Names and roles.
- **Notification Preferences**: Who gets notified on new submissions, completions, red flags.
- **Pipeline Status**: Shows whether the Python pipeline backend is connected and healthy. API key status (which APIs are configured and working).

## Design

- **Light mode default** — clean white background, professional and trustworthy feel. This is an internal tool for serious due diligence decisions, not a flashy dashboard.
- **Color palette**: Navy/dark blue for headers and primary actions. White/light gray for content areas. Risk colors: green (low), yellow (moderate), orange (elevated), red (high), dark red/black (critical).
- **Typography**: Clean sans-serif. Subject names large and bold. Scores and tiers highly prominent.
- **Desktop-first** but responsive. This will primarily be used on laptops.
- **Emphasis on scannability**: Someone should be able to glance at a vetting card and immediately know the risk level, recommendation, and whether a decision has been made.
- **Professional, government-adjacent aesthetic**: Think law firm intranet meets compliance software. No playful elements. Subtle shadows, clean borders, generous whitespace.
- **Left sidebar navigation** with icons for: New Vetting (+ icon), Active Vettings (dashboard icon), History (clock icon), Settings (gear icon).
- TMG branding: Include "The Messina Group" in the top-left with a simple wordmark. Subtitle: "Client Vetting System".

## Authentication

Use Supabase Auth with email/password. For MVP, seed 5 users: Jim, Ben, Tara, Shannon, and a generic "Admin" account. The login page should be simple — TMG branding, email, password, sign in button.

Role-based access:
- **Admin**: Full access including settings, client list management
- **Reviewer**: Can submit vettings and make decisions
- **Viewer**: Can view vettings and results but cannot submit or decide

## Important Implementation Notes

1. The Python pipeline backend does NOT exist in this app. The app stores vetting requests in Supabase and will eventually receive results via API. For now, include a way to manually paste/upload a JSON result into a vetting request (for testing). Add a small "Upload Results JSON" button on the detail page that accepts a JSON file and populates the result fields.

2. The `result_json` field contains the full unified output from the pipeline. The app should parse this JSON to populate all the scorecard, flags, evidence, and summary sections on the detail page.

3. The composite_score, risk_tier, recommendation, confidence, and flags fields are also stored as top-level columns (denormalized from result_json) for easy filtering and sorting in the dashboard and history views.

4. Every state change should create an audit_log entry: submission, pipeline start, completion, decision, reopen.

5. The pipeline_progress field is a JSON object like: `{"step_0_intake": "completed", "step_1_sanctions": "completed", "step_2_debarment": "running", "step_3_news": "pending"}` — use this to render the progress bar on active vetting cards.

6. File uploads go to Supabase Storage in a `vetting-documents` bucket, organized by vetting_id.

## Sample Result JSON Schema

This is the structure of the result_json that the pipeline will produce and that the app needs to parse for the detail page:

```json
{
  "subject": {
    "name": "John Smith",
    "type": "individual",
    "company": "Smith Enterprises LLC",
    "country": "US",
    "city": "Washington, DC"
  },
  "gates": {
    "sanctions": {
      "status": "PASS",
      "sources_checked": ["OFAC SDN", "UN Sanctions", "EU Sanctions", "OpenSanctions", "Interpol"],
      "matches": [],
      "checked_at": "2026-03-07T10:00:00Z"
    },
    "debarment": {
      "status": "PASS",
      "sources_checked": ["SAM.gov Exclusions", "HHS OIG LEIE"],
      "matches": [],
      "checked_at": "2026-03-07T10:00:05Z"
    }
  },
  "dimensions": {
    "litigation_legal": {
      "score": 3.5,
      "weight": 0.22,
      "confidence": "HIGH",
      "summary": "2 resolved civil cases, no criminal record, no active litigation.",
      "sub_factors": {
        "criminal_cases": {"score": 0, "detail": "No criminal cases found"},
        "civil_fraud_corruption": {"score": 0, "detail": "No fraud or corruption cases"},
        "repeated_civil_litigation": {"score": 4, "detail": "2 civil suits in past 5 years, both resolved"},
        "past_resolved": {"score": 3, "detail": "Smith v. Jones (2022), settled"},
        "bankruptcy": {"score": 0, "detail": "No bankruptcy filings"}
      },
      "evidence": [
        {
          "text": "Smith was defendant in breach of contract suit, settled 2022",
          "source": "CourtListener",
          "url": "https://courtlistener.com/case/12345",
          "date": "2022-06-15",
          "temporal_weight": 0.7
        }
      ]
    },
    "media_reputation": {
      "score": 2.0,
      "weight": 0.20,
      "confidence": "HIGH",
      "summary": "Limited media coverage, no major controversies.",
      "sub_factors": {},
      "evidence": []
    },
    "international_pep": {
      "score": 0.5,
      "weight": 0.15,
      "confidence": "HIGH",
      "summary": "US-based, not a PEP, no international risk factors.",
      "sub_factors": {
        "pep_status": {"score": 0, "detail": "Not a Politically Exposed Person"},
        "country_risk": {"score": 1, "detail": "US-based, low country risk"},
        "fara_exposure": {"score": 0, "detail": "No FARA registration issues"},
        "source_reliability": {"score": 1, "detail": "English-language sources readily available"}
      },
      "evidence": []
    },
    "financial_sec": {
      "score": 1.0,
      "weight": 0.12,
      "confidence": "HIGH",
      "summary": "No SEC enforcement actions. Clean filing history.",
      "sub_factors": {},
      "evidence": []
    },
    "corporate_business": {
      "score": 2.5,
      "weight": 0.11,
      "confidence": "MEDIUM",
      "summary": "3 active companies, ownership structure mostly clear. One LLC with limited public info.",
      "sub_factors": {},
      "evidence": []
    },
    "political_lobbying": {
      "score": 1.5,
      "weight": 0.10,
      "confidence": "HIGH",
      "summary": "Standard political contributions, no lobbying red flags.",
      "sub_factors": {
        "fara_issues": {"score": 0, "detail": "No FARA registration issues"},
        "investigation_links": {"score": 0, "detail": "No contributions to subjects under investigation"},
        "watchlist_lobbying": {"score": 0, "detail": "No lobbying for watchlisted entities"},
        "pay_to_play": {"score": 3, "detail": "Some contributions to officials with regulatory oversight"}
      },
      "evidence": []
    },
    "conflict_of_interest": {
      "score": 0,
      "weight": 0.10,
      "confidence": "HIGH",
      "summary": "No conflicts with current TMG clients.",
      "sub_factors": {
        "direct_conflict": {"score": 0, "detail": "No direct conflicts"},
        "indirect_conflict": {"score": 0, "detail": "No indirect conflicts"},
        "future_conflict": {"score": 0, "detail": "No foreseeable conflicts"}
      },
      "evidence": []
    }
  },
  "scoring": {
    "raw_composite": 1.73,
    "engagement_multiplier": 1.0,
    "adjusted_composite": 1.73,
    "confidence_modifier": "none",
    "final_composite": 1.73,
    "risk_tier": "LOW",
    "recommendation": "Approve"
  },
  "flags": {
    "red": [],
    "yellow": [
      {
        "category": "litigation",
        "title": "Repeated civil litigation",
        "description": "2 civil lawsuits in past 5 years",
        "source": "CourtListener",
        "date": "2022-2024",
        "severity": "minor"
      }
    ]
  },
  "executive_summary": "## Summary\n\nJohn Smith is a US-based business executive with a clean sanctions and regulatory record...\n\n## Key Findings\n\n- **Legal**: Two resolved civil suits...\n\n## Recommendation\n\n**APPROVE** — Low overall risk...",
  "metadata": {
    "pipeline_version": "v1.0",
    "vetting_level": "standard_vet",
    "steps_completed": ["intake", "sanctions", "debarment", "news", "litigation", "corporate", "fec", "sec", "lobbying", "synthesis"],
    "started_at": "2026-03-07T10:00:00Z",
    "completed_at": "2026-03-07T10:12:30Z",
    "total_duration_seconds": 750
  }
}
```
