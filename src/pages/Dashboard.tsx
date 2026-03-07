import { useNavigate } from "react-router-dom";
import { useVettingStore } from "@/lib/vetting-store";
import { Activity, Clock, CheckCircle, AlertTriangle } from "lucide-react";
import { VettingCard } from "@/components/VettingCard";
import { useState, useMemo } from "react";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";

export default function Dashboard() {
  const { vettings } = useVettingStore();
  const navigate = useNavigate();
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState<string>("all");
  const [sortBy, setSortBy] = useState<string>("recent");

  const active = vettings.filter((v) => v.status === "running" || v.status === "pending").length;
  const awaiting = vettings.filter((v) => v.status === "completed" && !v.decision).length;
  const completedMonth = vettings.filter((v) => {
    if (!v.completed_at) return false;
    const d = new Date(v.completed_at);
    const now = new Date();
    return d.getMonth() === now.getMonth() && d.getFullYear() === now.getFullYear();
  }).length;

  const avgTurnaround = useMemo(() => {
    const completed = vettings.filter((v) => v.completed_at && v.requested_at);
    if (!completed.length) return "—";
    const avg = completed.reduce((sum, v) => {
      return sum + (new Date(v.completed_at!).getTime() - new Date(v.requested_at).getTime());
    }, 0) / completed.length;
    const mins = Math.round(avg / 60000);
    return mins < 60 ? `${mins}m` : `${Math.round(mins / 60)}h ${mins % 60}m`;
  }, [vettings]);

  const filtered = useMemo(() => {
    let result = [...vettings];
    if (search) result = result.filter((v) => v.subject_name.toLowerCase().includes(search.toLowerCase()));
    if (statusFilter !== "all") result = result.filter((v) => v.status === statusFilter);
    switch (sortBy) {
      case "recent": result.sort((a, b) => new Date(b.requested_at).getTime() - new Date(a.requested_at).getTime()); break;
      case "risk": result.sort((a, b) => (b.composite_score ?? -1) - (a.composite_score ?? -1)); break;
      case "oldest": result.sort((a, b) => new Date(a.requested_at).getTime() - new Date(b.requested_at).getTime()); break;
      case "awaiting": result.sort((a, b) => {
        const aWait = a.status === "completed" && !a.decision ? 1 : 0;
        const bWait = b.status === "completed" && !b.decision ? 1 : 0;
        return bWait - aWait;
      }); break;
    }
    return result;
  }, [vettings, search, statusFilter, sortBy]);

  const stats = [
    { label: "Active Vettings", value: active, icon: Activity, accent: "text-[hsl(var(--status-running))]" },
    { label: "Awaiting Decision", value: awaiting, icon: AlertTriangle, accent: "text-[hsl(var(--risk-moderate))]" },
    { label: "Completed This Month", value: completedMonth, icon: CheckCircle, accent: "text-[hsl(var(--risk-low))]" },
    { label: "Avg. Turnaround", value: avgTurnaround, icon: Clock, accent: "text-muted-foreground" },
  ];

  return (
    <div className="page-container">
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-foreground">Active Vettings</h1>
        <p className="text-sm text-muted-foreground mt-1">Monitor ongoing vetting requests and review results</p>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        {stats.map((s) => (
          <div key={s.label} className="glass-card p-4">
            <div className="flex items-center justify-between mb-2">
              <span className="text-xs font-medium text-muted-foreground uppercase tracking-wider">{s.label}</span>
              <s.icon className={`w-4 h-4 ${s.accent}`} />
            </div>
            <div className="text-2xl font-bold text-foreground">{s.value}</div>
          </div>
        ))}
      </div>

      <div className="flex flex-col sm:flex-row gap-3 mb-6">
        <Input
          placeholder="Search by subject name..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="max-w-xs"
        />
        <Select value={statusFilter} onValueChange={setStatusFilter}>
          <SelectTrigger className="w-[160px]"><SelectValue placeholder="Status" /></SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Statuses</SelectItem>
            <SelectItem value="pending">Pending</SelectItem>
            <SelectItem value="running">Running</SelectItem>
            <SelectItem value="completed">Completed</SelectItem>
            <SelectItem value="gates_failed">Gates Failed</SelectItem>
            <SelectItem value="error">Error</SelectItem>
          </SelectContent>
        </Select>
        <Select value={sortBy} onValueChange={setSortBy}>
          <SelectTrigger className="w-[160px]"><SelectValue placeholder="Sort" /></SelectTrigger>
          <SelectContent>
            <SelectItem value="recent">Most Recent</SelectItem>
            <SelectItem value="risk">Highest Risk</SelectItem>
            <SelectItem value="oldest">Oldest First</SelectItem>
            <SelectItem value="awaiting">Awaiting Decision</SelectItem>
          </SelectContent>
        </Select>
      </div>

      <div className="space-y-3">
        {filtered.map((v) => (
          <VettingCard key={v.id} vetting={v} onClick={() => navigate(`/vetting/${v.id}`)} />
        ))}
        {filtered.length === 0 && (
          <div className="glass-card p-12 text-center text-muted-foreground">
            No vetting requests found.
          </div>
        )}
      </div>
    </div>
  );
}
