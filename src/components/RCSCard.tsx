import { useState } from "react";
import { ChevronDown, ChevronUp, ExternalLink } from "lucide-react";
import { Card } from "@/components/ui/card";
import { cn } from "@/lib/utils";
import { getScoreBarColor } from "@/lib/vetting-utils";

type SourceItem = { id: number; url: string; title: string; score: number };

interface RCSCardProps {
  label: string;
  score: number;
  weight: number;
  evidence: string;
  damagingHeadline?: string;
  sources?: SourceItem[];
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

function extractDomain(url: string): string {
  try {
    return new URL(url).hostname.replace(/^www\./, '').split('.')[0];
  } catch { return ''; }
}

function findSourcesInText(text: string, sources?: SourceItem[]): SourceItem[] {
  if (!sources || !text) return [];
  const lower = text.toLowerCase();
  const matches: SourceItem[] = [];
  for (const s of sources) {
    if (matches.length >= 5) break;
    if (matches.includes(s)) continue;
    const domain = extractDomain(s.url);
    if (domain && domain.length > 2) {
      const stripped = domain.replace(/^the/, '');
      if (lower.includes(domain) || (stripped.length > 2 && lower.includes(stripped))) {
        matches.push(s);
        continue;
      }
    }
    // Check key title words
    const titleWords = s.title.toLowerCase().split(/[\s\-:]+/).filter(w => w.length > 5);
    if (titleWords.some(w => lower.includes(w))) {
      matches.push(s);
    }
  }
  return matches;
}

export function RCSCard({ label, score, weight, evidence, damagingHeadline, sources }: RCSCardProps) {
  const [expanded, setExpanded] = useState(false);
  const badge = getRiskBadge(score);
  const cleanEvidence = evidence.replace(/\s*\[\d+\]\s*/g, ' ').replace(/\s*\[\w+\]\s*$/g, '').trim();
  const matchedSources = findSourcesInText(evidence, sources);

  return (
    <Card className="overflow-hidden">
      <div className="p-4">
        <div className="flex items-center justify-between gap-3 mb-2">
          <div className="flex items-center gap-3 flex-1 min-w-0">
            <h4 className="font-semibold text-foreground">{label}</h4>
            <span className={cn("text-[11px] px-2 py-0.5 rounded-md uppercase tracking-wide whitespace-nowrap", badge.className)}>
              {badge.label}
            </span>
          </div>
          <div className="flex items-center gap-2 flex-shrink-0">
            <span className={cn("text-xl font-bold", getScoreColor(score))}>{score.toFixed(1)}</span>
            <span className="text-sm text-muted-foreground">/ 10</span>
            <span className="text-sm text-muted-foreground ml-1">({(weight * 100).toFixed(0)}%)</span>
          </div>
        </div>

        <div className="w-full h-1.5 rounded-full bg-muted overflow-hidden mb-2">
          <div className={`h-full rounded-full transition-all ${getScoreBarColor(score)}`} style={{ width: `${(score / 10) * 100}%` }} />
        </div>

        <p className="text-sm text-muted-foreground leading-relaxed">{cleanEvidence}</p>
      </div>

      <button
        onClick={() => setExpanded(!expanded)}
        className="w-full px-4 py-2.5 border-t text-sm font-medium text-primary hover:bg-muted/50 transition-colors flex items-center justify-center gap-1"
      >
        {expanded ? "Hide Details" : "View Evidence"}
        {expanded ? <ChevronUp className="h-3.5 w-3.5" /> : <ChevronDown className="h-3.5 w-3.5" />}
      </button>

      {expanded && (
        <div className="border-t px-4 py-4 space-y-3 bg-muted/20">
          {matchedSources.length > 0 && (
            <div className="rounded-lg bg-primary/5 border border-primary/10 p-3">
              <h5 className="text-xs font-semibold text-primary uppercase tracking-wider mb-1.5">Sources</h5>
              <div className="flex flex-wrap gap-2">
                {matchedSources.map((src, i) => (
                  <a
                    key={i}
                    href={src.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-flex items-center gap-1 text-xs text-primary hover:underline bg-primary/5 px-2.5 py-1 rounded-full"
                  >
                    <ExternalLink className="h-3 w-3" />
                    {src.title.length > 50 ? src.title.slice(0, 50) + "…" : src.title}
                  </a>
                ))}
              </div>
            </div>
          )}

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
