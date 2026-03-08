# Lovable Prompt: Add Reputational Contagion Analysis to Dashboard

## Context
The Python vetting pipeline now produces TWO scores for each subject:

1. **Factual Risk Score** (0-10) — Traditional due diligence: sanctions, litigation, SEC, FEC, media
2. **Reputational Contagion Score (RCS)** (0-10) — TMG-specific: whether working with this client could harm TMG's brand, stakeholder relationships, or political reputation

The RCS is critical for TMG because the firm is Democratic-aligned (founded by Obama's campaign manager). A subject can be legally clean (low factual risk) but reputationally toxic (high RCS) — this is called the "Peter Thiel problem." The pipeline now detects this divergence.

The unified JSON files in `public/data/vettings/` already contain both scores. The `reputational_contagion` section is new and needs to be displayed in the dashboard.

## What to Do

### 1. Update TypeScript Types (`src/lib/types.ts`)

Add this interface and update `VettingResultJSON`:

```typescript
export type RCSTier = "LOW" | "MODERATE" | "ELEVATED" | "HIGH" | "CRITICAL";

export interface ReputationalContagion {
  q1_partisan_alignment: { score: number; weight: number; evidence: string };
  q2_stakeholder_backlash: { score: number; weight: number; evidence: string };
  q3_narrative_vulnerability: { score: number; weight: number; evidence: string; damaging_headline: string };
  q4_client_conflicts: { score: number; weight: number; evidence: string };
  q5_industry_toxicity: { score: number; weight: number; evidence: string };
  q6_temporal_context: { score: number; weight: number; evidence: string };
  composite_rcs: number;
  rcs_risk_tier: RCSTier;
  rcs_recommendation: string;
  divergence_alert: string | null;
  most_damaging_headline: string;
}
```

Add to `VettingResultJSON`:
```typescript
reputational_contagion?: ReputationalContagion;
```

Add RCS dimension labels:
```typescript
export const RCS_QUESTION_LABELS: Record<string, string> = {
  q1_partisan_alignment: "Partisan Alignment",
  q2_stakeholder_backlash: "Stakeholder Backlash",
  q3_narrative_vulnerability: "Narrative Vulnerability",
  q4_client_conflicts: "Conflict with Existing Clients",
  q5_industry_toxicity: "Industry / Sector Toxicity",
  q6_temporal_context: "Temporal / Political Context",
};
```

### 2. Update VettingDetail Page (`src/pages/VettingDetail.tsx`)

#### A. Dual Score Display in Header
Replace the single score circle in the header with TWO scores side by side:
- **Left circle**: Factual Risk Score (existing) — keep the same color coding
- **Right circle**: RCS Score — use the same circle style but with a different color scheme:
  - 0-2.5 LOW: green
  - 2.5-4.5 MODERATE: yellow/amber
  - 4.5-6.5 ELEVATED: orange
  - 6.5-8.0 HIGH: red
  - 8.0-10 CRITICAL: dark red/purple

Label them clearly: "Factual Risk" under the left circle, "Reputational Risk" under the right circle.

#### B. Divergence Alert Banner
If `reputational_contagion.divergence_alert` is not null, show a prominent warning banner between the header and gates sections:
- Use a distinctive amber/warning color (different from red flags)
- Icon: warning triangle or split-arrows icon
- Title: "DIVERGENCE ALERT"
- Body: The text from `divergence_alert`
- This is the key UX feature — it catches the "legally clean but reputationally toxic" scenario

#### C. Reputational Contagion Analysis Section
Add a new card section AFTER the "Scoring Modifiers" section and BEFORE the "Flags Inventory" section. This section should include:

1. **Section header**: "Reputational Contagion Analysis" with a shield/brand icon
2. **RCS composite score** and risk tier badge (same badge styling as factual risk tier)
3. **RCS Recommendation** text
4. **6-question scorecard** — similar to the risk dimensions display:
   - Each question on a row with label, weight percentage, score bar (0-10), and numeric score
   - Score bar colors based on the score (green for low, red for high)
   - Below each score bar: the evidence text (collapsible/expandable)
5. **Most Damaging Headline** — display in a quote-style block:
   - If present, show in italic in a bordered box with a newspaper/headline icon
   - This is the "Politico test" — the worst headline that could be written if the engagement became public

#### D. Updated Scoring Modifiers
Add an RCS row to the "Scoring Modifiers" section showing:
- RCS Score: X.XX / 10
- RCS Tier: LOW/MODERATE/ELEVATED/HIGH/CRITICAL
- RCS Recommendation text

### 3. Update Dashboard Page (`src/pages/Dashboard.tsx`)

On the dashboard cards that show each vetting:
- Show both scores: "Factual: X.X | RCS: X.X"
- If there's a divergence alert, show a small warning icon on the card
- The existing risk tier badge should stay (factual), but add a small second badge for RCS tier if it differs from factual tier

### 4. Fix Data Loading

The store currently fetches from `/data/vettings-index.json` and `/data/vettings/{file}`. The index file has been updated with real files:
- `peter_thiel.json` — Individual, domestic_political, standard_vet
- `palantir_technologies.json` — Organization, domestic_corporate, standard_vet

The `resultToVettingRequest` function in `vetting-store.ts` needs a small fix — it currently hardcodes `engagement_type` based on vetting_level. The actual engagement type should come from the intake data. For now, check if the result JSON has a metadata field or just keep the existing logic since it's close enough.

### 5. Submit Form → Email (SubmitVetting.tsx)

Change the "Confirm & Start Vetting" button behavior:
- Instead of calling an API, compose a mailto link to `shannon@themessinagroup.com`
- Subject: "New Vetting Request: {subject_name}"
- Body should include all form fields formatted nicely:
  ```
  New Vetting Request

  Subject: {name}
  Type: {individual/organization}
  Company: {company}
  Country: {country}
  City: {city}
  Bio: {bio}
  Referral: {referral}
  Engagement Type: {type}
  Vetting Level: {level}
  Requested By: {name}
  ```
- Open in a new window with `window.open(mailtoUrl)`
- Show a toast: "Email draft opened — send it to start the vetting"

### 6. Delete the old api.ts file
The `src/lib/api.ts` file references `localhost:8000` which is the deprecated FastAPI server. This file is no longer needed since we load from static JSON files. Remove it or empty it.

## Example Data Structure
Here's what the `reputational_contagion` section looks like in the JSON (from Palantir):

```json
{
  "reputational_contagion": {
    "q1_partisan_alignment": {
      "score": 3,
      "weight": 0.25,
      "evidence": "Palantir's co-founder Peter Thiel is a prominent Republican donor, but CEO Alex Karp is a Democrat and the company donates bipartisan..."
    },
    "q2_stakeholder_backlash": {
      "score": 6,
      "weight": 0.2,
      "evidence": "Palantir's ICE contracts would draw scrutiny from progressive stakeholders..."
    },
    "q3_narrative_vulnerability": {
      "score": 7,
      "weight": 0.15,
      "evidence": "...",
      "damaging_headline": "Obama Campaign Manager's Firm Now Helping Trump-Donor Thiel's Surveillance Company Target Americans"
    },
    "q4_client_conflicts": { "score": 2, "weight": 0.15, "evidence": "..." },
    "q5_industry_toxicity": { "score": 7, "weight": 0.15, "evidence": "..." },
    "q6_temporal_context": { "score": 5, "weight": 0.1, "evidence": "..." },
    "composite_rcs": 4.85,
    "rcs_risk_tier": "ELEVATED",
    "rcs_recommendation": "Requires Jim/Tara/partner sign-off with written justification",
    "divergence_alert": null,
    "most_damaging_headline": "Obama Campaign Manager's Firm Now Helping Trump-Donor Thiel's Surveillance Company Target Americans"
  }
}
```

## Important Notes
- The RCS is SEPARATE from the factual risk score — they measure different things
- A high RCS does NOT mean the subject is a criminal or legally problematic
- The RCS is about TMG's brand, reputation, and stakeholder relationships
- The "Most Damaging Headline" test is the most visceral output — display it prominently
- Peter Thiel (individual) will likely have a much higher RCS than Palantir (company) when re-run with the new module — this demonstrates why both entity types matter
