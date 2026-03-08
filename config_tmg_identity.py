"""
TMG Identity Context & Reputational Contagion Analysis (RCA) Configuration
===========================================================================
This file defines TMG's political identity, brand positioning, stakeholder
ecosystem, and known vulnerabilities — used by Claude during synthesis to
evaluate whether working with a subject could harm TMG's reputation.

Based on: "TMG Vetting Pipeline: Partisan Alignment & Reputational Contagion Analysis"
(Perplexity report, March 2026)

Update this file periodically as TMG's client base, political positioning,
and stakeholder relationships evolve.
"""

# ─── TMG Identity Context ──────────────────────────────────
# This block is injected into the Claude synthesis prompt so the LLM
# understands TMG's specific reputational vulnerabilities.

TMG_IDENTITY_CONTEXT = """
TMG IDENTITY CONTEXT:
- TMG is a Democratic-aligned strategic consulting firm founded by Jim Messina,
  President Obama's 2012 campaign manager
- TMG's brand promise: "only take on fights we believe in" and "helping change
  the world" and being "on the right side of history"
- TMG advises Democratic campaigns, progressive organizations, and corporate
  clients on political strategy
- TMG's core stakeholder ecosystem: DCCC, DNC, Democratic elected officials,
  progressive donors, allied advocacy organizations
- TMG also operates Signal Interactive Media, a court-appointed legal notice
  firm, which requires perceived neutrality
- Jim Messina has been publicly criticized for advising the UK Conservative
  Party and taking corporate clients perceived as ideologically misaligned
- TMG does bipartisan corporate work (strategic advisory, M&A, crisis
  management) but its political brand is Democratic

IMPORTANT: This analysis is about TMG's reputation, not the subject's legal
compliance. A subject can be fully legal and low-risk on factual dimensions
while being extremely high-risk for TMG's brand.
""".strip()


# ─── High-Toxicity Sectors ─────────────────────────────────
# Industries that are "third rail" for Democratic consultants

HIGH_TOXICITY_SECTORS = [
    "surveillance tech used against civil liberties",
    "private prisons / immigration enforcement",
    "fossil fuels / anti-climate companies",
    "payday lending / predatory finance",
    "tobacco",
    "gun manufacturers",
    "foreign authoritarian governments",
    "anti-democratic organizations",
]

MODERATE_TOXICITY_SECTORS = [
    "defense contractors",
    "big pharma",
    "extractive industries",
    "big tech (context-dependent)",
]

LOW_TOXICITY_SECTORS = [
    "healthcare",
    "education",
    "clean energy",
    "consumer products",
    "financial services (general)",
]


# ─── RCS Risk Tiers ────────────────────────────────────────
# Separate from factual risk tiers — these are reputational

RCS_RISK_TIERS = [
    {"range": (0, 2.5), "tier": "LOW", "recommendation": "Proceed normally; engagement aligns with TMG brand"},
    {"range": (2.5, 4.5), "tier": "MODERATE", "recommendation": "Flag for leadership discussion; document rationale for proceeding"},
    {"range": (4.5, 6.5), "tier": "ELEVATED", "recommendation": "Requires Jim/Tara/partner sign-off with written justification"},
    {"range": (6.5, 8.0), "tier": "HIGH", "recommendation": "Strong presumption against engagement; requires unanimous partner approval"},
    {"range": (8.0, 10.01), "tier": "CRITICAL", "recommendation": "Recommended reject; engagement would damage TMG's core brand and relationships"},
]


def get_rcs_tier(rcs_score: float) -> dict:
    """Return the RCS risk tier dict for a given Reputational Contagion Score."""
    for tier in RCS_RISK_TIERS:
        low, high = tier["range"]
        if low <= rcs_score < high:
            return tier
    return RCS_RISK_TIERS[-1]


# ─── RCA Prompt Block ──────────────────────────────────────
# This is appended to the synthesis prompt AFTER the factual risk analysis.
# Claude scores 6 questions (0-10 each) with specific weights.

REPUTATIONAL_CONTAGION_PROMPT = """
## REPUTATIONAL CONTAGION ANALYSIS

After completing the factual risk assessment, perform a separate Reputational
Contagion Analysis. This analysis evaluates whether working with this client
could harm TMG's reputation, brand, or relationships with its core stakeholders.

{tmg_identity}

Score each of the following 6 questions on a 0-10 scale. Provide specific
evidence from the research data for each score.

### Q1: PARTISAN ALIGNMENT (Weight: 25%)
Analyze the subject's political positioning relative to TMG's Democratic
alignment. Consider:
- FEC contribution history: Which parties, candidates, and PACs has the subject
  funded? Calculate the ratio of Republican vs Democratic contributions.
- Public political statements, endorsements, and affiliations
- Think tank, PAC, and advocacy group memberships
- Whether the subject has funded or supported candidates/causes that oppose
  core Democratic priorities (ACA, climate action, voting rights, labor rights,
  reproductive rights, gun safety)
- Whether the subject has been a significant donor to MAGA/Trump-aligned causes

Scoring: 0 = clearly Democratic-aligned or neutral; 5 = primarily Republican
but not prominently anti-Democratic; 10 = actively hostile to democratic
institutions or major figure in opposing political coalition.

### Q2: STAKEHOLDER BACKLASH POTENTIAL (Weight: 20%)
If TMG's engagement with this subject became public, how would TMG's core
stakeholders react? Consider:
- Would existing TMG clients (Democratic campaigns, progressive orgs) object?
- Would DCCC/DNC leadership view this as a loyalty issue?
- Would progressive media (The Nation, Jacobin, The Intercept, Daily Kos)
  cover this negatively?
- Would TMG staff have recruitment/retention concerns?
- Could this be used in opposition research against TMG's political clients?

Scoring: 0 = no one notices; 5 = moderate media coverage, some client friction;
10 = front-page political story, existential threat to client relationships.

### Q3: NARRATIVE VULNERABILITY (Weight: 15%)
Can the engagement be framed in a damaging one-sentence headline? Write the
most damaging plausible headline and assess how easily it could be constructed.

Scoring: 0 = no damaging narrative possible; 5 = plausible but requires spin;
10 = devastating headline writes itself and would be used against TMG.

### Q4: CONFLICT WITH EXISTING CLIENTS (Weight: 15%)
Does this subject's interests, positions, or public profile create reputational
conflict with TMG's existing clients? This is about perceived association, not
just direct business conflict.

Scoring: 0 = no conflicts; 5 = moderate reputational tension; 10 = direct
reputational conflict that would cause client terminations.

### Q5: INDUSTRY/SECTOR TOXICITY (Weight: 15%)
Is the subject's industry inherently risky for a Democratic-aligned firm?
HIGH-TOXICITY sectors for TMG: surveillance tech used against civil liberties,
private prisons, immigration enforcement, fossil fuels, payday lending,
tobacco, gun manufacturers, foreign authoritarian governments, anti-democratic
organizations.
MODERATE-TOXICITY: defense contractors, big pharma, extractive industries,
big tech (context-dependent).
LOW-TOXICITY: healthcare, education, clean energy, consumer products,
financial services (general).

Scoring: 0 = uncontroversial; 5 = moderately controversial; 10 = toxic sector.

### Q6: TEMPORAL/POLITICAL CONTEXT (Weight: 10%)
Given the current political moment, is this engagement more or less risky than
it would normally be? Consider current news cycles, active legislation, ongoing
political controversies, and whether the subject is at the center of any
active public debate.

Scoring: 0 = uncontroversial timing; 5 = somewhat sensitive; 10 = worst
possible timing.

### COMPOSITE SCORE
Calculate: RCS = (Q1 * 0.25) + (Q2 * 0.20) + (Q3 * 0.15) + (Q4 * 0.15)
                + (Q5 * 0.15) + (Q6 * 0.10)

Risk tiers:
- 0-2.5: LOW — Proceed normally
- 2.5-4.5: MODERATE — Flag for leadership; document rationale
- 4.5-6.5: ELEVATED — Requires Jim/Tara/partner sign-off
- 6.5-8.0: HIGH — Strong presumption against; requires unanimous partner approval
- 8.0-10: CRITICAL — Recommended reject

### OUTPUT FORMAT
Present the Reputational Contagion Analysis as a separate section in the
vetting report, AFTER the factual risk assessment. Include:
1. Each question's score with specific evidence
2. The composite RCS score and risk tier
3. The most damaging plausible headline (from Q3)
4. A clear recommendation that accounts for BOTH the factual risk score
   AND the reputational contagion score
5. If factual risk is LOW but RCS is HIGH, explicitly flag this divergence
   and explain why the subject passes traditional screening but fails the
   reputational fit test

NEVER let a low factual risk score override a high RCS. They measure
different things. A subject can be legally clean and reputationally toxic.
""".strip()


def get_rca_prompt() -> str:
    """Return the full RCA prompt with TMG identity context filled in."""
    return REPUTATIONAL_CONTAGION_PROMPT.format(tmg_identity=TMG_IDENTITY_CONTEXT)
