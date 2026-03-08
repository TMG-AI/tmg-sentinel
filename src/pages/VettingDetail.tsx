import { useParams, useNavigate } from "react-router-dom";
import { useVettingStore } from "@/lib/vetting-store";
import { ENGAGEMENT_LABELS, VETTING_LEVEL_LABELS, DIMENSION_LABELS, RCS_QUESTION_LABELS, Decision, ReputationalContagion } from "@/lib/types";
import {
  getRiskTierColor, getEngagementClass, getVettingLevelColor,
  getDecisionColor, getDecisionLabel, getScoreBarColor,
  getConfidenceColor, formatDateTime,
} from "@/lib/vetting-utils";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from "@/components/ui/accordion";
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from "@/components/ui/collapsible";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter, DialogDescription } from "@/components/ui/dialog";
import {
  CheckCircle, XCircle, ArrowLeft, AlertTriangle, ExternalLink, Upload,
  Shield, Skull, FileText, Clock, Newspaper, ChevronDown, ShieldAlert,
} from "lucide-react";
import { useState, useRef, useEffect } from "react";
import { useToast } from "@/hooks/use-toast";

function getRcsColor(score: number): string {
  if (score <= 2.5) return "hsl(var(--risk-low))";
  if (score <= 4.5) return "hsl(var(--risk-moderate))";
  if (score <= 6.5) return "hsl(var(--risk-elevated))";
  if (score <= 8.0) return "hsl(var(--risk-high))";
  return "hsl(var(--risk-critical, var(--risk-high)))";
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
  const gatesFailed = gates?.sanctions.status === "FAIL" || gates?.debarment.status === "FAIL";

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
    toast({ title: "Vetting Reopened", description: "Decision has been cleared. The vetting is now open for a new decision." });
  };

  const handleUploadJSON = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = (ev) => {
      try {
        const json = JSON.parse(ev.target?.result as string);
        uploadResults(v.id, json);
        toast({ title: "Results Uploaded", description: "Vetting results have been processed and applied." });
      } catch {
        toast({ title: "Error", description: "Invalid JSON file.", variant: "destructive" });
      }
    };
    reader.readAsText(file);
  };

  const dimensionOrder = dimensions
    ? Object.entries(dimensions).sort(([, a], [, b]) => b.weight - a.weight)
    : [];

  return (
    <div className="page-container max-w-5xl">
      {/* Back */}
      <button onClick={() => navigate(-1)} className="flex items-center gap-1.5 text-sm text-muted-foreground hover:text-foreground mb-6 transition-colors">
        <ArrowLeft className="w-4 h-4" /> Back
      </button>

      {/* Header */}
      <div className="glass-card p-6 mb-6">
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
            <div className="flex items-center gap-2 text-sm text-muted-foreground">
              <Clock className="w-3.5 h-3.5" />
              <span>Requested by {v.requested_by} on {formatDateTime(v.requested_at)}</span>
            </div>
            {v.brief_bio && <p className="text-sm text-muted-foreground mt-3 max-w-2xl">{v.brief_bio}</p>}
          </div>

          {/* Dual Scores */}
          <div className="flex gap-6 flex-shrink-0">
            {v.composite_score != null && (
              <div className="text-center">
                <ScoreCircle score={v.composite_score} color={v.composite_score <= 2.5 ? "hsl(var(--risk-low))" : v.composite_score <= 4.5 ? "hsl(var(--risk-moderate))" : v.composite_score <= 6.5 ? "hsl(var(--risk-elevated))" : "hsl(var(--risk-high))"} />
                <p className="text-xs font-semibold text-muted-foreground mt-1">Factual Risk</p>
                {v.risk_tier && (
                  <span className={`inline-block text-xs font-bold px-3 py-1 rounded mt-1 ${getRiskTierColor(v.risk_tier)}`}>
                    {v.risk_tier}
                  </span>
                )}
                {v.recommendation && (
                  <p className="text-xs font-semibold text-foreground mt-1">{v.recommendation}</p>
                )}
              </div>
            )}
            {rca && (
              <div className="text-center">
                <ScoreCircle score={rca.composite_rcs} color={getRcsColor(rca.composite_rcs)} />
                <p className="text-xs font-semibold text-muted-foreground mt-1">Reputational Risk</p>
                <span className={`inline-block text-xs font-bold px-3 py-1 rounded mt-1 ${getRiskTierColor(rca.rcs_risk_tier)}`}>
                  {rca.rcs_risk_tier}
                </span>
                <p className="text-xs font-semibold text-foreground mt-1">{rca.rcs_recommendation.split(';')[0]}</p>
              </div>
            )}
          </div>
        </div>

        {/* Upload JSON button for testing */}
        {(v.status === "pending" || v.status === "running") && (
          <div className="mt-4 pt-4 border-t">
            <input ref={fileInputRef} type="file" accept=".json" onChange={handleUploadJSON} className="hidden" />
            <Button variant="outline" size="sm" onClick={() => fileInputRef.current?.click()}>
              <Upload className="w-3.5 h-3.5 mr-2" /> Upload Results JSON (Testing)
            </Button>
          </div>
        )}
      </div>

      {/* Divergence Alert */}
      {rca?.divergence_alert && (
        <div className="mb-6 p-5 rounded-xl border-2 border-[hsl(var(--risk-moderate))] bg-[hsl(var(--risk-moderate)/0.06)]">
          <div className="flex items-start gap-3">
            <div className="p-2 rounded-lg bg-[hsl(var(--risk-moderate)/0.15)]">
              <ShieldAlert className="w-5 h-5 text-[hsl(var(--risk-moderate))]" />
            </div>
            <div>
              <h3 className="text-sm font-bold text-[hsl(var(--risk-moderate))] uppercase tracking-wide mb-1">Divergence Alert</h3>
              <p className="text-sm text-foreground">{rca.divergence_alert}</p>
            </div>
          </div>
        </div>
      )}

      {/* Gates */}
      {gates && (
        <div className="mb-6">
          {gatesFailed && (
            <div className="risk-badge-critical p-4 rounded-xl mb-4 flex items-center gap-3">
              <Skull className="w-6 h-6 flex-shrink-0" />
              <div>
                <p className="font-bold text-sm">AUTO-REJECTED — {gates.sanctions.status === "FAIL" ? "Sanctions" : "Debarment"} match found</p>
                <p className="text-xs opacity-90 mt-0.5">No composite score calculated. Legal counsel required to override.</p>
              </div>
            </div>
          )}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <GateCard title="Sanctions / Watchlist Gate" gate={gates.sanctions} />
            <GateCard title="Government Exclusion Gate" gate={gates.debarment} />
          </div>
        </div>
      )}

      {/* Dimensions */}
      {dimensions && !gatesFailed && dimensionOrder.length > 0 && (
        <div className="glass-card p-6 mb-6">
          <h2 className="section-title">Risk Dimension Scorecard</h2>
          <div className="space-y-5">
            {dimensionOrder.map(([key, dim]) => (
              <div key={key}>
                <div className="flex items-center justify-between mb-1.5">
                  <div className="flex items-center gap-2">
                    <span className="text-sm font-medium text-foreground">{DIMENSION_LABELS[key] || key}</span>
                    <span className="text-xs text-muted-foreground">({(dim.weight * 100).toFixed(0)}%)</span>
                  </div>
                  <span className="text-sm font-bold text-foreground">{dim.score.toFixed(1)}</span>
                </div>
                <div className="w-full h-2 rounded-full bg-muted overflow-hidden">
                  <div className={`h-full rounded-full transition-all ${getScoreBarColor(dim.score)}`} style={{ width: `${(dim.score / 10) * 100}%` }} />
                </div>
                <p className="text-xs text-muted-foreground mt-1">{dim.summary}</p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Modifiers */}
      {scoring && !gatesFailed && (
        <div className="glass-card p-6 mb-6">
          <h2 className="section-title">Scoring Modifiers</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 text-sm">
            <div className="p-4 rounded-xl bg-muted">
              <p className="font-medium text-foreground mb-1">Confidence</p>
              <p className="text-xs text-muted-foreground">{scoring.confidence_modifier === "none" ? "HIGH confidence — score used as-is" : `${scoring.confidence_modifier} applied`}</p>
            </div>
            <div className="p-4 rounded-xl bg-muted">
              <p className="font-medium text-foreground mb-1">Engagement Context</p>
              <p className="text-xs text-muted-foreground">{scoring.engagement_multiplier}x multiplier{scoring.engagement_multiplier !== 1 ? ` (${scoring.raw_composite.toFixed(2)} → ${scoring.adjusted_composite.toFixed(2)})` : ""}</p>
            </div>
            <div className="p-4 rounded-xl bg-muted">
              <p className="font-medium text-foreground mb-1">Final Score</p>
              <p className="text-xs text-muted-foreground">{scoring.final_composite.toFixed(2)} → {scoring.risk_tier}</p>
            </div>
            {rca && (
              <div className="p-4 rounded-xl bg-muted border border-[hsl(var(--risk-moderate)/0.2)]">
                <p className="font-medium text-foreground mb-1">RCS Score</p>
                <p className="text-xs text-muted-foreground">{rca.composite_rcs.toFixed(2)} / 10 — <span className={`font-bold ${getRiskTierColor(rca.rcs_risk_tier).includes('critical') ? 'text-destructive' : ''}`}>{rca.rcs_risk_tier}</span></p>
              </div>
            )}
          </div>
        </div>
      )}

      {/* RCA Section */}
      {rca && !gatesFailed && (
        <div className="glass-card p-6 mb-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="section-title flex items-center gap-2 mb-0">
              <ShieldAlert className="w-4 h-4" /> Reputational Contagion Analysis
            </h2>
            <div className="flex items-center gap-2">
              <span className="text-lg font-bold text-foreground">{rca.composite_rcs.toFixed(2)}</span>
              <span className="text-xs text-muted-foreground">/ 10</span>
              <span className={`text-xs font-bold px-3 py-1 rounded ${getRiskTierColor(rca.rcs_risk_tier)}`}>
                {rca.rcs_risk_tier}
              </span>
            </div>
          </div>
          <p className="text-sm text-muted-foreground mb-5">{rca.rcs_recommendation}</p>

          {/* 6-question scorecard */}
          <div className="space-y-4 mb-6">
            {(Object.keys(RCS_QUESTION_LABELS) as Array<keyof typeof RCS_QUESTION_LABELS>).map((qKey) => {
              const q = rca[qKey as keyof ReputationalContagion] as { score: number; weight: number; evidence: string } | undefined;
              if (!q || typeof q !== 'object' || !('score' in q)) return null;
              return (
                <RCSQuestionRow
                  key={qKey}
                  label={RCS_QUESTION_LABELS[qKey]}
                  weight={q.weight}
                  score={q.score}
                  evidence={q.evidence}
                />
              );
            })}
          </div>

          {/* Most Damaging Headline */}
          {rca.most_damaging_headline && (
            <div className="border-l-4 border-[hsl(var(--risk-elevated))] bg-[hsl(var(--risk-elevated)/0.04)] rounded-r-xl p-4">
              <div className="flex items-center gap-2 mb-2">
                <Newspaper className="w-4 h-4 text-[hsl(var(--risk-elevated))]" />
                <span className="text-xs font-bold text-[hsl(var(--risk-elevated))] uppercase tracking-wide">Most Damaging Headline</span>
              </div>
              <p className="text-sm italic text-foreground font-medium">"{rca.most_damaging_headline}"</p>
            </div>
          )}
        </div>
      )}

      {/* Flags */}
      {flags && (flags.red.length > 0 || flags.yellow.length > 0) && (
        <div className="mb-6">
          <h2 className="section-title">Flags Inventory</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <h3 className="text-xs font-semibold text-destructive uppercase mb-2">Red Flags ({flags.red.length})</h3>
              {flags.red.length === 0 ? (
                <p className="text-xs text-muted-foreground p-3 bg-muted rounded-xl">No red flags</p>
              ) : (
                <div className="space-y-2">
                  {flags.red.map((f, i) => (
                    <div key={i} className="p-3 rounded-xl border border-destructive/15 bg-[hsl(var(--destructive)/0.04)]">
                      <div className="flex items-center gap-2 mb-1">
                        <AlertTriangle className="w-3.5 h-3.5 text-destructive" />
                        <span className="text-sm font-medium text-foreground">{f.title}</span>
                      </div>
                      <p className="text-xs text-muted-foreground">{f.description}</p>
                      <p className="text-xs text-muted-foreground mt-1">{f.source} · {f.date}</p>
                    </div>
                  ))}
                </div>
              )}
            </div>
            <div>
              <h3 className="text-xs font-semibold text-[hsl(var(--risk-moderate))] uppercase mb-2">Yellow Flags ({flags.yellow.length})</h3>
              {flags.yellow.length === 0 ? (
                <p className="text-xs text-muted-foreground p-3 bg-muted rounded-xl">No yellow flags</p>
              ) : (
                <div className="space-y-2">
                  {flags.yellow.map((f, i) => (
                    <div key={i} className="p-3 rounded-xl border border-[hsl(var(--risk-moderate)/0.15)] bg-[hsl(var(--risk-moderate)/0.04)]">
                      <div className="flex items-center gap-2 mb-1">
                        <AlertTriangle className="w-3.5 h-3.5 text-[hsl(var(--risk-moderate))]" />
                        <span className="text-sm font-medium text-foreground">{f.title}</span>
                      </div>
                      <p className="text-xs text-muted-foreground">{f.description}</p>
                      <p className="text-xs text-muted-foreground mt-1">{f.source} · {f.date}</p>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>
      )}
      {flags && flags.red.length === 0 && flags.yellow.length === 0 && (
        <div className="glass-card p-4 mb-6 flex items-center gap-3 bg-[hsl(var(--risk-low)/0.04)] border-[hsl(var(--risk-low)/0.15)]">
          <CheckCircle className="w-5 h-5 text-risk-low flex-shrink-0" />
          <span className="text-sm text-foreground font-medium">No flags identified</span>
        </div>
      )}

      {/* Executive Summary */}
      {result?.executive_summary && (
        <div className="glass-card p-6 mb-6">
          <h2 className="section-title flex items-center gap-2"><FileText className="w-4 h-4" /> Executive Summary</h2>
          <div className="prose prose-sm max-w-none text-foreground">
            {result.executive_summary.split("\n").map((line, i) => {
              if (line.startsWith("## ")) return <h3 key={i} className="text-base font-bold mt-4 mb-2 text-foreground">{line.replace("## ", "")}</h3>;
              if (line.startsWith("**") && line.endsWith("**")) return <p key={i} className="font-bold text-foreground">{line.replace(/\*\*/g, "")}</p>;
              if (line.startsWith("- ")) return <li key={i} className="text-sm text-muted-foreground ml-4 mb-1">{line.replace("- ", "").replace(/\*\*(.*?)\*\*/g, "$1")}</li>;
              if (line.trim() === "") return <br key={i} />;
              return <p key={i} className="text-sm text-muted-foreground mb-2">{line.replace(/\*\*(.*?)\*\*/g, "$1")}</p>;
            })}
          </div>
        </div>
      )}

      {/* Sources */}
      {result?.sources && result.sources.length > 0 && (
        <div className="glass-card p-6 mb-6">
          <h2 className="section-title flex items-center gap-2"><ExternalLink className="w-4 h-4" /> Sources ({result.sources.length})</h2>
          <div className="space-y-2">
            {[...result.sources].sort((a, b) => b.score - a.score).map((src) => (
              <div key={src.id} className="flex items-center gap-3 p-2.5 rounded-lg bg-muted text-sm">
                <span className="text-xs font-mono text-muted-foreground w-6 text-right flex-shrink-0">{src.id}</span>
                <a href={src.url} target="_blank" rel="noopener noreferrer" className="text-primary hover:underline truncate flex-1">
                  {src.title}
                </a>
                <Badge variant="outline" className="text-xs flex-shrink-0 bg-primary/5 text-primary border-primary/20">
                  {(src.score * 100).toFixed(0)}%
                </Badge>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Evidence Accordion */}
      {dimensions && !gatesFailed && (
        <div className="glass-card p-6 mb-6">
          <h2 className="section-title">Evidence by Dimension</h2>
          <Accordion type="multiple">
            {dimensionOrder.map(([key, dim]) => (
              <AccordionItem key={key} value={key}>
                <AccordionTrigger className="text-sm font-medium text-foreground hover:no-underline">
                  {DIMENSION_LABELS[key] || key} ({dim.evidence.length} items)
                </AccordionTrigger>
                <AccordionContent>
                  {dim.evidence.length === 0 ? (
                    <p className="text-xs text-muted-foreground py-2">No evidence items collected for this dimension.</p>
                  ) : (
                     <div className="space-y-2">
                      {dim.evidence.map((ev, i) => (
                        <div key={i} className="p-3 rounded-lg bg-muted text-sm">
                          <p className="text-foreground">{ev.text}</p>
                          {ev.source_urls && ev.source_urls.length > 0 ? (
                            <div className="flex items-center gap-2 flex-wrap mt-2">
                              {ev.source_urls.map((su, si) => (
                                <a key={si} href={su.url} target="_blank" rel="noopener noreferrer"
                                  className="inline-flex items-center gap-1 text-xs px-2 py-0.5 rounded-full bg-primary/8 text-primary border border-primary/15 hover:bg-primary/15 transition-colors">
                                  {su.title} <ExternalLink className="w-2.5 h-2.5" />
                                </a>
                              ))}
                            </div>
                          ) : (
                            <div className="flex items-center gap-3 mt-2 text-xs text-muted-foreground">
                              <span>{ev.source}</span>
                              <span>{ev.date}</span>
                              {ev.url && (
                                <a href={ev.url} target="_blank" rel="noopener noreferrer" className="text-primary flex items-center gap-1 hover:underline">
                                  View <ExternalLink className="w-3 h-3" />
                                </a>
                              )}
                            </div>
                          )}
                        </div>
                      ))}
                    </div>
                  )}
                  {/* Sub-factors */}
                  {Object.keys(dim.sub_factors).length > 0 && (
                    <div className="mt-3 pt-3 border-t">
                      <p className="text-xs font-semibold text-muted-foreground mb-2">Sub-factors</p>
                      <div className="space-y-1">
                        {Object.entries(dim.sub_factors).map(([sk, sf]) => (
                          <div key={sk} className="flex items-center justify-between text-xs">
                            <span className="text-muted-foreground capitalize">{sk.replace(/_/g, " ")}</span>
                            <div className="flex items-center gap-2">
                              <span className="text-foreground font-medium">{sf.score}/10</span>
                              <span className="text-muted-foreground">— {sf.detail}</span>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </AccordionContent>
              </AccordionItem>
            ))}
          </Accordion>
        </div>
      )}

      {/* Decision Section */}
      {(v.status === "completed" || v.status === "gates_failed") && (
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
              <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-4">
                <Button onClick={() => handleDecisionClick("approved")} className="bg-[hsl(var(--risk-low))] hover:bg-[hsl(var(--risk-low)/0.9)] text-[hsl(var(--risk-low-foreground))]">
                  Approve
                </Button>
                <Button onClick={() => handleDecisionClick("conditionally_approved")} className="bg-[hsl(var(--risk-moderate))] hover:bg-[hsl(var(--risk-moderate)/0.9)] text-[hsl(var(--risk-moderate-foreground))]">
                  Conditional
                </Button>
                <Button onClick={() => handleDecisionClick("rejected")} variant="destructive">
                  Reject
                </Button>
                <Button onClick={() => handleDecisionClick("pending_review")} variant="outline" className="border-primary text-primary">
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
              placeholder="Explain the rationale for this decision..."
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

function ScoreCircle({ score, color }: { score: number; color: string }) {
  return (
    <div className="relative w-24 h-24 mx-auto">
      <svg viewBox="0 0 100 100" className="w-full h-full -rotate-90">
        <circle cx="50" cy="50" r="42" fill="none" stroke="hsl(var(--border))" strokeWidth="8" />
        <circle
          cx="50" cy="50" r="42" fill="none"
          stroke={color}
          strokeWidth="8" strokeLinecap="round"
          strokeDasharray={`${(score / 10) * 264} 264`}
        />
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <span className="text-xl font-bold text-foreground">{score.toFixed(1)}</span>
        <span className="text-[10px] text-muted-foreground">/ 10</span>
      </div>
    </div>
  );
}

function RCSQuestionRow({ label, weight, score, evidence }: { label: string; weight: number; score: number; evidence: string }) {
  const [open, setOpen] = useState(false);
  return (
    <div>
      <div className="flex items-center justify-between mb-1.5">
        <div className="flex items-center gap-2">
          <span className="text-sm font-medium text-foreground">{label}</span>
          <span className="text-xs text-muted-foreground">({(weight * 100).toFixed(0)}%)</span>
        </div>
        <span className="text-sm font-bold text-foreground">{score.toFixed(1)}</span>
      </div>
      <div className="w-full h-2 rounded-full bg-muted overflow-hidden">
        <div className={`h-full rounded-full transition-all ${getScoreBarColor(score)}`} style={{ width: `${(score / 10) * 100}%` }} />
      </div>
      <Collapsible open={open} onOpenChange={setOpen}>
        <CollapsibleTrigger className="flex items-center gap-1 text-xs text-muted-foreground hover:text-foreground mt-1 cursor-pointer transition-colors">
          <ChevronDown className={`w-3 h-3 transition-transform ${open ? 'rotate-180' : ''}`} />
          {open ? "Hide evidence" : "Show evidence"}
        </CollapsibleTrigger>
        <CollapsibleContent>
          <p className="text-xs text-muted-foreground mt-1 pl-4 border-l-2 border-muted">{evidence}</p>
        </CollapsibleContent>
      </Collapsible>
    </div>
  );
}

function GateCard({ title, gate }: { title: string; gate: { status: "PASS" | "FAIL"; sources_checked: string[]; matches: any[] } }) {
  const pass = gate.status === "PASS";
  return (
    <div className={`glass-card p-4 border-l-4 ${pass ? "border-l-risk-low" : "border-l-destructive"}`}>
      <div className="flex items-center gap-2 mb-2">
        {pass ? <CheckCircle className="w-5 h-5 text-risk-low" /> : <XCircle className="w-5 h-5 text-destructive" />}
        <span className="font-semibold text-sm text-foreground">{title}</span>
        <span className={`text-xs font-bold px-2 py-0.5 rounded ${pass ? "bg-[hsl(var(--risk-low)/0.10)] text-risk-low" : "bg-destructive/10 text-destructive"}`}>
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
