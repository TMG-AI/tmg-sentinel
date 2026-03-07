import { VettingRequest, ENGAGEMENT_LABELS, VETTING_LEVEL_LABELS } from "@/lib/types";
import {
  getRiskTierColor, getStatusColor, getEngagementClass, getVettingLevelColor,
  getDecisionColor, getDecisionLabel, formatDateTime, getPipelineProgress,
} from "@/lib/vetting-utils";
import { CheckCircle, XCircle, Loader2, AlertTriangle, Skull, Clock } from "lucide-react";
import { Badge } from "@/components/ui/badge";

interface Props {
  vetting: VettingRequest;
  onClick: () => void;
}

export function VettingCard({ vetting: v, onClick }: Props) {
  const progress = getPipelineProgress(v.pipeline_progress);

  return (
    <div
      onClick={onClick}
      className="glass-card p-5 cursor-pointer hover:shadow-md transition-all duration-200 hover:border-primary/20 group"
    >
      <div className="flex flex-col lg:flex-row lg:items-center gap-4">
        {/* Left: Main info */}
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-2 flex-wrap">
            <h3 className="text-lg font-bold text-foreground group-hover:text-primary transition-colors truncate">
              {v.subject_name}
            </h3>
            <Badge variant="outline" className={v.subject_type === "individual" ? "bg-[hsl(var(--domestic-political)/0.08)] text-[hsl(var(--domestic-political))] border-[hsl(var(--domestic-political)/0.15)]" : "bg-[hsl(var(--accent)/0.08)] text-[hsl(var(--accent))] border-[hsl(var(--accent)/0.15)]"}>
              {v.subject_type === "individual" ? "Individual" : "Organization"}
            </Badge>
          </div>
          <div className="flex items-center gap-2 flex-wrap mb-2">
            <span className={`inline-flex items-center text-xs font-medium px-2 py-0.5 rounded-full ${getEngagementClass(v.engagement_type)}`}>
              {ENGAGEMENT_LABELS[v.engagement_type].split(" ").slice(0, 3).join(" ")}
            </span>
            <span className={`inline-flex items-center text-xs font-medium px-2 py-0.5 rounded-full ${getVettingLevelColor(v.vetting_level)}`}>
              {VETTING_LEVEL_LABELS[v.vetting_level].title}
            </span>
            {v.country && (
              <span className="text-xs text-muted-foreground">{v.country}{v.city ? `, ${v.city}` : ""}</span>
            )}
          </div>
          <div className="flex items-center gap-2 text-xs text-muted-foreground">
            <Clock className="w-3 h-3" />
            <span>Requested by {v.requested_by} · {formatDateTime(v.requested_at)}</span>
          </div>
        </div>

        {/* Middle: Status */}
        <div className="flex items-center gap-3 flex-shrink-0">
          {v.status === "pending" && (
            <div className="flex items-center gap-2">
              <Loader2 className="w-4 h-4 text-muted-foreground animate-spin" />
              <span className="text-sm text-muted-foreground font-medium">Pending</span>
            </div>
          )}
          {v.status === "running" && (
            <div className="flex flex-col gap-1">
              <div className="flex items-center gap-2">
                <Loader2 className="w-4 h-4 text-primary animate-spin" />
                <span className="text-sm text-primary font-medium">
                  Step {progress.current}/{progress.total}
                </span>
              </div>
              {progress.currentStep && (
                <span className="text-xs text-muted-foreground capitalize">
                  {progress.currentStep}...
                </span>
              )}
              <div className="w-32 h-1.5 rounded-full bg-muted overflow-hidden">
                <div
                  className="h-full rounded-full bg-primary transition-all"
                  style={{ width: `${(progress.current / progress.total) * 100}%` }}
                />
              </div>
            </div>
          )}
          {v.status === "gates_failed" && (
            <div className="flex items-center gap-2">
              <Skull className="w-4 h-4 text-[hsl(var(--risk-critical))]" />
              <span className="text-sm font-bold risk-badge-critical px-2 py-0.5 rounded">Gates Failed</span>
            </div>
          )}
          {v.status === "completed" && (
            <div className="flex items-center gap-2">
              <CheckCircle className="w-4 h-4 text-[hsl(var(--risk-low))]" />
              <span className="text-sm text-[hsl(var(--risk-low))] font-medium">Completed</span>
            </div>
          )}
          {v.status === "error" && (
            <div className="flex items-center gap-2">
              <XCircle className="w-4 h-4 text-destructive" />
              <span className="text-sm text-destructive font-medium">Error</span>
            </div>
          )}
        </div>

        {/* Right: Score & Decision */}
        <div className="flex items-center gap-4 flex-shrink-0">
          {v.composite_score != null && (
            <div className="text-center">
              <div className="text-2xl font-bold text-foreground">{v.composite_score.toFixed(1)}</div>
              <div className="text-xs text-muted-foreground">/ 10</div>
            </div>
          )}
          {v.risk_tier && (
            <span className={`text-xs font-bold px-2.5 py-1 rounded ${getRiskTierColor(v.risk_tier)}`}>
              {v.risk_tier}
            </span>
          )}
          {v.decision && (
            <span className={`text-xs font-medium px-2.5 py-1 rounded ${getDecisionColor(v.decision)}`}>
              {getDecisionLabel(v.decision)}
            </span>
          )}
          {v.status === "completed" && !v.decision && (
            <span className="text-xs font-medium px-2.5 py-1 rounded bg-[hsl(var(--risk-moderate)/0.12)] text-[hsl(var(--risk-moderate))] animate-pulse-slow">
              <AlertTriangle className="w-3 h-3 inline mr-1" />
              Needs Decision
            </span>
          )}
        </div>
      </div>
    </div>
  );
}
