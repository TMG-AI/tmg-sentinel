export type SubjectType = "individual" | "organization";
export type EngagementType = "fara_foreign_political" | "foreign_corporate" | "domestic_political" | "domestic_corporate";
export type VettingLevel = "quick_screen" | "standard_vet" | "deep_dive";
export type VettingStatus = "pending" | "running" | "gates_failed" | "completed" | "error";
export type RiskTier = "LOW" | "MODERATE" | "ELEVATED" | "HIGH" | "CRITICAL";
export type Decision = "approved" | "conditionally_approved" | "rejected" | "pending_review";
export type Confidence = "HIGH" | "MEDIUM" | "LOW";
export type Recommendation = "Approve" | "Conditional Approve" | "Further Review" | "Recommend Reject" | "Auto-Reject";

export interface VettingRequest {
  id: string;
  subject_name: string;
  subject_type: SubjectType;
  company_affiliation: string | null;
  country: string | null;
  city: string | null;
  brief_bio: string | null;
  referral_source: string | null;
  engagement_type: EngagementType;
  vetting_level: VettingLevel;
  requested_by: string;
  requested_at: string;
  status: VettingStatus;
  pipeline_progress: Record<string, string> | null;
  result_json: VettingResultJSON | null;
  composite_score: number | null;
  risk_tier: RiskTier | null;
  recommendation: Recommendation | null;
  confidence: Confidence | null;
  decision: Decision | null;
  decided_by: string | null;
  decided_at: string | null;
  decision_notes: string | null;
  completed_at: string | null;
  flags: { red: Flag[]; yellow: Flag[] } | null;
}

export interface Flag {
  category: string;
  title: string;
  description: string;
  source: string;
  date: string;
  severity: string;
}

export interface VettingResultJSON {
  subject: {
    name: string;
    type: string;
    company: string;
    country: string;
    city: string;
  };
  gates: {
    sanctions: GateResult;
    debarment: GateResult;
  };
  dimensions: Record<string, DimensionResult>;
  scoring: {
    raw_composite: number;
    engagement_multiplier: number;
    adjusted_composite: number;
    confidence_modifier: string;
    final_composite: number;
    risk_tier: RiskTier;
    recommendation: Recommendation;
  };
  flags: {
    red: Flag[];
    yellow: Flag[];
  };
  executive_summary: string;
  metadata: {
    pipeline_version: string;
    vetting_level: string;
    steps_completed: string[];
    started_at: string;
    completed_at: string;
    total_duration_seconds: number;
  };
}

export interface GateResult {
  status: "PASS" | "FAIL";
  sources_checked: string[];
  matches: GateMatch[];
  checked_at: string;
}

export interface GateMatch {
  list: string;
  matched_name: string;
  confidence: number;
  details: string;
}

export interface DimensionResult {
  score: number;
  weight: number;
  confidence: Confidence;
  summary: string;
  sub_factors: Record<string, { score: number; detail: string }>;
  evidence: Evidence[];
}

export interface Evidence {
  text: string;
  source: string;
  url: string;
  date: string;
  temporal_weight: number;
}

export interface AuditLogEntry {
  id: string;
  vetting_id: string;
  action: string;
  performed_by: string;
  performed_at: string;
  details: Record<string, unknown> | null;
}

export interface TMGClient {
  id: string;
  client_name: string;
  industry: string | null;
  engagement_type: string | null;
  active: boolean;
  added_at: string;
}

export const TEAM_MEMBERS = ["Liza", "Jim", "Ben", "Tara"] as const;

export const ENGAGEMENT_LABELS: Record<EngagementType, string> = {
  fara_foreign_political: "FARA-Registerable Foreign Political Work",
  foreign_corporate: "Foreign Corporate Engagement",
  domestic_political: "Domestic Political Engagement",
  domestic_corporate: "Routine Domestic Corporate",
};

export const ENGAGEMENT_MULTIPLIERS: Record<EngagementType, string | null> = {
  fara_foreign_political: "1.3x risk multiplier",
  foreign_corporate: "1.15x risk multiplier",
  domestic_political: null,
  domestic_corporate: "0.85x risk multiplier — lower risk context",
};

export const VETTING_LEVEL_LABELS: Record<VettingLevel, { title: string; description: string; time: string; bestFor: string }> = {
  quick_screen: {
    title: "Quick Screen",
    description: "Sanctions, debarment, basic news scan",
    time: "~5 minutes",
    bestFor: "Known quantities, quick checks",
  },
  standard_vet: {
    title: "Standard Vet",
    description: "Full domestic background check",
    time: "~15 minutes",
    bestFor: "Most new clients",
  },
  deep_dive: {
    title: "Deep Dive",
    description: "Comprehensive international investigation",
    time: "~30 minutes",
    bestFor: "Foreign clients, high-profile individuals",
  },
};

export const DIMENSION_LABELS: Record<string, string> = {
  litigation_legal: "Litigation / Legal Risk",
  media_reputation: "Media / Reputation Risk",
  international_pep: "International / PEP Risk",
  financial_sec: "Financial / SEC Risk",
  corporate_business: "Corporate / Business Risk",
  political_lobbying: "Political / Lobbying Risk",
  conflict_of_interest: "Conflict of Interest",
};
