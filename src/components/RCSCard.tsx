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
  if (score <= 2.5) return { label: "LOW", className: "bg-white text-[hsl(var(--risk-low))] font-bold border-2 border-[hsl(var(--risk-low)/0.3)]" };
  if (score <= 4.5) return { label: "MODERATE", className: "bg-white text-[hsl(25,70%,30%)] font-bold border-2 border-[hsl(var(--risk-moderate)/0.4)]" };
  if (score <= 6.5) return { label: "ELEVATED", className: "bg-white text-[hsl(25,80%,32%)] font-bold border-2 border-[hsl(var(--risk-elevated)/0.5)]" };
  return { label: "HIGH", className: "bg-white text-[hsl(var(--risk-high))] font-bold border-2 border-[hsl(var(--risk-high)/0.4)]" };
}

export function RCSCard({ label, score, weight, evidence, damagingHeadline }: RCSCardProps) {
  const [expanded, setExpanded] = useState(false);
  const badge = getRiskBadge(score);

  return (
    <Card className="overflow-hidden flex flex-col">
      <div className="p-4 flex-1">
        {/* Header */}
        <div className="flex items-start justify-between gap-2 mb-3">
          <h4 className="text-sm font-semibold leading-tight text-foreground">{label}</h4>
          <span className={cn("text-[10px] px-2 py-0.5 rounded-md uppercase tracking-wide whitespace-nowrap", badge.className)}>
            {badge.label}
          </span>
        </div>

        {/* Score */}
        <div className="mb-2">
          <span className={cn("text-2xl font-bold", getScoreColor(score))}>{score.toFixed(1)}</span>
          <span className="text-xs text-muted-foreground"> / 10</span>
        </div>

        {/* Weight */}
        <p className="text-xs text-muted-foreground mb-3">Weight: {(weight * 100).toFixed(0)}%</p>

        {/* Score bar */}
        <div className="w-full h-2 rounded-full bg-muted overflow-hidden mb-3">
          <div className={`h-full rounded-full transition-all ${getScoreBarColor(score)}`} style={{ width: `${(score / 10) * 100}%` }} />
        </div>

        {/* Evidence preview */}
        <p className="text-xs text-muted-foreground leading-relaxed line-clamp-3">{evidence}</p>
      </div>

      {/* Expand button */}
      <button
        onClick={() => setExpanded(!expanded)}
        className="w-full px-4 py-2.5 border-t text-xs font-medium text-primary hover:bg-muted/50 transition-colors flex items-center justify-center gap-1"
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
