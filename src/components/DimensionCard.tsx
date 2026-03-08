import { useState } from "react";
import { ChevronDown, ChevronUp, ExternalLink } from "lucide-react";
import { Card } from "@/components/ui/card";
import { cn } from "@/lib/utils";
import { DIMENSION_LABELS, type DimensionResult } from "@/lib/types";
import { getScoreBarColor } from "@/lib/vetting-utils";

interface DimensionCardProps {
  dimensionKey: string;
  dimension: DimensionResult;
}

function getScoreColor(score: number) {
  if (score <= 2.5) return "text-[hsl(var(--risk-low))]";
  if (score <= 4.5) return "text-[hsl(var(--risk-moderate))]";
  if (score <= 6.5) return "text-[hsl(var(--risk-elevated))]";
  return "text-[hsl(var(--risk-high))]";
}

function getStanceBadge(score: number) {
  if (score <= 2.5) return { label: "LOW", className: "bg-white text-[hsl(var(--risk-low))] font-bold border-2 border-[hsl(var(--risk-low)/0.3)]" };
  if (score <= 4.5) return { label: "MODERATE", className: "bg-white text-[hsl(25,70%,30%)] font-bold border-2 border-[hsl(var(--risk-moderate)/0.4)]" };
  if (score <= 6.5) return { label: "ELEVATED", className: "bg-white text-[hsl(25,80%,32%)] font-bold border-2 border-[hsl(var(--risk-elevated)/0.5)]" };
  return { label: "HIGH", className: "bg-white text-[hsl(var(--risk-high))] font-bold border-2 border-[hsl(var(--risk-high)/0.4)]" };
}

export function DimensionCard({ dimensionKey, dimension }: DimensionCardProps) {
  const [expanded, setExpanded] = useState(false);
  const label = DIMENSION_LABELS[dimensionKey] || dimensionKey;
  const stance = getStanceBadge(dimension.score);
  const subFactorEntries = Object.entries(dimension.sub_factors);

  return (
    <Card className="overflow-hidden flex flex-col">
      <div className="p-4 flex-1">
        {/* Header: title + risk badge */}
        <div className="flex items-start justify-between gap-2 mb-3">
          <h4 className="text-sm font-semibold leading-tight text-foreground">{label}</h4>
          <span className={cn("text-[10px] px-2 py-0.5 rounded-md uppercase tracking-wide whitespace-nowrap", stance.className)}>
            {stance.label}
          </span>
        </div>

        {/* Score */}
        <div className="mb-2">
          <span className={cn("text-2xl font-bold", getScoreColor(dimension.score))}>{dimension.score.toFixed(1)}</span>
          <span className="text-xs text-muted-foreground"> / 10</span>
        </div>

        {/* Weight + Confidence */}
        <div className="flex items-center gap-3 mb-3">
          <span className="text-xs text-muted-foreground">Weight: {(dimension.weight * 100).toFixed(0)}%</span>
          <span className="text-xs text-muted-foreground">{dimension.confidence} confidence</span>
        </div>

        {/* Score bar */}
        <div className="w-full h-2 rounded-full bg-muted overflow-hidden mb-3">
          <div className={`h-full rounded-full transition-all ${getScoreBarColor(dimension.score)}`} style={{ width: `${(dimension.score / 10) * 100}%` }} />
        </div>

        {/* Summary */}
        <p className="text-xs text-muted-foreground leading-relaxed line-clamp-3">{dimension.summary}</p>

        {/* Sub-factors preview */}
        {subFactorEntries.length > 0 && (
          <div className="mt-3 space-y-1.5">
            {subFactorEntries.slice(0, 3).map(([sk, sf]) => (
              <div key={sk} className="flex items-center justify-between text-xs">
                <span className="text-muted-foreground capitalize truncate mr-2">{sk.replace(/_/g, " ")}</span>
                <span className="font-medium text-foreground whitespace-nowrap">{sf.score}/10</span>
              </div>
            ))}
            {subFactorEntries.length > 3 && (
              <span className="text-[10px] text-muted-foreground">+{subFactorEntries.length - 3} more</span>
            )}
          </div>
        )}
      </div>

      {/* Expand button */}
      <button
        onClick={() => setExpanded(!expanded)}
        className="w-full px-4 py-2.5 border-t text-xs font-medium text-primary hover:bg-muted/50 transition-colors flex items-center justify-center gap-1"
      >
        {expanded ? "Hide Details" : "View Evidence"}
        {expanded ? <ChevronUp className="h-3.5 w-3.5" /> : <ChevronDown className="h-3.5 w-3.5" />}
      </button>

      {/* Expanded evidence section */}
      {expanded && (
        <div className="border-t px-4 py-4 space-y-4 bg-muted/20">
          {/* Full summary */}
          <div className="rounded-lg bg-primary/5 border border-primary/10 p-3">
            <h5 className="text-xs font-semibold text-primary uppercase tracking-wider mb-1.5">Summary</h5>
            <p className="text-sm text-muted-foreground leading-relaxed">{dimension.summary}</p>
          </div>

          {/* All sub-factors */}
          {subFactorEntries.length > 0 && (
            <div>
              <h5 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-2">Sub-Factors</h5>
              <div className="rounded-lg border border-border overflow-hidden">
                <table className="w-full text-xs">
                  <thead>
                    <tr className="bg-muted">
                      <th className="text-left py-2 px-3 font-medium text-muted-foreground">Factor</th>
                      <th className="text-right py-2 px-3 font-medium text-muted-foreground w-16">Score</th>
                      <th className="text-left py-2 px-3 font-medium text-muted-foreground">Detail</th>
                    </tr>
                  </thead>
                  <tbody>
                    {subFactorEntries.map(([sk, sf]) => (
                      <tr key={sk} className="border-t border-border">
                        <td className="py-2 px-3 text-foreground capitalize whitespace-nowrap">{sk.replace(/_/g, " ")}</td>
                        <td className="py-2 px-3 text-right font-medium text-foreground">{sf.score}/10</td>
                        <td className="py-2 px-3 text-muted-foreground">{sf.detail}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* Evidence items */}
          {dimension.evidence.length > 0 && (
            <div>
              <h5 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-2">
                Evidence ({dimension.evidence.length})
              </h5>
              <div className="space-y-2">
                {dimension.evidence.map((ev, i) => (
                  <EvidenceItem key={i} evidence={ev} />
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </Card>
  );
}

function EvidenceItem({ evidence }: { evidence: DimensionResult["evidence"][0] }) {
  const [showSources, setShowSources] = useState(false);
  const hasSourceUrls = evidence.source_urls && evidence.source_urls.length > 0;
  const hasUrl = !!evidence.url;
  const hasLinks = hasSourceUrls || hasUrl;

  return (
    <div className="rounded-lg border bg-muted/30 p-3">
      <div className="flex items-start gap-2">
        <p className="text-sm text-foreground/80 leading-relaxed flex-1">
          {evidence.text.replace(/\[\d+\]/g, "")}
        </p>
        {hasLinks && (
          <button
            onClick={() => setShowSources(!showSources)}
            className={cn(
              "flex-shrink-0 p-1 rounded-md transition-colors",
              showSources ? "bg-primary/10 text-primary" : "text-muted-foreground hover:text-primary hover:bg-primary/5"
            )}
            title="View sources"
          >
            <ExternalLink className="h-3.5 w-3.5" />
          </button>
        )}
      </div>
      {showSources && hasLinks && (
        <div className="flex flex-wrap gap-2 pt-2 mt-2 border-t border-border/50">
          {hasSourceUrls && evidence.source_urls!.map((src, i) => (
            <a
              key={i}
              href={src.url}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-1 text-[10px] text-primary hover:underline bg-primary/5 px-2 py-0.5 rounded-full"
            >
              <ExternalLink className="h-2.5 w-2.5" />
              {src.title.length > 50 ? src.title.slice(0, 50) + "…" : src.title}
            </a>
          ))}
          {!hasSourceUrls && hasUrl && (
            <a
              href={evidence.url}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-1 text-[10px] text-primary hover:underline bg-primary/5 px-2 py-0.5 rounded-full"
            >
              <ExternalLink className="h-2.5 w-2.5" />
              {evidence.source || "View source"}
            </a>
          )}
        </div>
      )}
    </div>
  );
}
