# Lovable Prompt: Complete Dashboard Update

## Context
This app is a vetting dashboard for The Messina Group (TMG), a Democratic-aligned political consulting firm (founded by Obama's campaign manager). The Python pipeline runs background checks on potential clients and produces a unified JSON file that the dashboard reads from `public/data/vettings/`.

The pipeline has been significantly upgraded with **5 major additions** to the unified JSON. This prompt covers ALL of them in one shot.

### What's New in the JSON
1. **`reputational_contagion`** — A second scoring dimension (0-10) measuring whether working with this subject could harm TMG's brand, stakeholder relationships, or political reputation
2. **`combined_decision`** — Takes the MORE CAUTIOUS of factual risk vs reputational risk. THIS is the primary recommendation to display.
3. **`key_executives`** — When vetting an organization, we identify top executives via SEC EDGAR and run mini due diligence on each (FEC donations, news, sanctions)
4. **`government_contracts`** — Federal contract awards from USAspending.gov (amounts, agencies, descriptions)
5. **Enhanced `conflict_of_interest` dimension** — Now contains structured sub-factors (`direct_conflict`, `indirect_conflict`, `future_conflict`) with specific TMG client names and sensitivity tiers embedded in the detail text

---

## 1. Update TypeScript Types (`src/lib/types.ts`)

Add these interfaces and update `VettingResultJSON`:

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

export interface CombinedDecision {
  recommendation: string; // "Approve" | "Conditional Approve" | "Further Review" | "Recommend Reject"
  combined_tier: string;  // The MORE CAUTIOUS of factual vs RCS tier
  factual_tier: string;
  factual_score: number;
  rcs_tier: string;
  rcs_score: number;
  driver: string;         // "factual_risk" | "reputational_contagion" | "both_equal"
  driver_detail: string;  // Human-readable explanation of which score drove the decision
}

export interface KeyExecutive {
  name: string;
  title: string;
  is_officer: boolean;
  is_director: boolean;
  fec_total: number;       // Total $ in FEC donations
  fec_count: number;       // Number of FEC contributions
  fec_top_recipients: { name: string; total: number; count: number }[];
  news_count: number;      // Number of news results found
  news_headlines: string[];  // Top 3 headlines
  sanctions_flag: boolean; // True if sanctions match found
}

export interface GovernmentContracts {
  total_awards: number;
  total_amount: number;     // Total $ across all awards
  agencies_count: number;
  top_agencies: { agency: string; total: number; count: number }[];
  top_awards: {
    award_amount: number;
    awarding_agency: string;
    awarding_sub_agency: string;
    description: string;
    start_date: string;
    end_date: string;
  }[];
}
```

Update `VettingResultJSON` to include:
```typescript
export interface VettingResultJSON {
  // ... existing fields ...
  reputational_contagion?: ReputationalContagion;
  combined_decision?: CombinedDecision;
  key_executives?: KeyExecutive[];
  government_contracts?: GovernmentContracts;
}
```

Add label maps:
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

---

## 2. VettingDetail Page — Header Changes

### A. Combined Decision = Primary Recommendation
The `combined_decision.recommendation` should be displayed as THE primary recommendation, NOT `scoring.recommendation`. The combined decision is the more cautious of the two scores.

Show it prominently at the top:
- **Recommendation badge**: Use `combined_decision.recommendation` (e.g., "Further Review")
- **Combined Tier badge**: Use `combined_decision.combined_tier`
- **Driver explanation**: Below the badges, show `combined_decision.driver_detail` in smaller text explaining which score drove the decision

### B. Dual Score Display
Replace the single score circle with TWO scores side by side:
- **Left circle**: Factual Risk Score (`scoring.final_composite`) — keep existing color coding
- **Right circle**: RCS Score (`reputational_contagion.composite_rcs`) — same circle style, labeled "Reputational Risk"
  - 0-2.5 LOW: green
  - 2.5-4.5 MODERATE: yellow/amber
  - 4.5-6.5 ELEVATED: orange
  - 6.5-8.0 HIGH: red
  - 8.0-10 CRITICAL: dark red/purple

### C. Divergence Alert Banner
If `reputational_contagion.divergence_alert` is not null, show a prominent warning banner:
- Amber/warning color, warning triangle icon
- Title: "DIVERGENCE ALERT"
- Body: The `divergence_alert` text
- This catches the "legally clean but reputationally toxic" scenario

---

## 3. VettingDetail Page — New Sections

### A. Reputational Contagion Analysis Section
Add after "Scoring Modifiers", before "Flags Inventory":

1. Section header: "Reputational Contagion Analysis" with shield icon
2. RCS composite score + risk tier badge
3. RCS Recommendation text
4. **6-question scorecard** — each row shows:
   - Question label (from RCS_QUESTION_LABELS)
   - Weight percentage
   - Score bar (0-10, colored green→red)
   - Evidence text (collapsible)
5. **"Most Damaging Headline"** — displayed in italic in a bordered quote block with newspaper icon. This is the worst headline that could appear if the engagement became public.

### B. Enhanced Client Conflict Display (conflict_of_interest dimension)

The `conflict_of_interest` dimension now has structured sub-factors that identify SPECIFIC TMG clients at risk. **Render this dimension differently from the other 6 dimensions** — it needs a richer breakdown.

#### Where the data lives:
- **Factual conflicts**: `dimensions.conflict_of_interest.sub_factors` — has `direct_conflict`, `indirect_conflict`, `future_conflict` each with a score (0-10) and detail text that names specific TMG clients with sensitivity tiers like "Keep Americans Covered (HIGH)" or "Google LLC (HIGH)"
- **Reputational conflicts**: `reputational_contagion.q4_client_conflicts` — has a score and evidence text covering the reputational angle

#### What to build:

**1. Sub-factor Breakdown Cards**
Render each sub-factor as its own row or card:
- Labels: "Direct Conflict", "Indirect Conflict", "Future / Emerging Conflict"
- Sub-score with a small colored indicator (red if score >= 7, amber if 4-6, green if <= 3)
- The detail text

**2. Affected TMG Client Chips**
Parse the detail text from each sub-factor for TMG client names. The pipeline writes client names with their sensitivity tier in parentheses — e.g., "Keep Americans Covered (HIGH)", "Google LLC (HIGH)", "DaVita (HIGH)".

Extract these and render as colored chips/badges:
- HIGH sensitivity = red chip
- MEDIUM sensitivity = amber/yellow chip
- LOW sensitivity = gray chip

Display chips grouped under each sub-factor card, or in a single "Affected Clients" row.

**3. Reputational Cross-Reference**
Below the factual conflict sub-factors, add a small secondary section labeled "Reputational Conflict Assessment" that pulls from `reputational_contagion.q4_client_conflicts`:
- Show the RCA score (0-10) with colored indicator
- Show the evidence text

This gives the reviewer both angles: "Here are the specific factual conflicts" AND "Here's why this is reputationally dangerous for TMG."

**4. Divergence Note**
If `conflict_of_interest.score` and `q4_client_conflicts.score` differ by more than 3 points, show a small info banner: "Factual conflict score (X) differs significantly from reputational conflict score (Y) — review both assessments."

#### Example data (Palantir):
```json
"conflict_of_interest": {
  "score": 6,
  "weight": 0.10,
  "confidence": "HIGH",
  "summary": "Palantir has active disputes in sectors where TMG has HIGH-sensitivity clients...",
  "sub_factors": {
    "direct_conflict": {
      "score": 7,
      "detail": "Palantir's ICE immigration enforcement work directly conflicts with Keep Americans Covered (HIGH) and Mayday Health (HIGH), both TMG clients focused on healthcare access and reproductive rights"
    },
    "indirect_conflict": {
      "score": 5,
      "detail": "Palantir's surveillance technology and data mining practices conflict with privacy positions held by Google LLC (HIGH) and Lyft (HIGH); Palantir's Pentagon AI contracts create tension with Suno (MEDIUM) on AI ethics"
    },
    "future_conflict": {
      "score": 4,
      "detail": "Expansion into healthcare analytics may create competitive friction with DaVita (HIGH), Guardant Health (MEDIUM), and Ascension Health Services (HIGH)"
    }
  }
}
```

### C. Key Executives Section (organizations only)
Only show this section if `key_executives` exists and has entries. Add after the main scoring sections.

1. Section header: "Key Executives" with a people/org icon
2. For each executive, show a card or row:
   - **Name** (bold) and **Title**
   - **FEC Donations**: total amount, count, top 3 recipients with amounts
   - **News**: count, top headlines (collapsible)
   - **Sanctions**: green checkmark if clear, red flag if `sanctions_flag` is true
3. Summary line at top: "X executives identified, $Y total in political donations"

### D. Government Contracts Section
Only show if `government_contracts` exists. Add near the financial/corporate sections.

1. Section header: "Government Contracts" with a government building icon
2. **Summary bar**: "X awards totaling $Y across Z agencies"
3. **Top Agencies breakdown** — horizontal bar chart or table:
   - Agency name, total amount, number of awards
   - Color-code by agency type (DoD = blue, DHS = orange, etc.) or just neutral colors
4. **Largest Awards table** (top 10):
   - Amount, Agency, Sub-agency, Description, Period
   - Sort by amount descending

---

## 4. Dashboard Page Changes

On each vetting card:
- Show `combined_decision.recommendation` as the primary badge (not `scoring.recommendation`)
- Show both scores: "Factual: X.X | RCS: X.X"
- If there's a divergence alert, show a small warning icon
- If `government_contracts` exists, show "$X federal contracts" as a small stat

---

## 5. Submit Form → Email (SubmitVetting.tsx)

Change "Confirm & Start Vetting" to compose a mailto link:
- To: `shannon@themessinagroup.com`
- Subject: "New Vetting Request: {subject_name}"
- Body: All form fields formatted clearly
- Open with `window.open(mailtoUrl)`
- Show toast: "Email draft opened — send it to start the vetting"

---

## 6. Fix Data Loading

The store fetches from `/data/vettings-index.json` and `/data/vettings/{file}`. Make sure it handles the new optional fields gracefully (they may not exist on older vettings).

Delete or empty `src/lib/api.ts` — it references `localhost:8000` which is a deprecated FastAPI server.

---

## Example JSON Structures

### Combined Decision (Peter Thiel):
```json
{
  "combined_decision": {
    "recommendation": "Recommend Reject — Engagement would damage TMG's core brand",
    "combined_tier": "CRITICAL",
    "factual_tier": "ELEVATED",
    "factual_score": 5.38,
    "rcs_tier": "CRITICAL",
    "rcs_score": 8.4,
    "driver": "reputational_contagion",
    "driver_detail": "Combined recommendation driven by Reputational Contagion Score (8.4/10 CRITICAL) which is more cautious than Factual Risk Score (5.38/10 ELEVATED)"
  }
}
```

### Key Executives (Palantir — organization):
```json
{
  "key_executives": [
    {
      "name": "Karp Alexander C.",
      "title": "Chief Executive Officer",
      "is_officer": true,
      "is_director": true,
      "fec_total": 0,
      "fec_count": 0,
      "fec_top_recipients": [],
      "news_count": 10,
      "news_headlines": ["Palantir CEO pledges to keep America skeptical on migration"],
      "sanctions_flag": false
    },
    {
      "name": "Sankar Shyam",
      "title": "COO & EVP",
      "is_officer": true,
      "is_director": false,
      "fec_total": 65825,
      "fec_count": 170,
      "fec_top_recipients": [
        {"name": "YOUNG VICTORY COMMITTEE", "total": 12000, "count": 2},
        {"name": "FRIENDS OF TODD YOUNG, INC.", "total": 7000, "count": 1}
      ],
      "news_count": 10,
      "news_headlines": ["Palantir CTO acknowledged internal concerns over ICE work"],
      "sanctions_flag": false
    }
  ]
}
```

### Government Contracts (Palantir):
```json
{
  "government_contracts": {
    "total_awards": 414,
    "total_amount": 3937199589,
    "agencies_count": 15,
    "top_agencies": [
      {"agency": "Department of Defense", "total": 2312643417, "count": 172},
      {"agency": "Department of Health and Human Services", "total": 405348502, "count": 96},
      {"agency": "Department of Homeland Security", "total": 352592360, "count": 17},
      {"agency": "Department of Justice", "total": 209253822, "count": 57}
    ],
    "top_awards": [
      {
        "award_amount": 292680689,
        "awarding_agency": "Department of Defense",
        "awarding_sub_agency": "Department of the Army",
        "description": "MAVEN SMART SYSTEM - UI/UX PROTOTYPE",
        "start_date": "2024-09-30",
        "end_date": "2026-09-29"
      }
    ]
  }
}
```

### Conflict of Interest with Client Names (Peter Thiel):
```json
{
  "conflict_of_interest": {
    "score": 8.5,
    "weight": 0.10,
    "confidence": "HIGH",
    "summary": "Severe conflicts with multiple TMG clients including TikTok, Google, and Democratic-aligned organizations due to political positions and business activities.",
    "sub_factors": {
      "direct_conflict": {
        "score": 9,
        "detail": "Direct opposition to multiple TMG clients through political funding and surveillance tech"
      },
      "indirect_conflict": {
        "score": 8,
        "detail": "Palantir's work conflicts with privacy and civil liberties positions of TMG progressive clients"
      },
      "future_conflict": {
        "score": 8,
        "detail": "Ongoing political activities likely to create future conflicts"
      }
    }
  }
}
```

---

## Visual Notes
- The conflict_of_interest section should feel MORE DETAILED than other dimensions since client conflicts are one of the most actionable findings in a vetting
- Client chips should be immediately scannable — the reviewer needs to see at a glance which of TMG's actual clients are at risk
- Sub-factor cards can be collapsible if space is tight
- Match existing card/panel styling throughout

## Important Notes
- `combined_decision` is THE primary recommendation — always display it over `scoring.recommendation`
- RCS is SEPARATE from factual risk — they measure different things
- A high RCS does NOT mean the subject is a criminal — it means working with them could hurt TMG
- `key_executives` only exists for organizations — check before rendering
- `government_contracts` only exists when contracts were found — check before rendering
- FEC data for executives captures individual itemized contributions only — large PAC-level donations (e.g., $1M to MAGA Inc) show up in news, not FEC
- The "Most Damaging Headline" is the most visceral output — display it prominently
- All new fields are optional (older vettings won't have them) — use optional chaining
- Client names with sensitivity tiers are embedded in sub_factor detail text as "ClientName (TIER)" — parse with a regex like `/([^,;]+?)\s*\((HIGH|MEDIUM|LOW)\)/g`
