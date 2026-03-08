import { useState } from "react";
import { ChevronDown, ChevronUp } from "lucide-react";
import { Card } from "@/components/ui/card";
import { cn } from "@/lib/utils";
import { getScoreBarColor } from "@/lib/vetting-utils";

interface RCSCardProps {
  label: string;
  score: number;
  weight: number;
  evidence: string;
  damagingHeadline?: string;
}

function getScoreColor(score: number) {
  if (score <= 2.5) return "text-[hsl(var(--risk-low))]";
  if (score <= 4.5) return "text-[hsl(var(--risk-moderate))]";
  if (score <= 6.5) return "text-[hsl(var(--risk-elevated))]";
  return "text-[hsl(var(--risk-high))]";
}

function getRiskBadge(score: number) {
  if (score <= 2.5) return { label: "LOW", className: "risk-badge-low" };
  if (score <= 4.5) return { label: "MODERATE", className: "risk-badge-moderate" };
  if (score <= 6.5) return { label: "ELEVATED", className: "risk-badge-elevated" };
  return { label: "HIGH", className: "risk-badge-high" };
}

export function RCSCard({ label, score, weight, evidence, damagingHeadline }: RCSCardProps) {
  const [expanded, setExpanded] = useState(false);
  const badge = getRiskBadge(score);

  return (
    <Card className="overflow-hidden">
      {/* Top row: title, score, weight, badge, expand toggle */}
      <div className="p-4">
        <div className="flex items-center justify-between gap-3 mb-2">
          <div className="flex items-center gap-3 flex-1 min-w-0">
            <h4 className="text-sm font-semibold text-foreground truncate">{label}</h4>
            <span className={cn("text-[10px] px-2 py-0.5 rounded-md uppercase tracking-wide whitespace-nowrap", badge.className)}>
              {badge.label}
            </span>
          </div>
          <div className="flex items-center gap-2 flex-shrink-0">
            <span className={cn("text-xl font-bold", getScoreColor(score))}>{score.toFixed(1)}</span>
            <span className="text-xs text-muted-foreground">/ 10</span>
            <span className="text-xs text-muted-foreground ml-1">({(weight * 100).toFixed(0)}%)</span>
          </div>
        </div>

        {/* Score bar */}
        <div className="w-full h-1.5 rounded-full bg-muted overflow-hidden mb-2">
          <div className={`h-full rounded-full transition-all ${getScoreBarColor(score)}`} style={{ width: `${(score / 10) * 100}%` }} />
        </div>

        {/* Evidence preview */}
        <p className="text-xs text-muted-foreground leading-relaxed line-clamp-2">{evidence}</p>
      </div>

      {/* Expand button */}
      <button
        onClick={() => setExpanded(!expanded)}
        className="w-full px-4 py-2 border-t text-xs font-medium text-primary hover:bg-muted/50 transition-colors flex items-center justify-center gap-1"
      >
        {expanded ? "Hide Details" : "View Evidence"}
        {expanded ? <ChevronUp className="h-3.5 w-3.5" /> : <ChevronDown className="h-3.5 w-3.5" />}
      </button>

      {/* Expanded evidence */}
      {expanded && (
        <div className="border-t px-4 py-4 space-y-3 bg-muted/20">
          <div className="rounded-lg bg-primary/5 border border-primary/10 p-3">
            <h5 className="text-xs font-semibold text-primary uppercase tracking-wider mb-1.5">Evidence</h5>
            <p className="text-sm text-muted-foreground leading-relaxed">{evidence}</p>
          </div>

          {damagingHeadline && (
            <div className="rounded-lg border-l-4 border-[hsl(var(--risk-elevated))] bg-[hsl(var(--risk-elevated)/0.04)] p-3">
              <h5 className="text-xs font-bold text-[hsl(var(--risk-elevated))] uppercase tracking-wider mb-1.5">Potential Headline</h5>
              <p className="text-sm italic text-foreground font-medium">"{damagingHeadline}"</p>
            </div>
          )}
        </div>
      )}
    </Card>
  );
}
