import { useNavigate } from "react-router-dom";
import { useVettingStore } from "@/lib/vetting-store";
import { Activity, Clock, CheckCircle, AlertTriangle, Plus } from "lucide-react";
import { VettingCard } from "@/components/VettingCard";
import { useState, useMemo } from "react";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Link } from "react-router-dom";

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
    { 
      label: "Active Vettings", 
      value: active, 
      icon: Activity, 
      color: "text-primary",
      bgColor: "bg-primary/8",
    },
    { 
      label: "Awaiting Decision", 
      value: awaiting, 
      icon: AlertTriangle, 
      color: "text-[hsl(var(--risk-moderate))]",
      bgColor: "bg-[hsl(var(--risk-moderate)/0.08)]",
    },
    { 
      label: "Completed This Month", 
      value: completedMonth, 
      icon: CheckCircle, 
      color: "text-[hsl(var(--risk-low))]",
      bgColor: "bg-[hsl(var(--risk-low)/0.08)]",
    },
    { 
      label: "Avg. Turnaround", 
      value: avgTurnaround, 
      icon: Clock, 
      color: "text-accent",
      bgColor: "bg-accent/8",
    },
  ];

  return (
    <div className="page-container">
      {/* Page Header */}
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-2xl font-bold text-foreground">Active Vettings</h1>
          <p className="text-sm text-muted-foreground mt-1">Monitor ongoing vetting requests and review results</p>
        </div>
        <Link to="/submit">
          <Button className="gap-2">
            <Plus className="w-4 h-4" />
            New Vetting
          </Button>
        </Link>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        {stats.map((s) => (
          <div key={s.label} className="glass-card p-5 group">
            <div className="flex items-start justify-between mb-3">
              <div className={`p-2.5 rounded-xl ${s.bgColor}`}>
                <s.icon className={`w-5 h-5 ${s.color}`} />
              </div>
            </div>
            <p className={`text-3xl font-bold ${s.color}`}>{s.value}</p>
            <p className="text-sm text-muted-foreground font-medium mt-1">{s.label}</p>
          </div>
        ))}
      </div>

      {/* Filters */}
      <div className="flex flex-col sm:flex-row gap-3 mb-6">
        <div className="relative flex-1 max-w-sm">
          <Input
            placeholder="Search by subject name..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="bg-card pl-4"
          />
        </div>
        <Select value={statusFilter} onValueChange={setStatusFilter}>
          <SelectTrigger className="w-[160px] bg-card"><SelectValue placeholder="Status" /></SelectTrigger>
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
          <SelectTrigger className="w-[180px] bg-card"><SelectValue placeholder="Sort" /></SelectTrigger>
          <SelectContent>
            <SelectItem value="recent">Most Recent</SelectItem>
            <SelectItem value="risk">Highest Risk</SelectItem>
            <SelectItem value="oldest">Oldest First</SelectItem>
            <SelectItem value="awaiting">Awaiting Decision</SelectItem>
          </SelectContent>
        </Select>
      </div>

      {/* Vetting Cards */}
      <div className="space-y-3">
        {filtered.map((v) => (
          <VettingCard key={v.id} vetting={v} onClick={() => navigate(`/vetting/${v.id}`)} />
        ))}
        {filtered.length === 0 && (
          <div className="glass-card p-16 text-center">
            <p className="text-muted-foreground text-lg">No vetting requests found.</p>
            <Link to="/submit">
              <Button className="mt-4 gap-2">
                <Plus className="w-4 h-4" />
                Submit New Vetting
              </Button>
            </Link>
          </div>
        )}
      </div>
    </div>
  );
}
