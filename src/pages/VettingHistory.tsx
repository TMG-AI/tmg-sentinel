import { useVettingStore } from "@/lib/vetting-store";
import { useNavigate } from "react-router-dom";
import { ENGAGEMENT_LABELS, VETTING_LEVEL_LABELS } from "@/lib/types";
import { getRiskTierColor, getDecisionColor, getDecisionLabel, formatDate } from "@/lib/vetting-utils";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Input } from "@/components/ui/input";
import { useState, useMemo } from "react";

export default function VettingHistory() {
  const { vettings } = useVettingStore();
  const navigate = useNavigate();
  const [search, setSearch] = useState("");

  const filtered = useMemo(() => {
    if (!search) return vettings;
    const q = search.toLowerCase();
    return vettings.filter((v) =>
      v.subject_name.toLowerCase().includes(q) ||
      v.requested_by.toLowerCase().includes(q) ||
      (v.decision_notes && v.decision_notes.toLowerCase().includes(q))
    );
  }, [vettings, search]);

  return (
    <div className="page-container">
      <div className="flex items-center justify-between mb-6 flex-wrap gap-4">
        <div>
          <h1 className="text-2xl font-bold text-foreground">Vetting History</h1>
          <p className="text-sm text-muted-foreground mt-1">Complete record of all vetting requests</p>
        </div>
        <Input placeholder="Search..." value={search} onChange={(e) => setSearch(e.target.value)} className="max-w-xs" />
      </div>

      <div className="glass-card overflow-hidden">
        <div className="overflow-x-auto">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Subject</TableHead>
                <TableHead>Type</TableHead>
                <TableHead>Engagement</TableHead>
                <TableHead>Level</TableHead>
                <TableHead>Score</TableHead>
                <TableHead>Risk</TableHead>
                <TableHead>Decision</TableHead>
                <TableHead>Requested By</TableHead>
                <TableHead>Date</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {filtered.map((v) => (
                <TableRow key={v.id} className="cursor-pointer hover:bg-muted/50" onClick={() => navigate(`/vetting/${v.id}`)}>
                  <TableCell className="font-medium text-foreground">{v.subject_name}</TableCell>
                  <TableCell className="text-xs capitalize text-muted-foreground">{v.subject_type}</TableCell>
                  <TableCell className="text-xs text-muted-foreground">{ENGAGEMENT_LABELS[v.engagement_type].split(" ").slice(0, 2).join(" ")}</TableCell>
                  <TableCell className="text-xs text-muted-foreground">{VETTING_LEVEL_LABELS[v.vetting_level].title}</TableCell>
                  <TableCell className="font-mono text-sm">{v.composite_score != null ? v.composite_score.toFixed(1) : "—"}</TableCell>
                  <TableCell>
                    {v.risk_tier ? (
                      <span className={`text-xs font-bold px-2 py-0.5 rounded ${getRiskTierColor(v.risk_tier)}`}>{v.risk_tier}</span>
                    ) : "—"}
                  </TableCell>
                  <TableCell>
                    {v.decision ? (
                      <span className={`text-xs font-medium px-2 py-0.5 rounded ${getDecisionColor(v.decision)}`}>{getDecisionLabel(v.decision)}</span>
                    ) : "—"}
                  </TableCell>
                  <TableCell className="text-xs text-muted-foreground">{v.requested_by}</TableCell>
                  <TableCell className="text-xs text-muted-foreground">{formatDate(v.requested_at)}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>
      </div>
    </div>
  );
}
