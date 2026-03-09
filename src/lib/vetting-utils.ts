import { RiskTier, VettingStatus, EngagementType, VettingLevel, Confidence, Decision } from "./types";

export function getRiskTierColor(tier: RiskTier | null): string {
  switch (tier) {
    case "LOW": return "risk-badge-low";
    case "MODERATE": return "risk-badge-moderate";
    case "ELEVATED": return "risk-badge-elevated";
    case "HIGH": return "risk-badge-high";
    case "CRITICAL": return "risk-badge-critical";
    default: return "bg-muted text-muted-foreground";
  }
}

export function getStatusColor(status: VettingStatus): string {
  switch (status) {
    case "pending": return "bg-muted text-muted-foreground";
    case "running": return "bg-primary/10 text-primary";
    case "gates_failed": return "risk-badge-critical";
    case "completed": return "bg-[hsl(var(--risk-low)/0.10)] text-[hsl(var(--risk-low))]";
    case "error": return "bg-destructive/10 text-destructive";
  }
}

export function getEngagementClass(type: EngagementType): string {
  switch (type) {
    case "fara_foreign_political": return "engagement-fara";
    case "foreign_corporate": return "engagement-foreign-corp";
    case "government_affairs": return "engagement-gov-affairs";
    case "corporate_political_advisory": return "engagement-corp-advisory";
    case "campaign_electoral": return "engagement-campaign";
    case "domestic_political": return "engagement-domestic-political";
    case "domestic_corporate": return "engagement-domestic-corp";
  }
}

export function getVettingLevelColor(level: VettingLevel): string {
  switch (level) {
    case "quick_screen": return "bg-[hsl(var(--risk-low)/0.10)] text-[hsl(var(--risk-low))]";
    case "standard_vet": return "bg-[hsl(var(--domestic-political)/0.10)] text-[hsl(var(--domestic-political))]";
    case "deep_dive": return "bg-[hsl(var(--accent)/0.10)] text-[hsl(var(--accent))]";
  }
}

export function getDecisionColor(decision: Decision | null): string {
  switch (decision) {
    case "approved": return "bg-[hsl(var(--risk-low)/0.10)] text-[hsl(var(--risk-low))]";
    case "conditionally_approved": return "bg-[hsl(var(--risk-moderate)/0.12)] text-[hsl(var(--risk-moderate))]";
    case "rejected": return "bg-destructive/10 text-destructive";
    case "pending_review": return "bg-primary/10 text-primary";
    default: return "";
  }
}

export function getDecisionLabel(decision: Decision | null): string {
  switch (decision) {
    case "approved": return "Approved";
    case "conditionally_approved": return "Conditionally Approved";
    case "rejected": return "Rejected";
    case "pending_review": return "Pending Review";
    default: return "";
  }
}

export function getScoreBarColor(score: number): string {
  if (score <= 2.5) return "bg-risk-low";
  if (score <= 4.5) return "bg-risk-moderate";
  if (score <= 6.5) return "bg-risk-elevated";
  return "bg-risk-high";
}

export function getConfidenceColor(c: Confidence | null): string {
  switch (c) {
    case "HIGH": return "bg-[hsl(var(--risk-low)/0.10)] text-[hsl(var(--risk-low))]";
    case "MEDIUM": return "bg-[hsl(var(--risk-moderate)/0.12)] text-[hsl(var(--risk-moderate))]";
    case "LOW": return "bg-destructive/10 text-destructive";
    default: return "";
  }
}

export function formatDate(iso: string | null): string {
  if (!iso) return "—";
  return new Date(iso).toLocaleDateString("en-US", { timeZone: "America/New_York", month: "short", day: "numeric", year: "numeric" });
}

export function formatDateTime(iso: string | null): string {
  if (!iso) return "—";
  return new Date(iso).toLocaleString("en-US", { timeZone: "America/New_York", month: "short", day: "numeric", year: "numeric", hour: "numeric", minute: "2-digit", timeZoneName: "short" });
}

export function getPipelineProgress(progress: Record<string, string> | null): { current: number; total: number; currentStep: string } {
  if (!progress) return { current: 0, total: 0, currentStep: "" };
  const entries = Object.entries(progress);
  const total = entries.length;
  const completed = entries.filter(([, v]) => v === "completed").length;
  const running = entries.find(([, v]) => v === "running");
  const stepName = running ? running[0].replace(/^step_\d+_/, "").replace(/_/g, " ") : "";
  return { current: completed, total, currentStep: stepName };
}
