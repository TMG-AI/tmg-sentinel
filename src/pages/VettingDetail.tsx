import { useParams, useNavigate } from "react-router-dom";
import { useVettingStore } from "@/lib/vetting-store";
import { ENGAGEMENT_LABELS, VETTING_LEVEL_LABELS, RCS_QUESTION_LABELS, Decision, ReputationalContagion, Flag as FlagType, DIMENSION_LABELS, KeyExecutive } from "@/lib/types";
import { DimensionCard } from "@/components/DimensionCard";
import { RCSCard } from "@/components/RCSCard";
import {
  getRiskTierColor, getEngagementClass, getVettingLevelColor,
  getDecisionColor, getDecisionLabel,
  formatDateTime, getScoreBarColor,
} from "@/lib/vetting-utils";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter, DialogDescription } from "@/components/ui/dialog";
import {
  CheckCircle, XCircle, ArrowLeft, AlertTriangle, ExternalLink, Upload,
  Shield, Skull, FileText, Clock, Newspaper, ChevronDown, ShieldAlert,
  BarChart3, Flag, Link2, Users, Landmark, ChevronUp, DollarSign, Globe, Info,
} from "lucide-react";
import { isInternationalSubject, getCountryFlag } from "@/lib/international-utils";
import { useState, useRef, useEffect } from "react";
import { useToast } from "@/hooks/use-toast";

type SourceItem = { id: number; url: string; title: string; score: number };

function extractDomain(url: string): string {
  try {
    return new URL(url).hostname.replace(/^www\./, '').split('.')[0];
  } catch { return ''; }
}

function findFlagSources(sourceStr: string, sources?: SourceItem[]): SourceItem[] {
  if (!sources || !sourceStr) return [];
  const matches: SourceItem[] = [];
  const idPattern = /\[(\d+)\]/g;
  let m;
  while ((m = idPattern.exec(sourceStr)) !== null) {
    const id = parseInt(m[1]);
    const src = sources.find(s => s.id === id);
    if (src && !matches.includes(src)) matches.push(src);
  }
  if (matches.length === 0) {
    const cleaned = sourceStr.replace(/\[\d+\]/g, '').replace(/[,\/]/g, ' ');
    const parts = cleaned.split(/\s+/).map(s => s.trim().toLowerCase()).filter(p => p.length >= 3 && !['multiple', 'bio', 'the'].includes(p));
    for (const part of parts) {
      for (const s of sources) {
        if (matches.includes(s)) continue;
        const domain = extractDomain(s.url);
        if (domain.includes(part) || part.includes(domain) ||
            s.title.toLowerCase().includes(part) || s.url.toLowerCase().includes(part)) {
          matches.push(s);
        }
      }
    }
  }
  return matches.slice(0, 5);
}

function findSourcesForEvidence(evidence: string, sources?: SourceItem[]): SourceItem[] {
  if (!sources || !evidence) return [];
  const lower = evidence.toLowerCase();
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
    const titleWords = s.title.toLowerCase().split(/[\s\-:]+/).filter(w => w.length > 5);
    if (titleWords.some(w => lower.includes(w))) {
      matches.push(s);
    }
  }
  return matches;
}

function FlagCard({ flag, sources, variant }: { flag: FlagType; sources?: SourceItem[]; variant: "red" | "yellow" }) {
  const cleanDesc = flag.description.replace(/\s*\[\d+\]\s*/g, '').replace(/\s*\[\w+\]\s*$/g, '').trim();
  const cleanSource = flag.source.replace(/\s*\[\d+\]\s*/g, '').replace(/[,\s]+$/, '').trim();
  const matchedSources = findFlagSources(flag.source, sources);
  const borderClass = variant === "red" ? "border-l-destructive" : "border-l-[hsl(var(--risk-moderate))]";
  const iconClass = variant === "red" ? "text-destructive" : "text-[hsl(var(--risk-moderate))]";

  return (
    <div className={`glass-card p-4 border-l-4 ${borderClass}`}>
      <div className="flex items-center gap-2 mb-1.5">
        <AlertTriangle className={`w-4 h-4 ${iconClass}`} />
        <span className="font-semibold text-foreground">{flag.title}</span>
      </div>
      <p className="text-muted-foreground leading-relaxed">{cleanDesc}</p>
      <div className="flex flex-wrap items-center gap-2 mt-3">
        {matchedSources.length > 0 ? (
          matchedSources.map((src, i) => (
            <a key={i} href={src.url} target="_blank" rel="noopener noreferrer"
              className="inline-flex items-center gap-1 text-xs text-primary hover:underline bg-primary/5 px-2.5 py-1 rounded-full">
              <ExternalLink className="h-3 w-3" />
              {src.title.length > 50 ? src.title.slice(0, 50) + "…" : src.title}
            </a>
          ))
        ) : (
          <span className="text-xs text-muted-foreground">{cleanSource}</span>
        )}
        <span className="text-xs text-muted-foreground">· {flag.date}</span>
      </div>
    </div>
  );
}

function getRcsColor(score: number): string {
  if (score <= 2.5) return "hsl(var(--risk-low))";
  if (score <= 4.5) return "hsl(var(--risk-moderate))";
  if (score <= 6.5) return "hsl(var(--risk-elevated))";
  if (score <= 8.0) return "hsl(var(--risk-high))";
  return "hsl(var(--risk-critical, var(--risk-high)))";
}

function formatUSD(amount: number): string {
  if (amount >= 1e9) return `$${(amount / 1e9).toFixed(2)}B`;
  if (amount >= 1e6) return `$${(amount / 1e6).toFixed(1)}M`;
  if (amount >= 1e3) return `$${(amount / 1e3).toFixed(0)}K`;
  return `$${amount.toLocaleString()}`;
}

/** Parse "ClientName (TIER)" patterns from text */
function parseClientChips(text: string): { name: string; tier: string }[] {
  const regex = /([^,;]+?)\s*\((HIGH|MEDIUM|LOW)\)/g;
  const chips: { name: string; tier: string }[] = [];
  let m;
  while ((m = regex.exec(text)) !== null) {
    chips.push({ name: m[1].trim(), tier: m[2] });
  }
  return chips;
}

function getSubScoreColor(score: number): string {
  if (score >= 7) return "text-[hsl(var(--risk-high))]";
  if (score >= 4) return "text-[hsl(var(--risk-elevated))]";
  return "text-[hsl(var(--risk-low))]";
}

function getSubScoreBg(score: number): string {
  if (score >= 7) return "bg-[hsl(var(--risk-high)/0.08)]";
  if (score >= 4) return "bg-[hsl(var(--risk-elevated)/0.08)]";
  return "bg-[hsl(var(--risk-low)/0.08)]";
}

type TabId = "summary" | "gates" | "scorecard" | "rca" | "conflicts" | "executives" | "contracts" | "flags" | "sources" | "decision";

interface TabDef {
  id: TabId;
  label: string;
  icon: React.ReactNode;
  show: boolean;
}

export default function VettingDetail() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { vettings, makeDecision, reopenVetting, uploadResults, loadVettings } = useVettingStore();
  useEffect(() => { loadVettings(); }, [loadVettings]);
  const { toast } = useToast();

  const v = vettings.find((x) => x.id === id);
  const [decisionNotes, setDecisionNotes] = useState("");
  const [pendingDecision, setPendingDecision] = useState<Decision | null>(null);
  const [showDecisionDialog, setShowDecisionDialog] = useState(false);
  const [activeTab, setActiveTab] = useState<TabId>("summary");
  const fileInputRef = useRef<HTMLInputElement>(null);

  if (!v) {
    return (
      <div className="page-container text-center py-20">
        <p className="text-muted-foreground">Vetting not found.</p>
        <Button variant="outline" onClick={() => navigate("/")} className="mt-4">Back to Dashboard</Button>
      </div>
    );
  }

  const result = v.result_json;
  const gates = result?.gates;
  const dimensions = result?.dimensions;
  const scoring = result?.scoring;
  const flags = result?.flags || v.flags;
  const rca = result?.reputational_contagion;
  const combined = result?.combined_decision;
  const executives = result?.key_executives;
  const contracts = result?.government_contracts;
  const gatesFailed = gates?.sanctions.status === "FAIL" || gates?.debarment.status === "FAIL";
  const conflictDim = dimensions?.conflict_of_interest;

  const handleDecisionClick = (d: Decision) => {
    setPendingDecision(d);
    setShowDecisionDialog(true);
  };

  const confirmDecision = () => {
    if (!pendingDecision) return;
    makeDecision(v.id, pendingDecision, "Admin", decisionNotes);
    setShowDecisionDialog(false);
    setDecisionNotes("");
    setPendingDecision(null);
    toast({ title: "Decision Recorded", description: `${getDecisionLabel(pendingDecision)} decision has been recorded.` });
  };

  const handleReopen = () => {
    reopenVetting(v.id, "Admin");
    toast({ title: "Vetting Reopened", description: "Decision has been cleared." });
  };

  const handleUploadJSON = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = (ev) => {
      try {
        const json = JSON.parse(ev.target?.result as string);
        uploadResults(v.id, json);
        toast({ title: "Results Uploaded", description: "Vetting results have been processed." });
      } catch {
        toast({ title: "Error", description: "Invalid JSON file.", variant: "destructive" });
      }
    };
    reader.readAsText(file);
  };

  const dimensionOrder = dimensions
    ? Object.entries(dimensions).filter(([key]) => key !== "conflict_of_interest").sort(([, a], [, b]) => b.weight - a.weight)
    : [];

  const hasFlags = flags && (flags.red.length > 0 || flags.yellow.length > 0);

  // Primary recommendation comes from combined_decision if available
  const normalizeRecommendation = (r: string | null | undefined) => r?.replace("Conditional Approve", "Conditional Approval") ?? null;
  const primaryRecommendation = normalizeRecommendation(combined?.recommendation || v.recommendation);
  const primaryTier = combined?.combined_tier || v.risk_tier;

  const tabs: TabDef[] = ([
    { id: "summary" as const, label: "Summary", icon: <FileText className="w-3.5 h-3.5" />, show: !!result?.executive_summary },
    { id: "gates" as const, label: "Gates", icon: <Shield className="w-3.5 h-3.5" />, show: !!gates },
    { id: "scorecard" as const, label: "Scorecard", icon: <BarChart3 className="w-3.5 h-3.5" />, show: !!dimensions && !gatesFailed },
    { id: "rca" as const, label: "Reputational Risk", icon: <ShieldAlert className="w-3.5 h-3.5" />, show: !!rca && !gatesFailed },
    { id: "conflicts" as const, label: "Client Conflicts", icon: <AlertTriangle className="w-3.5 h-3.5" />, show: !!conflictDim && !gatesFailed },
    { id: "executives" as const, label: `Executives${executives?.length ? ` (${executives.length})` : ""}`, icon: <Users className="w-3.5 h-3.5" />, show: !!(executives && executives.length > 0) },
    { id: "contracts" as const, label: "Gov Contracts", icon: <Landmark className="w-3.5 h-3.5" />, show: !!contracts },
    { id: "flags" as const, label: `Flags${hasFlags ? ` (${(flags?.red.length || 0) + (flags?.yellow.length || 0)})` : ""}`, icon: <Flag className="w-3.5 h-3.5" />, show: !!flags },
    { id: "sources" as const, label: `Sources${result?.sources ? ` (${result.sources.length})` : ""}`, icon: <Link2 className="w-3.5 h-3.5" />, show: !!(result?.sources && result.sources.length > 0) },
    { id: "decision" as const, label: "Decision", icon: <CheckCircle className="w-3.5 h-3.5" />, show: v.status === "completed" || v.status === "gates_failed" },
  ] satisfies TabDef[]).filter((t) => t.show);

  return (
    <div className="page-container max-w-5xl">
      {/* Back */}
      <button onClick={() => navigate(-1)} className="flex items-center gap-1.5 text-sm text-muted-foreground hover:text-foreground mb-4 transition-colors">
        <ArrowLeft className="w-4 h-4" /> Back
      </button>

      {/* Header */}
      <div className="glass-card p-6 mb-0 rounded-b-none border-b-0">
        <div className="flex flex-col lg:flex-row lg:items-start gap-6">
          <div className="flex-1">
            <h1 className="text-3xl font-bold text-foreground mb-3">{v.subject_name}</h1>
            <div className="flex items-center gap-2 flex-wrap mb-3">
              <Badge variant="outline" className={v.subject_type === "individual" ? "bg-[hsl(var(--domestic-political)/0.08)] text-[hsl(var(--domestic-political))] border-[hsl(var(--domestic-political)/0.15)]" : "bg-[hsl(var(--accent)/0.08)] text-[hsl(var(--accent))] border-[hsl(var(--accent)/0.15)]"}>
                {v.subject_type === "individual" ? "Individual" : "Organization"}
              </Badge>
              <span className={`text-xs font-medium px-2 py-0.5 rounded-full ${getEngagementClass(v.engagement_type)}`}>
                {ENGAGEMENT_LABELS[v.engagement_type]}
              </span>
              <span className={`text-xs font-medium px-2 py-0.5 rounded-full ${getVettingLevelColor(v.vetting_level)}`}>
                {VETTING_LEVEL_LABELS[v.vetting_level].title}
              </span>
              {v.country && <span className="text-xs text-muted-foreground">{v.country}{v.city ? `, ${v.city}` : ""}</span>}
            </div>

            {/* Combined Decision — Primary Recommendation */}
            {combined && (
              <div className="flex items-center gap-2 flex-wrap mb-3">
                <span className={`text-sm font-bold px-3 py-1 rounded ${getRiskTierColor(combined.combined_tier as any)}`}>
                  {combined.combined_tier}
                </span>
                <span className="text-sm font-semibold text-foreground">{normalizeRecommendation(combined.recommendation)}</span>
              </div>
            )}
            {/* driver_detail removed — duplicative with summary */}

            <div className="flex items-center gap-2 text-sm text-muted-foreground">
              <Clock className="w-3.5 h-3.5" />
              <span>Requested by {v.requested_by} on {formatDateTime(v.requested_at)}</span>
            </div>
          </div>

          {/* Scores — Combined first when available */}
          <div className="flex gap-6 flex-shrink-0">
            {v.composite_score != null && (
              <div className="text-center">
                <ScoreCircle score={v.composite_score} color={v.composite_score <= 2.5 ? "hsl(var(--risk-low))" : v.composite_score <= 4.5 ? "hsl(var(--risk-moderate))" : v.composite_score <= 6.5 ? "hsl(var(--risk-elevated))" : "hsl(var(--risk-high))"} />
                <p className="text-xs font-semibold text-muted-foreground mt-1">Factual</p>
                {v.risk_tier && (
                  <span className={`inline-block text-xs font-bold px-3 py-1 rounded mt-1 ${getRiskTierColor(v.risk_tier)}`}>
                    {v.risk_tier}
                  </span>
                )}
              </div>
            )}
            {rca && (
              <div className="text-center">
                <ScoreCircle score={rca.composite_rcs} color={getRcsColor(rca.composite_rcs)} />
                <p className="text-xs font-semibold text-muted-foreground mt-1">Reputational</p>
                <span className={`inline-block text-xs font-bold px-3 py-1 rounded mt-1 ${getRiskTierColor(rca.rcs_risk_tier)}`}>
                  {rca.rcs_risk_tier}
                </span>
              </div>
            )}
          </div>
        </div>

        {/* Upload JSON for testing */}
        {(v.status === "pending" || v.status === "running") && (
          <div className="mt-4 pt-4 border-t">
            <input ref={fileInputRef} type="file" accept=".json" onChange={handleUploadJSON} className="hidden" />
            <Button variant="outline" size="sm" onClick={() => fileInputRef.current?.click()}>
              <Upload className="w-3.5 h-3.5 mr-2" /> Upload Results JSON
            </Button>
          </div>
        )}
      </div>

      {/* Divergence Alert — always visible */}
      {rca?.divergence_alert && (
        <div className="p-4 border-x border-border bg-[hsl(var(--risk-elevated)/0.10)] border-t border-t-[hsl(var(--risk-elevated)/0.3)]">
          <div className="flex items-start gap-3">
            <ShieldAlert className="w-5 h-5 text-[hsl(var(--risk-elevated))] flex-shrink-0 mt-0.5" />
            <div>
              <span className="text-xs font-bold text-[hsl(var(--risk-elevated))] tracking-wide">⚠ Divergence Alert</span>
              <p className="text-sm text-foreground mt-0.5 font-medium">{rca.divergence_alert}</p>
            </div>
          </div>
        </div>
      )}

      {/* Tab Navigation */}
      <div className="sticky top-0 z-20 bg-card border border-border rounded-b-xl mb-6 overflow-x-auto">
        <div className="flex items-center gap-1 px-3 py-2">
          {tabs.map((t) => (
            <button
              key={t.id}
              onClick={() => setActiveTab(t.id)}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm font-medium whitespace-nowrap transition-all ${
              activeTab === t.id
                  ? "bg-foreground text-background"
                  : "text-muted-foreground hover:text-foreground hover:bg-muted"
              }`}
            >
              {t.icon}
              {t.label}
            </button>
          ))}
        </div>
      </div>

      {/* ===== SUMMARY TAB ===== */}
      {activeTab === "summary" && result?.executive_summary && (
        <div className="glass-card p-6 mb-6">
          <h2 className="section-title flex items-center gap-2"><FileText className="w-4 h-4" /> Executive Summary</h2>
          <div className="max-w-none text-foreground space-y-2">
            {result.executive_summary.split("\n").filter(line => line.trim() !== "").map((line, i) => {
              const clean = (s: string) => s.replace(/\s*\[\d+\]\s*/g, ' ').replace(/\*\*(.*?)\*\*/g, "$1").trim();
              const renderText = (text: string) => {
                if (text.includes("REJECT —") || text.includes("REJECT —")) {
                  const parts = text.split(/(REJECT\s*[—\u2014])/);
                  return parts.map((part, j) => /REJECT\s*[—\u2014]/.test(part) ? <span key={j} className="font-black text-[hsl(var(--risk-critical))]">{part}</span> : part);
                }
                return text;
              };
              if (line.startsWith("## ")) return <h3 key={i} className="text-base font-bold mt-5 mb-2 text-foreground">{renderText(clean(line.replace("## ", "")))}</h3>;
              if (line.startsWith("**") && line.endsWith("**")) return <p key={i} className="font-bold text-foreground mt-4 mb-1.5">{renderText(clean(line))}</p>;
              if (line.startsWith("- ")) return <li key={i} className="text-muted-foreground ml-4 mb-1.5 leading-relaxed">{renderText(clean(line.replace("- ", "")))}</li>;
              return <p key={i} className="text-muted-foreground mb-2 leading-relaxed">{renderText(clean(line))}</p>;
            })}
          </div>
        </div>
      )}

      {/* ===== GATES TAB ===== */}
      {activeTab === "gates" && gates && (
        <div className="mb-6">
          {gatesFailed && (
            <div className="risk-badge-critical p-4 rounded-xl mb-4 flex items-center gap-3">
              <Skull className="w-6 h-6 flex-shrink-0" />
              <div>
                <p className="font-bold text-sm">Auto-Rejected — {gates.sanctions.status === "FAIL" ? "Sanctions" : "Debarment"} match found</p>
                <p className="text-xs opacity-90 mt-0.5">Legal counsel required to override.</p>
              </div>
            </div>
          )}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <GateCard title="Sanctions / Watchlist Gate" gate={gates.sanctions} />
            <GateCard title="Government Exclusion Gate" gate={gates.debarment} />
          </div>
        </div>
      )}

      {/* ===== SCORECARD TAB ===== */}
      {activeTab === "scorecard" && dimensions && !gatesFailed && (
        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4 mb-6">
          {dimensionOrder.map(([key, dim]) => (
            <DimensionCard key={key} dimensionKey={key} dimension={dim} />
          ))}
        </div>
      )}

      {/* ===== RCA TAB ===== */}
      {activeTab === "rca" && rca && !gatesFailed && (
        <div className="mb-6">
          <div className="glass-card p-4 mb-4 flex items-center justify-between">
            <div className="flex items-center gap-2">
              <ShieldAlert className="w-4 h-4 text-foreground" />
              <span className="text-sm font-semibold text-foreground">Reputational Contagion Score</span>
            </div>
            <div className="flex items-center gap-2">
              <span className="text-lg font-bold text-foreground">{rca.composite_rcs.toFixed(2)}</span>
              <span className="text-xs text-muted-foreground">/ 10</span>
              <span className={`text-xs font-bold px-3 py-1 rounded ${getRiskTierColor(rca.rcs_risk_tier)}`}>
                {rca.rcs_risk_tier}
              </span>
            </div>
          </div>

          {rca.rcs_recommendation && (
            <p className="text-sm text-muted-foreground mb-4 px-1">{rca.rcs_recommendation}</p>
          )}

          <div className="space-y-4 mb-4">
            {(Object.keys(RCS_QUESTION_LABELS) as Array<keyof typeof RCS_QUESTION_LABELS>).map((qKey) => {
              const q = rca[qKey as keyof ReputationalContagion] as { score: number; weight: number; evidence: string; damaging_headline?: string } | undefined;
              if (!q || typeof q !== 'object' || !('score' in q)) return null;
              return (
                <RCSCard
                  key={qKey}
                  label={RCS_QUESTION_LABELS[qKey]}
                  weight={q.weight}
                  score={q.score}
                  evidence={q.evidence}
                  damagingHeadline={qKey === "q3_narrative_vulnerability" ? q.damaging_headline : undefined}
                  sources={result?.sources}
                />
              );
            })}
          </div>

        </div>
      )}

      {/* ===== CLIENT CONFLICTS TAB ===== */}
      {activeTab === "conflicts" && !gatesFailed && (
        <div className="mb-6 space-y-4">
          {/* Primary: RCS conflict assessment (richer data) */}
          {rca?.q4_client_conflicts && rca.q4_client_conflicts.score > 0 && (
            <div className={`glass-card p-5 border-l-4 ${rca.q4_client_conflicts.score >= 7 ? "border-l-[hsl(var(--risk-high))]" : rca.q4_client_conflicts.score >= 4 ? "border-l-[hsl(var(--risk-elevated))]" : "border-l-[hsl(var(--risk-low))]"}`}>
              <div className="flex items-center justify-between mb-3">
                <h2 className="section-title mb-0 flex items-center gap-2"><AlertTriangle className="w-4 h-4" /> Client Conflict Analysis</h2>
                <div className="flex items-center gap-2">
                  <span className={`text-xl font-bold ${getSubScoreColor(rca.q4_client_conflicts.score)}`}>{rca.q4_client_conflicts.score.toFixed(1)}</span>
                  <span className="text-xs text-muted-foreground">/ 10</span>
                  <span className="text-xs text-muted-foreground ml-1">({(rca.q4_client_conflicts.weight * 100).toFixed(0)}% weight)</span>
                </div>
              </div>
              <div className="w-full h-1.5 rounded-full bg-muted overflow-hidden mb-3">
                <div className={`h-full rounded-full transition-all ${getScoreBarColor(rca.q4_client_conflicts.score)}`} style={{ width: `${(rca.q4_client_conflicts.score / 10) * 100}%` }} />
              </div>
              {/* Split evidence into bullet points on semicolons */}
              <ul className="space-y-2">
                {rca.q4_client_conflicts.evidence.split(';').map((point, i) => {
                  const trimmed = point.replace(/\s*\[\d+\]\s*/g, ' ').trim();
                  if (!trimmed) return null;
                  return (
                    <li key={i} className="flex items-start gap-2 text-sm text-muted-foreground leading-relaxed">
                      <span className="mt-1.5 w-1.5 h-1.5 rounded-full bg-muted-foreground/40 flex-shrink-0" />
                      {trimmed.charAt(0).toUpperCase() + trimmed.slice(1)}
                    </li>
                  );
                })}
              </ul>
            </div>
          )}

          {/* Factual sub-factors (only show if they have non-zero scores) */}
          {conflictDim && Object.entries(conflictDim.sub_factors).some(([, sf]) => sf.score > 0) && (
            <>
              <h3 className="text-xs font-semibold text-muted-foreground tracking-wider">Factual Conflict Sub-Factors</h3>
              {Object.entries(conflictDim.sub_factors).filter(([, sf]) => sf.score > 0).map(([key, sf]) => {
                const label = key === "direct_conflict" ? "Direct Conflict" : key === "indirect_conflict" ? "Indirect Conflict" : "Future / Emerging Conflict";
                const chips = parseClientChips(sf.detail);
                return (
                  <div key={key} className={`glass-card p-4 border-l-4 ${sf.score >= 7 ? "border-l-[hsl(var(--risk-high))]" : sf.score >= 4 ? "border-l-[hsl(var(--risk-elevated))]" : "border-l-[hsl(var(--risk-low))]"}`}>
                    <div className="flex items-center justify-between mb-2">
                      <span className="font-semibold text-foreground">{label}</span>
                      <span className={`text-sm font-bold px-2 py-0.5 rounded ${getSubScoreBg(sf.score)} ${getSubScoreColor(sf.score)}`}>
                        {sf.score}/10
                      </span>
                    </div>
                    <p className="text-sm text-muted-foreground leading-relaxed mb-3">{sf.detail}</p>
                    {chips.length > 0 && (
                      <div className="flex flex-wrap gap-1.5">
                        {chips.map((c, i) => (
                          <span key={i} className={`text-xs font-medium px-2 py-0.5 rounded-full ${
                            c.tier === "HIGH" ? "bg-[hsl(var(--risk-high)/0.10)] text-[hsl(var(--risk-high))] border border-[hsl(var(--risk-high)/0.25)]"
                            : c.tier === "MEDIUM" ? "bg-[hsl(var(--risk-moderate)/0.10)] text-[hsl(var(--risk-moderate))] border border-[hsl(var(--risk-moderate)/0.25)]"
                            : "bg-muted text-muted-foreground border border-border"
                          }`}>
                            {c.name} ({c.tier})
                          </span>
                        ))}
                      </div>
                    )}
                  </div>
                );
              })}
            </>
          )}

          {/* Evidence items */}
          {conflictDim && conflictDim.evidence.length > 0 && conflictDim.evidence.some(ev => ev.text && !ev.text.toLowerCase().includes('no conflicts found')) && (
            <div className="glass-card p-5">
              <h3 className="text-xs font-semibold text-muted-foreground tracking-wider mb-3">Supporting Evidence ({conflictDim.evidence.filter(ev => !ev.text.toLowerCase().includes('no conflicts found')).length})</h3>
              <div className="space-y-2">
                {conflictDim.evidence.filter(ev => !ev.text.toLowerCase().includes('no conflicts found')).map((ev, i) => {
                  const hasSourceUrls = ev.source_urls && ev.source_urls.length > 0;
                  const hasUrl = !!ev.url;
                  return (
                    <div key={i} className="rounded-lg border bg-muted/30 p-3">
                      <p className="text-sm text-foreground/80 leading-relaxed">
                        {ev.text.replace(/\s*\[\d+\]\s*/g, ' ').replace(/\s*\[\w+\]\s*$/g, '').trim()}
                      </p>
                      {(hasSourceUrls || hasUrl) && (
                        <div className="flex flex-wrap gap-2 pt-2 mt-2 border-t border-border/50">
                          {hasSourceUrls && ev.source_urls!.map((src, j) => (
                            <a key={j} href={src.url} target="_blank" rel="noopener noreferrer"
                              className="inline-flex items-center gap-1 text-[10px] text-primary hover:underline bg-primary/5 px-2 py-0.5 rounded-full">
                              <ExternalLink className="h-2.5 w-2.5" />
                              {src.title.length > 50 ? src.title.slice(0, 50) + "…" : src.title}
                            </a>
                          ))}
                          {!hasSourceUrls && hasUrl && (
                            <a href={ev.url} target="_blank" rel="noopener noreferrer"
                              className="inline-flex items-center gap-1 text-[10px] text-primary hover:underline bg-primary/5 px-2 py-0.5 rounded-full">
                              <ExternalLink className="h-2.5 w-2.5" />
                              {ev.source || "View source"}
                            </a>
                          )}
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {/* Divergence note */}
          {conflictDim && rca?.q4_client_conflicts && conflictDim.score !== rca.q4_client_conflicts.score && Math.abs(conflictDim.score - rca.q4_client_conflicts.score) > 3 && (
            <div className="p-3 rounded-lg bg-[hsl(var(--risk-moderate)/0.06)] border border-[hsl(var(--risk-moderate)/0.15)] flex items-start gap-2">
              <AlertTriangle className="w-4 h-4 text-[hsl(var(--risk-moderate))] flex-shrink-0 mt-0.5" />
              <p className="text-xs text-muted-foreground">
                Factual conflict score ({conflictDim.score}) differs significantly from reputational conflict score ({rca.q4_client_conflicts.score}) — review both assessments.
              </p>
            </div>
          )}

          {/* Empty state */}
          {(!rca?.q4_client_conflicts || rca.q4_client_conflicts.score === 0) && (!conflictDim || conflictDim.score === 0) && (
            <div className="glass-card p-5 text-center">
              <p className="text-sm text-muted-foreground">No client conflicts identified.</p>
            </div>
          )}
        </div>
      )}

      {/* ===== EXECUTIVES TAB ===== */}
      {activeTab === "executives" && executives && executives.length > 0 && (
        <div className="mb-6 space-y-4">
          <div className="glass-card p-4">
            <div className="flex items-center gap-2 mb-1">
              <Users className="w-4 h-4 text-foreground" />
              <span className="text-sm font-semibold text-foreground">
                {executives.length} executives identified
              </span>
            </div>
            <p className="text-xs text-muted-foreground">
              {formatUSD(executives.reduce((sum, e) => sum + e.fec_total, 0))} total in political donations
            </p>
          </div>

          {executives.map((exec, i) => (
            <ExecutiveCard key={i} exec={exec} />
          ))}
        </div>
      )}

      {/* ===== GOVERNMENT CONTRACTS TAB ===== */}
      {activeTab === "contracts" && contracts && (
        <div className="mb-6 space-y-4">
          {/* Summary */}
          <div className="glass-card p-5">
            <div className="flex items-center gap-2 mb-2">
              <Landmark className="w-4 h-4 text-foreground" />
              <h2 className="text-sm font-semibold text-foreground">Government Contracts</h2>
            </div>
            <div className="flex items-center gap-4 flex-wrap">
              <div className="text-center px-3">
                <p className="text-2xl font-bold text-foreground">{contracts.total_awards}</p>
                <p className="text-xs text-muted-foreground">Awards</p>
              </div>
              <div className="text-center px-3 border-l border-border">
                <p className="text-2xl font-bold text-foreground">{formatUSD(contracts.total_amount)}</p>
                <p className="text-xs text-muted-foreground">Total Value</p>
              </div>
              <div className="text-center px-3 border-l border-border">
                <p className="text-2xl font-bold text-foreground">{contracts.agencies_count}</p>
                <p className="text-xs text-muted-foreground">Agencies</p>
              </div>
            </div>
          </div>

          {/* Top Agencies */}
          {contracts.top_agencies.length > 0 && (
            <div className="glass-card p-5">
              <h3 className="text-xs font-semibold tracking-wider text-muted-foreground mb-3">Top Agencies</h3>
              <div className="space-y-2">
                {contracts.top_agencies.slice(0, 10).map((a, i) => {
                  const pct = (a.total / contracts.total_amount) * 100;
                  return (
                    <div key={i}>
                      <div className="flex items-center justify-between text-sm mb-1">
                        <span className="text-foreground font-medium truncate mr-2">{a.agency}</span>
                        <span className="text-muted-foreground whitespace-nowrap">{formatUSD(a.total)} · {a.count} awards</span>
                      </div>
                      <div className="w-full h-2 rounded-full bg-muted overflow-hidden">
                        <div className="h-full rounded-full bg-primary transition-all" style={{ width: `${pct}%` }} />
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {/* Top Awards Table */}
          {contracts.top_awards.length > 0 && (
            <div className="glass-card p-5">
              <h3 className="text-xs font-semibold tracking-wider text-muted-foreground mb-3">Largest Awards</h3>
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-border">
                      <th className="text-left py-2 pr-3 font-medium text-muted-foreground">Amount</th>
                      <th className="text-left py-2 pr-3 font-medium text-muted-foreground">Agency</th>
                      <th className="text-left py-2 pr-3 font-medium text-muted-foreground">Description</th>
                      <th className="text-left py-2 font-medium text-muted-foreground">Period</th>
                    </tr>
                  </thead>
                  <tbody>
                    {contracts.top_awards.slice(0, 10).map((award, i) => (
                      <tr key={i} className="border-b border-border/50">
                        <td className="py-2 pr-3 font-semibold text-foreground whitespace-nowrap">{formatUSD(award.award_amount)}</td>
                        <td className="py-2 pr-3 text-muted-foreground">
                          <div className="text-foreground text-xs">{award.awarding_sub_agency || award.awarding_agency}</div>
                        </td>
                        <td className="py-2 pr-3 text-muted-foreground text-xs max-w-xs">
                          {award.description.length > 120 ? award.description.slice(0, 120) + "…" : award.description}
                        </td>
                        <td className="py-2 text-xs text-muted-foreground whitespace-nowrap">
                          {award.start_date} — {award.end_date}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </div>
      )}

      {/* ===== FLAGS TAB ===== */}
      {activeTab === "flags" && (
        <div className="mb-6">
          {hasFlags ? (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                 <h3 className="text-xs font-semibold text-destructive mb-2">Red Flags ({flags!.red.length})</h3>
                {flags!.red.length === 0 ? (
                  <p className="text-xs text-muted-foreground p-3 bg-muted rounded-xl">No red flags</p>
                ) : (
                  <div className="space-y-2">
                    {flags!.red.map((f, i) => (
                      <FlagCard key={i} flag={f} sources={result?.sources} variant="red" />
                    ))}
                  </div>
                )}
              </div>
              <div>
                <h3 className="text-xs font-semibold text-[hsl(var(--risk-moderate))] mb-2">Yellow Flags ({flags!.yellow.length})</h3>
                {flags!.yellow.length === 0 ? (
                  <p className="text-xs text-muted-foreground p-3 bg-muted rounded-xl">No yellow flags</p>
                ) : (
                  <div className="space-y-2">
                    {flags!.yellow.map((f, i) => (
                      <FlagCard key={i} flag={f} sources={result?.sources} variant="yellow" />
                    ))}
                  </div>
                )}
              </div>
            </div>
          ) : (
            <div className="glass-card p-4 flex items-center gap-3 bg-[hsl(var(--risk-low)/0.04)] border-[hsl(var(--risk-low)/0.15)]">
              <CheckCircle className="w-5 h-5 text-[hsl(var(--risk-low))] flex-shrink-0" />
              <span className="text-sm text-foreground font-medium">No flags identified</span>
            </div>
          )}
        </div>
      )}

      {/* ===== SOURCES TAB ===== */}
      {activeTab === "sources" && result?.sources && result.sources.length > 0 && (
        <div className="glass-card p-6 mb-6">
          <h2 className="section-title flex items-center gap-2"><Link2 className="w-4 h-4" /> All Research Sources ({result.sources.length})</h2>
          <p className="text-xs text-muted-foreground mb-4">Complete list of sources researched by the pipeline.</p>
          <div className="space-y-1">
            {[...result.sources].sort((a, b) => b.score - a.score).map((src) => (
              <div key={src.id} className="flex items-center gap-3 p-2 rounded-lg hover:bg-muted transition-colors text-sm">
                <a href={src.url} target="_blank" rel="noopener noreferrer" className="text-foreground hover:text-primary hover:underline truncate flex-1">
                  {src.title}
                </a>
                <ExternalLink className="w-3 h-3 text-muted-foreground flex-shrink-0" />
              </div>
            ))}
          </div>
        </div>
      )}

      {/* ===== DECISION TAB ===== */}
      {activeTab === "decision" && (v.status === "completed" || v.status === "gates_failed") && (
        <div className="glass-card p-6 mb-6">
          <h2 className="section-title flex items-center gap-2"><Shield className="w-4 h-4" /> Decision</h2>
          {v.decision ? (
            <div>
              <div className="flex items-center gap-3 mb-3">
                <span className={`text-sm font-bold px-3 py-1.5 rounded ${getDecisionColor(v.decision)}`}>
                  {getDecisionLabel(v.decision)}
                </span>
                <span className="text-sm text-muted-foreground">
                  by {v.decided_by} on {formatDateTime(v.decided_at)}
                </span>
              </div>
              {v.decision_notes && (
                <div className="p-3 rounded-lg bg-muted text-sm text-muted-foreground mb-4">{v.decision_notes}</div>
              )}
              <Button variant="outline" size="sm" onClick={handleReopen}>Reopen Vetting</Button>
            </div>
          ) : (
            <div>
              <p className="text-sm text-muted-foreground mb-4">
                {primaryRecommendation && <>Pipeline recommends: <strong>{primaryRecommendation}</strong></>}
              </p>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                <Button onClick={() => handleDecisionClick("approved")} className="bg-[hsl(var(--risk-low))] hover:bg-[hsl(var(--risk-low)/0.85)] text-white font-bold shadow-sm">
                  ✓ Approve
                </Button>
                <Button onClick={() => handleDecisionClick("conditionally_approved")} className="bg-[hsl(var(--risk-elevated))] hover:bg-[hsl(var(--risk-elevated)/0.85)] text-white font-bold shadow-sm">
                  Conditional
                </Button>
                <Button onClick={() => handleDecisionClick("rejected")} className="bg-[hsl(var(--risk-high))] hover:bg-[hsl(var(--risk-high)/0.85)] text-white font-bold shadow-sm">
                  ✕ Reject
                </Button>
                <Button onClick={() => handleDecisionClick("pending_review")} className="bg-[hsl(var(--gov-affairs))] hover:bg-[hsl(var(--gov-affairs)/0.85)] text-white font-bold shadow-sm">
                  Further Review
                </Button>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Decision Dialog */}
      <Dialog open={showDecisionDialog} onOpenChange={setShowDecisionDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Record Decision: {pendingDecision ? getDecisionLabel(pendingDecision) : ""}</DialogTitle>
            <DialogDescription>Provide rationale for this decision</DialogDescription>
          </DialogHeader>
          <div>
            <Textarea
              value={decisionNotes}
              onChange={(e) => setDecisionNotes(e.target.value)}
              placeholder="Explain the rationale..."
              rows={4}
              className="bg-background"
            />
            {(pendingDecision === "conditionally_approved" || pendingDecision === "rejected") && !decisionNotes.trim() && (
              <p className="text-xs text-destructive mt-1">Notes are required for this decision type.</p>
            )}
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowDecisionDialog(false)}>Cancel</Button>
            <Button
              onClick={confirmDecision}
              disabled={(pendingDecision === "conditionally_approved" || pendingDecision === "rejected") && !decisionNotes.trim()}
            >
              Confirm Decision
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}

/* ===== Executive Card Component ===== */
function ExecutiveCard({ exec }: { exec: KeyExecutive }) {
  const [expanded, setExpanded] = useState(false);
  const isFalsePositive = exec.sanctions_flag && exec.sanctions_datasets && exec.sanctions_datasets.every(
    ds => ["wikidata", "wd_categories", "wd_peps", "us_congress", "everypolitician", "ann_pep_positions"].includes(ds)
  );
  return (
    <div className="glass-card p-4">
      <div className="flex items-start justify-between gap-3">
        <div className="flex-1">
          <div className="flex items-center gap-2 flex-wrap mb-1">
             <span className="font-semibold text-foreground">{exec.name}</span>
            {exec.sanctions_flag && !isFalsePositive && (
              <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-[hsl(var(--risk-high)/0.10)] text-[hsl(var(--risk-high))] border border-[hsl(var(--risk-high)/0.25)]">
                ⚠ Sanctions Match
              </span>
            )}
            {exec.sanctions_flag && isFalsePositive && (
              <span className="text-[10px] font-medium px-2 py-0.5 rounded-full bg-muted text-muted-foreground border border-border">
                PEP / Public Figure
              </span>
            )}
            {!exec.sanctions_flag && (
              <CheckCircle className="w-3.5 h-3.5 text-[hsl(var(--risk-low))]" />
            )}
          </div>
          {/* Sanctions explanation */}
          {exec.sanctions_flag && exec.sanctions_datasets && exec.sanctions_datasets.length > 0 && (
            <p className="text-[11px] text-muted-foreground mb-1">
              {isFalsePositive
                ? `Matched in public-figure databases: ${exec.sanctions_datasets.join(", ")}. Not an actual sanctions listing.`
                : `Matched in: ${exec.sanctions_datasets.join(", ")}`}
            </p>
          )}
          <p className="text-xs text-muted-foreground mb-2">
            {exec.title && exec.title !== "See Remarks" ? exec.title : ""}
            {exec.is_officer && exec.is_director ? (exec.title && exec.title !== "See Remarks" ? " · " : "") + "Officer & Director" : exec.is_officer ? (exec.title && exec.title !== "See Remarks" ? " · " : "") + "Officer" : exec.is_director ? (exec.title && exec.title !== "See Remarks" ? " · " : "") + "Director" : ""}
          </p>
          <div className="flex items-center gap-4 text-xs text-muted-foreground">
            <span className="flex items-center gap-1">
              <DollarSign className="w-3 h-3" />
              {formatUSD(exec.fec_total)} ({exec.fec_count} contributions)
            </span>
            <span className="flex items-center gap-1">
              <Newspaper className="w-3 h-3" />
              {exec.news_count} news hits
            </span>
          </div>
          {/* Top headline always visible */}
          {exec.news_headlines.length > 0 && (
            <div className="mt-2 text-xs text-muted-foreground">
              <span className="mr-1">•</span>
              {exec.news_urls?.[0] ? (
                <a href={exec.news_urls[0]} target="_blank" rel="noopener noreferrer" className="text-primary hover:underline">
                  {exec.news_headlines[0]}
                </a>
              ) : exec.news_headlines[0]}
            </div>
          )}
        </div>
      </div>

      {(exec.fec_top_recipients.length > 0 || exec.news_headlines.length > 0) && (
        <button
          onClick={() => setExpanded(!expanded)}
          className="w-full mt-3 pt-2 border-t text-xs font-medium text-primary hover:text-primary/80 flex items-center justify-center gap-1"
        >
          {expanded ? "Hide Details" : "View Details"}
          {expanded ? <ChevronUp className="h-3 w-3" /> : <ChevronDown className="h-3 w-3" />}
        </button>
      )}

      {expanded && (
        <div className="mt-3 space-y-3">
          {exec.fec_top_recipients.length > 0 && (
            <div>
              <h5 className="text-xs font-semibold text-muted-foreground tracking-wider mb-1.5">Top FEC Recipients</h5>
              <div className="space-y-1">
                {exec.fec_top_recipients.slice(0, 5).map((r, i) => (
                  <div key={i} className="flex items-center justify-between text-xs p-1.5 rounded bg-muted/50">
                    <span className="text-foreground truncate mr-2">{r.name}</span>
                    <span className="text-muted-foreground whitespace-nowrap">{formatUSD(r.total)} · {r.count}x</span>
                  </div>
                ))}
              </div>
            </div>
          )}
          {exec.news_headlines.length > 0 && (
            <div>
              <h5 className="text-xs font-semibold text-muted-foreground tracking-wider mb-1.5">Headlines</h5>
              <ul className="space-y-1">
                {exec.news_headlines.slice(0, 3).map((h, i) => {
                  const url = exec.news_urls?.[i];
                  return (
                    <li key={i} className="text-xs text-muted-foreground leading-relaxed flex items-start gap-1.5">
                      <span className="mt-0.5">•</span>
                      {url ? (
                        <a href={url} target="_blank" rel="noopener noreferrer" className="text-primary hover:underline">
                          {h}
                        </a>
                      ) : h}
                    </li>
                  );
                })}
              </ul>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

function ScoreCircle({ score, color }: { score: number; color: string }) {
  return (
    <div className="relative w-24 h-24 mx-auto">
      <svg viewBox="0 0 100 100" className="w-full h-full -rotate-90">
        <circle cx="50" cy="50" r="42" fill="none" stroke="hsl(var(--border))" strokeWidth="8" />
        <circle cx="50" cy="50" r="42" fill="none" stroke={color} strokeWidth="8" strokeLinecap="round"
          strokeDasharray={`${(score / 10) * 264} 264`} />
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <span className="text-xl font-bold text-foreground">{score.toFixed(1)}</span>
        <span className="text-[10px] text-muted-foreground">/ 10</span>
      </div>
    </div>
  );
}

function GateCard({ title, gate }: { title: string; gate: { status: "PASS" | "FAIL"; sources_checked: string[]; matches: any[] } }) {
  const pass = gate.status === "PASS";
  return (
    <div className={`glass-card p-4 border-l-4 ${pass ? "border-l-[hsl(var(--risk-low))]" : "border-l-destructive"}`}>
      <div className="flex items-center gap-2 mb-2">
        {pass ? <CheckCircle className="w-5 h-5 text-[hsl(var(--risk-low))]" /> : <XCircle className="w-5 h-5 text-destructive" />}
        <span className="font-semibold text-sm text-foreground">{title}</span>
        <span className={`text-xs font-bold px-2 py-0.5 rounded ${pass ? "bg-[hsl(var(--risk-low)/0.10)] text-[hsl(var(--risk-low))]" : "bg-destructive/10 text-destructive"}`}>
          {gate.status}
        </span>
      </div>
      {!pass && gate.matches.length > 0 && (
        <div className="space-y-1 mb-2">
          {gate.matches.map((m: any, i: number) => (
            <div key={i} className="text-xs p-2 rounded-lg bg-[hsl(var(--destructive)/0.04)] border border-destructive/10">
              <p className="font-medium text-destructive">{m.list}: {m.matched_name} ({m.confidence}% match)</p>
              <p className="text-muted-foreground mt-0.5">{m.details}</p>
            </div>
          ))}
        </div>
      )}
      <p className="text-xs text-muted-foreground">Sources: {gate.sources_checked.join(", ")}</p>
    </div>
  );
}
