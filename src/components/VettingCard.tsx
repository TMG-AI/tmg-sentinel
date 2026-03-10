import { VettingRequest, ENGAGEMENT_LABELS, VETTING_LEVEL_LABELS } from "@/lib/types";
import {
  getRiskTierColor, getEngagementClass, getVettingLevelColor,
  getDecisionColor, getDecisionLabel, formatDateTime, getPipelineProgress,
} from "@/lib/vetting-utils";
import { CheckCircle, XCircle, Loader2, AlertTriangle, Skull, Clock, ChevronRight, ShieldAlert, Landmark } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { isInternationalSubject, getCountryFlag } from "@/lib/international-utils";

interface Props {
  vetting: VettingRequest;
  onClick: () => void;
}

function formatUSD(amount: number): string {
  if (amount >= 1e9) return `$${(amount / 1e9).toFixed(2)}B`;
  if (amount >= 1e6) return `$${(amount / 1e6).toFixed(1)}M`;
  if (amount >= 1e3) return `$${(amount / 1e3).toFixed(0)}K`;
  return `$${amount.toLocaleString()}`;
}

export function VettingCard({ vetting: v, onClick }: Props) {
  const progress = getPipelineProgress(v.pipeline_progress);
  const rca = v.result_json?.reputational_contagion;
  const combined = v.result_json?.combined_decision;
  const contracts = v.result_json?.government_contracts;
  const hasDivergence = !!rca?.divergence_alert;

  // Primary recommendation from combined_decision
  const primaryTier = combined?.combined_tier || v.risk_tier;

  return (
    <div
      onClick={onClick}
      className="glass-card p-5 cursor-pointer group border-l-4 transition-all duration-200"
      style={{
        borderLeftColor: v.status === "gates_failed" ? "hsl(var(--risk-critical))" 
          : v.status === "completed" && primaryTier === "HIGH" ? "hsl(var(--risk-high))"
          : v.status === "completed" && primaryTier === "CRITICAL" ? "hsl(var(--risk-critical))"
          : v.status === "completed" && primaryTier === "ELEVATED" ? "hsl(var(--risk-elevated))"
          : v.status === "completed" && primaryTier === "MODERATE" ? "hsl(var(--risk-moderate))"
          : v.status === "completed" ? "hsl(var(--risk-low))"
          : v.status === "running" ? "hsl(var(--primary))"
          : v.status === "error" ? "hsl(var(--destructive))"
          : "hsl(var(--border))"
      }}
    >
      <div className="flex flex-col lg:flex-row lg:items-center gap-4">
        {/* Left: Main info */}
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2.5 mb-2 flex-wrap">
            <h3 className="text-lg font-bold text-foreground group-hover:text-primary transition-colors truncate">
              {v.subject_name}
            </h3>
            <Badge variant="outline" className={v.subject_type === "individual" ? "bg-[hsl(var(--domestic-political)/0.08)] text-[hsl(var(--domestic-political))] border-[hsl(var(--domestic-political)/0.15)]" : "bg-[hsl(var(--accent)/0.08)] text-[hsl(var(--accent))] border-[hsl(var(--accent)/0.15)]"}>
              {v.subject_type === "individual" ? "Individual" : "Organization"}
            </Badge>
            {hasDivergence && (
              <span className="inline-flex items-center gap-1 text-xs font-bold px-2 py-0.5 rounded-full bg-white text-[hsl(0,72%,38%)] border-2 border-[hsl(var(--risk-high)/0.50)]">
                <ShieldAlert className="w-3 h-3" /> Divergence
              </span>
            )}
          </div>

          {/* Combined decision recommendation */}
          {combined && (
            <div className="flex items-center gap-2 mb-2 flex-wrap">
              <span className={`text-xs font-bold px-2 py-0.5 rounded ${getRiskTierColor(combined.combined_tier as any)}`}>
                {combined.combined_tier}
              </span>
              <span className="text-xs font-medium text-foreground truncate max-w-xs">
                {combined.recommendation.split("—")[0].trim().replace("Conditional Approve", "Conditional Approval")}
              </span>
            </div>
          )}

          <div className="flex items-center gap-2 flex-wrap mb-2">
            <span className={`inline-flex items-center text-xs px-2.5 py-1 rounded-full ${getEngagementClass(v.engagement_type)}`}>
              {ENGAGEMENT_LABELS[v.engagement_type].split(" ").slice(0, 3).join(" ")}
            </span>
            <span className={`inline-flex items-center text-xs px-2.5 py-1 rounded-full ${getVettingLevelColor(v.vetting_level)}`}>
              {VETTING_LEVEL_LABELS[v.vetting_level].title}
            </span>
            {contracts && (
              <span className="inline-flex items-center gap-1 text-xs text-muted-foreground px-2 py-1 rounded-full bg-muted">
                <Landmark className="w-3 h-3" />
                {formatUSD(contracts.total_amount)} federal contracts
              </span>
            )}
            {v.country && (
              <span className="text-xs text-muted-foreground">{v.country}{v.city ? `, ${v.city}` : ""}</span>
            )}
          </div>
          <div className="flex items-center gap-2 text-xs text-muted-foreground">
            <Clock className="w-3 h-3" />
            <span>Requested by <span className="font-medium text-foreground">{v.requested_by}</span> · {formatDateTime(v.requested_at)}</span>
          </div>
        </div>

        {/* Middle: Status */}
        <div className="flex items-center gap-3 flex-shrink-0">
          {v.status === "pending" && (
            <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-muted">
              <Loader2 className="w-4 h-4 text-muted-foreground animate-spin" />
              <span className="text-sm text-muted-foreground font-medium">Pending</span>
            </div>
          )}
          {v.status === "running" && (
            <div className="flex flex-col gap-1.5">
              <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-primary/8">
                <Loader2 className="w-4 h-4 text-primary animate-spin" />
                <span className="text-sm text-primary font-semibold">
                  Step {progress.current}/{progress.total}
                </span>
              </div>
              {progress.currentStep && (
                <span className="text-xs text-muted-foreground capitalize pl-1">
                  {progress.currentStep}...
                </span>
              )}
              <div className="w-36 h-2 rounded-full bg-primary/10 overflow-hidden">
                <div
                  className="h-full rounded-full bg-primary transition-all"
                  style={{ width: `${(progress.current / progress.total) * 100}%` }}
                />
              </div>
            </div>
          )}
          {v.status === "gates_failed" && (
            <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg risk-badge-critical">
              <Skull className="w-4 h-4" />
              <span className="text-sm font-bold">Gates Failed</span>
            </div>
          )}
          {v.status === "completed" && (
            <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-[hsl(var(--risk-low)/0.08)]">
              <CheckCircle className="w-4 h-4 text-[hsl(var(--risk-low))]" />
              <span className="text-sm text-[hsl(var(--risk-low))] font-semibold">Completed</span>
            </div>
          )}
          {v.status === "error" && (
            <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-destructive/8">
              <XCircle className="w-4 h-4 text-destructive" />
              <span className="text-sm text-destructive font-semibold">Error</span>
            </div>
          )}
        </div>

        {/* Right: Score & Decision */}
        <div className="flex items-center gap-4 flex-shrink-0">
          {v.composite_score != null && (
            <div className="text-center px-3">
              <div className="text-lg font-bold text-foreground">{v.composite_score.toFixed(1)}</div>
              <div className="text-[10px] text-muted-foreground uppercase tracking-wider font-medium">Factual</div>
            </div>
          )}
          {rca && (
            <div className="text-center px-3 border-l border-border">
              <div className="text-lg font-bold text-foreground">{rca.composite_rcs.toFixed(1)}</div>
              <div className="text-[10px] text-muted-foreground uppercase tracking-wider font-medium">RCS</div>
            </div>
          )}
          {primaryTier && (
            <span className={`text-xs px-3 py-1.5 rounded-lg ${getRiskTierColor(primaryTier as any)}`}>
              {primaryTier}
            </span>
          )}
          {v.decision && (
            <span className={`text-xs font-medium px-3 py-1.5 rounded-lg ${getDecisionColor(v.decision)}`}>
              {getDecisionLabel(v.decision)}
            </span>
          )}
          {v.status === "completed" && !v.decision && (
            <span className="text-xs font-bold px-3 py-1.5 rounded-lg bg-white text-[hsl(0,72%,38%)] border-2 border-[hsl(var(--risk-high)/0.50)]">
              <AlertTriangle className="w-3 h-3 inline mr-1" />
              Needs Decision
            </span>
          )}
          <ChevronRight className="w-4 h-4 text-muted-foreground group-hover:text-primary transition-colors" />
        </div>
      </div>
    </div>
  );
}
