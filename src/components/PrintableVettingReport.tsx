import type { VettingRequest, ReputationalContagion, KeyExecutive, GovernmentContracts, DimensionResult, Flag } from "@/lib/types";
import { ENGAGEMENT_LABELS, VETTING_LEVEL_LABELS, DIMENSION_LABELS, RCS_QUESTION_LABELS } from "@/lib/types";

interface PrintableVettingReportProps {
  vetting: VettingRequest;
}

const riskColors: Record<string, { bg: string; text: string; border: string }> = {
  LOW: { bg: "#dcfce7", text: "#166534", border: "#22c55e" },
  MODERATE: { bg: "#fef3c7", text: "#92400e", border: "#f59e0b" },
  ELEVATED: { bg: "#fef3c7", text: "#92400e", border: "#f59e0b" },
  HIGH: { bg: "#fee2e2", text: "#991b1b", border: "#ef4444" },
  CRITICAL: { bg: "#fce4ec", text: "#880e4f", border: "#e91e63" },
};

function getTierStyle(tier: string | null | undefined) {
  return riskColors[tier || ""] || { bg: "#f3f4f6", text: "#374151", border: "#9ca3af" };
}

function scoreColor(score: number): string {
  if (score <= 2.5) return "#059669";
  if (score <= 4.5) return "#d97706";
  if (score <= 6.5) return "#ea580c";
  return "#dc2626";
}

function formatUSD(amount: number): string {
  if (amount >= 1e9) return `$${(amount / 1e9).toFixed(2)}B`;
  if (amount == null) return "$0";
  if (amount >= 1e6) return `$${(amount / 1e6).toFixed(1)}M`;
  if (amount >= 1e3) return `$${(amount / 1e3).toFixed(0)}K`;
  return `$${amount.toLocaleString()}`;
}

function cleanText(text: string): string {
  return text.replace(/\s*\[\d+\]\s*/g, " ").replace(/\s*\[\w+\]\s*$/g, "").replace(/\*\*(.*?)\*\*/g, "$1").trim();
}

const sectionHeader = (title: string) => ({
  fontSize: "0.875rem" as const,
  fontWeight: 700 as const,
  marginBottom: "0.5rem",
  borderBottom: "2px solid #e5e7eb",
  paddingBottom: "0.25rem",
  textTransform: "uppercase" as const,
  letterSpacing: "0.03em",
  color: "#111827",
});

/** Find the source URL by citation number like [1] */
function findSourceUrl(sources: { id: number; url: string; title: string; score: number }[] | undefined, id: number): string | undefined {
  return sources?.find(s => s.id === id)?.url;
}

/** Render text with inline [n] citations turned into clickable links */
function renderTextWithCitations(text: string, sources: { id: number; url: string; title: string; score: number }[] | undefined): (string | JSX.Element)[] {
  if (!sources || sources.length === 0) return [cleanText(text)];
  const parts: (string | JSX.Element)[] = [];
  const regex = /\[(\d+)\]/g;
  let lastIndex = 0;
  let match: RegExpExecArray | null;
  const cleaned = text.replace(/\*\*(.*?)\*\*/g, "$1");
  while ((match = regex.exec(cleaned)) !== null) {
    if (match.index > lastIndex) {
      parts.push(cleaned.slice(lastIndex, match.index));
    }
    const id = parseInt(match[1], 10);
    const url = findSourceUrl(sources, id);
    if (url) {
      parts.push(
        <a key={`cite-${match.index}`} href={url} target="_blank" rel="noopener noreferrer" style={{ color: "#2563eb", textDecoration: "underline" }}>
          [{id}]
        </a>
      );
    } else {
      parts.push(`[${id}]`);
    }
    lastIndex = regex.lastIndex;
  }
  if (lastIndex < cleaned.length) {
    parts.push(cleaned.slice(lastIndex));
  }
  return parts;
}

export function PrintableVettingReport({ vetting: v }: PrintableVettingReportProps) {
  const result = v.result_json;
  const combined = result?.combined_decision;
  const rca = result?.reputational_contagion;
  const gates = result?.gates;
  const dimensions = result?.dimensions;
  const flags = result?.flags || v.flags;
  const executives = result?.key_executives;
  const contracts = result?.government_contracts;
  const scoring = result?.scoring;
  const sources = result?.sources;
  const primaryTier = combined?.combined_tier || v.risk_tier;
  const tc = getTierStyle(primaryTier);

  const dimensionOrder = dimensions
    ? Object.entries(dimensions).sort(([, a], [, b]) => b.weight - a.weight)
    : [];

  return (
    <div style={{ fontFamily: "system-ui, -apple-system, 'Segoe UI', Roboto, sans-serif", lineHeight: 1.5, maxWidth: "8.5in", margin: "0 auto", padding: "0.5in", color: "#111827", fontSize: "13px" }}>

      {/* HEADER */}
      <div style={{ display: "flex", gap: "1.5rem", marginBottom: "1.25rem", paddingBottom: "1rem", borderBottom: `3px solid ${tc.border}` }}>
        <div style={{ flex: 1 }}>
          <h1 style={{ fontSize: "1.75rem", fontWeight: 700, margin: 0, color: "#111827" }}>
            {v.subject_name}
          </h1>
          <p style={{ fontSize: "0.9rem", color: "#6b7280", margin: "0.25rem 0 0.75rem" }}>
            {v.subject_type === "individual" ? "Individual" : "Organization"}
            {v.company_affiliation ? ` · ${v.company_affiliation}` : ""}
            {v.country ? ` · ${v.country}` : ""}
            {v.city ? `, ${v.city}` : ""}
          </p>
          <div style={{ display: "flex", gap: "0.5rem", flexWrap: "wrap" }}>
            <span style={{ padding: "0.25rem 0.75rem", borderRadius: "4px", fontSize: "0.8rem", fontWeight: 700, backgroundColor: tc.bg, color: tc.text }}>
              {primaryTier || "PENDING"}
            </span>
            {combined && (
              <span style={{ padding: "0.25rem 0.75rem", borderRadius: "4px", fontSize: "0.8rem", fontWeight: 600, backgroundColor: "#f3f4f6", color: "#374151" }}>
                {combined.recommendation?.replace("Conditional Approve", "Conditional Approval")}
              </span>
            )}
            <span style={{ padding: "0.25rem 0.75rem", borderRadius: "4px", fontSize: "0.75rem", fontWeight: 500, backgroundColor: "#eff6ff", color: "#1e40af" }}>
              {ENGAGEMENT_LABELS[v.engagement_type].split(" ").slice(0, 4).join(" ")}
            </span>
            <span style={{ padding: "0.25rem 0.75rem", borderRadius: "4px", fontSize: "0.75rem", fontWeight: 500, backgroundColor: "#f5f3ff", color: "#5b21b6" }}>
              {VETTING_LEVEL_LABELS[v.vetting_level].title}
            </span>
          </div>
        </div>
        <div style={{ display: "flex", gap: "1rem", flexShrink: 0 }}>
          {v.composite_score != null && (
            <div style={{ textAlign: "center", padding: "0.75rem 1rem", backgroundColor: "#f9fafb", borderRadius: "8px", minWidth: "90px" }}>
              <p style={{ fontSize: "0.6rem", textTransform: "uppercase", color: "#6b7280", margin: 0, letterSpacing: "0.05em" }}>Factual Risk</p>
              <p style={{ fontSize: "1.75rem", fontWeight: 700, margin: "0.25rem 0", color: scoreColor(v.composite_score) }}>{v.composite_score.toFixed(1)}</p>
              <p style={{ fontSize: "0.7rem", color: "#6b7280", margin: 0 }}>/ 10</p>
            </div>
          )}
          {rca && (
            <div style={{ textAlign: "center", padding: "0.75rem 1rem", backgroundColor: "#f9fafb", borderRadius: "8px", minWidth: "90px" }}>
              <p style={{ fontSize: "0.6rem", textTransform: "uppercase", color: "#6b7280", margin: 0, letterSpacing: "0.05em" }}>Reputational</p>
              <p style={{ fontSize: "1.75rem", fontWeight: 700, margin: "0.25rem 0", color: scoreColor(rca.composite_rcs) }}>{rca.composite_rcs.toFixed(1)}</p>
              <p style={{ fontSize: "0.7rem", color: "#6b7280", margin: 0 }}>/ 10</p>
            </div>
          )}
        </div>
      </div>

      {/* Request info */}
      <div style={{ fontSize: "0.75rem", color: "#6b7280", marginBottom: "1.25rem" }}>
        Requested by {v.requested_by} · {v.requested_at ? new Date(v.requested_at).toLocaleDateString("en-US", { year: "numeric", month: "long", day: "numeric", timeZone: "America/New_York" }) : "N/A"}
        {v.decision && ` · Decision: ${v.decision.replace("_", " ").replace(/\b\w/g, c => c.toUpperCase())} by ${v.decided_by}`}
      </div>

      {/* DIVERGENCE ALERT */}
      {rca?.divergence_alert && (
        <div style={{ marginBottom: "1.25rem", padding: "0.75rem", borderRadius: "6px", borderLeft: "4px solid #ea580c", backgroundColor: "#fff7ed" }}>
          <p style={{ fontSize: "0.75rem", fontWeight: 700, color: "#ea580c", margin: "0 0 0.25rem", textTransform: "uppercase" }}>⚠ Divergence Alert</p>
          <p style={{ fontSize: "0.8rem", color: "#374151", margin: 0 }}>{rca.divergence_alert}</p>
        </div>
      )}

      {/* EXECUTIVE SUMMARY */}
      {result?.executive_summary && (
        <div style={{ marginBottom: "1.5rem" }}>
          <h2 style={sectionHeader("Executive Summary")}>Executive Summary</h2>
          <div style={{ fontSize: "0.8rem", color: "#374151", lineHeight: 1.6 }}>
            {result.executive_summary.split("\n").filter(l => l.trim()).map((line, i) => {
              const clean = cleanText(line);
              if (line.startsWith("## ")) return <h3 key={i} style={{ fontSize: "0.85rem", fontWeight: 700, marginTop: "0.75rem", marginBottom: "0.25rem", color: "#111827" }}>{clean.replace("## ", "")}</h3>;
              if (line.startsWith("**") && line.endsWith("**")) return <p key={i} style={{ fontWeight: 700, color: "#111827", marginTop: "0.5rem", marginBottom: "0.25rem" }}>{clean}</p>;
              if (line.startsWith("- ")) return <li key={i} style={{ marginLeft: "1rem", marginBottom: "0.25rem", color: "#374151" }}>{renderTextWithCitations(line.replace("- ", ""), sources)}</li>;
              return <p key={i} style={{ marginBottom: "0.35rem", color: "#374151" }}>{renderTextWithCitations(line, sources)}</p>;
            })}
          </div>
        </div>
      )}

      {/* GATES */}
      {gates && (
        <div style={{ marginBottom: "1.5rem" }}>
          <h2 style={sectionHeader("Compliance Gates")}>Compliance Gates</h2>
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "0.75rem" }}>
            {(["sanctions", "debarment"] as const).map(gateKey => {
              const gate = gates[gateKey];
              const pass = gate.status === "PASS";
              return (
                <div key={gateKey} style={{ padding: "0.75rem", borderRadius: "6px", borderLeft: `4px solid ${pass ? "#22c55e" : "#ef4444"}`, backgroundColor: pass ? "#f0fdf4" : "#fef2f2" }}>
                  <div style={{ display: "flex", alignItems: "center", gap: "0.5rem", marginBottom: "0.25rem" }}>
                    <span style={{ fontSize: "0.85rem", fontWeight: 600, color: "#111827" }}>{gateKey === "sanctions" ? "Sanctions / Watchlist" : "Government Exclusion"}</span>
                    <span style={{ fontSize: "0.7rem", fontWeight: 700, padding: "0.1rem 0.4rem", borderRadius: "4px", backgroundColor: pass ? "#dcfce7" : "#fee2e2", color: pass ? "#166534" : "#991b1b" }}>
                      {gate.status}
                    </span>
                  </div>
                  <p style={{ fontSize: "0.7rem", color: "#6b7280", margin: 0 }}>Sources: {gate.sources_checked.join(", ")}</p>
                  {!pass && gate.matches.length > 0 && gate.matches.map((m, i) => (
                    <p key={i} style={{ fontSize: "0.7rem", color: "#991b1b", marginTop: "0.25rem" }}>
                      {m.list}: {m.matched_name} ({m.confidence}% match) — {m.details}
                    </p>
                  ))}
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* RISK SCORECARD */}
      {dimensionOrder.length > 0 && (
        <div style={{ marginBottom: "1.5rem" }}>
          <h2 style={sectionHeader("Risk Scorecard")}>Risk Scorecard</h2>
          <table style={{ width: "100%", fontSize: "0.75rem", borderCollapse: "collapse" }}>
            <thead>
              <tr style={{ backgroundColor: "#f9fafb" }}>
                <th style={{ padding: "0.5rem", textAlign: "left", fontWeight: 600 }}>Dimension</th>
                <th style={{ padding: "0.5rem", textAlign: "center", fontWeight: 600 }}>Score</th>
                <th style={{ padding: "0.5rem", textAlign: "center", fontWeight: 600 }}>Weight</th>
                <th style={{ padding: "0.5rem", textAlign: "center", fontWeight: 600 }}>Confidence</th>
                <th style={{ padding: "0.5rem", textAlign: "left", fontWeight: 600 }}>Summary</th>
              </tr>
            </thead>
            <tbody>
              {dimensionOrder.map(([key, dim]) => (
                <tr key={key} style={{ borderBottom: "1px solid #f3f4f6" }}>
                  <td style={{ padding: "0.5rem", fontWeight: 500 }}>{DIMENSION_LABELS[key] || key}</td>
                  <td style={{ padding: "0.5rem", textAlign: "center", fontWeight: 700, color: scoreColor(dim.score) }}>{dim.score.toFixed(1)}</td>
                  <td style={{ padding: "0.5rem", textAlign: "center", color: "#6b7280" }}>{(dim.weight * 100).toFixed(0)}%</td>
                  <td style={{ padding: "0.5rem", textAlign: "center", color: "#6b7280" }}>{dim.confidence}</td>
                  <td style={{ padding: "0.5rem", fontSize: "0.7rem", color: "#4b5563" }}>{cleanText(dim.summary)}</td>
                </tr>
              ))}
              {scoring && (
                <tr style={{ backgroundColor: "#f9fafb", fontWeight: 700 }}>
                  <td style={{ padding: "0.5rem", borderTop: "2px solid #d1d5db" }}>Composite Score</td>
                  <td style={{ padding: "0.5rem", textAlign: "center", borderTop: "2px solid #d1d5db", color: scoreColor(scoring.final_composite) }}>{scoring.final_composite.toFixed(2)}</td>
                  <td colSpan={3} style={{ padding: "0.5rem", borderTop: "2px solid #d1d5db", textAlign: "center", color: "#6b7280", fontSize: "0.7rem" }}>
                    Raw {scoring.raw_composite.toFixed(2)} × {scoring.engagement_multiplier}x multiplier → {scoring.risk_tier}
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      )}

      {/* DIMENSION EVIDENCE DETAILS */}
      {dimensionOrder.length > 0 && (
        <div style={{ marginBottom: "1.5rem" }}>
          <h2 style={sectionHeader("Detailed Evidence by Dimension")}>Detailed Evidence by Dimension</h2>
          {dimensionOrder.map(([key, dim]) => (
            <div key={key} style={{ marginBottom: "1rem" }}>
              <div style={{ display: "flex", alignItems: "center", gap: "0.5rem", marginBottom: "0.375rem" }}>
                <h3 style={{ fontSize: "0.8rem", fontWeight: 600, margin: 0 }}>{DIMENSION_LABELS[key] || key}</h3>
                <span style={{ fontSize: "0.7rem", fontWeight: 700, color: scoreColor(dim.score) }}>{dim.score.toFixed(1)}/10</span>
                <span style={{ fontSize: "0.65rem", color: "#6b7280" }}>{dim.confidence}</span>
              </div>
              {/* Sub-factors */}
              {dim.sub_factors && Object.keys(dim.sub_factors).length > 0 && (
                <div style={{ marginBottom: "0.5rem" }}>
                  {Object.entries(dim.sub_factors).map(([sfKey, sf]) => (
                    <div key={sfKey} style={{ display: "flex", gap: "0.5rem", fontSize: "0.7rem", marginBottom: "0.2rem" }}>
                      <span style={{ fontWeight: 600, color: scoreColor(sf.score), minWidth: "30px" }}>{sf.score}/10</span>
                      <span style={{ color: "#4b5563" }}>{sfKey.replace(/_/g, " ")}: {renderTextWithCitations(sf.detail, sources)}</span>
                    </div>
                  ))}
                </div>
              )}
              {/* Evidence */}
              {dim.evidence.length > 0 && (
                <ul style={{ margin: 0, paddingLeft: "1.25rem", fontSize: "0.7rem", color: "#4b5563" }}>
                  {dim.evidence.map((ev, i) => (
                    <li key={i} style={{ marginBottom: "0.2rem" }}>
                      {renderTextWithCitations(ev.text, sources)}
                      {ev.source && ev.url ? (
                        <a href={ev.url} target="_blank" rel="noopener noreferrer" style={{ color: "#2563eb", textDecoration: "underline", marginLeft: "0.25rem", fontSize: "0.65rem" }}>
                          ({ev.source})
                        </a>
                      ) : ev.source ? (
                        <span style={{ color: "#9ca3af", marginLeft: "0.25rem" }}> ({ev.source})</span>
                      ) : null}
                    </li>
                  ))}
                </ul>
              )}
            </div>
          ))}
        </div>
      )}

      {/* REPUTATIONAL CONTAGION */}
      {rca && (
        <div style={{ marginBottom: "1.5rem" }}>
          <h2 style={sectionHeader("Reputational Contagion Analysis")}>Reputational Contagion Analysis</h2>
          <div style={{ display: "flex", alignItems: "center", gap: "0.75rem", marginBottom: "0.75rem" }}>
            <span style={{ fontSize: "1.25rem", fontWeight: 700, color: scoreColor(rca.composite_rcs) }}>{rca.composite_rcs.toFixed(2)}</span>
            <span style={{ fontSize: "0.75rem", color: "#6b7280" }}>/ 10</span>
            <span style={{ padding: "0.2rem 0.5rem", borderRadius: "4px", fontSize: "0.7rem", fontWeight: 700, ...(() => { const s = getTierStyle(rca.rcs_risk_tier); return { backgroundColor: s.bg, color: s.text }; })() }}>
              {rca.rcs_risk_tier}
            </span>
          </div>
          {rca.rcs_recommendation && (
            <p style={{ fontSize: "0.75rem", color: "#4b5563", marginBottom: "0.75rem" }}>{rca.rcs_recommendation}</p>
          )}
          <table style={{ width: "100%", fontSize: "0.7rem", borderCollapse: "collapse" }}>
            <thead>
              <tr style={{ backgroundColor: "#f9fafb" }}>
                <th style={{ padding: "0.4rem", textAlign: "left", fontWeight: 600 }}>Factor</th>
                <th style={{ padding: "0.4rem", textAlign: "center", fontWeight: 600 }}>Score</th>
                <th style={{ padding: "0.4rem", textAlign: "center", fontWeight: 600 }}>Weight</th>
                <th style={{ padding: "0.4rem", textAlign: "left", fontWeight: 600 }}>Evidence</th>
              </tr>
            </thead>
            <tbody>
              {(Object.keys(RCS_QUESTION_LABELS) as string[]).map(qKey => {
                const q = rca[qKey as keyof ReputationalContagion] as any;
                if (!q || typeof q !== "object" || !("score" in q)) return null;
                return (
                  <tr key={qKey} style={{ borderBottom: "1px solid #f3f4f6" }}>
                    <td style={{ padding: "0.4rem", fontWeight: 500 }}>{RCS_QUESTION_LABELS[qKey]}</td>
                    <td style={{ padding: "0.4rem", textAlign: "center", fontWeight: 700, color: scoreColor(q.score) }}>{q.score.toFixed(1)}</td>
                    <td style={{ padding: "0.4rem", textAlign: "center", color: "#6b7280" }}>{(q.weight * 100).toFixed(0)}%</td>
                    <td style={{ padding: "0.4rem", fontSize: "0.65rem", color: "#4b5563" }}>{renderTextWithCitations(q.evidence, sources)}</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
          {/* Most Damaging Headline */}
          {rca.most_damaging_headline && (
            <div style={{ marginTop: "0.75rem", padding: "0.5rem 0.75rem", borderRadius: "6px", borderLeft: "4px solid #ea580c", backgroundColor: "#fff7ed" }}>
              <p style={{ fontSize: "0.65rem", fontWeight: 700, color: "#ea580c", margin: "0 0 0.2rem", textTransform: "uppercase" }}>Most Damaging Headline</p>
              <p style={{ fontSize: "0.8rem", fontStyle: "italic", fontWeight: 500, color: "#111827", margin: 0 }}>"{rca.most_damaging_headline}"</p>
            </div>
          )}
        </div>
      )}

      {/* FLAGS */}
      {flags && (flags.red.length > 0 || flags.yellow.length > 0) && (
        <div style={{ marginBottom: "1.5rem" }}>
          <h2 style={sectionHeader("Flags")}>Flags</h2>
          {flags.red.length > 0 && (
            <div style={{ marginBottom: "0.75rem" }}>
              <h3 style={{ fontSize: "0.75rem", fontWeight: 700, color: "#dc2626", marginBottom: "0.375rem" }}>Red Flags ({flags.red.length})</h3>
              {flags.red.map((f, i) => (
                <div key={i} style={{ padding: "0.5rem", borderLeft: "3px solid #ef4444", backgroundColor: "#fef2f2", borderRadius: "4px", marginBottom: "0.375rem" }}>
                  <p style={{ fontWeight: 600, fontSize: "0.75rem", margin: "0 0 0.15rem", color: "#111827" }}>{f.title}</p>
                  <p style={{ fontSize: "0.7rem", color: "#374151", margin: 0 }}>{renderTextWithCitations(f.description, sources)}</p>
                  <p style={{ fontSize: "0.6rem", color: "#9ca3af", margin: "0.15rem 0 0" }}>{f.source} · {f.date}</p>
                </div>
              ))}
            </div>
          )}
          {flags.yellow.length > 0 && (
            <div>
              <h3 style={{ fontSize: "0.75rem", fontWeight: 700, color: "#d97706", marginBottom: "0.375rem" }}>Yellow Flags ({flags.yellow.length})</h3>
              {flags.yellow.map((f, i) => (
                <div key={i} style={{ padding: "0.5rem", borderLeft: "3px solid #f59e0b", backgroundColor: "#fffbeb", borderRadius: "4px", marginBottom: "0.375rem" }}>
                  <p style={{ fontWeight: 600, fontSize: "0.75rem", margin: "0 0 0.15rem", color: "#111827" }}>{f.title}</p>
                  <p style={{ fontSize: "0.7rem", color: "#374151", margin: 0 }}>{renderTextWithCitations(f.description, sources)}</p>
                  <p style={{ fontSize: "0.6rem", color: "#9ca3af", margin: "0.15rem 0 0" }}>{f.source} · {f.date}</p>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* KEY EXECUTIVES */}
      {executives && executives.length > 0 && (
        <div style={{ marginBottom: "1.5rem" }}>
          <h2 style={sectionHeader("Key Executives")}>Key Executives ({executives.length})</h2>
          <table style={{ width: "100%", fontSize: "0.7rem", borderCollapse: "collapse" }}>
            <thead>
              <tr style={{ backgroundColor: "#f9fafb" }}>
                <th style={{ padding: "0.4rem", textAlign: "left", fontWeight: 600 }}>Name</th>
                <th style={{ padding: "0.4rem", textAlign: "left", fontWeight: 600 }}>Title</th>
                <th style={{ padding: "0.4rem", textAlign: "center", fontWeight: 600 }}>FEC Total</th>
                <th style={{ padding: "0.4rem", textAlign: "center", fontWeight: 600 }}>News</th>
                <th style={{ padding: "0.4rem", textAlign: "center", fontWeight: 600 }}>Sanctions</th>
              </tr>
            </thead>
            <tbody>
              {executives.map((exec, i) => (
                <tr key={i} style={{ borderBottom: "1px solid #f3f4f6" }}>
                  <td style={{ padding: "0.4rem", fontWeight: 500 }}>{exec.name}</td>
                  <td style={{ padding: "0.4rem", color: "#6b7280" }}>{exec.title && exec.title !== "See Remarks" ? exec.title : (exec.is_officer ? "Officer" : exec.is_director ? "Director" : "")}</td>
                  <td style={{ padding: "0.4rem", textAlign: "center" }}>{formatUSD(exec.fec_total)}</td>
                  <td style={{ padding: "0.4rem", textAlign: "center" }}>{exec.news_count}</td>
                  <td style={{ padding: "0.4rem", textAlign: "center", color: exec.sanctions_flag ? "#dc2626" : "#059669", fontWeight: 600 }}>
                    {exec.sanctions_flag ? "⚠ Yes" : "✓ Clear"}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          {/* Top FEC recipients per exec */}
          {executives.filter(e => e.fec_top_recipients.length > 0).slice(0, 3).map((exec, i) => (
            <div key={i} style={{ marginTop: "0.5rem" }}>
              <p style={{ fontSize: "0.65rem", fontWeight: 600, color: "#6b7280", marginBottom: "0.2rem" }}>{exec.name} — Top Recipients:</p>
              <div style={{ fontSize: "0.65rem", color: "#4b5563" }}>
                {exec.fec_top_recipients.slice(0, 3).map((r, j) => (
                  <span key={j}>{r.name} ({formatUSD(r.total)}){j < Math.min(exec.fec_top_recipients.length, 3) - 1 ? " · " : ""}</span>
                ))}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* GOVERNMENT CONTRACTS */}
      {contracts && (
        <div style={{ marginBottom: "1.5rem" }}>
          <h2 style={sectionHeader("Government Contracts")}>Government Contracts</h2>
          <div style={{ display: "flex", gap: "2rem", marginBottom: "0.75rem" }}>
            <div>
              <p style={{ fontSize: "1.25rem", fontWeight: 700, margin: 0, color: "#111827" }}>{contracts.total_awards}</p>
              <p style={{ fontSize: "0.65rem", color: "#6b7280", margin: 0 }}>Awards</p>
            </div>
            <div>
              <p style={{ fontSize: "1.25rem", fontWeight: 700, margin: 0, color: "#111827" }}>{formatUSD(contracts.total_amount)}</p>
              <p style={{ fontSize: "0.65rem", color: "#6b7280", margin: 0 }}>Total Value</p>
            </div>
            <div>
              <p style={{ fontSize: "1.25rem", fontWeight: 700, margin: 0, color: "#111827" }}>{contracts.agencies_count}</p>
              <p style={{ fontSize: "0.65rem", color: "#6b7280", margin: 0 }}>Agencies</p>
            </div>
          </div>
          {contracts.top_agencies.length > 0 && (
            <table style={{ width: "100%", fontSize: "0.7rem", borderCollapse: "collapse", marginBottom: "0.75rem" }}>
              <thead>
                <tr style={{ backgroundColor: "#f9fafb" }}>
                  <th style={{ padding: "0.4rem", textAlign: "left", fontWeight: 600 }}>Agency</th>
                  <th style={{ padding: "0.4rem", textAlign: "right", fontWeight: 600 }}>Amount</th>
                  <th style={{ padding: "0.4rem", textAlign: "right", fontWeight: 600 }}>Awards</th>
                </tr>
              </thead>
              <tbody>
                {contracts.top_agencies.slice(0, 8).map((a, i) => (
                  <tr key={i} style={{ borderBottom: "1px solid #f3f4f6" }}>
                    <td style={{ padding: "0.4rem" }}>{a.agency}</td>
                    <td style={{ padding: "0.4rem", textAlign: "right" }}>{formatUSD(a.total)}</td>
                    <td style={{ padding: "0.4rem", textAlign: "right" }}>{a.count}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
          {contracts.top_awards.length > 0 && (
            <>
              <p style={{ fontSize: "0.7rem", fontWeight: 600, color: "#6b7280", marginBottom: "0.25rem" }}>Largest Awards:</p>
              <table style={{ width: "100%", fontSize: "0.65rem", borderCollapse: "collapse" }}>
                <thead>
                  <tr style={{ backgroundColor: "#f9fafb" }}>
                    <th style={{ padding: "0.3rem", textAlign: "left", fontWeight: 600 }}>Amount</th>
                    <th style={{ padding: "0.3rem", textAlign: "left", fontWeight: 600 }}>Agency</th>
                    <th style={{ padding: "0.3rem", textAlign: "left", fontWeight: 600 }}>Description</th>
                    <th style={{ padding: "0.3rem", textAlign: "left", fontWeight: 600 }}>Period</th>
                  </tr>
                </thead>
                <tbody>
                  {contracts.top_awards.slice(0, 8).map((aw, i) => (
                    <tr key={i} style={{ borderBottom: "1px solid #f3f4f6" }}>
                      <td style={{ padding: "0.3rem", fontWeight: 600 }}>{formatUSD(aw.award_amount)}</td>
                      <td style={{ padding: "0.3rem" }}>{aw.awarding_sub_agency || aw.awarding_agency}</td>
                      <td style={{ padding: "0.3rem" }}>{aw.description}</td>
                      <td style={{ padding: "0.3rem", whiteSpace: "nowrap" }}>{aw.start_date} — {aw.end_date}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </>
          )}
        </div>
      )}

      {/* SOURCES */}
      {sources && sources.length > 0 && (
        <div style={{ marginBottom: "1.5rem" }}>
          <h2 style={sectionHeader("Research Sources")}>Research Sources ({sources.length})</h2>
          <div style={{ fontSize: "0.65rem", color: "#4b5563" }}>
            {[...sources].sort((a, b) => b.score - a.score).map((src, i) => (
              <p key={i} style={{ margin: "0 0 0.3rem" }}>
                <span style={{ color: "#9ca3af", marginRight: "0.25rem" }}>[{src.id}]</span>
                {src.url ? (
                  <a href={src.url} target="_blank" rel="noopener noreferrer" style={{ color: "#2563eb", textDecoration: "underline" }}>
                    {src.title}
                  </a>
                ) : (
                  src.title
                )}
              </p>
            ))}
          </div>
        </div>
      )}

      {/* PIPELINE METADATA */}
      {result?.metadata && (
        <div style={{ marginBottom: "1rem" }}>
          <h2 style={sectionHeader("Pipeline Metadata")}>Pipeline Metadata</h2>
          <div style={{ fontSize: "0.7rem", color: "#6b7280", display: "grid", gridTemplateColumns: "1fr 1fr", gap: "0.25rem 1rem" }}>
            <p style={{ margin: 0 }}>Version: {result.metadata.pipeline_version}</p>
            <p style={{ margin: 0 }}>Level: {result.metadata.vetting_level}</p>
            <p style={{ margin: 0 }}>Duration: {result.metadata.total_duration_seconds ? `${Math.round(result.metadata.total_duration_seconds)}s` : "N/A"}</p>
            <p style={{ margin: 0 }}>Steps: {result.metadata.steps_completed?.length || 0}</p>
          </div>
        </div>
      )}

      {/* FOOTER */}
      <div style={{ borderTop: "1px solid #e5e7eb", paddingTop: "0.75rem", fontSize: "0.6rem", color: "#9ca3af", textAlign: "center" }}>
        <p style={{ margin: 0 }}>TMG Sentinel Vetting Report · Generated {new Date().toLocaleDateString("en-US", { year: "numeric", month: "long", day: "numeric", timeZone: "America/New_York" })}</p>
        <p style={{ margin: "0.15rem 0 0" }}>CONFIDENTIAL — For internal use only</p>
      </div>
    </div>
  );
}
